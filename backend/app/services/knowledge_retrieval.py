"""Recuperación de conocimiento — contrato RAG V1."""
from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.knowledge_models import EmployeeKnowledgeGrant, KnowledgeChunk, KnowledgeDocument
from app.services.knowledge_processor import chunk_text


def retrieve_knowledge(
    db: Session,
    *,
    tenant_id: str,
    query: str,
    filters: dict[str, Any] | None = None,
    limit: int = 10,
    context: dict[str, Any] | None = None,
    employee_id: str | None = None,
) -> list[dict]:
    """Contrato de recuperación desacoplado de proveedores de embeddings."""
    filters = filters or {}
    context = context or {}
    pattern = f"%{query.strip()}%"
    chunk_query = (
        db.query(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .filter(
            KnowledgeChunk.organization_id == tenant_id,
            KnowledgeDocument.status == "AVAILABLE",
            KnowledgeDocument.is_active.is_(True),
        )
    )
    if employee_id:
        allowed_ids = [
            row.document_id
            for row in db.query(EmployeeKnowledgeGrant)
            .filter(
                EmployeeKnowledgeGrant.organization_id == tenant_id,
                EmployeeKnowledgeGrant.employee_id == employee_id,
                EmployeeKnowledgeGrant.is_active.is_(True),
            )
            .all()
        ]
        if not allowed_ids:
            return []
        chunk_query = chunk_query.filter(KnowledgeChunk.document_id.in_(allowed_ids))
    if filters.get("document_id"):
        chunk_query = chunk_query.filter(KnowledgeChunk.document_id == filters["document_id"])
    if filters.get("source_type"):
        chunk_query = chunk_query.filter(KnowledgeDocument.source_type == filters["source_type"])
    chunk_query = chunk_query.filter(KnowledgeChunk.content.ilike(pattern))
    rows = chunk_query.order_by(KnowledgeChunk.position).limit(limit).all()
    results = []
    for chunk, document in rows:
        relevance = _score_relevance(chunk.content, query)
        metadata = json.loads(chunk.metadata_json) if chunk.metadata_json else {}
        results.append(
            {
                "chunk_id": chunk.id,
                "document_id": document.id,
                "document_name": document.name,
                "content": chunk.content,
                "position": chunk.position,
                "page_number": chunk.page_number,
                "section": chunk.section,
                "metadata": metadata,
                "relevance": relevance,
            }
        )
    results.sort(key=lambda item: item["relevance"] or 0.0, reverse=True)
    return results[:limit]


def _score_relevance(content: str, query: str) -> float:
    if not query.strip():
        return 0.0
    tokens = [token for token in re.split(r"\W+", query.lower()) if token]
    if not tokens:
        return 0.0
    haystack = content.lower()
    hits = sum(1 for token in tokens if token in haystack)
    return round(hits / len(tokens), 4)
