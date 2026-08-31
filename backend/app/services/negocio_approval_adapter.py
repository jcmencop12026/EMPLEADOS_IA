"""Frontera de aprobaciones — adaptador local reemplazable por Gobierno Operacional."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import User
from app.negocio_enums import (
    DEFAULT_APPROVAL_LEVELS,
    ApprovalLevel,
    ApprovalStatus,
)
from app.negocio_models import NegocioApprovalPolicy, NegocioApprovalRecord, NegocioProposalExtension


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _parse(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


class ApprovalPort(Protocol):
    """Contrato para integración con Gobierno Operacional transversal (Agente A)."""

    def required_levels(self, db: Session, org_id: str, proposal_id: str) -> list[str]: ...

    def ensure_records(self, db: Session, org_id: str, proposal_id: str, version_number: int) -> list[NegocioApprovalRecord]: ...

    def can_present(self, db: Session, org_id: str, proposal_id: str, version_number: int) -> tuple[bool, list[str]]: ...

    def approve(
        self,
        db: Session,
        user: User,
        org_id: str,
        proposal_id: str,
        nivel: str,
        *,
        comentario: str | None = None,
        version_number: int | None = None,
    ) -> NegocioApprovalRecord: ...

    def reset_for_version(self, db: Session, org_id: str, proposal_id: str, version_number: int) -> None: ...


class LocalNegocioApprovalAdapter:
    """Implementación provisional — reemplazar por adaptador Gobierno Operacional."""

    def required_levels(self, db: Session, org_id: str, proposal_id: str) -> list[str]:
        ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()
        if ext and ext.approval_policy_json:
            levels = _parse(ext.approval_policy_json)
            if isinstance(levels, list) and levels:
                return [str(x) for x in levels]
        policy = db.query(NegocioApprovalPolicy).filter(NegocioApprovalPolicy.organization_id == org_id).first()
        if policy and policy.enabled:
            levels = _parse(policy.levels_json)
            if isinstance(levels, list) and levels:
                return [str(x) for x in levels]
        return list(DEFAULT_APPROVAL_LEVELS)

    def ensure_records(self, db: Session, org_id: str, proposal_id: str, version_number: int) -> list[NegocioApprovalRecord]:
        levels = self.required_levels(db, org_id, proposal_id)
        existing = {
            r.nivel: r
            for r in db.query(NegocioApprovalRecord)
            .filter(
                NegocioApprovalRecord.proposal_id == proposal_id,
                NegocioApprovalRecord.organization_id == org_id,
                NegocioApprovalRecord.version_number == version_number,
            )
            .all()
        }
        out: list[NegocioApprovalRecord] = []
        for nivel in levels:
            if nivel in existing:
                out.append(existing[nivel])
                continue
            row = NegocioApprovalRecord(
                proposal_id=proposal_id,
                organization_id=org_id,
                version_number=version_number,
                nivel=nivel,
                estado=ApprovalStatus.PENDIENTE,
            )
            db.add(row)
            out.append(row)
        db.flush()
        return out

    def can_present(self, db: Session, org_id: str, proposal_id: str, version_number: int) -> tuple[bool, list[str]]:
        levels = self.required_levels(db, org_id, proposal_id)
        if not levels:
            return True, []
        records = self.ensure_records(db, org_id, proposal_id, version_number)
        missing = [r.nivel for r in records if r.estado != ApprovalStatus.APROBADO]
        return len(missing) == 0, missing

    def approve(
        self,
        db: Session,
        user: User,
        org_id: str,
        proposal_id: str,
        nivel: str,
        *,
        comentario: str | None = None,
        version_number: int | None = None,
    ) -> NegocioApprovalRecord:
        if nivel not in ApprovalLevel.ALL:
            raise HTTPException(status_code=400, detail="Nivel de aprobación no válido")
        ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()
        ver = version_number or (ext.version_actual if ext else 1)
        records = self.ensure_records(db, org_id, proposal_id, ver)
        row = next((r for r in records if r.nivel == nivel), None)
        if not row:
            raise HTTPException(status_code=404, detail="Registro de aprobación no encontrado")
        row.estado = ApprovalStatus.APROBADO
        row.actor_id = user.id
        row.comentario = comentario
        row.decided_at = _utcnow()
        write_audit(
            db,
            action="negocio.aprobacion.nivel",
            organization_id=org_id,
            user_id=user.id,
            detail=_json({"proposal_id": proposal_id, "nivel": nivel, "version": ver}),
            commit=False,
        )
        db.flush()
        return row

    def reset_for_version(self, db: Session, org_id: str, proposal_id: str, version_number: int) -> None:
        self.ensure_records(db, org_id, proposal_id, version_number)


def get_approval_adapter() -> ApprovalPort:
    return LocalNegocioApprovalAdapter()


def list_approval_status(db: Session, org_id: str, proposal_id: str, version_number: int | None = None) -> list[dict[str, Any]]:
    adapter = get_approval_adapter()
    ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()
    ver = version_number or (ext.version_actual if ext else 1)
    records = adapter.ensure_records(db, org_id, proposal_id, ver)
    from app.negocio_labels import label_approval_level

    return [
        {
            "nivel": r.nivel,
            "nivel_label": label_approval_level(r.nivel),
            "estado": r.estado,
            "actor_id": r.actor_id,
            "comentario": r.comentario,
            "decided_at": r.decided_at.isoformat() if r.decided_at else None,
            "version_number": r.version_number,
        }
        for r in records
    ]


def set_org_approval_policy(db: Session, org_id: str, levels: list[str], enabled: bool = True) -> NegocioApprovalPolicy:
    for lvl in levels:
        if lvl not in ApprovalLevel.ALL:
            raise HTTPException(status_code=400, detail=f"Nivel no válido: {lvl}")
    row = db.query(NegocioApprovalPolicy).filter(NegocioApprovalPolicy.organization_id == org_id).first()
    if not row:
        row = NegocioApprovalPolicy(organization_id=org_id, levels_json=_json(levels), enabled=enabled)
        db.add(row)
    else:
        row.levels_json = _json(levels)
        row.enabled = enabled
        row.updated_at = _utcnow()
    db.flush()
    return row
