from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_850 import KnowledgeCreateRequest, KnowledgeIngestRequest, KnowledgeUpdateRequest
from app.schemas_knowledge import (
    EmployeeKnowledgeGrantOut,
    KnowledgeActivityOut,
    KnowledgeDocumentDetail,
    KnowledgeDocumentOut,
    KnowledgeDocumentUpdate,
    KnowledgeRetrieveFragment,
    KnowledgeRetrieveRequest,
    KnowledgeSearchResult,
    KnowledgeTextCreate,
)
from app.services import knowledge_service
from app.services.knowledge_retrieval import retrieve_knowledge

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def _handle_value_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _handle_lookup(exc: LookupError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


# --- Centro de conocimiento empresarial (CONOCIMIENTO-930) ---


@router.get("", response_model=list[KnowledgeDocumentOut])
def list_documents(
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    source_type: str | None = None,
    file_type: str | None = None,
    active_only: bool | None = None,
    sort: str = "desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.view", db)
    return knowledge_service.list_documents(
        db,
        user.organization_id,
        search=search,
        status=status_filter,
        source_type=source_type,
        file_type=file_type,
        active_only=active_only,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.post("/text", response_model=KnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
def create_text_document(
    body: KnowledgeTextCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.upload", db)
    try:
        return knowledge_service.create_text_document(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            name=body.name,
            content=body.content,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.post("/upload", response_model=KnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    name: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.upload", db)
    data = await file.read()
    filename = file.filename or "documento.txt"
    try:
        return knowledge_service.create_file_document(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            filename=name or filename,
            data=data,
            mime_type=file.content_type,
        )
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.get("/search", response_model=list[KnowledgeSearchResult])
def search_knowledge(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.view", db)
    return knowledge_service.search_documents(db, user.organization_id, q, limit=limit)


@router.post("/retrieve", response_model=list[KnowledgeRetrieveFragment])
def retrieve_knowledge_endpoint(
    body: KnowledgeRetrieveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.use", db)
    fragments = retrieve_knowledge(
        db,
        tenant_id=user.organization_id,
        query=body.query,
        filters=body.filters,
        limit=body.limit,
        context=body.context,
        employee_id=body.employee_id,
    )
    seen: set[str] = set()
    for fragment in fragments:
        doc_id = fragment["document_id"]
        if doc_id in seen:
            continue
        seen.add(doc_id)
        knowledge_service.log_consultation(
            db,
            organization_id=user.organization_id,
            document_id=doc_id,
            user_id=user.id,
            query=body.query,
        )
    return fragments


@router.get("/employees/{employee_id}/grants", response_model=list[EmployeeKnowledgeGrantOut])
def list_employee_grants(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.manage", db)
    try:
        return knowledge_service.list_employee_grants(db, user.organization_id, employee_id)
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.post("/employees/{employee_id}/grant/{document_id}", response_model=EmployeeKnowledgeGrantOut)
def grant_document(
    employee_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    try:
        return knowledge_service.grant_document_to_employee(
            db,
            organization_id=user.organization_id,
            employee_id=employee_id,
            document_id=document_id,
            user_id=user.id,
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.delete("/employees/{employee_id}/grant/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_document(
    employee_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    try:
        knowledge_service.revoke_document_from_employee(
            db,
            organization_id=user.organization_id,
            employee_id=employee_id,
            document_id=document_id,
            user_id=user.id,
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


# --- Catálogo de fuentes (CAPABILITIES-850 / preint #10) ---


@router.get("/sources")
def list_knowledge_sources(
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


@router.get("/sources/{source_id}")
def get_knowledge_source_detail(
    source_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.view", db)
    detail = knowledge_service.get_knowledge_detail(db, user.organization_id, source_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuente no encontrada")
    return detail


@router.post("/sources")
def create_knowledge_source(
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


@router.patch("/sources/{source_id}")
def update_knowledge_source(
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


@router.post("/sources/{source_id}/activate")
def activate_knowledge_source(
    source_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    return knowledge_service.set_knowledge_status(db, user.organization_id, user.id, source_id, active=True)


@router.post("/sources/{source_id}/deactivate")
def deactivate_knowledge_source(
    source_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    return knowledge_service.set_knowledge_status(db, user.organization_id, user.id, source_id, active=False)


@router.post("/sources/{source_id}/ingest")
def ingest_knowledge_source(
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


# --- Documentos empresariales (rutas con parámetro al final) ---


@router.get("/{document_id}", response_model=KnowledgeDocumentDetail)
def get_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.view", db)
    try:
        return knowledge_service.get_document_detail(db, user.organization_id, document_id)
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.patch("/{document_id}", response_model=KnowledgeDocumentOut)
def update_document(
    document_id: str,
    body: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "knowledge.manage", db)
    try:
        return knowledge_service.update_document(
            db,
            organization_id=user.organization_id,
            document_id=document_id,
            user_id=user.id,
            name=body.name,
            metadata=body.metadata,
            is_active=body.is_active,
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.delete", db)
    try:
        knowledge_service.delete_document(
            db, organization_id=user.organization_id, document_id=document_id, user_id=user.id
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.post("/{document_id}/process", response_model=KnowledgeDocumentDetail)
def process_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.manage", db)
    try:
        return knowledge_service.process_document(
            db, organization_id=user.organization_id, document_id=document_id, user_id=user.id
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.post("/{document_id}/reprocess", response_model=KnowledgeDocumentDetail)
def reprocess_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.manage", db)
    try:
        return knowledge_service.process_document(
            db,
            organization_id=user.organization_id,
            document_id=document_id,
            user_id=user.id,
            reprocess=True,
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.post("/{document_id}/activate", response_model=KnowledgeDocumentOut)
def activate_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.manage", db)
    try:
        return knowledge_service.set_active(
            db, organization_id=user.organization_id, document_id=document_id, user_id=user.id, active=True
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.post("/{document_id}/deactivate", response_model=KnowledgeDocumentOut)
def deactivate_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.manage", db)
    try:
        return knowledge_service.set_active(
            db, organization_id=user.organization_id, document_id=document_id, user_id=user.id, active=False
        )
    except LookupError as exc:
        raise _handle_lookup(exc) from exc


@router.get("/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.view", db)
    try:
        filename, data, mime_type = knowledge_service.download_document(db, user.organization_id, document_id)
        knowledge_service.log_consultation(
            db,
            organization_id=user.organization_id,
            document_id=document_id,
            user_id=user.id,
            query="descarga",
        )
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=data, media_type=mime_type or "application/octet-stream", headers=headers)
    except LookupError as exc:
        raise _handle_lookup(exc) from exc
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.get("/{document_id}/activity", response_model=list[KnowledgeActivityOut])
def document_activity(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "knowledge.view", db)
    try:
        return knowledge_service.list_activity(db, user.organization_id, document_id)
    except LookupError as exc:
        raise _handle_lookup(exc) from exc
