"""Servicio de gobierno de datos — BLOQUE 1350."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.governance_models import (
    GovAccessLog,
    GovAiUsageGrant,
    GovAuthorization,
    GovCatalogEntry,
    GovClassificationLevel,
    GovCorrectiveAction,
    GovDataCategory,
    GovExportRecord,
    GovFinding,
    GovGlobalPolicy,
    GovLegalHold,
    GovLineageEvent,
    GovOrgPolicySetting,
    GovProviderPolicy,
    GovPurpose,
    GovRetentionPolicy,
    GovSubjectRequest,
)
from app.services.governance_masking import apply_mask, sanitize_secret_fields


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_load(raw: str | None) -> Any:
    if not raw:
        return None
    return json.loads(raw)


def _json_dump(data: Any) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


DEFAULT_CLASSIFICATIONS = [
    ("PUBLICO", "Público", 0),
    ("INTERNO", "Interno", 1),
    ("CONFIDENCIAL", "Confidencial", 2),
    ("RESTRINGIDO", "Restringido", 3),
]

DEFAULT_CATEGORIES = [
    ("DATOS_PERSONALES", "Datos personales"),
    ("DATOS_FINANCIEROS", "Datos financieros"),
    ("DATOS_COMERCIALES", "Datos comerciales"),
    ("DATOS_OPERATIVOS", "Datos operativos"),
    ("CREDENCIALES", "Credenciales"),
    ("DOCUMENTOS", "Documentos"),
    ("CONOCIMIENTO", "Conocimiento"),
    ("DATOS_SENSIBLES", "Datos sensibles"),
    ("OTROS", "Otros"),
]

DEFAULT_PURPOSES = [
    ("OPERACION", "Operación"),
    ("ANALISIS", "Análisis"),
    ("AUTOMATIZACION", "Automatización"),
    ("AUDITORIA", "Auditoría"),
    ("SOPORTE", "Soporte"),
    ("ENTRENAMIENTO_INTERNO", "Entrenamiento interno"),
    ("OTRO", "Otro"),
]


def ensure_org_defaults(db: Session, organization_id: str) -> None:
    for code, name, rank in DEFAULT_CLASSIFICATIONS:
        exists = (
            db.query(GovClassificationLevel)
            .filter(
                GovClassificationLevel.organization_id == organization_id,
                GovClassificationLevel.code == code,
            )
            .first()
        )
        if not exists:
            db.add(
                GovClassificationLevel(
                    organization_id=organization_id,
                    code=code,
                    name=name,
                    sensitivity_rank=rank,
                    is_system=True,
                )
            )
    for code, name in DEFAULT_CATEGORIES:
        exists = (
            db.query(GovDataCategory)
            .filter(GovDataCategory.organization_id == organization_id, GovDataCategory.code == code)
            .first()
        )
        if not exists:
            db.add(GovDataCategory(organization_id=organization_id, code=code, name=name, is_system=True))
    for code, name in DEFAULT_PURPOSES:
        exists = (
            db.query(GovPurpose)
            .filter(GovPurpose.organization_id == organization_id, GovPurpose.code == code)
            .first()
        )
        if not exists:
            db.add(GovPurpose(organization_id=organization_id, code=code, name=name))
    db.commit()


def _org_filter(model, organization_id: str):
    return model.organization_id == organization_id


def list_classification_levels(db: Session, organization_id: str) -> list[dict[str, Any]]:
    ensure_org_defaults(db, organization_id)
    rows = (
        db.query(GovClassificationLevel)
        .filter(
            (GovClassificationLevel.organization_id == organization_id)
            | (GovClassificationLevel.organization_id.is_(None))
        )
        .order_by(GovClassificationLevel.sensitivity_rank)
        .all()
    )
    return [classification_to_dict(r) for r in rows]


def classification_to_dict(row: GovClassificationLevel) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "code": row.code,
        "name": row.name,
        "sensitivity_rank": row.sensitivity_rank,
        "description": row.description,
        "is_active": row.is_active,
        "is_system": row.is_system,
    }


def create_classification_level(
    db: Session,
    organization_id: str,
    *,
    code: str,
    name: str,
    sensitivity_rank: int = 0,
    description: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    row = GovClassificationLevel(
        organization_id=organization_id,
        code=code.upper(),
        name=name,
        sensitivity_rank=sensitivity_rank,
        description=description,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.classification.create", organization_id=organization_id, user_id=user_id, detail=code)
    db.commit()
    db.refresh(row)
    return classification_to_dict(row)


def list_categories(db: Session, organization_id: str) -> list[dict[str, Any]]:
    ensure_org_defaults(db, organization_id)
    rows = (
        db.query(GovDataCategory)
        .filter(
            (GovDataCategory.organization_id == organization_id) | (GovDataCategory.organization_id.is_(None))
        )
        .order_by(GovDataCategory.code)
        .all()
    )
    return [category_to_dict(r) for r in rows]


def category_to_dict(row: GovDataCategory) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "is_active": row.is_active,
        "is_system": row.is_system,
    }


def create_category(
    db: Session,
    organization_id: str,
    *,
    code: str,
    name: str,
    description: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    row = GovDataCategory(
        organization_id=organization_id,
        code=code.upper(),
        name=name,
        description=description,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.category.create", organization_id=organization_id, user_id=user_id, detail=code)
    db.commit()
    db.refresh(row)
    return category_to_dict(row)


def list_purposes(db: Session, organization_id: str) -> list[dict[str, Any]]:
    ensure_org_defaults(db, organization_id)
    rows = db.query(GovPurpose).filter(GovPurpose.organization_id == organization_id).order_by(GovPurpose.code).all()
    return [purpose_to_dict(r) for r in rows]


def purpose_to_dict(row: GovPurpose) -> dict[str, Any]:
    return {"id": row.id, "organization_id": row.organization_id, "code": row.code, "name": row.name, "is_active": row.is_active}


def catalog_to_dict(row: GovCatalogEntry, db: Session | None = None) -> dict[str, Any]:
    payload = sanitize_secret_fields(
        {
            "id": row.id,
            "organization_id": row.organization_id,
            "name": row.name,
            "description": row.description,
            "source": row.source,
            "origin_system": row.origin_system,
            "responsible_user_id": row.responsible_user_id,
            "functional_owner": row.functional_owner,
            "classification_level_id": row.classification_level_id,
            "categories": _json_load(row.categories_json) or [],
            "logical_location": row.logical_location,
            "format": row.format,
            "retention_policy_id": row.retention_policy_id,
            "authorized_use": row.authorized_use,
            "status": row.status,
            "data_environment": row.data_environment,
            "secret_status": row.secret_status,
            "purpose_id": row.purpose_id,
            "metadata": _json_load(row.metadata_json),
            "created_by_id": row.created_by_id,
            "updated_by_id": row.updated_by_id,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    )
    if db and row.classification_level_id:
        cls = db.get(GovClassificationLevel, row.classification_level_id)
        if cls:
            payload["classification_code"] = cls.code
            payload["classification_name"] = cls.name
    return payload


def get_catalog_entry(db: Session, organization_id: str, entry_id: str) -> GovCatalogEntry | None:
    return (
        db.query(GovCatalogEntry)
        .filter(GovCatalogEntry.id == entry_id, GovCatalogEntry.organization_id == organization_id)
        .first()
    )


def list_catalog_entries(db: Session, organization_id: str, *, status: str | None = None) -> list[dict[str, Any]]:
    query = db.query(GovCatalogEntry).filter(GovCatalogEntry.organization_id == organization_id)
    if status:
        query = query.filter(GovCatalogEntry.status == status.upper())
    rows = query.order_by(GovCatalogEntry.updated_at.desc()).all()
    return [catalog_to_dict(r, db) for r in rows]


def create_catalog_entry(
    db: Session,
    organization_id: str,
    user_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    ensure_org_defaults(db, organization_id)
    row = GovCatalogEntry(
        organization_id=organization_id,
        name=data["name"],
        description=data.get("description"),
        source=data.get("source"),
        origin_system=data.get("origin_system"),
        responsible_user_id=data.get("responsible_user_id"),
        functional_owner=data.get("functional_owner"),
        classification_level_id=data.get("classification_level_id"),
        categories_json=_json_dump(data.get("categories")),
        logical_location=data.get("logical_location"),
        format=data.get("format"),
        retention_policy_id=data.get("retention_policy_id"),
        authorized_use=data.get("authorized_use"),
        status=data.get("status", "ACTIVO"),
        data_environment=data.get("data_environment", "PRODUCCION"),
        secret_status=data.get("secret_status"),
        purpose_id=data.get("purpose_id"),
        metadata_json=_json_dump(data.get("metadata")),
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.catalog.create", organization_id=organization_id, user_id=user_id, detail=row.name)
    db.commit()
    db.refresh(row)
    return catalog_to_dict(row, db)


def update_catalog_entry(
    db: Session,
    organization_id: str,
    entry_id: str,
    user_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    row = get_catalog_entry(db, organization_id, entry_id)
    if not row:
        raise LookupError("Entrada de catálogo no encontrada.")
    for field in (
        "name", "description", "source", "origin_system", "responsible_user_id",
        "functional_owner", "classification_level_id", "logical_location", "format",
        "retention_policy_id", "authorized_use", "status", "data_environment",
        "secret_status", "purpose_id",
    ):
        if field in data:
            setattr(row, field, data[field])
    if "categories" in data:
        row.categories_json = _json_dump(data["categories"])
    if "metadata" in data:
        row.metadata_json = _json_dump(data["metadata"])
    row.updated_by_id = user_id
    db.flush()
    write_audit(db, action="gov.catalog.update", organization_id=organization_id, user_id=user_id, detail=entry_id)
    db.commit()
    db.refresh(row)
    return catalog_to_dict(row, db)


def retention_to_dict(row: GovRetentionPolicy) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "name": row.name,
        "scope_type": row.scope_type,
        "scope_ref": row.scope_ref,
        "duration_unit": row.duration_unit,
        "duration_value": row.duration_value,
        "disposition": row.disposition,
        "is_active": row.is_active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def list_retention_policies(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(GovRetentionPolicy)
        .filter(GovRetentionPolicy.organization_id == organization_id)
        .order_by(GovRetentionPolicy.name)
        .all()
    )
    return [retention_to_dict(r) for r in rows]


def create_retention_policy(db: Session, organization_id: str, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = GovRetentionPolicy(
        organization_id=organization_id,
        name=data["name"],
        scope_type=data.get("scope_type", "ORGANIZACION"),
        scope_ref=data.get("scope_ref"),
        duration_unit=data.get("duration_unit", "MESES"),
        duration_value=data.get("duration_value"),
        disposition=data.get("disposition", "REVISIÓN_MANUAL"),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.retention.create", organization_id=organization_id, user_id=user_id, detail=row.name)
    db.commit()
    db.refresh(row)
    return retention_to_dict(row)


def lineage_to_dict(row: GovLineageEvent) -> dict[str, Any]:
    return {
        "id": row.id,
        "catalog_entry_id": row.catalog_entry_id,
        "step_type": row.step_type,
        "label": row.label,
        "detail": row.detail,
        "related_process_id": row.related_process_id,
        "related_employee_id": row.related_employee_id,
        "parent_event_id": row.parent_event_id,
        "metadata": _json_load(row.metadata_json),
        "created_at": row.created_at,
    }


def add_lineage_event(db: Session, organization_id: str, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    entry = get_catalog_entry(db, organization_id, data["catalog_entry_id"])
    if not entry:
        raise LookupError("Entrada de catálogo no encontrada.")
    row = GovLineageEvent(
        organization_id=organization_id,
        catalog_entry_id=data["catalog_entry_id"],
        step_type=data["step_type"].upper(),
        label=data["label"],
        detail=data.get("detail"),
        related_process_id=data.get("related_process_id"),
        related_employee_id=data.get("related_employee_id"),
        parent_event_id=data.get("parent_event_id"),
        metadata_json=_json_dump(data.get("metadata")),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return lineage_to_dict(row)


def list_lineage(db: Session, organization_id: str, catalog_entry_id: str) -> list[dict[str, Any]]:
    entry = get_catalog_entry(db, organization_id, catalog_entry_id)
    if not entry:
        raise LookupError("Entrada de catálogo no encontrada.")
    rows = (
        db.query(GovLineageEvent)
        .filter(
            GovLineageEvent.organization_id == organization_id,
            GovLineageEvent.catalog_entry_id == catalog_entry_id,
        )
        .order_by(GovLineageEvent.created_at)
        .all()
    )
    return [lineage_to_dict(r) for r in rows]


def ai_usage_to_dict(row: GovAiUsageGrant) -> dict[str, Any]:
    return {
        "id": row.id,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "source_type": row.source_type,
        "source_ref": row.source_ref,
        "permission": row.permission,
        "purpose_id": row.purpose_id,
        "is_active": row.is_active,
        "created_at": row.created_at,
    }


def create_ai_usage_grant(db: Session, organization_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = GovAiUsageGrant(
        organization_id=organization_id,
        target_type=data["target_type"].upper(),
        target_id=data["target_id"],
        source_type=data["source_type"].upper(),
        source_ref=data["source_ref"],
        permission=data["permission"].upper(),
        purpose_id=data.get("purpose_id"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ai_usage_to_dict(row)


def list_ai_usage_grants(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = db.query(GovAiUsageGrant).filter(GovAiUsageGrant.organization_id == organization_id).all()
    return [ai_usage_to_dict(r) for r in rows]


def provider_policy_to_dict(row: GovProviderPolicy) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "classification_level_id": row.classification_level_id,
        "category_id": row.category_id,
        "decision": row.decision,
        "minimization_action": row.minimization_action,
        "provider_scope": row.provider_scope,
        "is_mandatory_global": row.is_mandatory_global,
        "metadata": _json_load(row.metadata_json),
    }


def create_provider_policy(db: Session, organization_id: str | None, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = GovProviderPolicy(
        organization_id=organization_id,
        classification_level_id=data.get("classification_level_id"),
        category_id=data.get("category_id"),
        decision=data["decision"].upper(),
        minimization_action=data.get("minimization_action"),
        provider_scope=data.get("provider_scope"),
        is_mandatory_global=data.get("is_mandatory_global", False),
        metadata_json=_json_dump(data.get("metadata")),
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="gov.provider_policy.create",
        organization_id=organization_id,
        user_id=user_id,
        detail=row.decision,
    )
    db.commit()
    db.refresh(row)
    return provider_policy_to_dict(row)


def list_provider_policies(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(GovProviderPolicy)
        .filter(
            (GovProviderPolicy.organization_id == organization_id)
            | (GovProviderPolicy.is_mandatory_global.is_(True))
        )
        .all()
    )
    return [provider_policy_to_dict(r) for r in rows]


def _match_provider_policy(
    db: Session,
    organization_id: str,
    classification_level_id: str | None,
    category_id: str | None,
    provider: str | None,
) -> GovProviderPolicy | None:
    policies = (
        db.query(GovProviderPolicy)
        .filter(
            (GovProviderPolicy.organization_id == organization_id)
            | (GovProviderPolicy.is_mandatory_global.is_(True))
        )
        .all()
    )
    best: GovProviderPolicy | None = None
    best_score = -1
    for pol in policies:
        if pol.classification_level_id and pol.classification_level_id != classification_level_id:
            continue
        if pol.category_id and pol.category_id != category_id:
            continue
        if pol.provider_scope and provider and pol.provider_scope.lower() != provider.lower():
            continue
        score = 0
        if pol.is_mandatory_global:
            score += 100
        if pol.classification_level_id:
            score += 10
        if pol.category_id:
            score += 5
        if pol.provider_scope:
            score += 3
        if score > best_score:
            best_score = score
            best = pol
    return best


def evaluate_provider_export(
    db: Session,
    organization_id: str,
    *,
    catalog_entry_id: str | None = None,
    classification_level_id: str | None = None,
    category_id: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    entry: GovCatalogEntry | None = None
    if catalog_entry_id:
        entry = get_catalog_entry(db, organization_id, catalog_entry_id)
        if not entry:
            return {"result": "DENEGADO", "reasons": ["Entrada de catálogo no encontrada en la organización."]}
        classification_level_id = entry.classification_level_id
        cats = _json_load(entry.categories_json) or []
        if cats and not category_id:
            category_id = cats[0] if isinstance(cats[0], str) else None

    policy = _match_provider_policy(db, organization_id, classification_level_id, category_id, provider)
    if not policy:
        cls = db.get(GovClassificationLevel, classification_level_id) if classification_level_id else None
        if cls and cls.sensitivity_rank >= 3:
            return {
                "result": "DENEGADO",
                "reasons": ["Sin política explícita para dato restringido — denegado por defecto."],
            }
        return {"result": "PERMITIDO", "reasons": ["Sin restricción aplicable."]}

    decision = policy.decision.upper()
    if decision == "PROHIBIDO":
        return {
            "result": "DENEGADO",
            "reasons": ["Política de organización/clasificación prohíbe envío a proveedor externo."],
            "policy_id": policy.id,
        }
    if decision in ("PERMITIDO_CON_RESTRICCIONES", "PERMITIDO_CON_TRANSFORMACIÓN"):
        action = policy.minimization_action or "ENMASCARAR"
        return {
            "result": "PERMITIDO_CON_TRANSFORMACIÓN",
            "reasons": [f"Requiere transformación: {action}."],
            "minimization_action": action,
            "policy_id": policy.id,
        }
    return {"result": "PERMITIDO", "reasons": ["Política permite envío a proveedor."], "policy_id": policy.id}


def get_connector_policy_view(db: Session, organization_id: str, catalog_entry_id: str) -> dict[str, Any] | None:
    entry = get_catalog_entry(db, organization_id, catalog_entry_id)
    if not entry:
        return None
    cls = db.get(GovClassificationLevel, entry.classification_level_id) if entry.classification_level_id else None
    purpose = db.get(GovPurpose, entry.purpose_id) if entry.purpose_id else None
    retention = db.get(GovRetentionPolicy, entry.retention_policy_id) if entry.retention_policy_id else None
    export_eval = evaluate_provider_export(db, organization_id, catalog_entry_id=catalog_entry_id)
    restrictions: list[str] = []
    if export_eval["result"] == "DENEGADO":
        restrictions.append("No enviar a proveedores externos")
    elif export_eval["result"] == "PERMITIDO_CON_TRANSFORMACIÓN":
        restrictions.append(f"Transformación requerida: {export_eval.get('minimization_action')}")
    holds = (
        db.query(GovLegalHold)
        .filter(
            GovLegalHold.organization_id == organization_id,
            GovLegalHold.status == "ACTIVO",
            (GovLegalHold.catalog_entry_id == catalog_entry_id) | (GovLegalHold.catalog_entry_id.is_(None)),
        )
        .count()
    )
    if holds:
        restrictions.append("Retención especial / legal hold activo")
    return {
        "classification_code": cls.code if cls else None,
        "classification_name": cls.name if cls else None,
        "provider_decision": export_eval["result"],
        "retention_policy_id": entry.retention_policy_id,
        "retention_disposition": retention.disposition if retention else None,
        "purpose_code": purpose.code if purpose else None,
        "restrictions": restrictions,
        "metadata": sanitize_secret_fields(_json_load(entry.metadata_json) or {}),
    }


def record_access(
    db: Session,
    organization_id: str,
    user_id: str | None,
    *,
    catalog_entry_id: str | None = None,
    resource_ref: str | None = None,
    action: str,
    result: str = "OK",
    purpose_id: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    safe_detail = detail
    if safe_detail and len(safe_detail) > 500:
        safe_detail = safe_detail[:500] + "…"
    row = GovAccessLog(
        organization_id=organization_id,
        user_id=user_id,
        catalog_entry_id=catalog_entry_id,
        resource_ref=resource_ref,
        action=action,
        result=result,
        purpose_id=purpose_id,
        detail=safe_detail,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return access_log_to_dict(row)


def access_log_to_dict(row: GovAccessLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "catalog_entry_id": row.catalog_entry_id,
        "resource_ref": row.resource_ref,
        "action": row.action,
        "result": row.result,
        "purpose_id": row.purpose_id,
        "detail": row.detail,
        "created_at": row.created_at,
    }


def list_access_logs(db: Session, organization_id: str, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        db.query(GovAccessLog)
        .filter(GovAccessLog.organization_id == organization_id)
        .order_by(GovAccessLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [access_log_to_dict(r) for r in rows]


def authorization_to_dict(row: GovAuthorization) -> dict[str, Any]:
    return {
        "id": row.id,
        "auth_type": row.auth_type,
        "purpose": row.purpose,
        "source_ref": row.source_ref,
        "valid_from": row.valid_from,
        "valid_until": row.valid_until,
        "status": row.status,
        "evidence_ref": row.evidence_ref,
        "metadata": sanitize_secret_fields(_json_load(row.metadata_json) or {}),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def create_authorization(db: Session, organization_id: str, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = GovAuthorization(
        organization_id=organization_id,
        auth_type=data["auth_type"],
        purpose=data.get("purpose"),
        source_ref=data.get("source_ref"),
        valid_from=data.get("valid_from"),
        valid_until=data.get("valid_until"),
        status=data.get("status", "VIGENTE"),
        evidence_ref=data.get("evidence_ref"),
        metadata_json=_json_dump(sanitize_secret_fields(data.get("metadata") or {})),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.authorization.create", organization_id=organization_id, user_id=user_id, detail=row.auth_type)
    db.commit()
    db.refresh(row)
    return authorization_to_dict(row)


def list_authorizations(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = db.query(GovAuthorization).filter(GovAuthorization.organization_id == organization_id).all()
    return [authorization_to_dict(r) for r in rows]


def subject_request_to_dict(row: GovSubjectRequest) -> dict[str, Any]:
    return {
        "id": row.id,
        "request_type": row.request_type,
        "subject_ref": row.subject_ref,
        "catalog_entry_id": row.catalog_entry_id,
        "status": row.status,
        "requested_by_id": row.requested_by_id,
        "assigned_to_id": row.assigned_to_id,
        "resolution_note": row.resolution_note,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "resolved_at": row.resolved_at,
    }


def create_subject_request(db: Session, organization_id: str, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = GovSubjectRequest(
        organization_id=organization_id,
        request_type=data["request_type"].upper(),
        subject_ref=data.get("subject_ref"),
        catalog_entry_id=data.get("catalog_entry_id"),
        status="RECIBIDA",
        requested_by_id=user_id,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.request.create", organization_id=organization_id, user_id=user_id, detail=row.request_type)
    db.commit()
    db.refresh(row)
    return subject_request_to_dict(row)


def update_subject_request(
    db: Session,
    organization_id: str,
    request_id: str,
    user_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    row = (
        db.query(GovSubjectRequest)
        .filter(GovSubjectRequest.id == request_id, GovSubjectRequest.organization_id == organization_id)
        .first()
    )
    if not row:
        raise LookupError("Solicitud no encontrada.")
    if "status" in data:
        row.status = data["status"].upper()
        if row.status in ("EJECUTADA", "CERRADA", "RECHAZADA"):
            row.resolved_at = _utcnow()
    if "assigned_to_id" in data:
        row.assigned_to_id = data["assigned_to_id"]
    if "resolution_note" in data:
        row.resolution_note = data["resolution_note"]
    db.flush()
    write_audit(db, action="gov.request.update", organization_id=organization_id, user_id=user_id, detail=request_id)
    db.commit()
    db.refresh(row)
    return subject_request_to_dict(row)


def list_subject_requests(db: Session, organization_id: str, status: str | None = None) -> list[dict[str, Any]]:
    query = db.query(GovSubjectRequest).filter(GovSubjectRequest.organization_id == organization_id)
    if status:
        query = query.filter(GovSubjectRequest.status == status.upper())
    rows = query.order_by(GovSubjectRequest.created_at.desc()).all()
    return [subject_request_to_dict(r) for r in rows]


def record_export(
    db: Session,
    organization_id: str,
    user_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    entry_id = data.get("catalog_entry_id")
    if entry_id:
        entry = get_catalog_entry(db, organization_id, entry_id)
        if not entry:
            raise LookupError("No puede exportar datos de otra organización.")
        export_eval = evaluate_provider_export(db, organization_id, catalog_entry_id=entry_id)
        if export_eval["result"] == "DENEGADO":
            raise ValueError("Exportación denegada por política de proveedor/clasificación.")
    row = GovExportRecord(
        organization_id=organization_id,
        user_id=user_id,
        catalog_entry_id=entry_id,
        reason=data.get("reason"),
        format=data.get("format"),
        result=data.get("result", "OK"),
        metadata_json=_json_dump(sanitize_secret_fields(data.get("metadata") or {})),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.export", organization_id=organization_id, user_id=user_id, detail=entry_id or "general")
    db.commit()
    db.refresh(row)
    return export_to_dict(row)


def export_to_dict(row: GovExportRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "catalog_entry_id": row.catalog_entry_id,
        "reason": row.reason,
        "format": row.format,
        "result": row.result,
        "metadata": sanitize_secret_fields(_json_load(row.metadata_json) or {}),
        "exported_at": row.exported_at,
    }


def list_exports(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(GovExportRecord)
        .filter(GovExportRecord.organization_id == organization_id)
        .order_by(GovExportRecord.exported_at.desc())
        .all()
    )
    return [export_to_dict(r) for r in rows]


def create_legal_hold(db: Session, organization_id: str, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = GovLegalHold(
        organization_id=organization_id,
        catalog_entry_id=data.get("catalog_entry_id"),
        scope_ref=data.get("scope_ref"),
        reason=data["reason"],
        hold_until=data.get("hold_until"),
        created_by_id=user_id,
        status="ACTIVO",
    )
    db.add(row)
    db.flush()
    write_audit(db, action="gov.legal_hold.create", organization_id=organization_id, user_id=user_id, detail=row.reason[:120])
    db.commit()
    db.refresh(row)
    return legal_hold_to_dict(row)


def release_legal_hold(db: Session, organization_id: str, hold_id: str, user_id: str) -> dict[str, Any]:
    row = (
        db.query(GovLegalHold)
        .filter(GovLegalHold.id == hold_id, GovLegalHold.organization_id == organization_id)
        .first()
    )
    if not row:
        raise LookupError("Bloqueo de retención no encontrado.")
    row.status = "LIBERADO"
    row.released_at = _utcnow()
    db.flush()
    write_audit(db, action="gov.legal_hold.release", organization_id=organization_id, user_id=user_id, detail=hold_id)
    db.commit()
    db.refresh(row)
    return legal_hold_to_dict(row)


def legal_hold_to_dict(row: GovLegalHold) -> dict[str, Any]:
    return {
        "id": row.id,
        "catalog_entry_id": row.catalog_entry_id,
        "scope_ref": row.scope_ref,
        "reason": row.reason,
        "status": row.status,
        "hold_until": row.hold_until,
        "created_by_id": row.created_by_id,
        "created_at": row.created_at,
        "released_at": row.released_at,
    }


def list_legal_holds(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = db.query(GovLegalHold).filter(GovLegalHold.organization_id == organization_id).all()
    return [legal_hold_to_dict(r) for r in rows]


def upsert_org_policy(db: Session, organization_id: str, user_id: str, policy_key: str, value: Any) -> dict[str, Any]:
    row = (
        db.query(GovOrgPolicySetting)
        .filter(GovOrgPolicySetting.organization_id == organization_id, GovOrgPolicySetting.policy_key == policy_key)
        .first()
    )
    if not row:
        row = GovOrgPolicySetting(organization_id=organization_id, policy_key=policy_key)
        db.add(row)
    row.policy_value_json = _json_dump(value)
    db.flush()
    write_audit(db, action="gov.org_policy.update", organization_id=organization_id, user_id=user_id, detail=policy_key)
    db.commit()
    db.refresh(row)
    return {"policy_key": row.policy_key, "policy_value": _json_load(row.policy_value_json)}


def upsert_global_policy(db: Session, user_id: str, policy_key: str, value: Any, is_mandatory: bool = True) -> dict[str, Any]:
    row = db.query(GovGlobalPolicy).filter(GovGlobalPolicy.policy_key == policy_key).first()
    if not row:
        row = GovGlobalPolicy(policy_key=policy_key)
        db.add(row)
    row.policy_value_json = _json_dump(value)
    row.is_mandatory = is_mandatory
    db.flush()
    write_audit(db, action="gov.global_policy.update", organization_id=None, user_id=user_id, detail=policy_key)
    db.commit()
    db.refresh(row)
    return {
        "policy_key": row.policy_key,
        "policy_value": _json_load(row.policy_value_json),
        "is_mandatory": row.is_mandatory,
    }


def compute_risk(db: Session, organization_id: str, catalog_entry_id: str) -> dict[str, Any]:
    entry = get_catalog_entry(db, organization_id, catalog_entry_id)
    if not entry:
        raise LookupError("Entrada no encontrada.")
    score = 0
    factors: list[str] = []
    cls = db.get(GovClassificationLevel, entry.classification_level_id) if entry.classification_level_id else None
    if cls:
        score += cls.sensitivity_rank * 15
        factors.append(f"Sensibilidad {cls.name}")
    else:
        score += 20
        factors.append("Sin clasificación")
    if not entry.retention_policy_id:
        score += 10
        factors.append("Retención no definida")
    export_eval = evaluate_provider_export(db, organization_id, catalog_entry_id=catalog_entry_id)
    if export_eval["result"] == "PERMITIDO":
        score += 15
        factors.append("Exposición a proveedores permitida")
    elif export_eval["result"] == "PERMITIDO_CON_TRANSFORMACIÓN":
        score += 8
        factors.append("Exposición con transformación")
    exports = (
        db.query(func.count(GovExportRecord.id))
        .filter(GovExportRecord.organization_id == organization_id, GovExportRecord.catalog_entry_id == catalog_entry_id)
        .scalar()
        or 0
    )
    if exports:
        score += min(exports * 3, 15)
        factors.append(f"Exportaciones registradas: {exports}")
    access_count = (
        db.query(func.count(GovAccessLog.id))
        .filter(GovAccessLog.organization_id == organization_id, GovAccessLog.catalog_entry_id == catalog_entry_id)
        .scalar()
        or 0
    )
    if access_count > 50:
        score += 10
        factors.append("Alto volumen de accesos")
    if not entry.functional_owner:
        score += 5
        factors.append("Sin propietario funcional")
    if score >= 60:
        level = "CRÍTICO"
    elif score >= 40:
        level = "ALTO"
    elif score >= 20:
        level = "MEDIO"
    else:
        level = "BAJO"
    return {
        "catalog_entry_id": catalog_entry_id,
        "risk_level": level,
        "score": score,
        "factors": factors,
    }


def finding_to_dict(row: GovFinding) -> dict[str, Any]:
    return {
        "id": row.id,
        "finding_type": row.finding_type,
        "severity": row.severity,
        "catalog_entry_id": row.catalog_entry_id,
        "description": row.description,
        "status": row.status,
        "detected_at": row.detected_at,
        "metadata": _json_load(row.metadata_json),
    }


def scan_findings(db: Session, organization_id: str, user_id: str | None = None) -> list[dict[str, Any]]:
    ensure_org_defaults(db, organization_id)
    created: list[dict[str, Any]] = []
    entries = db.query(GovCatalogEntry).filter(GovCatalogEntry.organization_id == organization_id).all()
    for entry in entries:
        if not entry.classification_level_id:
            row = GovFinding(
                organization_id=organization_id,
                finding_type="SIN_CLASIFICACION",
                severity="MEDIA",
                catalog_entry_id=entry.id,
                description=f"Fuente '{entry.name}' sin clasificación asignada.",
            )
            db.add(row)
            db.flush()
            created.append(finding_to_dict(row))
        if not entry.retention_policy_id:
            row = GovFinding(
                organization_id=organization_id,
                finding_type="RETENCION_AUSENTE",
                severity="MEDIA",
                catalog_entry_id=entry.id,
                description=f"Fuente '{entry.name}' sin política de retención.",
            )
            db.add(row)
            db.flush()
            created.append(finding_to_dict(row))
        if not entry.functional_owner:
            row = GovFinding(
                organization_id=organization_id,
                finding_type="SIN_PROPIETARIO",
                severity="BAJA",
                catalog_entry_id=entry.id,
                description=f"Fuente '{entry.name}' sin propietario funcional.",
            )
            db.add(row)
            db.flush()
            created.append(finding_to_dict(row))
        export_eval = evaluate_provider_export(db, organization_id, catalog_entry_id=entry.id)
        cls = db.get(GovClassificationLevel, entry.classification_level_id) if entry.classification_level_id else None
        if cls and cls.sensitivity_rank >= 3 and export_eval["result"] == "PERMITIDO":
            row = GovFinding(
                organization_id=organization_id,
                finding_type="EXPORTACION_RESTRINGIDA_PERMITIDA",
                severity="ALTA",
                catalog_entry_id=entry.id,
                description=f"Dato restringido '{entry.name}' con exportación a proveedor permitida.",
            )
            db.add(row)
            db.flush()
            created.append(finding_to_dict(row))
        if export_eval["result"] == "PERMITIDO" and cls and cls.sensitivity_rank >= 2:
            policies = list_provider_policies(db, organization_id)
            if not policies:
                row = GovFinding(
                    organization_id=organization_id,
                    finding_type="SIN_POLITICA_PROVEEDOR",
                    severity="ALTA",
                    catalog_entry_id=entry.id,
                    description=f"Dato sensible '{entry.name}' sin política de proveedor definida.",
                )
                db.add(row)
                created.append(finding_to_dict(row))
    db.commit()
    if user_id:
        write_audit(db, action="gov.findings.scan", organization_id=organization_id, user_id=user_id, detail=str(len(created)))
    return created


def list_findings(db: Session, organization_id: str, status: str | None = None) -> list[dict[str, Any]]:
    query = db.query(GovFinding).filter(GovFinding.organization_id == organization_id)
    if status:
        query = query.filter(GovFinding.status == status.upper())
    rows = query.order_by(GovFinding.detected_at.desc()).all()
    return [finding_to_dict(r) for r in rows]


def corrective_action_to_dict(row: GovCorrectiveAction) -> dict[str, Any]:
    return {
        "id": row.id,
        "finding_id": row.finding_id,
        "responsible_user_id": row.responsible_user_id,
        "target_date": row.target_date,
        "status": row.status,
        "outcome": row.outcome,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def create_corrective_action(db: Session, organization_id: str, data: dict[str, Any]) -> dict[str, Any]:
    finding = (
        db.query(GovFinding)
        .filter(GovFinding.id == data["finding_id"], GovFinding.organization_id == organization_id)
        .first()
    )
    if not finding:
        raise LookupError("Hallazgo no encontrado.")
    row = GovCorrectiveAction(
        organization_id=organization_id,
        finding_id=data["finding_id"],
        responsible_user_id=data.get("responsible_user_id"),
        target_date=data.get("target_date"),
        status=data.get("status", "PENDIENTE"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return corrective_action_to_dict(row)


def list_corrective_actions(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = db.query(GovCorrectiveAction).filter(GovCorrectiveAction.organization_id == organization_id).all()
    return [corrective_action_to_dict(r) for r in rows]


def detect_purpose_mismatch(
    db: Session,
    organization_id: str,
    catalog_entry_id: str,
    declared_purpose_id: str | None,
    actual_purpose_id: str | None,
) -> bool:
    entry = get_catalog_entry(db, organization_id, catalog_entry_id)
    if not entry:
        return False
    expected = entry.purpose_id
    if expected and actual_purpose_id and expected != actual_purpose_id:
        record_access(
            db,
            organization_id,
            None,
            catalog_entry_id=catalog_entry_id,
            action="USO_FUERA_PROPOSITO",
            result="ALERTA",
            purpose_id=actual_purpose_id,
            detail="Uso detectado fuera del propósito declarado",
        )
        return True
    if declared_purpose_id and actual_purpose_id and declared_purpose_id != actual_purpose_id:
        return True
    return False


def mask_field(field_type: str, value: str) -> dict[str, str]:
    return {"original_length": str(len(value or "")), "masked": apply_mask(field_type, value)}


def dashboard_summary(db: Session, organization_id: str) -> dict[str, Any]:
    ensure_org_defaults(db, organization_id)
    total = db.query(func.count(GovCatalogEntry.id)).filter(GovCatalogEntry.organization_id == organization_id).scalar() or 0
    unclassified = (
        db.query(func.count(GovCatalogEntry.id))
        .filter(GovCatalogEntry.organization_id == organization_id, GovCatalogEntry.classification_level_id.is_(None))
        .scalar()
        or 0
    )
    high_risk = 0
    for entry in db.query(GovCatalogEntry).filter(GovCatalogEntry.organization_id == organization_id).limit(200).all():
        risk = compute_risk(db, organization_id, entry.id)
        if risk["risk_level"] in ("ALTO", "CRÍTICO"):
            high_risk += 1
    open_requests = (
        db.query(func.count(GovSubjectRequest.id))
        .filter(
            GovSubjectRequest.organization_id == organization_id,
            GovSubjectRequest.status.in_(["RECIBIDA", "EN_REVISIÓN", "APROBADA"]),
        )
        .scalar()
        or 0
    )
    open_findings = (
        db.query(func.count(GovFinding.id))
        .filter(GovFinding.organization_id == organization_id, GovFinding.status == "ABIERTO")
        .scalar()
        or 0
    )
    pending_actions = (
        db.query(func.count(GovCorrectiveAction.id))
        .filter(GovCorrectiveAction.organization_id == organization_id, GovCorrectiveAction.status == "PENDIENTE")
        .scalar()
        or 0
    )
    exports_count = (
        db.query(func.count(GovExportRecord.id))
        .filter(GovExportRecord.organization_id == organization_id)
        .scalar()
        or 0
    )
    retention_overdue = 0
    for entry in db.query(GovCatalogEntry).filter(GovCatalogEntry.organization_id == organization_id).all():
        if not entry.retention_policy_id:
            continue
        pol = db.get(GovRetentionPolicy, entry.retention_policy_id)
        if not pol or pol.duration_unit == "INDEFINIDO":
            continue
        if pol.duration_value and entry.created_at:
            delta_days = 0
            if pol.duration_unit == "DIAS":
                delta_days = pol.duration_value
            elif pol.duration_unit == "MESES":
                delta_days = pol.duration_value * 30
            elif pol.duration_unit == "ANOS":
                delta_days = pol.duration_value * 365
            if delta_days and entry.created_at + timedelta(days=delta_days) < _utcnow():
                holds = (
                    db.query(GovLegalHold)
                    .filter(
                        GovLegalHold.organization_id == organization_id,
                        GovLegalHold.status == "ACTIVO",
                        (GovLegalHold.catalog_entry_id == entry.id) | (GovLegalHold.catalog_entry_id.is_(None)),
                    )
                    .count()
                )
                if not holds:
                    retention_overdue += 1
    return {
        "fuentes_catalogadas": total,
        "sin_clasificar": unclassified,
        "riesgo_alto": high_risk,
        "retencion_vencida": retention_overdue,
        "exportaciones": exports_count,
        "solicitudes_abiertas": open_requests,
        "hallazgos_abiertos": open_findings,
        "acciones_pendientes": pending_actions,
    }
