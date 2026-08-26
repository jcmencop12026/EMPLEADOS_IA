from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.enums import KnowledgeEventType, KnowledgeIngestionStatus, KnowledgeSourceType
from app.orchestration_models import EmployeeKnowledgeSource, KnowledgeIngestion, KnowledgeSource
from app.services.authorization import get_employee, get_knowledge_source


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
