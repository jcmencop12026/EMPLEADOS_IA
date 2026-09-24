"""Sincronización controlada oportunidad ↔ Centro de Negocios."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.evaluacion_models import EvaluacionExpediente
from app.negocio_enums import SyncDirection
from app.negocio_models import NegocioProposalExtension, NegocioSyncLog
from app.opportunity_models import Opportunity


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _log_sync(
    db: Session,
    *,
    org_id: str,
    proposal_id: str | None,
    opportunity_id: str | None,
    direction: str,
    field_name: str,
    old_value: Any,
    new_value: Any,
) -> None:
    db.add(
        NegocioSyncLog(
            organization_id=org_id,
            proposal_id=proposal_id,
            opportunity_id=opportunity_id,
            direction=direction,
            field_name=field_name,
            old_value=_json(old_value) if old_value is not None else None,
            new_value=_json(new_value) if new_value is not None else None,
        )
    )


def sync_from_opportunity(db: Session, org_id: str, proposal_id: str) -> dict[str, Any]:
    """Oportunidad es canónica para título/estado comercial de oportunidad."""
    ext = (
        db.query(NegocioProposalExtension)
        .filter(NegocioProposalExtension.proposal_id == proposal_id, NegocioProposalExtension.organization_id == org_id)
        .first()
    )
    if not ext or not ext.opportunity_id:
        return {"synced": False, "reason": "sin_oportunidad_vinculada"}
    opp = (
        db.query(Opportunity)
        .filter(Opportunity.id == ext.opportunity_id, Opportunity.organization_id == org_id)
        .first()
    )
    if not opp:
        return {"synced": False, "reason": "oportunidad_no_encontrada"}
    from app.commercial_models import CommercialProposal

    proposal = db.query(CommercialProposal).filter(CommercialProposal.id == proposal_id).first()
    if not proposal:
        return {"synced": False, "reason": "propuesta_no_encontrada"}
    changes: dict[str, Any] = {}
    if opp.titulo and opp.titulo != proposal.titulo:
        old = proposal.titulo
        proposal.titulo = opp.titulo
        changes["titulo"] = {"old": old, "new": opp.titulo}
        _log_sync(
            db,
            org_id=org_id,
            proposal_id=proposal_id,
            opportunity_id=opp.id,
            direction=SyncDirection.OPP_TO_NEGOCIO,
            field_name="titulo",
            old_value=old,
            new_value=opp.titulo,
        )
    ext.sync_revision = (ext.sync_revision or 0) + 1
    db.flush()
    return {"synced": bool(changes), "changes": changes, "sync_revision": ext.sync_revision}


def sync_to_opportunity(db: Session, org_id: str, proposal_id: str, *, actor_id: str | None = None) -> dict[str, Any]:
    """Negocio es canónico para próximo paso comercial en extensión."""
    ext = (
        db.query(NegocioProposalExtension)
        .filter(NegocioProposalExtension.proposal_id == proposal_id, NegocioProposalExtension.organization_id == org_id)
        .first()
    )
    if not ext or not ext.opportunity_id:
        return {"synced": False, "reason": "sin_oportunidad_vinculada"}
    opp = (
        db.query(Opportunity)
        .filter(Opportunity.id == ext.opportunity_id, Opportunity.organization_id == org_id)
        .first()
    )
    if not opp:
        return {"synced": False, "reason": "oportunidad_no_encontrada"}
    changes: dict[str, Any] = {}
    if ext.proximo_paso:
        note = f"[Centro Negocios] {ext.proximo_paso}"
        old = opp.descripcion
        if note not in (old or ""):
            opp.descripcion = f"{old or ''}\n{note}".strip()
            changes["descripcion"] = note
            _log_sync(
                db,
                org_id=org_id,
                proposal_id=proposal_id,
                opportunity_id=opp.id,
                direction=SyncDirection.NEGOCIO_TO_OPP,
                field_name="proximo_paso",
                old_value=old,
                new_value=opp.descripcion,
            )
    ext.sync_revision = (ext.sync_revision or 0) + 1
    db.flush()
    return {"synced": bool(changes), "changes": changes, "sync_revision": ext.sync_revision}


def get_sync_log(db: Session, org_id: str, proposal_id: str, limit: int = 30) -> list[dict[str, Any]]:
    rows = (
        db.query(NegocioSyncLog)
        .filter(NegocioSyncLog.organization_id == org_id, NegocioSyncLog.proposal_id == proposal_id)
        .order_by(NegocioSyncLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "direction": r.direction,
            "field_name": r.field_name,
            "old_value": r.old_value,
            "new_value": r.new_value,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def resolve_prospecto_name(db: Session, ext: NegocioProposalExtension | None) -> str | None:
    if not ext or not ext.evaluacion_id:
        return None
    exp = db.query(EvaluacionExpediente).filter(EvaluacionExpediente.id == ext.evaluacion_id).first()
    return exp.entidad_nombre if exp else None
