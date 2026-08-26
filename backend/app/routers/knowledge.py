from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_850 import KnowledgeCreateRequest, KnowledgeIngestRequest, KnowledgeUpdateRequest
from app.services import knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("")
def list_knowledge(
    search: str | None = None,
    source_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.view", db)
    return knowledge_service.list_knowledge_sources(
        db, user.organization_id, search=search, source_type=source_type, status=status,
    )


@router.get("/employees/{employee_id}/assignments")
def employee_knowledge_assignments(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.view", db)
    return knowledge_service.list_employee_knowledge(db, user.organization_id, employee_id)


@router.post("/employees/{employee_id}/assign/{source_id}")
def assign_knowledge(
    employee_id: str,
    source_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    result = knowledge_service.assign_knowledge(db, user.organization_id, user.id, employee_id, source_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.delete("/employees/{employee_id}/assign/{source_id}")
def remove_knowledge(
    employee_id: str,
    source_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    result = knowledge_service.remove_knowledge(db, user.organization_id, user.id, employee_id, source_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/{source_id}")
def get_knowledge(source_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.view", db)
    detail = knowledge_service.get_knowledge_detail(db, user.organization_id, source_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuente no encontrada")
    return detail


@router.post("")
def create_knowledge(
    body: KnowledgeCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    result = knowledge_service.create_knowledge_source(
        db, user.organization_id, user.id,
        name=body.name, source_type=body.source_type, code=body.code,
        description=body.description, configuration=body.configuration, secret_ref=body.secret_ref,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.patch("/{source_id}")
def update_knowledge(
    source_id: str,
    body: KnowledgeUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    result = knowledge_service.update_knowledge_source(
        db, user.organization_id, user.id, source_id, body.model_dump(exclude_none=True),
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/{source_id}/activate")
def activate_knowledge(source_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.manage", db)
    return knowledge_service.set_knowledge_status(db, user.organization_id, user.id, source_id, active=True)


@router.post("/{source_id}/deactivate")
def deactivate_knowledge(source_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.manage", db)
    return knowledge_service.set_knowledge_status(db, user.organization_id, user.id, source_id, active=False)


@router.post("/{source_id}/ingest")
def ingest_knowledge(
    source_id: str,
    body: KnowledgeIngestRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    return knowledge_service.ingest_knowledge(
        db, user.organization_id, user.id, source_id,
        content=body.content, content_type=body.content_type,
    )
