"""Escrituras del Centro Estratégico — delega a servicios canónicos sin tablas paralelas."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import User
from app.opportunity_models import Opportunity
from app.permissions import user_permissions
from app.services import evaluacion_service as eval_svc
from app.services import proactive_service as opp_svc
from app.services import transformacion_service as trans_svc
from app.transformacion_models import DossierEmpresarial


def _has(permissions: set[str], code: str) -> bool:
    return code in permissions


def _dossier_write_context(db: Session, org_id: str) -> dict[str, Any]:
    """Dossier canónico — crea si no existe en flujos de escritura."""
    dossier = trans_svc.get_or_create_dossier(db, org_id)
    return {
        "dossier_id": dossier.id,
        "correlation_id": dossier.correlation_id,
        "expediente_id": dossier.expediente_activo_id,
        "organization_id": org_id,
    }


def _audit_decision(
    db: Session,
    *,
    action: str,
    org_id: str,
    user: User,
    ctx: dict[str, Any],
    objeto_tipo: str,
    objeto_id: str | None,
    valor_anterior: Any,
    valor_nuevo: Any,
    motivo: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    detail = {
        "empresa": org_id,
        "dossier_id": ctx.get("dossier_id"),
        "correlation_id": ctx.get("correlation_id"),
        "expediente_id": ctx.get("expediente_id"),
        "objeto_tipo": objeto_tipo,
        "objeto_id": objeto_id,
        "valor_anterior": valor_anterior,
        "valor_nuevo": valor_nuevo,
        "motivo": motivo,
        **(extra or {}),
    }
    write_audit(
        db,
        action=f"strategic_control.{action}",
        organization_id=org_id,
        user_id=user.id,
        detail=json.dumps(detail, ensure_ascii=False, default=str),
        commit=False,
    )


def count_dossiers(db: Session, org_id: str) -> int:
    return db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == org_id).count()


def registrar_necesidad(
    db: Session,
    user: User,
    org_id: str,
    *,
    titulo: str,
    necesidad: str,
    objetivo: str | None = None,
    entidad_nombre: str | None = None,
) -> dict[str, Any]:
    permissions = user_permissions(user, db)
    if not _has(permissions, "transformacion.manage"):
        raise HTTPException(status_code=403, detail="Requiere transformacion.manage")
    antes_count = count_dossiers(db, org_id)
    result = trans_svc.registrar_necesidad(
        db,
        org_id,
        user.id,
        titulo=titulo,
        necesidad=necesidad,
        objetivo=objetivo,
        entidad_nombre=entidad_nombre,
    )
    ctx = _dossier_write_context(db, org_id)
    _audit_decision(
        db,
        action="registrar_necesidad",
        org_id=org_id,
        user=user,
        ctx=ctx,
        objeto_tipo="dossier",
        objeto_id=ctx["dossier_id"],
        valor_anterior={"dossier_count": antes_count},
        valor_nuevo={"dossier_id": ctx["dossier_id"], "expediente_id": ctx["expediente_id"]},
        motivo=necesidad[:200],
    )
    return {
        "dossier_id": ctx["dossier_id"],
        "expediente_id": ctx["expediente_id"],
        "dossier_count": count_dossiers(db, org_id),
        "resultado": result,
    }


def preparar_publicacion(
    db: Session,
    user: User,
    org_id: str,
    *,
    hallazgo_id: str,
    visible_entidad: bool,
    motivo: str | None = None,
) -> dict[str, Any]:
    permissions = user_permissions(user, db)
    if not _has(permissions, "evaluacion.visibility"):
        raise HTTPException(status_code=403, detail="Requiere evaluacion.visibility")
    ctx = _dossier_write_context(db, org_id)
    exp_id = ctx.get("expediente_id")
    if not exp_id:
        raise HTTPException(status_code=400, detail="Sin expediente activo en dossier")
    hallazgo = eval_svc.set_visibilidad(
        db,
        exp_id,
        org_id,
        objeto_tipo="hallazgo",
        objeto_id=hallazgo_id,
        visible_entidad=visible_entidad,
        user_id=user.id,
    )
    _audit_decision(
        db,
        action="preparar_publicacion",
        org_id=org_id,
        user=user,
        ctx=ctx,
        objeto_tipo="hallazgo",
        objeto_id=hallazgo_id,
        valor_anterior=not visible_entidad,
        valor_nuevo=visible_entidad,
        motivo=motivo,
        extra={"autoridad": "evaluacion.visibility"},
    )
    return {"hallazgo": hallazgo, "dossier_id": ctx["dossier_id"], "publicacion_autoridad": "evaluacion.visibility"}


def actualizar_supuesto(
    db: Session,
    user: User,
    org_id: str,
    *,
    item_id: str,
    respuesta: str,
    motivo: str | None = None,
) -> dict[str, Any]:
    permissions = user_permissions(user, db)
    if not _has(permissions, "evaluacion.manage"):
        raise HTTPException(status_code=403, detail="Requiere evaluacion.manage")
    ctx = _dossier_write_context(db, org_id)
    exp_id = ctx.get("expediente_id")
    if not exp_id:
        raise HTTPException(status_code=400, detail="Sin expediente activo en dossier")
    from app.evaluacion_models import EvaluacionInformacionItem

    prev_item = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.id == item_id, EvaluacionInformacionItem.expediente_id == exp_id)
        .first()
    )
    valor_anterior = prev_item.respuesta if prev_item else None
    item = eval_svc.update_informacion_item(
        db, exp_id, org_id, item_id, respuesta=respuesta,
    )
    _audit_decision(
        db,
        action="actualizar_supuesto",
        org_id=org_id,
        user=user,
        ctx=ctx,
        objeto_tipo="informacion",
        objeto_id=item_id,
        valor_anterior=valor_anterior,
        valor_nuevo=respuesta,
        motivo=motivo,
    )
    return {"item_id": item.id, "dossier_id": ctx["dossier_id"], "campo": item.campo}


def priorizar_oportunidades(db: Session, user: User, org_id: str) -> dict[str, Any]:
    permissions = user_permissions(user, db)
    if not _has(permissions, "oportunidades.evaluate"):
        raise HTTPException(status_code=403, detail="Requiere oportunidades.evaluate")
    ctx = _dossier_write_context(db, org_id)
    result = opp_svc.prioritize_opportunities_global(db, org_id)
    _audit_decision(
        db,
        action="priorizar_oportunidades",
        org_id=org_id,
        user=user,
        ctx=ctx,
        objeto_tipo="oportunidades",
        objeto_id=None,
        valor_anterior=None,
        valor_nuevo=result.get("por_que_primero"),
        motivo="Priorización global desde Centro Estratégico",
        extra={"total": result.get("total")},
    )
    return {"dossier_id": ctx["dossier_id"], "priorizacion": result}


def registrar_decision_oportunidad(
    db: Session,
    user: User,
    org_id: str,
    *,
    opportunity_id: str,
    aprobado: bool,
    motivo: str | None = None,
) -> dict[str, Any]:
    permissions = user_permissions(user, db)
    if not _has(permissions, "oportunidades.approve"):
        raise HTTPException(status_code=403, detail="Requiere oportunidades.approve")
    ctx = _dossier_write_context(db, org_id)
    opp = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.organization_id == org_id,
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    estado_anterior = opp.estado
    try:
        opp_svc.approve_opportunity(db, opp, user_id=user.id, aprobado=aprobado, motivo=motivo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit_decision(
        db,
        action="registrar_decision",
        org_id=org_id,
        user=user,
        ctx=ctx,
        objeto_tipo="oportunidad",
        objeto_id=opportunity_id,
        valor_anterior=estado_anterior,
        valor_nuevo=opp.estado,
        motivo=motivo,
    )
    return {"oportunidad_id": opportunity_id, "estado": opp.estado, "dossier_id": ctx["dossier_id"]}
