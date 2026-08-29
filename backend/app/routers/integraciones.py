"""Router — Integraciones reales y conectores (1330)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_integration import ConnectorCreate, ConnectorUpdate, ExecuteRequest, WebhookReceiveRequest
from app.services import integration_service as svc

router = APIRouter(prefix="/api/integraciones", tags=["integraciones"])


def _validation_error(exc: svc.IntegrationValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/catalogo")
def get_catalog(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.view", db)
    return svc.list_catalog()


@router.get("/conectores")
def list_connectors(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.view", db)
    return [svc.connector_to_dict(c) for c in svc.list_connectors(db, user.organization_id)]


@router.post("/conectores", status_code=status.HTTP_201_CREATED)
def create_connector(body: ConnectorCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.create", db)
    try:
        row = svc.create_connector(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        out = svc.connector_to_dict(row)
        token_once = getattr(row, "_webhook_token_once", None)
        if token_once:
            out["webhook_token"] = token_once
            out["webhook_url_hint"] = f"/api/integraciones/webhook/{row.id}"
        return out
    except svc.IntegrationValidationError as exc:
        db.rollback()
        raise _validation_error(exc) from exc


@router.get("/conectores/{connector_id}")
def get_connector(connector_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.view", db)
    return svc.connector_to_dict(svc._get_connector(db, user.organization_id, connector_id))


@router.put("/conectores/{connector_id}")
def update_connector(connector_id: str, body: ConnectorUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.configure", db)
    try:
        row = svc.update_connector(db, user.organization_id, connector_id, body.model_dump(exclude_none=True), user.id)
        db.commit()
        return svc.connector_to_dict(row)
    except svc.IntegrationValidationError as exc:
        db.rollback()
        raise _validation_error(exc) from exc


@router.post("/conectores/{connector_id}/probar")
def test_connector(connector_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.test", db)
    result = svc.test_connection(db, user.organization_id, connector_id, user.id)
    db.commit()
    return result


@router.post("/conectores/{connector_id}/ejecutar")
def execute_connector(connector_id: str, body: ExecuteRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.execute", db)
    try:
        result = svc.execute_connector(
            db, user.organization_id, connector_id, user.id,
            idempotency_key=body.idempotency_key, payload=body.payload,
        )
        db.commit()
        return result
    except svc.IntegrationValidationError as exc:
        db.commit()
        raise _validation_error(exc) from exc


@router.get("/conectores/{connector_id}/ejecuciones")
def list_executions(connector_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.view", db)
    return svc.list_executions(db, user.organization_id, connector_id)


@router.get("/conectores/{connector_id}/salud")
def get_health(connector_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.view", db)
    return svc.get_health(db, user.organization_id, connector_id)


@router.post("/webhook/{connector_id}")
def receive_webhook(connector_id: str, body: WebhookReceiveRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "integraciones.execute", db)
    try:
        result = svc.receive_webhook(db, user.organization_id, connector_id, body.token, body.payload)
        db.commit()
        return result
    except svc.IntegrationValidationError as exc:
        db.rollback()
        raise _validation_error(exc) from exc
