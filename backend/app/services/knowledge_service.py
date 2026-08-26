"""Servicio del Centro de Conocimiento — CONOCIMIENTO-930."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.enums import KnowledgeEventType, KnowledgeIngestionStatus, KnowledgeSourceType
from app.knowledge_models import EmployeeKnowledgeGrant, KnowledgeActivity, KnowledgeChunk, KnowledgeDocument
from app.orchestration_models import AIEmployee, EmployeeKnowledgeSource, KnowledgeIngestion, KnowledgeSource
from app.services import knowledge_processor, knowledge_storage
from app.services.authorization import get_employee, get_knowledge_source
from app.services.knowledge_retrieval import retrieve_knowledge


def _filename_stem(filename: str) -> str:
    return Path(filename).stem or filename


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _load_metadata(row: KnowledgeDocument) -> dict[str, Any]:
    if not row.metadata_json:
        return {}
    return json.loads(row.metadata_json)


def _save_metadata(row: KnowledgeDocument, metadata: dict[str, Any] | None) -> None:
    row.metadata_json = json.dumps(metadata or {}, ensure_ascii=False)


def _log_activity(
    db: Session,
    *,
    document_id: str,
    organization_id: str,
    user_id: str | None,
    action: str,
    detail: str | None = None,
) -> None:
    db.add(
        KnowledgeActivity(
            document_id=document_id,
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            detail=detail,
        )
    )


def document_to_dict(row: KnowledgeDocument, *, include_content: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": row.id,
        "organization_id": row.organization_id,
        "name": row.name,
        "source_type": row.source_type,
        "file_type": row.file_type,
        "mime_type": row.mime_type,
        "status": row.status,
        "original_filename": row.original_filename,
        "size_bytes": row.size_bytes,
        "version": row.version,
        "is_active": row.is_active,
        "error_message": row.error_message,
        "association_count": row.association_count,
        "metadata": _load_metadata(row),
        "created_by_id": row.created_by_id,
        "updated_by_id": row.updated_by_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "processed_at": row.processed_at,
        "has_content": bool(row.processed_content),
    }
    if include_content:
        payload["processed_content"] = row.processed_content
    return payload


def get_document(db: Session, organization_id: str, document_id: str) -> KnowledgeDocument | None:
    return (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.id == document_id, KnowledgeDocument.organization_id == organization_id)
        .first()
    )


def list_documents(
    db: Session,
    organization_id: str,
    *,
    search: str | None = None,
    status: str | None = None,
    source_type: str | None = None,
    file_type: str | None = None,
    active_only: bool | None = None,
    sort: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query = db.query(KnowledgeDocument).filter(KnowledgeDocument.organization_id == organization_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(KnowledgeDocument.name.ilike(pattern), KnowledgeDocument.processed_content.ilike(pattern)))
    if status:
        query = query.filter(KnowledgeDocument.status == status.upper())
    if source_type:
        query = query.filter(KnowledgeDocument.source_type == source_type.upper())
    if file_type:
        query = query.filter(KnowledgeDocument.file_type == file_type.lower())
    if active_only is True:
        query = query.filter(KnowledgeDocument.is_active.is_(True))
    if active_only is False:
        query = query.filter(KnowledgeDocument.is_active.is_(False))
    order = KnowledgeDocument.updated_at.asc() if sort == "asc" else KnowledgeDocument.updated_at.desc()
    rows = query.order_by(order).offset(offset).limit(limit).all()
    return [document_to_dict(row) for row in rows]


def create_text_document(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    name: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not content.strip():
        raise ValueError("El archivo está vacío.")
    row = KnowledgeDocument(
        organization_id=organization_id,
        name=name.strip(),
        source_type="TEXT",
        file_type="txt",
        mime_type="text/plain",
        status="PENDING",
        size_bytes=len(content.encode("utf-8")),
        processed_content=content,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    _save_metadata(row, metadata)
    db.add(row)
    db.flush()
    _log_activity(db, document_id=row.id, organization_id=organization_id, user_id=user_id, action="CARGA", detail="Documento de texto")
    db.commit()
    db.refresh(row)
    process_document(db, organization_id=organization_id, document_id=row.id, user_id=user_id)
    db.refresh(row)
    return document_to_dict(row)


def create_file_document(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    filename: str,
    data: bytes,
    mime_type: str | None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = knowledge_storage.normalize_filename(filename)
    extension = knowledge_storage.validate_extension(normalized)
    file_type = extension.lstrip(".")
    document_id = knowledge_storage.new_document_id()
    storage_key = knowledge_storage.save_bytes(organization_id, document_id, extension, data)
    row = KnowledgeDocument(
        id=document_id,
        organization_id=organization_id,
        name=_filename_stem(normalized),
        source_type="FILE",
        file_type=file_type,
        mime_type=mime_type,
        status="PENDING",
        original_filename=normalized,
        storage_key=storage_key,
        size_bytes=len(data),
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    _save_metadata(row, metadata)
    db.add(row)
    db.flush()
    _log_activity(db, document_id=row.id, organization_id=organization_id, user_id=user_id, action="CARGA", detail=f"Archivo {normalized}")
    db.commit()
    db.refresh(row)
    process_document(db, organization_id=organization_id, document_id=row.id, user_id=user_id)
    db.refresh(row)
    return document_to_dict(row)


def update_document(
    db: Session,
    *,
    organization_id: str,
    document_id: str,
    user_id: str,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    row = get_document(db, organization_id, document_id)
    if not row:
        raise LookupError("El documento no existe o no está disponible.")
    if name is not None:
        row.name = name.strip()
    if metadata is not None:
        current = _load_metadata(row)
        current.update(metadata)
        _save_metadata(row, current)
    if is_active is not None:
        row.is_active = is_active
    row.updated_by_id = user_id
    row.updated_at = _utcnow()
    row.version += 1
    _log_activity(db, document_id=row.id, organization_id=organization_id, user_id=user_id, action="MODIFICACION")
    db.commit()
    db.refresh(row)
    return document_to_dict(row)


def delete_document(db: Session, *, organization_id: str, document_id: str, user_id: str) -> None:
    row = get_document(db, organization_id, document_id)
    if not row:
        raise LookupError("El documento no existe o no está disponible.")
    knowledge_storage.delete_stored_file(row.storage_key)
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == row.id).delete(synchronize_session=False)
    db.query(EmployeeKnowledgeGrant).filter(EmployeeKnowledgeGrant.document_id == row.id).delete(synchronize_session=False)
    db.query(KnowledgeActivity).filter(KnowledgeActivity.document_id == row.id).delete(synchronize_session=False)
    db.delete(row)
    db.commit()


def process_document(
    db: Session,
    *,
    organization_id: str,
    document_id: str,
    user_id: str | None,
    reprocess: bool = False,
) -> dict[str, Any]:
    row = get_document(db, organization_id, document_id)
    if not row:
        raise LookupError("El documento no existe o no está disponible.")
    action = "REPROCESAMIENTO" if reprocess else "PROCESAMIENTO"
    row.status = "PROCESSING"
    row.error_message = None
    row.updated_at = _utcnow()
    db.commit()
    try:
        if row.source_type == "TEXT":
            content = row.processed_content or ""
        elif row.storage_key:
            data = knowledge_storage.read_stored_file(row.storage_key)
            content = knowledge_processor.extract_text_from_bytes(data, row.file_type, row.original_filename)
        else:
            raise ValueError("No fue posible procesar el documento.")
        if not content.strip():
            raise ValueError("El archivo está vacío.")
        row.processed_content = content
        db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == row.id).delete()
        for chunk_data in knowledge_processor.chunk_text(
            content, document_id=row.id, organization_id=organization_id
        ):
            db.add(KnowledgeChunk(**chunk_data))
        row.status = "AVAILABLE"
        row.processed_at = _utcnow()
        row.version += 1
        _log_activity(db, document_id=row.id, organization_id=organization_id, user_id=user_id, action=action)
    except Exception as exc:  # noqa: BLE001 — persistir error de procesamiento
        row.status = "ERROR"
        row.error_message = str(exc)
        _log_activity(
            db,
            document_id=row.id,
            organization_id=organization_id,
            user_id=user_id,
            action="ERROR",
            detail=str(exc)[:500],
        )
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return document_to_dict(row, include_content=True)


def get_document_detail(db: Session, organization_id: str, document_id: str) -> dict[str, Any]:
    row = get_document(db, organization_id, document_id)
    if not row:
        raise LookupError("El documento no existe o no está disponible.")
    payload = document_to_dict(row, include_content=True)
    payload["chunks_count"] = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == row.id).count()
    return payload


def search_documents(db: Session, organization_id: str, query: str, *, limit: int = 50) -> list[dict[str, Any]]:
    pattern = f"%{query.strip()}%"
    rows = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.organization_id == organization_id,
            KnowledgeDocument.status == "AVAILABLE",
            or_(
                KnowledgeDocument.name.ilike(pattern),
                KnowledgeDocument.processed_content.ilike(pattern),
                KnowledgeDocument.metadata_json.ilike(pattern),
            ),
        )
        .order_by(KnowledgeDocument.updated_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for row in rows:
        snippet = None
        if row.processed_content and query.strip():
            lower = row.processed_content.lower()
            idx = lower.find(query.strip().lower())
            if idx >= 0:
                start = max(0, idx - 60)
                snippet = row.processed_content[start : start + 180]
        results.append(
            {
                "id": row.id,
                "name": row.name,
                "source_type": row.source_type,
                "file_type": row.file_type,
                "status": row.status,
                "snippet": snippet,
                "relevance": None,
            }
        )
    return results


def download_document(db: Session, organization_id: str, document_id: str) -> tuple[str, bytes, str | None]:
    row = get_document(db, organization_id, document_id)
    if not row:
        raise LookupError("El documento no existe o no está disponible.")
    if row.source_type == "TEXT":
        content = (row.processed_content or "").encode("utf-8")
        filename = f"{row.name}.txt"
        return filename, content, "text/plain; charset=utf-8"
    if not row.storage_key:
        raise LookupError("El documento no existe o no está disponible.")
    data = knowledge_storage.read_stored_file(row.storage_key)
    filename = row.original_filename or f"{row.name}.{row.file_type or 'bin'}"
    return filename, data, row.mime_type


def set_active(
    db: Session,
    *,
    organization_id: str,
    document_id: str,
    user_id: str,
    active: bool,
) -> dict[str, Any]:
    row = get_document(db, organization_id, document_id)
    if not row:
        raise LookupError("El documento no existe o no está disponible.")
    row.is_active = active
    row.status = "INACTIVE" if not active and row.status != "ERROR" else row.status
    if active and row.status == "INACTIVE" and row.processed_content:
        row.status = "AVAILABLE"
    row.updated_by_id = user_id
    row.updated_at = _utcnow()
    _log_activity(
        db,
        document_id=row.id,
        organization_id=organization_id,
        user_id=user_id,
        action="ACTIVACION" if active else "DESACTIVACION",
    )
    db.commit()
    db.refresh(row)
    return document_to_dict(row)


def list_activity(db: Session, organization_id: str, document_id: str) -> list[dict[str, Any]]:
    row = get_document(db, organization_id, document_id)
    if not row:
        raise LookupError("El documento no existe o no está disponible.")
    rows = (
        db.query(KnowledgeActivity)
        .filter(KnowledgeActivity.document_id == document_id, KnowledgeActivity.organization_id == organization_id)
        .order_by(KnowledgeActivity.created_at.desc())
        .all()
    )
    return [
        {
            "id": item.id,
            "action": item.action,
            "detail": item.detail,
            "user_id": item.user_id,
            "created_at": item.created_at,
        }
        for item in rows
    ]


def grant_document_to_employee(
    db: Session,
    *,
    organization_id: str,
    employee_id: str,
    document_id: str,
    user_id: str,
) -> dict[str, Any]:
    employee = (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == organization_id)
        .first()
    )
    if not employee:
        raise LookupError("Empleado no encontrado")
    document = get_document(db, organization_id, document_id)
    if not document:
        raise LookupError("El documento no existe o no está disponible.")
    existing = (
        db.query(EmployeeKnowledgeGrant)
        .filter(
            EmployeeKnowledgeGrant.employee_id == employee_id,
            EmployeeKnowledgeGrant.document_id == document_id,
        )
        .first()
    )
    if existing:
        existing.is_active = True
        grant = existing
    else:
        grant = EmployeeKnowledgeGrant(
            organization_id=organization_id,
            employee_id=employee_id,
            document_id=document_id,
        )
        db.add(grant)
        document.association_count += 1
    _log_activity(
        db,
        document_id=document.id,
        organization_id=organization_id,
        user_id=user_id,
        action="ASOCIACION",
        detail=f"Empleado {employee_id}",
    )
    db.commit()
    db.refresh(grant)
    return {
        "id": grant.id,
        "employee_id": grant.employee_id,
        "document_id": grant.document_id,
        "document_name": document.name,
        "is_active": grant.is_active,
        "created_at": grant.created_at,
    }


def revoke_document_from_employee(
    db: Session,
    *,
    organization_id: str,
    employee_id: str,
    document_id: str,
    user_id: str,
) -> None:
    grant = (
        db.query(EmployeeKnowledgeGrant)
        .filter(
            EmployeeKnowledgeGrant.organization_id == organization_id,
            EmployeeKnowledgeGrant.employee_id == employee_id,
            EmployeeKnowledgeGrant.document_id == document_id,
        )
        .first()
    )
    if not grant:
        raise LookupError("Asociación no encontrada")
    grant.is_active = False
    _log_activity(
        db,
        document_id=document_id,
        organization_id=organization_id,
        user_id=user_id,
        action="DESASOCIACION",
        detail=f"Empleado {employee_id}",
    )
    db.commit()


def list_employee_grants(db: Session, organization_id: str, employee_id: str) -> list[dict[str, Any]]:
    employee = (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == organization_id)
        .first()
    )
    if not employee:
        raise LookupError("Empleado no encontrado")
    rows = (
        db.query(EmployeeKnowledgeGrant, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeDocument.id == EmployeeKnowledgeGrant.document_id)
        .filter(
            EmployeeKnowledgeGrant.organization_id == organization_id,
            EmployeeKnowledgeGrant.employee_id == employee_id,
            EmployeeKnowledgeGrant.is_active.is_(True),
        )
        .all()
    )
    return [
        {
            "id": grant.id,
            "employee_id": grant.employee_id,
            "document_id": grant.document_id,
            "document_name": document.name,
            "is_active": grant.is_active,
            "created_at": grant.created_at,
        }
        for grant, document in rows
    ]


def log_consultation(db: Session, *, organization_id: str, document_id: str, user_id: str | None, query: str) -> None:
    _log_activity(
        db,
        document_id=document_id,
        organization_id=organization_id,
        user_id=user_id,
        action="CONSULTA",
        detail=query[:200],
    )
    db.commit()


# --- Catálogo de fuentes (CAPABILITIES-850 / preint #10) ---


def _slug_code(name: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    safe = dict(config or {})
    for key in list(safe.keys()):
        if re.search(r"(password|secret|token|api_key|apikey)", key, re.I):
            safe[key] = "***"
    return safe


def _source_out(source: KnowledgeSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "organization_id": source.organization_id,
        "code": source.code,
        "name": source.name,
        "description": source.description,
        "source_type": source.source_type,
        "status": "ACTIVA" if source.is_active else "INACTIVA",
        "configuration": _sanitize_config(json.loads(source.config_json) if source.config_json else {}),
        "has_secret_ref": bool(source.secret_ref),
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }


def list_knowledge_sources(
    db: Session,
    org_id: str,
    *,
    search: str | None = None,
    source_type: str | None = None,
    status: str | None = None,
    include_inactive: bool = True,
) -> list[dict[str, Any]]:
    q = db.query(KnowledgeSource).filter(KnowledgeSource.organization_id == org_id)
    if source_type:
        q = q.filter(KnowledgeSource.source_type == source_type)
    if not include_inactive:
        q = q.filter(KnowledgeSource.is_active.is_(True))
    if status == "ACTIVA":
        q = q.filter(KnowledgeSource.is_active.is_(True))
    elif status == "INACTIVA":
        q = q.filter(KnowledgeSource.is_active.is_(False))
    rows = q.order_by(KnowledgeSource.name).all()
    if search:
        needle = search.lower()
        rows = [r for r in rows if needle in r.name.lower() or needle in r.code.lower()]
    return [_source_out(r) for r in rows]


def get_knowledge_detail(db: Session, org_id: str, source_id: str) -> dict[str, Any] | None:
    try:
        source = get_knowledge_source(db, org_id, source_id)
    except Exception:
        return None
    detail = _source_out(source)
    ingestions = (
        db.query(KnowledgeIngestion)
        .filter(KnowledgeIngestion.knowledge_source_id == source.id)
        .order_by(KnowledgeIngestion.created_at.desc())
        .limit(20)
        .all()
    )
    detail["ingestions"] = [
        {
            "id": i.id,
            "status": i.status,
            "content_type": i.content_type,
            "error_message": i.error_message,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "completed_at": i.completed_at.isoformat() if i.completed_at else None,
        }
        for i in ingestions
    ]
    return detail


def create_knowledge_source(
    db: Session,
    org_id: str,
    user_id: str,
    *,
    name: str,
    source_type: str,
    code: str | None = None,
    description: str | None = None,
    configuration: dict | None = None,
    secret_ref: str | None = None,
) -> dict[str, Any]:
    final_code = code or _slug_code(name)
    existing = (
        db.query(KnowledgeSource)
        .filter(KnowledgeSource.organization_id == org_id, KnowledgeSource.code == final_code)
        .first()
    )
    if existing:
        return {"error": "Ya existe una fuente con ese código"}
    source = KnowledgeSource(
        organization_id=org_id,
        code=final_code,
        name=name,
        description=description,
        source_type=source_type,
        config_json=json.dumps(_sanitize_config(configuration or {}), ensure_ascii=False),
        secret_ref=secret_ref,
    )
    db.add(source)
    db.commit()
    write_audit(db, action=KnowledgeEventType.CREATED, organization_id=org_id, user_id=user_id, detail=final_code)
    return _source_out(source)


def update_knowledge_source(
    db: Session,
    org_id: str,
    user_id: str,
    source_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    source = get_knowledge_source(db, org_id, source_id)
    if "name" in payload:
        source.name = payload["name"]
    if "description" in payload:
        source.description = payload["description"]
    if "source_type" in payload:
        source.source_type = payload["source_type"]
    if "configuration" in payload:
        source.config_json = json.dumps(_sanitize_config(payload["configuration"] or {}), ensure_ascii=False)
    if "secret_ref" in payload:
        source.secret_ref = payload["secret_ref"]
    if "code" in payload and payload["code"] != source.code:
        dup = (
            db.query(KnowledgeSource)
            .filter(KnowledgeSource.organization_id == org_id, KnowledgeSource.code == payload["code"], KnowledgeSource.id != source.id)
            .first()
        )
        if dup:
            return {"error": "Ya existe una fuente con ese código"}
        source.code = payload["code"]
    source.updated_at = _utcnow()
    db.commit()
    write_audit(db, action=KnowledgeEventType.UPDATED, organization_id=org_id, user_id=user_id, detail=source.code)
    return _source_out(source)


def set_knowledge_status(
    db: Session,
    org_id: str,
    user_id: str,
    source_id: str,
    *,
    active: bool,
) -> dict[str, Any]:
    source = get_knowledge_source(db, org_id, source_id)
    source.is_active = active
    source.updated_at = _utcnow()
    db.commit()
    write_audit(
        db,
        action=KnowledgeEventType.UPDATED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{source.code}:{'ACTIVA' if active else 'INACTIVA'}",
    )
    return _source_out(source)


def list_employee_knowledge(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    links = (
        db.query(EmployeeKnowledgeSource)
        .filter(
            EmployeeKnowledgeSource.employee_id == employee.id,
            EmployeeKnowledgeSource.organization_id == org_id,
            EmployeeKnowledgeSource.is_active.is_(True),
        )
        .all()
    )
    assigned_ids = {link.knowledge_source_id for link in links if link.knowledge_source_id}
    assigned = []
    for link in links:
        if link.knowledge_source_id:
            source = db.query(KnowledgeSource).filter(KnowledgeSource.id == link.knowledge_source_id).first()
            if source:
                item = _source_out(source)
                item["assignment_id"] = link.id
                assigned.append(item)
        else:
            assigned.append({
                "assignment_id": link.id,
                "id": link.id,
                "name": link.name,
                "source_type": link.source_type,
                "status": "ACTIVA" if link.is_active else "INACTIVA",
                "legacy": True,
            })
    available = [s for s in list_knowledge_sources(db, org_id, include_inactive=False) if s["id"] not in assigned_ids]
    return {"assigned": assigned, "available": available}


def assign_knowledge(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    knowledge_source_id: str,
) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    source = get_knowledge_source(db, org_id, knowledge_source_id)
    if not source.is_active:
        return {"error": "La fuente está inactiva"}
    link = (
        db.query(EmployeeKnowledgeSource)
        .filter(
            EmployeeKnowledgeSource.employee_id == employee.id,
            EmployeeKnowledgeSource.knowledge_source_id == source.id,
        )
        .first()
    )
    if link:
        link.is_active = True
    else:
        db.add(EmployeeKnowledgeSource(
            organization_id=org_id,
            employee_id=employee.id,
            knowledge_source_id=source.id,
            source_type=source.source_type,
            name=source.name,
            config_json=source.config_json,
            is_active=True,
        ))
    db.commit()
    write_audit(
        db,
        action=KnowledgeEventType.ASSIGNED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{employee.code}:{source.code}",
    )
    return list_employee_knowledge(db, org_id, employee_id)


def remove_knowledge(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    knowledge_source_id: str,
) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    source = get_knowledge_source(db, org_id, knowledge_source_id)
    link = (
        db.query(EmployeeKnowledgeSource)
        .filter(
            EmployeeKnowledgeSource.employee_id == employee.id,
            EmployeeKnowledgeSource.knowledge_source_id == source.id,
        )
        .first()
    )
    if not link:
        return {"error": "Asignación no encontrada"}
    link.is_active = False
    db.commit()
    write_audit(
        db,
        action=KnowledgeEventType.REMOVED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{employee.code}:{source.code}",
    )
    return list_employee_knowledge(db, org_id, employee_id)


def ingest_knowledge(
    db: Session,
    org_id: str,
    user_id: str,
    source_id: str,
    *,
    content: str | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    source = get_knowledge_source(db, org_id, source_id)
    ingestion = KnowledgeIngestion(
        organization_id=org_id,
        knowledge_source_id=source.id,
        status=KnowledgeIngestionStatus.PROCESSING,
        content_type=content_type,
    )
    db.add(ingestion)
    db.flush()

    try:
        if source.source_type == KnowledgeSourceType.TEXT:
            if not content or not content.strip():
                raise ValueError("El contenido de texto está vacío")
            result = {"chars": len(content), "preview": content[:200]}
            ingestion.status = KnowledgeIngestionStatus.COMPLETED
        elif source.source_type == KnowledgeSourceType.FILE:
            if not content:
                raise ValueError("No se proporcionó contenido de archivo")
            if content_type and "pdf" in content_type.lower():
                if content.strip().startswith("%PDF"):
                    raise ValueError("El PDF no contiene texto extraíble en esta versión")
            result = {"chars": len(content), "format": content_type or "text/plain"}
            ingestion.status = KnowledgeIngestionStatus.COMPLETED
        elif source.source_type in (KnowledgeSourceType.URL, KnowledgeSourceType.DATABASE, KnowledgeSourceType.API):
            result = {"registered": True, "note": "Definición registrada; conector no implementado en V1"}
            ingestion.status = KnowledgeIngestionStatus.COMPLETED
        else:
            raise ValueError("Tipo de fuente no soportado")
        ingestion.result_json = json.dumps(result, ensure_ascii=False)
        ingestion.completed_at = _utcnow()
    except Exception as exc:
        ingestion.status = KnowledgeIngestionStatus.FAILED
        ingestion.error_message = str(exc)
        ingestion.completed_at = _utcnow()

    db.commit()
    write_audit(
        db,
        action=KnowledgeEventType.INGESTED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{source.code}:{ingestion.status}",
    )
    return {
        "id": ingestion.id,
        "status": ingestion.status,
        "content_type": ingestion.content_type,
        "error_message": ingestion.error_message,
        "result": json.loads(ingestion.result_json) if ingestion.result_json else None,
        "created_at": ingestion.created_at.isoformat() if ingestion.created_at else None,
        "completed_at": ingestion.completed_at.isoformat() if ingestion.completed_at else None,
    }
