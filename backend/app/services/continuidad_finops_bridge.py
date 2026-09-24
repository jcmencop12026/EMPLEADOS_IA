"""Puente contrato → presupuesto operacional FinOps (sin duplicar FinOps)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.commercial_models import CommercialProposal
from app.finops_enums import FinOpsBudgetPolicy
from app.finops_models import FinOpsBudget
from app.negocio_models import NegocioContractRecord, NegocioProposalExtension


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _operational_envelope(ext: NegocioProposalExtension) -> dict[str, Any]:
    """Límite operacional desde consumo IA incluido — no precio comercial."""
    ia = _parse(ext.ia_consumo_json) or {}
    presupuesto = (
        ia.get("presupuesto_operacional")
        or ia.get("limite_costo_operacional")
        or ia.get("consumo_incluido_usd")
    )
    return {
        "consumo_ia_incluido": ia.get("consumo_incluido") or ia.get("consumo_incluido_tokens") or ia.get("tokens_incluidos"),
        "presupuesto_operacional": presupuesto,
        "periodicidad": ia.get("periodicidad") or "MENSUAL",
        "infraestructura_incluida": ia.get("infraestructura_incluida") or ia.get("infraestructura_licencias"),
        "servicios_incluidos": ia.get("servicios_incluidos"),
        "sobrecosto_politica": ia.get("sobrecosto_politica") or ia.get("excedente_overage"),
    }


def ensure_operational_budget_from_contract(
    db: Session,
    *,
    org_id: str,
    contract: NegocioContractRecord,
    ext: NegocioProposalExtension,
    proposal: CommercialProposal,
) -> FinOpsBudget | None:
    """Crea presupuesto operacional vinculado al contrato. El precio comercial queda en snapshot contractual."""
    if contract.finops_budget_id:
        existing = db.query(FinOpsBudget).filter(FinOpsBudget.id == contract.finops_budget_id).first()
        if existing:
            return existing

    envelope = _operational_envelope(ext)
    limit = envelope.get("presupuesto_operacional")
    if limit is None:
        return None

    now = _utcnow()
    periodicidad = (envelope.get("periodicidad") or "MENSUAL").upper()
    if periodicidad == "ANUAL":
        period_end = now + timedelta(days=365)
    elif periodicidad == "TRIMESTRAL":
        period_end = now + timedelta(days=90)
    else:
        period_end = now + timedelta(days=30)

    budget = FinOpsBudget(
        organization_id=org_id,
        scope_type="proceso",
        scope_id=contract.id,
        period_start=now,
        period_end=period_end,
        amount_limit=Decimal(str(limit)),
        currency="USD",
        policy=FinOpsBudgetPolicy.SOLO_INFORMAR,
        alert_threshold_pct=85,
        name=f"Operación contrato {proposal.codigo}",
        active=True,
    )
    db.add(budget)
    db.flush()
    contract.finops_budget_id = budget.id
    return budget


def contract_finops_summary(db: Session, contract: NegocioContractRecord, ext: NegocioProposalExtension) -> dict[str, Any]:
    """Resumen económico: ingreso comercial separado de costo operacional."""
    budget = None
    if contract.finops_budget_id:
        budget = db.query(FinOpsBudget).filter(FinOpsBudget.id == contract.finops_budget_id).first()
    envelope = _operational_envelope(ext)
    return {
        "ingreso_comercial": {
            "precio_contratado": float(contract.precio_contratado) if contract.precio_contratado is not None else None,
            "modelo_comercial": contract.modelo_comercial or ext.modelo_comercial,
            "nota": "Precio comercial — no es costo operacional",
        },
        "costo_operacional": {
            "presupuesto_id": budget.id if budget else None,
            "limite": float(budget.amount_limit) if budget else envelope.get("presupuesto_operacional"),
            "consumo_ia_incluido": envelope.get("consumo_ia_incluido"),
            "periodicidad": envelope.get("periodicidad"),
        },
    }
