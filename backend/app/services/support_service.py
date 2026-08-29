"""Servicio — Mesa de Ayuda y Soporte (MB-12)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.notifications import emit_event
from app.support_enums import ESTADOS_ABIERTOS, ESTADOS_CASO, SLA_ESTADOS, TIPOS_CASO
from app.support_models import (
    SupportAutoDedup,
    SupportCase,
    SupportCaseComment,
    SupportCaseHistory,
    SupportSlaPolicy,
)

DEDUP_WINDOW_HOURS = 4
_SECRET_PATTERNS = re.compile(
    r"(password|contraseña|api[_-]?key|token|secret|bearer)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def sanitize_text(text: str) -> str:
    """Elimina patrones de secretos del texto visible."""
    return _SECRET_PATTERNS.sub("[dato sensible omitido]", text or "")


def _next_case_number(db: Session, org_id: str) -> int:
    current = (
        db.query(func.max(SupportCase.numero))
        .filter(SupportCase.organization_id == org_id)
        .scalar()
    )
    return int(current or 0) + 1


def _find_sla_policy(db: Session, org_id: str, prioridad: str) -> SupportSlaPolicy | None:
    return (
        db.query(SupportSlaPolicy)
        .filter(
            SupportSlaPolicy.organization_id == org_id,
            SupportSlaPolicy.prioridad == prioridad,
            SupportSlaPolicy.is_active.is_(True),
        )
        .order_by(SupportSlaPolicy.created_at.desc())
        .first()
    )


def _apply_sla_limits(case: SupportCase, policy: SupportSlaPolicy | None, now: datetime) -> None:
    if not policy:
        case.fecha_limite = None
        case.primera_respuesta_limite = None
        case.resolucion_limite = None
        return
    if policy.minutos_primera_respuesta:
        case.primera_respuesta_limite = now + timedelta(minutes=policy.minutos_primera_respuesta)
    if policy.minutos_resolucion:
        case.resolucion_limite = now + timedelta(minutes=policy.minutos_resolucion)
        case.fecha_limite = case.resolucion_limite
    case.sla_policy_id = policy.id


def compute_sla_estado(case: SupportCase, now: datetime | None = None) -> str:
    now = _as_utc(now or _utcnow())
    if case.estado in ("CERRADO", "CANCELADO", "RESUELTO"):
        return "NO_APLICA"
    limite = case.resolucion_limite or case.fecha_limite
    if not limite:
        return "NO_APLICA"
    limite = _as_utc(limite)
    if now > limite:
        return "VENCIDO"
    if now > limite - timedelta(minutes=60):
        return "PROXIMO"
    return "DENTRO"


def _record_history(
    db: Session,
    *,
    org_id: str,
    case_id: str,
    accion: str,
    user_id: str | None,
    detalle: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> None:
    db.add(
        SupportCaseHistory(
            organization_id=org_id,
            case_id=case_id,
            accion=accion,
            usuario_id=user_id,
            detalle_json=json.dumps(detalle, ensure_ascii=False) if detalle else None,
            correlation_id=correlation_id,
        )
    )


def _notify(
    db: Session,
    *,
    event_type: str,
    org_id: str,
    case: SupportCase,
    title: str,
    message: str,
    recipient_user_id: str | None = None,
) -> None:
    emit_event(
        event_type,
        org_id,
        source_type="support_case",
        source_id=case.id,
        payload={
            "title": title,
            "message": sanitize_text(message),
            "recipient_user_id": recipient_user_id,
            "notification_type": "WARNING" if "SLA" in event_type else "INFO",
            "correlation_id": case.correlation_id,
            "case_id": case.id,
            "case_numero": case.numero,
        },
        db=db,
    )


def case_to_dict(case: SupportCase, *, include_description: bool = True) -> dict[str, Any]:
    return {
        "id": case.id,
        "organization_id": case.organization_id,
        "numero": case.numero,
        "referencia": f"SUP-{case.numero:05d}",
        "tipo": case.tipo,
        "categoria": case.categoria,
        "asunto": case.asunto,
        "descripcion": sanitize_text(case.descripcion) if include_description else None,
        "prioridad": case.prioridad,
        "impacto": case.impacto,
        "urgencia": case.urgencia,
        "estado": case.estado,
        "solicitante_id": case.solicitante_id,
        "responsable_id": case.responsable_id,
        "grupo": case.grupo,
        "modulo_relacionado": case.modulo_relacionado,
        "entidad_relacionada": case.entidad_relacionada,
        "correlation_id": case.correlation_id,
        "origen": case.origen,
        "origen_tipo": case.origen_tipo,
        "resolucion": sanitize_text(case.resolucion) if case.resolucion else None,
        "sla_estado": compute_sla_estado(case),
        "primera_respuesta_limite": case.primera_respuesta_limite,
        "resolucion_limite": case.resolucion_limite,
        "fecha_limite": case.fecha_limite,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "resuelto_at": case.resuelto_at,
        "cerrado_at": case.cerrado_at,
    }


def get_case(db: Session, org_id: str, case_id: str) -> SupportCase | None:
    return (
        db.query(SupportCase)
        .filter(SupportCase.id == case_id, SupportCase.organization_id == org_id)
        .first()
    )


def list_cases(
    db: Session,
    org_id: str,
    *,
    user: User,
    can_view_all: bool,
    estado: str | None = None,
    tipo: str | None = None,
    prioridad: str | None = None,
    sla_estado: str | None = None,
    q: str | None = None,
    solo_mios: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = db.query(SupportCase).filter(SupportCase.organization_id == org_id)
    if not can_view_all or solo_mios:
        query = query.filter(
            (SupportCase.solicitante_id == user.id) | (SupportCase.responsable_id == user.id)
        )
    if estado:
        query = query.filter(SupportCase.estado == estado.upper())
    if tipo:
        query = query.filter(SupportCase.tipo == tipo.upper())
    if prioridad:
        query = query.filter(SupportCase.prioridad == prioridad.upper())
    if q:
        like = f"%{q}%"
        query = query.filter(
            (SupportCase.asunto.ilike(like)) | (SupportCase.descripcion.ilike(like))
        )
    rows = query.order_by(SupportCase.created_at.desc()).limit(min(limit, 500)).all()
    items = [case_to_dict(r) for r in rows]
    if sla_estado:
        items = [i for i in items if i.get("sla_estado") == sla_estado.upper()]
    return items


def create_case_manual(
    db: Session,
    org_id: str,
    user: User,
    data: dict[str, Any],
) -> dict[str, Any]:
    tipo = (data.get("tipo") or "SOLICITUD").upper()
    if tipo not in TIPOS_CASO:
        raise ValueError(f"Tipo de caso no válido: {tipo}")
    now = _utcnow()
    policy = _find_sla_policy(db, org_id, (data.get("prioridad") or "MEDIA").upper())
    case = SupportCase(
        organization_id=org_id,
        numero=_next_case_number(db, org_id),
        tipo=tipo,
        categoria=data.get("categoria"),
        asunto=sanitize_text(data["asunto"]),
        descripcion=sanitize_text(data["descripcion"]),
        prioridad=(data.get("prioridad") or "MEDIA").upper(),
        impacto=(data.get("impacto") or "MEDIO").upper(),
        urgencia=(data.get("urgencia") or "MEDIA").upper(),
        estado="NUEVO",
        solicitante_id=user.id,
        modulo_relacionado=data.get("modulo_relacionado"),
        entidad_relacionada=data.get("entidad_relacionada"),
        correlation_id=data.get("correlation_id"),
        evidencia_ref=data.get("evidencia_ref"),
        grupo=data.get("grupo"),
        origen="MANUAL",
    )
    _apply_sla_limits(case, policy, now)
    db.add(case)
    db.flush()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CREACION",
        user_id=user.id,
        detalle={"origen": "MANUAL", "tipo": tipo},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def _dedup_key(org_id: str, origen_tipo: str, origen_id: str) -> str:
    raw = f"{org_id}|{origen_tipo}|{origen_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_case_auto(
    db: Session,
    org_id: str,
    data: dict[str, Any],
    *,
    actor_id: str | None = None,
) -> dict[str, Any]:
    origen_tipo = data["origen_tipo"]
    origen_id = data["origen_id"]
    key = _dedup_key(org_id, origen_tipo, origen_id)
    now = _utcnow()
    existing = (
        db.query(SupportAutoDedup)
        .filter(
            SupportAutoDedup.organization_id == org_id,
            SupportAutoDedup.dedup_key == key,
            SupportAutoDedup.ventana_fin >= now,
        )
        .first()
    )
    if existing:
        case = get_case(db, org_id, existing.case_id)
        if case:
            return {**case_to_dict(case), "deduplicado": True}

    solicitante_id = data.get("solicitante_id")
    if not solicitante_id:
        admin = (
            db.query(User)
            .filter(User.organization_id == org_id, User.role == "admin", User.is_active.is_(True))
            .first()
        )
        solicitante_id = admin.id if admin else actor_id
    if not solicitante_id:
        raise ValueError("No se pudo determinar solicitante para caso automático.")

    policy = _find_sla_policy(db, org_id, (data.get("prioridad") or "MEDIA").upper())
    case = SupportCase(
        organization_id=org_id,
        numero=_next_case_number(db, org_id),
        tipo=(data.get("tipo") or "INCIDENTE").upper(),
        asunto=sanitize_text(data["asunto"]),
        descripcion=sanitize_text(data["descripcion"]),
        prioridad=(data.get("prioridad") or "MEDIA").upper(),
        impacto=(data.get("impacto") or "MEDIO").upper(),
        urgencia=(data.get("urgencia") or "MEDIA").upper(),
        estado="NUEVO",
        solicitante_id=solicitante_id,
        modulo_relacionado=data.get("modulo_relacionado"),
        entidad_relacionada=data.get("entidad_relacionada"),
        correlation_id=data.get("correlation_id"),
        origen="AUTOMATICO",
        origen_tipo=origen_tipo,
        origen_id=origen_id,
    )
    _apply_sla_limits(case, policy, now)
    db.add(case)
    db.flush()
    db.add(
        SupportAutoDedup(
            organization_id=org_id,
            dedup_key=key,
            case_id=case.id,
            origen_tipo=origen_tipo,
            origen_id=origen_id,
            ventana_fin=now + timedelta(hours=DEDUP_WINDOW_HOURS),
        )
    )
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CREACION",
        user_id=actor_id,
        detalle={"origen": "AUTOMATICO", "origen_tipo": origen_tipo, "origen_id": origen_id},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def assign_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    responsable_id: str | None,
    grupo: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    case.responsable_id = responsable_id
    if grupo is not None:
        case.grupo = grupo
    if case.estado == "NUEVO":
        case.estado = "ASIGNADO"
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="ASIGNACION",
        user_id=user.id,
        detalle={"responsable_id": responsable_id, "grupo": grupo},
        correlation_id=case.correlation_id,
    )
    db.commit()
    if responsable_id:
        _notify(
            db,
            event_type="SUPPORT_CASE_ASSIGNED",
            org_id=org_id,
            case=case,
            title=f"Caso {case.numero} asignado",
            message=f"Se le asignó el caso: {case.asunto}",
            recipient_user_id=responsable_id,
        )
        db.commit()
    db.refresh(case)
    return case_to_dict(case)


def update_status(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    estado: str,
    nota: str | None = None,
) -> dict[str, Any]:
    estado = estado.upper()
    if estado not in ESTADOS_CASO:
        raise ValueError(f"Estado no válido: {estado}")
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    prev = case.estado
    case.estado = estado
    case.updated_at = _utcnow()
    if estado == "RESUELTO":
        case.resuelto_at = _utcnow()
    if estado in ("CERRADO", "CANCELADO"):
        case.cerrado_at = _utcnow()
    if not case.primera_respuesta_at and estado in ("EN_PROCESO", "PENDIENTE_USUARIO", "RESUELTO"):
        case.primera_respuesta_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CAMBIO_ESTADO",
        user_id=user.id,
        detalle={"de": prev, "a": estado, "nota": sanitize_text(nota) if nota else None},
        correlation_id=case.correlation_id,
    )
    _notify(
        db,
        event_type="SUPPORT_CASE_STATUS",
        org_id=org_id,
        case=case,
        title=f"Caso {case.numero}: {estado}",
        message=nota or f"El caso cambió de {prev} a {estado}.",
        recipient_user_id=case.solicitante_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def resolve_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    resolucion: str,
    cerrar: bool = False,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    case.resolucion = sanitize_text(resolucion)
    case.estado = "CERRADO" if cerrar else "RESUELTO"
    case.resuelto_at = _utcnow()
    if cerrar:
        case.cerrado_at = _utcnow()
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="RESOLUCION",
        user_id=user.id,
        detalle={"resolucion": case.resolucion, "cerrar": cerrar},
        correlation_id=case.correlation_id,
    )
    _notify(
        db,
        event_type="SUPPORT_CASE_RESOLVED",
        org_id=org_id,
        case=case,
        title=f"Caso {case.numero} resuelto",
        message=case.resolucion or "Su caso fue resuelto.",
        recipient_user_id=case.solicitante_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def close_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    nota: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    case.estado = "CERRADO"
    case.cerrado_at = _utcnow()
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CIERRE",
        user_id=user.id,
        detalle={"nota": sanitize_text(nota) if nota else None},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def add_comment(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    cuerpo: str,
    es_interno: bool = False,
    evidencia_ref: str | None = None,
    can_view_internal: bool = False,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    if es_interno and not can_view_internal:
        raise PermissionError("No puede crear comentarios internos.")
    comment = SupportCaseComment(
        organization_id=org_id,
        case_id=case_id,
        usuario_id=user.id,
        cuerpo=sanitize_text(cuerpo),
        es_interno=es_interno,
        evidencia_ref=evidencia_ref,
    )
    db.add(comment)
    if not case.primera_respuesta_at and user.id != case.solicitante_id:
        case.primera_respuesta_at = _utcnow()
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="COMENTARIO",
        user_id=user.id,
        detalle={"es_interno": es_interno},
        correlation_id=case.correlation_id,
    )
    recipient = case.responsable_id if user.id == case.solicitante_id else case.solicitante_id
    if recipient and not es_interno:
        _notify(
            db,
            event_type="SUPPORT_CASE_COMMENT",
            org_id=org_id,
            case=case,
            title=f"Nuevo comentario en caso {case.numero}",
            message=cuerpo[:200],
            recipient_user_id=recipient,
        )
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "usuario_id": comment.usuario_id,
        "cuerpo": comment.cuerpo,
        "es_interno": comment.es_interno,
        "evidencia_ref": comment.evidencia_ref,
        "created_at": comment.created_at,
    }


def get_case_detail(
    db: Session,
    org_id: str,
    case_id: str,
    *,
    can_view_internal: bool,
) -> dict[str, Any] | None:
    case = get_case(db, org_id, case_id)
    if not case:
        return None
    hist = (
        db.query(SupportCaseHistory)
        .filter(SupportCaseHistory.case_id == case_id)
        .order_by(SupportCaseHistory.created_at.asc())
        .all()
    )
    comments_q = db.query(SupportCaseComment).filter(SupportCaseComment.case_id == case_id)
    if not can_view_internal:
        comments_q = comments_q.filter(SupportCaseComment.es_interno.is_(False))
    comments = comments_q.order_by(SupportCaseComment.created_at.asc()).all()
    detail = case_to_dict(case)
    detail["historial"] = [
        {
            "id": h.id,
            "accion": h.accion,
            "usuario_id": h.usuario_id,
            "detalle": json.loads(h.detalle_json) if h.detalle_json else None,
            "correlation_id": h.correlation_id,
            "created_at": h.created_at,
        }
        for h in hist
    ]
    detail["comentarios"] = [
        {
            "id": c.id,
            "usuario_id": c.usuario_id,
            "cuerpo": c.cuerpo,
            "es_interno": c.es_interno,
            "evidencia_ref": c.evidencia_ref,
            "created_at": c.created_at,
        }
        for c in comments
    ]
    return detail


def create_sla_policy(db: Session, org_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = SupportSlaPolicy(
        organization_id=org_id,
        nombre=data["nombre"],
        prioridad=(data.get("prioridad") or "MEDIA").upper(),
        minutos_primera_respuesta=data.get("minutos_primera_respuesta"),
        minutos_resolucion=data.get("minutos_resolucion"),
        horario_servicio_json=json.dumps(data["horario_servicio_json"]) if data.get("horario_servicio_json") else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "nombre": row.nombre,
        "prioridad": row.prioridad,
        "minutos_primera_respuesta": row.minutos_primera_respuesta,
        "minutos_resolucion": row.minutos_resolucion,
    }


def contrato_mi_trabajo(db: Session, org_id: str, user_id: str) -> dict[str, Any]:
    base = db.query(SupportCase).filter(
        SupportCase.organization_id == org_id,
        SupportCase.responsable_id == user_id,
        SupportCase.estado.in_(list(ESTADOS_ABIERTOS)),
    )
    asignados = base.count()
    vencidos = sum(1 for c in base.all() if compute_sla_estado(c) == "VENCIDO")
    accion = base.filter(SupportCase.estado.in_(["NUEVO", "ASIGNADO", "PENDIENTE_USUARIO"])).count()
    return {
        "casos_asignados": asignados,
        "casos_vencidos": vencidos,
        "casos_accion_requerida": accion,
        "endpoint": "/api/soporte/contrato/mi-trabajo",
    }


def contrato_centro_control(db: Session, org_id: str) -> dict[str, Any]:
    abiertos_q = db.query(SupportCase).filter(
        SupportCase.organization_id == org_id,
        SupportCase.estado.in_(list(ESTADOS_ABIERTOS)),
    )
    abiertos = abiertos_q.all()
    criticos = sum(1 for c in abiertos if c.prioridad in ("CRITICA", "ALTA"))
    vencidos = sum(1 for c in abiertos if compute_sla_estado(c) == "VENCIDO")
    categorias: dict[str, int] = {}
    for c in abiertos:
        cat = c.categoria or c.tipo
        categorias[cat] = categorias.get(cat, 0) + 1
    top_cats = sorted(categorias.items(), key=lambda x: -x[1])[:5]
    resueltos = (
        db.query(SupportCase)
        .filter(SupportCase.organization_id == org_id, SupportCase.resuelto_at.isnot(None))
        .order_by(SupportCase.resuelto_at.desc())
        .limit(50)
        .all()
    )
    tmr: list[float] = []
    tmo: list[float] = []
    for c in resueltos:
        if c.primera_respuesta_at and c.created_at:
            tmr.append((c.primera_respuesta_at - c.created_at).total_seconds() / 60)
        if c.resuelto_at and c.created_at:
            tmo.append((c.resuelto_at - c.created_at).total_seconds() / 60)
    return {
        "casos_abiertos": len(abiertos),
        "casos_criticos": criticos,
        "casos_vencidos": vencidos,
        "tiempo_medio_respuesta_min": round(sum(tmr) / len(tmr), 1) if tmr else None,
        "tiempo_medio_resolucion_min": round(sum(tmo) / len(tmo), 1) if tmo else None,
        "principales_categorias": [{"categoria": k, "cantidad": v} for k, v in top_cats],
        "endpoint": "/api/soporte/contrato/centro-control",
    }
