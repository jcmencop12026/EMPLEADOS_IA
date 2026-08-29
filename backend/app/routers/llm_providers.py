"""API de proveedores IA y LLM Gateway."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.gateway import gateway as llm_gateway
from app.models import User
from app.permissions import check_permission
from app.schemas_llm import (
    LlmCompleteRequest,
    LlmCompleteResponse,
    LlmInferenceLogOut,
    LlmProviderCreate,
    LlmProviderOut,
    LlmProviderUpdate,
    LlmTestConnectionResult,
)
from app.services.llm_execution import run_llm_for_task
from app.services.llm_provider_service import (
    create_provider,
    get_provider,
    list_inference_logs,
    list_providers,
    update_provider,
)

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/providers", response_model=list[LlmProviderOut])
def api_list_providers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "llm.view", db)
    return list_providers(db, user.organization_id)


@router.post("/providers", response_model=LlmProviderOut, status_code=201)
def api_create_provider(
    data: LlmProviderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "llm.manage", db)
    return create_provider(db, user.organization_id, data, user_id=user.id)


@router.get("/providers/{provider_id}", response_model=LlmProviderOut)
def api_get_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "llm.view", db)
    row = get_provider(db, user.organization_id, provider_id)
    if not row:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    return row


@router.patch("/providers/{provider_id}", response_model=LlmProviderOut)
def api_update_provider(
    provider_id: str,
    data: LlmProviderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "llm.manage", db)
    row = update_provider(db, user.organization_id, provider_id, data, user_id=user.id)
    if not row:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    return row


@router.post("/providers/{provider_id}/test", response_model=LlmTestConnectionResult)
def api_test_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "llm.manage", db)
    result = llm_gateway.test_provider_connection(db, user.organization_id, provider_id)
    if result.success:
        return LlmTestConnectionResult(
            success=True,
            status="disponible",
            message="Conexión exitosa con el proveedor.",
            provider=result.provider,
            model=result.model,
            latency_ms=result.latency_ms,
        )
    error = result.error
    status_map = {
        "AUTH_ERROR": "autenticacion_fallida",
        "TIMEOUT": "timeout",
        "MODEL_NOT_FOUND": "modelo_no_disponible",
        "CONFIGURATION_ERROR": "configuracion_invalida",
    }
    category = error.category if error else "ERROR"
    return LlmTestConnectionResult(
        success=False,
        status=status_map.get(str(category), "error"),
        message=error.message if error else "Error de conexión.",
        provider=result.provider,
        model=result.model,
        latency_ms=result.latency_ms,
        error_category=str(category) if error else None,
    )


@router.get("/inference-logs", response_model=list[LlmInferenceLogOut])
def api_inference_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "llm.view", db)
    return list_inference_logs(db, user.organization_id, limit=min(limit, 200))


@router.post("/complete", response_model=LlmCompleteResponse)
def api_complete(
    data: LlmCompleteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "llm.use", db)
    from app.orchestration_models import AIEmployee

    employee = None
    if data.employee_id:
        employee = (
            db.query(AIEmployee)
            .filter(AIEmployee.id == data.employee_id, AIEmployee.organization_id == user.organization_id)
            .first()
        )
    context = {"include_knowledge": data.include_knowledge}
    output = run_llm_for_task(
        db,
        organization_id=user.organization_id,
        employee=employee,
        user_prompt=data.prompt,
        context=context,
        user_id=user.id,
    )
    if output.get("error"):
        return LlmCompleteResponse(
            text=None,
            error=output.get("error"),
            trace_id=output.get("trace_id"),
            fallback_used=output.get("fallback_used", False),
        )
    return LlmCompleteResponse(
        text=output.get("response"),
        provider=output.get("provider"),
        model=output.get("model"),
        tokens_in=output.get("tokens_in"),
        tokens_out=output.get("tokens_out"),
        tokens_total=output.get("tokens_total"),
        latency_ms=output.get("latency_ms"),
        finish_reason=output.get("finish_reason"),
        trace_id=output.get("trace_id"),
        fallback_used=output.get("fallback_used", False),
    )
