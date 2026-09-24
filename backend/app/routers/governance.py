"""API de gobierno de datos — BLOQUE 1350."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_governance import (
    AccessLogIn,
    AccessLogOut,
    AiUsageGrantIn,
    AiUsageGrantOut,
    AuthorizationIn,
    AuthorizationOut,
    CatalogEntryIn,
    CatalogEntryOut,
    CatalogEntryPatch,
    ClassificationLevelIn,
    ClassificationLevelOut,
    CorrectiveActionIn,
    CorrectiveActionOut,
    DashboardOut,
    DataCategoryIn,
    DataCategoryOut,
    ExportRecordIn,
    ExportRecordOut,
    FindingOut,
    GlobalPolicyIn,
    LegalHoldIn,
    LegalHoldOut,
    LineageEventIn,
    LineageEventOut,
    MaskIn,
    MaskOut,
    OrgPolicyIn,
    ProviderExportEvalIn,
    ProviderExportEvalOut,
    ProviderPolicyIn,
    ProviderPolicyOut,
    PurposeOut,
    RetentionPolicyIn,
    RetentionPolicyOut,
    RiskOut,
    SubjectRequestIn,
    SubjectRequestOut,
    SubjectRequestPatch,
)
from app.services import governance_service as svc
from app.services.governance_adapters import GovernanceConnectorAdapter, GovernanceProviderAdapter

router = APIRouter(prefix="/api/gobierno-datos", tags=["gobierno-datos"])


def _lookup(exc: LookupError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


def _value(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.dashboard_summary(db, user.organization_id)


@router.get("/clasificaciones", response_model=list[ClassificationLevelOut])
def list_classifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.list_classification_levels(db, user.organization_id)


@router.post("/clasificaciones", response_model=ClassificationLevelOut, status_code=status.HTTP_201_CREATED)
def create_classification(
    body: ClassificationLevelIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.classify", db)
    return svc.create_classification_level(
        db,
        user.organization_id,
        code=body.code,
        name=body.name,
        sensitivity_rank=body.sensitivity_rank,
        description=body.description,
        user_id=user.id,
    )


@router.get("/categorias", response_model=list[DataCategoryOut])
def list_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.list_categories(db, user.organization_id)


@router.post("/categorias", response_model=DataCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    body: DataCategoryIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.classify", db)
    return svc.create_category(
        db,
        user.organization_id,
        code=body.code,
        name=body.name,
        description=body.description,
        user_id=user.id,
    )


@router.get("/propositos", response_model=list[PurposeOut])
def list_purposes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.list_purposes(db, user.organization_id)


@router.get("/catalogo", response_model=list[CatalogEntryOut])
def list_catalog(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.view", db)
    return svc.list_catalog_entries(db, user.organization_id, status=status_filter)


@router.post("/catalogo", response_model=CatalogEntryOut, status_code=status.HTTP_201_CREATED)
def create_catalog(
    body: CatalogEntryIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.classify", db)
    return svc.create_catalog_entry(db, user.organization_id, user.id, body.model_dump())


@router.get("/catalogo/{entry_id}", response_model=CatalogEntryOut)
def get_catalog(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    row = svc.get_catalog_entry(db, user.organization_id, entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Entrada no encontrada.")
    svc.record_access(
        db,
        user.organization_id,
        user.id,
        catalog_entry_id=entry_id,
        action="CONSULTA",
        result="OK",
    )
    return svc.catalog_to_dict(row, db)


@router.patch("/catalogo/{entry_id}", response_model=CatalogEntryOut)
def patch_catalog(
    entry_id: str,
    body: CatalogEntryPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.classify", db)
    try:
        return svc.update_catalog_entry(
            db,
            user.organization_id,
            entry_id,
            user.id,
            body.model_dump(exclude_unset=True),
        )
    except LookupError as exc:
        raise _lookup(exc) from exc


@router.get("/catalogo/{entry_id}/riesgo", response_model=RiskOut)
def catalog_risk(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    try:
        return svc.compute_risk(db, user.organization_id, entry_id)
    except LookupError as exc:
        raise _lookup(exc) from exc


@router.get("/retencion", response_model=list[RetentionPolicyOut])
def list_retention(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.retention", db)
    return svc.list_retention_policies(db, user.organization_id)


@router.post("/retencion", response_model=RetentionPolicyOut, status_code=status.HTTP_201_CREATED)
def create_retention(
    body: RetentionPolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.retention", db)
    return svc.create_retention_policy(db, user.organization_id, user.id, body.model_dump())


@router.get("/catalogo/{entry_id}/linaje", response_model=list[LineageEventOut])
def list_lineage(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    try:
        return svc.list_lineage(db, user.organization_id, entry_id)
    except LookupError as exc:
        raise _lookup(exc) from exc


@router.post("/linaje", response_model=LineageEventOut, status_code=status.HTTP_201_CREATED)
def add_lineage(
    body: LineageEventIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.manage_policy", db)
    try:
        return svc.add_lineage_event(db, user.organization_id, user.id, body.model_dump())
    except LookupError as exc:
        raise _lookup(exc) from exc


@router.get("/usos-ia", response_model=list[AiUsageGrantOut])
def list_ai_usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.list_ai_usage_grants(db, user.organization_id)


@router.post("/usos-ia", response_model=AiUsageGrantOut, status_code=status.HTTP_201_CREATED)
def create_ai_usage(
    body: AiUsageGrantIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.manage_policy", db)
    return svc.create_ai_usage_grant(db, user.organization_id, body.model_dump())


@router.get("/politicas-proveedor", response_model=list[ProviderPolicyOut])
def list_provider_policies(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.list_provider_policies(db, user.organization_id)


@router.post("/politicas-proveedor", response_model=ProviderPolicyOut, status_code=status.HTTP_201_CREATED)
def create_provider_policy(
    body: ProviderPolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.manage_policy", db)
    org_id: str | None = user.organization_id
    if body.is_mandatory_global:
        check_permission(user, "platform.organization.view", db)
        org_id = None
    return svc.create_provider_policy(db, org_id, user.id, body.model_dump())


@router.post("/evaluar-proveedor", response_model=ProviderExportEvalOut)
def evaluate_provider(
    body: ProviderExportEvalIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.view", db)
    return svc.evaluate_provider_export(
        db,
        user.organization_id,
        catalog_entry_id=body.catalog_entry_id,
        classification_level_id=body.classification_level_id,
        category_id=body.category_id,
        provider=body.provider,
    )


@router.post("/adaptador-1270/evaluar", response_model=ProviderExportEvalOut)
def adapter_1270_evaluate(
    body: ProviderExportEvalIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.view", db)
    adapter = GovernanceProviderAdapter(db)
    decision = adapter.can_send_to_provider(
        user.organization_id,
        catalog_entry_id=body.catalog_entry_id,
        classification_level_id=body.classification_level_id,
        category_id=body.category_id,
        provider=body.provider,
    )
    return {
        "result": decision.result,
        "reasons": decision.reasons,
        "minimization_action": decision.minimization_action,
        "policy_id": decision.policy_id,
    }


@router.get("/adaptador-1330/catalogo/{entry_id}")
def adapter_1330_policy(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    adapter = GovernanceConnectorAdapter(db)
    view = adapter.get_resource_policy(user.organization_id, entry_id)
    if view is None:
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    return {
        "classification_code": view.classification_code,
        "classification_name": view.classification_name,
        "provider_decision": view.provider_decision,
        "retention_policy_id": view.retention_policy_id,
        "retention_disposition": view.retention_disposition,
        "purpose_code": view.purpose_code,
        "restrictions": view.restrictions,
        "metadata": view.metadata,
    }


@router.get("/accesos", response_model=list[AccessLogOut])
def list_accesses(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.audit", db)
    return svc.list_access_logs(db, user.organization_id, limit=limit)


@router.post("/accesos", response_model=AccessLogOut, status_code=status.HTTP_201_CREATED)
def record_access_endpoint(
    body: AccessLogIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.audit", db)
    return svc.record_access(
        db,
        user.organization_id,
        user.id,
        catalog_entry_id=body.catalog_entry_id,
        resource_ref=body.resource_ref,
        action=body.action,
        result=body.result,
        purpose_id=body.purpose_id,
        detail=body.detail,
    )


@router.get("/autorizaciones", response_model=list[AuthorizationOut])
def list_authorizations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.list_authorizations(db, user.organization_id)


@router.post("/autorizaciones", response_model=AuthorizationOut, status_code=status.HTTP_201_CREATED)
def create_authorization(
    body: AuthorizationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.manage_policy", db)
    return svc.create_authorization(db, user.organization_id, user.id, body.model_dump())


@router.get("/solicitudes", response_model=list[SubjectRequestOut])
def list_requests(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.requests", db)
    return svc.list_subject_requests(db, user.organization_id, status=status_filter)


@router.post("/solicitudes", response_model=SubjectRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    body: SubjectRequestIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.requests", db)
    return svc.create_subject_request(db, user.organization_id, user.id, body.model_dump())


@router.patch("/solicitudes/{request_id}", response_model=SubjectRequestOut)
def patch_request(
    request_id: str,
    body: SubjectRequestPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.requests", db)
    try:
        return svc.update_subject_request(
            db,
            user.organization_id,
            request_id,
            user.id,
            body.model_dump(exclude_unset=True),
        )
    except LookupError as exc:
        raise _lookup(exc) from exc


@router.get("/exportaciones", response_model=list[ExportRecordOut])
def list_exports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.export", db)
    return svc.list_exports(db, user.organization_id)


@router.post("/exportaciones", response_model=ExportRecordOut, status_code=status.HTTP_201_CREATED)
def create_export(
    body: ExportRecordIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.export", db)
    try:
        return svc.record_export(db, user.organization_id, user.id, body.model_dump())
    except (LookupError, ValueError) as exc:
        if isinstance(exc, LookupError):
            raise _lookup(exc) from exc
        raise _value(exc) from exc


@router.get("/legal-hold", response_model=list[LegalHoldOut])
def list_legal_holds(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.retention", db)
    return svc.list_legal_holds(db, user.organization_id)


@router.post("/legal-hold", response_model=LegalHoldOut, status_code=status.HTTP_201_CREATED)
def create_legal_hold(
    body: LegalHoldIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.retention", db)
    return svc.create_legal_hold(db, user.organization_id, user.id, body.model_dump())


@router.post("/legal-hold/{hold_id}/liberar", response_model=LegalHoldOut)
def release_hold(hold_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.retention", db)
    try:
        return svc.release_legal_hold(db, user.organization_id, hold_id, user.id)
    except LookupError as exc:
        raise _lookup(exc) from exc


@router.post("/politicas-organizacion", status_code=status.HTTP_200_OK)
def upsert_org_policy(
    body: OrgPolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.manage_policy", db)
    return svc.upsert_org_policy(db, user.organization_id, user.id, body.policy_key, body.policy_value)


@router.post("/politicas-globales", status_code=status.HTTP_200_OK)
def upsert_global_policy(
    body: GlobalPolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "platform.organization.view", db)
    return svc.upsert_global_policy(db, user.id, body.policy_key, body.policy_value, body.is_mandatory)


@router.get("/hallazgos", response_model=list[FindingOut])
def list_findings(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.audit", db)
    return svc.list_findings(db, user.organization_id, status=status_filter)


@router.post("/hallazgos/escanear", response_model=list[FindingOut])
def scan_findings_endpoint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.audit", db)
    return svc.scan_findings(db, user.organization_id, user.id)


@router.get("/acciones", response_model=list[CorrectiveActionOut])
def list_actions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.audit", db)
    return svc.list_corrective_actions(db, user.organization_id)


@router.post("/acciones", response_model=CorrectiveActionOut, status_code=status.HTTP_201_CREATED)
def create_action(
    body: CorrectiveActionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "datos.manage_policy", db)
    try:
        return svc.create_corrective_action(db, user.organization_id, body.model_dump())
    except LookupError as exc:
        raise _lookup(exc) from exc


@router.post("/enmascarar", response_model=MaskOut)
def mask_value(body: MaskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "datos.view", db)
    return svc.mask_field(body.field_type, body.value)
