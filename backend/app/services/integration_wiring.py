"""Cableado 1330 ↔ 1350 ↔ 1360 — helpers cross-módulo con organization_id explícito."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.continuidad_enums import EstadoOperacional
from app.continuidad_models import ContinuidadAlerta, ContinuidadServicioCritico
from app.governance_models import GovAccessLog, GovAuthorization, GovLegalHold, GovLineageEvent
from app.integration_models import IntegrationConnector
from app.models import User
from app.services import continuidad_service as cont_svc
from app.services import governance_adapters
from app.services import governance_masking
from app.services import governance_service as gov_svc
from app.services.security_policy_service import is_mfa_required_for_user, user_has_mfa_enabled

PROVEEDOR_REF_PREFIX = "connector:"
EVENT_INTEGRACION_SALUD_RECUPERADA = "INTEGRACION_SALUD_RECUPERADA"
EVENT_RESTORE_BLOQUEADO_PRIVACIDAD = "RESTORE_BLOQUEADO_PRIVACIDAD"

ALERT_DEDUP_MINUTES = 5


@dataclass
class GovPreflightResult:
    allowed: bool
    decision: str
    reasons: list[str] = field(default_factory=list)
    minimization_action: str | None = None
    catalog_entry_id: str | None = None
    purpose_code: str | None = None
    correlation_id: str = ""


def new_correlation_id() -> str:
    return str(uuid.uuid4())


def proveedor_ref_for_connector(connector_id: str) -> str:
    return f"{PROVEEDOR_REF_PREFIX}{connector_id}"


def validate_gov_catalog_entry(db: Session, organization_id: str, catalog_entry_id: str) -> None:
    """WIRING-01 — catálogo debe pertenecer a la organización."""
    entry = gov_svc.get_catalog_entry(db, organization_id, catalog_entry_id)
    if not entry:
        raise ValueError("Entrada de catálogo de gobierno no encontrada en esta organización")


def _has_active_legal_hold(db: Session, organization_id: str, catalog_entry_id: str) -> bool:
    return (
        db.query(GovLegalHold)
        .filter(
            GovLegalHold.organization_id == organization_id,
            GovLegalHold.status == "ACTIVO",
            (GovLegalHold.catalog_entry_id == catalog_entry_id) | (GovLegalHold.catalog_entry_id.is_(None)),
        )
        .count()
        > 0
    )


def _consent_ok(db: Session, organization_id: str, purpose_code: str | None) -> bool:
    if not purpose_code:
        return True
    rows = (
        db.query(GovAuthorization)
        .filter(
            GovAuthorization.organization_id == organization_id,
            GovAuthorization.status == "VIGENTE",
            GovAuthorization.purpose == purpose_code,
        )
        .count()
    )
    return rows > 0


def gov_preflight(
    db: Session,
    organization_id: str,
    connector: IntegrationConnector,
    correlation_id: str,
) -> GovPreflightResult:
    """WIRING-02/03 — política, legal hold, consentimiento antes de ejecutar."""
    catalog_id = connector.gov_catalog_entry_id
    if not catalog_id:
        return GovPreflightResult(
            allowed=True,
            decision="PERMITIDA",
            reasons=["Sin catálogo gobierno vinculado — modo operativo sin preflight gov"],
            correlation_id=correlation_id,
        )

    entry = gov_svc.get_catalog_entry(db, organization_id, catalog_id)
    if not entry:
        return GovPreflightResult(
            allowed=False,
            decision="DENEGADA",
            reasons=["Catálogo gobierno no encontrado en esta organización"],
            catalog_entry_id=catalog_id,
            correlation_id=correlation_id,
        )

    if entry.status and entry.status.upper() not in ("ACTIVO", "VIGENTE", "APROBADO"):
        return GovPreflightResult(
            allowed=False,
            decision="DENEGADA",
            reasons=[f"Catálogo en estado no operativo: {entry.status}"],
            catalog_entry_id=catalog_id,
            correlation_id=correlation_id,
        )

    policy_view = gov_svc.get_connector_policy_view(db, organization_id, catalog_id)
    if not policy_view:
        return GovPreflightResult(
            allowed=False,
            decision="DENEGADA",
            reasons=["No se pudo resolver política de gobierno"],
            catalog_entry_id=catalog_id,
            correlation_id=correlation_id,
        )

    reasons: list[str] = list(policy_view.get("restrictions") or [])
    export_decision = policy_view.get("provider_decision") or "PERMITIDO"
    export_eval = gov_svc.evaluate_provider_export(db, organization_id, catalog_entry_id=catalog_id)

    if _has_active_legal_hold(db, organization_id, catalog_id):
        reasons.append("Retención especial / legal hold activo")
        return GovPreflightResult(
            allowed=False,
            decision="DENEGADA",
            reasons=reasons,
            catalog_entry_id=catalog_id,
            purpose_code=policy_view.get("purpose_code"),
            correlation_id=correlation_id,
        )

    if export_decision == "DENEGADO":
        return GovPreflightResult(
            allowed=False,
            decision="DENEGADA",
            reasons=reasons or ["Política de exportación DENEGADA"],
            catalog_entry_id=catalog_id,
            purpose_code=policy_view.get("purpose_code"),
            correlation_id=correlation_id,
        )

    purpose_code = policy_view.get("purpose_code")
    if purpose_code and not _consent_ok(db, organization_id, purpose_code):
        return GovPreflightResult(
            allowed=False,
            decision="REQUIERE_APROBACION",
            reasons=[f"Falta autorización vigente para purpose {purpose_code}"],
            catalog_entry_id=catalog_id,
            purpose_code=purpose_code,
            correlation_id=correlation_id,
        )

    minimization = None
    decision = "PERMITIDA"
    if export_decision == "PERMITIDO_CON_TRANSFORMACIÓN":
        decision = "PERMITIDA_CON_TRANSFORMACION"
        minimization = export_eval.get("minimization_action") or "confidencial"

    return GovPreflightResult(
        allowed=True,
        decision=decision,
        reasons=reasons,
        minimization_action=minimization,
        catalog_entry_id=catalog_id,
        purpose_code=purpose_code,
        correlation_id=correlation_id,
    )


def apply_gov_masking(
    db: Session,
    organization_id: str,
    records: list[dict],
    minimization_action: str | None,
) -> list[dict]:
    """WIRING-04 — enmascaramiento en salida."""
    if not minimization_action or not records:
        return records
    masked: list[dict] = []
    for rec in records:
        out = dict(rec)
        for key, val in list(out.items()):
            if isinstance(val, str) and val:
                try:
                    out[key] = governance_masking.apply_mask(minimization_action, val)
                except Exception as exc:
                    raise ValueError(f"Enmascaramiento falló para campo {key}: {exc}") from exc
        masked.append(out)
    return masked


def gov_register_access(
    db: Session,
    organization_id: str,
    user_id: str | None,
    *,
    catalog_entry_id: str | None,
    connector_id: str,
    action: str,
    result: str,
    correlation_id: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """WIRING-05 — acceso gobierno sin commit (flush)."""
    if not catalog_entry_id:
        return
    payload = {"connector_id": connector_id, "correlation_id": correlation_id}
    if detail:
        payload.update(detail)
    row = GovAccessLog(
        organization_id=organization_id,
        user_id=user_id,
        catalog_entry_id=catalog_entry_id,
        resource_ref=f"connector:{connector_id}",
        action=action,
        result=result,
        detail=json.dumps(payload, ensure_ascii=False, default=str)[:500],
    )
    db.add(row)
    db.flush()


def gov_register_lineage(
    db: Session,
    organization_id: str,
    user_id: str | None,
    *,
    catalog_entry_id: str,
    connector_id: str,
    execution_id: str,
    status: str,
    records_valid: int,
    records_rejected: int,
    correlation_id: str,
) -> None:
    """WIRING-07 — linaje gobierno."""
    row = GovLineageEvent(
        organization_id=organization_id,
        catalog_entry_id=catalog_entry_id,
        step_type="INTEGRACION",
        label=f"Ejecución conector {connector_id}",
        detail=f"status={status} valid={records_valid} rejected={records_rejected}",
        related_process_id=execution_id,
        metadata_json=json.dumps(
            {"connector_id": connector_id, "correlation_id": correlation_id},
            ensure_ascii=False,
        ),
    )
    db.add(row)
    db.flush()


def gov_register_execution_result(
    db: Session,
    organization_id: str,
    user_id: str | None,
    *,
    catalog_entry_id: str,
    connector_id: str,
    execution_id: str,
    technical_status: str,
    functional_ok: bool,
    correlation_id: str,
) -> None:
    """WIRING-08 — resultado en gobierno (vía acceso + audit)."""
    result = "OK" if functional_ok and technical_status in ("EXITOSA", "PARCIAL") else "ERROR"
    gov_register_access(
        db,
        organization_id,
        user_id,
        catalog_entry_id=catalog_entry_id,
        connector_id=connector_id,
        action="INTEGRACION_RESULTADO",
        result=result,
        correlation_id=correlation_id,
        detail={"execution_id": execution_id, "technical_status": technical_status},
    )


def ensure_continuidad_servicio(
    db: Session,
    organization_id: str,
    connector: IntegrationConnector,
    user_id: str | None,
) -> ContinuidadServicioCritico:
    """WIRING-09 — servicio crítico vinculado por proveedor_ref."""
    ref = proveedor_ref_for_connector(connector.id)
    existing = (
        db.query(ContinuidadServicioCritico)
        .filter(
            ContinuidadServicioCritico.organization_id == organization_id,
            ContinuidadServicioCritico.proveedor_ref == ref,
            ContinuidadServicioCritico.is_active.is_(True),
        )
        .first()
    )
    if existing:
        return existing
    return cont_svc.create_servicio(
        db,
        organization_id,
        {
            "nombre": f"Integración: {connector.name}",
            "tipo": "INTEGRACION",
            "criticidad": "MEDIA",
            "proveedor_ref": ref,
        },
        user_id,
    )


def _recent_alert_exists(db: Session, organization_id: str, servicio_id: str, tipo: str) -> bool:
    since = datetime.now(timezone.utc) - timedelta(minutes=ALERT_DEDUP_MINUTES)
    return (
        db.query(ContinuidadAlerta)
        .filter(
            ContinuidadAlerta.organization_id == organization_id,
            ContinuidadAlerta.entidad_ref == servicio_id,
            ContinuidadAlerta.tipo == tipo,
            ContinuidadAlerta.created_at >= since,
        )
        .count()
        > 0
    )


def sync_continuidad_from_connector(
    db: Session,
    organization_id: str,
    connector: IntegrationConnector,
    *,
    prev_estado: str | None,
    user_id: str | None,
    correlation_id: str,
) -> None:
    """WIRING-10 — salud conector → continuidad."""
    servicio = ensure_continuidad_servicio(db, organization_id, connector, user_id)
    until = connector.circuit_open_until
    if until and until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    circuit_open = bool(until and until > datetime.now(timezone.utc))
    if circuit_open or connector.status == "DEGRADADO":
        estado = EstadoOperacional.DEGRADADO
        if connector.consecutive_failures >= connector.circuit_breaker_threshold:
            estado = EstadoOperacional.NO_DISPONIBLE
    elif connector.status == "ACTIVO":
        estado = EstadoOperacional.DISPONIBLE
    else:
        estado = EstadoOperacional.DESCONOCIDO

    if estado in (EstadoOperacional.DEGRADADO, EstadoOperacional.NO_DISPONIBLE):
        tipo = "SERVICIO_DEGRADADO" if estado == EstadoOperacional.DEGRADADO else "SERVICIO_CAIDO"
        if not _recent_alert_exists(db, organization_id, servicio.id, tipo):
            cont_svc.update_estado_servicio(
                db,
                organization_id,
                servicio.id,
                estado,
                f"Conector {connector.code} — correlation={correlation_id}",
            )
    else:
        cont_svc.update_estado_servicio(
            db,
            organization_id,
            servicio.id,
            estado,
            f"Sincronización salud conector {connector.code}",
        )
        if prev_estado in (EstadoOperacional.DEGRADADO, EstadoOperacional.NO_DISPONIBLE):
            if not _recent_alert_exists(db, organization_id, servicio.id, EVENT_INTEGRACION_SALUD_RECUPERADA):
                cont_svc._alerta(
                    db,
                    organization_id,
                    EVENT_INTEGRACION_SALUD_RECUPERADA,
                    f"Conector {connector.name} recuperado",
                    "MEDIA",
                    servicio.id,
                )
                write_audit(
                    db,
                    action="integraciones.salud.recuperada",
                    organization_id=organization_id,
                    user_id=user_id,
                    detail=json.dumps(
                        {"connector_id": connector.id, "correlation_id": correlation_id},
                        ensure_ascii=False,
                    ),
                    commit=False,
                )


def register_connector_backup_metadata(
    db: Session,
    organization_id: str,
    connector: IntegrationConnector,
    user_id: str | None,
    correlation_id: str,
) -> None:
    """WIRING-11 — metadata backup con organization_id explícito (auditoría)."""
    write_audit(
        db,
        action="integraciones.backup.metadata",
        organization_id=organization_id,
        user_id=user_id,
        detail=json.dumps(
            {
                "connector_id": connector.id,
                "organization_id": organization_id,
                "proveedor_ref": proveedor_ref_for_connector(connector.id),
                "gov_catalog_entry_id": connector.gov_catalog_entry_id,
                "correlation_id": correlation_id,
            },
            ensure_ascii=False,
        ),
        commit=False,
    )


def validate_restore_privacy(
    db: Session,
    organization_id: str,
    catalog_entry_id: str,
    user_id: str | None,
) -> None:
    """WIRING-12 — bloqueo restore por política / legal hold."""
    entry = gov_svc.get_catalog_entry(db, organization_id, catalog_entry_id)
    if not entry:
        raise ValueError("Catálogo no encontrado en esta organización")

    if _has_active_legal_hold(db, organization_id, catalog_entry_id):
        write_audit(
            db,
            action="continuidad.restore.bloqueado",
            organization_id=organization_id,
            user_id=user_id,
            detail=json.dumps(
                {"reason": "legal_hold", "catalog_entry_id": catalog_entry_id, "event": EVENT_RESTORE_BLOQUEADO_PRIVACIDAD},
                ensure_ascii=False,
            ),
            commit=False,
        )
        cont_svc._alerta(
            db,
            organization_id,
            EVENT_RESTORE_BLOQUEADO_PRIVACIDAD,
            "Restauración bloqueada por legal hold activo",
            "ALTA",
            catalog_entry_id,
        )
        raise ValueError("Restauración bloqueada: legal hold activo")

    export_eval = gov_svc.evaluate_provider_export(db, organization_id, catalog_entry_id=catalog_entry_id)
    if export_eval.get("result") == "DENEGADO":
        write_audit(
            db,
            action="continuidad.restore.bloqueado",
            organization_id=organization_id,
            user_id=user_id,
            detail=json.dumps(
                {"reason": "privacidad", "catalog_entry_id": catalog_entry_id, "event": EVENT_RESTORE_BLOQUEADO_PRIVACIDAD},
                ensure_ascii=False,
            ),
            commit=False,
        )
        cont_svc._alerta(
            db,
            organization_id,
            EVENT_RESTORE_BLOQUEADO_PRIVACIDAD,
            "Restauración bloqueada por política de privacidad",
            "ALTA",
            catalog_entry_id,
        )
        raise ValueError("Restauración bloqueada por política de privacidad")


def identity_preflight_execute(db: Session, organization_id: str, user_id: str | None) -> None:
    """WIRING-13 — MFA / identidad antes de ejecutar."""
    if not user_id:
        return
    user = db.get(User, user_id)
    if not user or user.organization_id != organization_id:
        raise ValueError("Usuario no válido para esta organización")
    if not user.is_active:
        raise ValueError("Usuario inactivo")
    if is_mfa_required_for_user(db, user) and not user_has_mfa_enabled(db, user_id):
        raise ValueError("MFA obligatorio para ejecutar integraciones en esta organización")


def audit_preflight_denied(
    db: Session,
    organization_id: str,
    user_id: str | None,
    connector_id: str,
    preflight: GovPreflightResult,
) -> None:
    write_audit(
        db,
        action="integraciones.preflight.denegado",
        organization_id=organization_id,
        user_id=user_id,
        detail=json.dumps(
            {
                "connector_id": connector_id,
                "decision": preflight.decision,
                "reasons": preflight.reasons,
                "correlation_id": preflight.correlation_id,
            },
            ensure_ascii=False,
        ),
        commit=False,
    )
    if preflight.catalog_entry_id:
        gov_register_access(
            db,
            organization_id,
            user_id,
            catalog_entry_id=preflight.catalog_entry_id,
            connector_id=connector_id,
            action="INTEGRACION_PREFLIGHT",
            result="DENEGADO",
            correlation_id=preflight.correlation_id,
            detail={"reasons": preflight.reasons},
        )
