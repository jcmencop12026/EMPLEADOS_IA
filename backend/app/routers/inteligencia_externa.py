"""API — Inteligencia externa y oportunidades estratégicas (1240)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.schemas_external import (
    ClassificationPatch,
    ExternalContextIn,
    ExternalSignalIngest,
    ExternalSourceCreate,
    ExternalSourcePatch,
    RelevancePatch,
    RiskRegister,
)
from app.services import external_intelligence_service as ext_svc

router = APIRouter(prefix="/api/inteligencia-externa", tags=["Inteligencia externa"])


@router.get("/contexto")
def get_context(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.view")),
):
    ctx = ext_svc.get_or_create_context(db, user.organization_id)
    return ext_svc.context_to_dict(ctx)


@router.put("/contexto")
def update_context(
    body: ExternalContextIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.manage")),
):
    ctx = ext_svc.update_context(db, user.organization_id, body.model_dump(exclude_none=True), user.id)
    db.commit()
    return ext_svc.context_to_dict(ctx)


@router.get("/fuentes")
def list_sources(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.view")),
):
    rows = ext_svc.list_external_sources(db, user.organization_id)
    return [ext_svc.external_source_to_dict(r) for r in rows]


@router.post("/fuentes", status_code=201)
def create_source(
    body: ExternalSourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.manage")),
):
    row = ext_svc.create_external_source(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        **body.model_dump(),
    )
    db.commit()
    return ext_svc.external_source_to_dict(row)


@router.patch("/fuentes/{source_id}")
def patch_source(
    source_id: str,
    body: ExternalSourcePatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.manage")),
):
    row = ext_svc.update_external_source(
        db,
        user.organization_id,
        source_id,
        user.id,
        body.model_dump(exclude_none=True),
    )
    db.commit()
    return ext_svc.external_source_to_dict(row)


@router.post("/ingesta", status_code=201)
def ingest_external(
    body: ExternalSignalIngest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.ingest")),
):
    result = ext_svc.ingest_external_signal(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        data=body.model_dump(),
        auto_process=body.auto_process,
    )
    db.commit()
    return result


@router.get("/senales")
def list_external_signals(
    limit: int = Query(50, ge=1, le=200),
    classification: str | None = None,
    relevance: str | None = None,
    source_type: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.view")),
):
    items = ext_svc.list_external_signals(
        db,
        user.organization_id,
        limit=limit,
        classification=classification,
        relevance=relevance,
        source_type=source_type,
    )
    if not items:
        return {"items": [], "message": "Sin información externa disponible"}
    return {"items": items}


@router.get("/senales/{signal_id}")
def external_signal_detail(
    signal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.view")),
):
    return ext_svc.get_external_signal_detail(db, user.organization_id, signal_id)


@router.patch("/senales/{signal_id}/clasificacion")
def patch_classification(
    signal_id: str,
    body: ClassificationPatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.manage")),
):
    ext = ext_svc.update_classification(db, user.organization_id, signal_id, body.classification, user.id)
    db.commit()
    return ext_svc.extension_to_dict(ext)


@router.patch("/senales/{signal_id}/relevancia")
def patch_relevance(
    signal_id: str,
    body: RelevancePatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.manage")),
):
    ext = ext_svc.update_relevance(db, user.organization_id, signal_id, body.relevance, user.id)
    db.commit()
    return ext_svc.extension_to_dict(ext)


@router.post("/senales/{signal_id}/validar")
def validate_signal(
    signal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.validate")),
):
    ext = ext_svc.validate_external_analysis(db, user.organization_id, signal_id, user.id)
    db.commit()
    return ext_svc.extension_to_dict(ext)


@router.post("/senales/{signal_id}/oportunidad")
def create_opportunity(
    signal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.manage")),
):
    opp = ext_svc.create_opportunity_from_external(db, user.organization_id, signal_id, user.id)
    db.commit()
    return {"opportunity_id": opp.id, "codigo": opp.codigo, "titulo": opp.titulo}


@router.post("/senales/{signal_id}/riesgo")
def register_risk(
    signal_id: str,
    body: RiskRegister,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_externa.manage")),
):
    ext = ext_svc.register_external_risk(
        db, user.organization_id, signal_id, user.id, risk_type=body.risk_type
    )
    db.commit()
    return ext_svc.extension_to_dict(ext)
