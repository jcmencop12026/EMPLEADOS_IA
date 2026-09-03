"""Router — Inteligencia económica + simulación + valor empresarial (1740)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.inteligencia_economica_models import EconomicScenarioRun
from app.models import User
from app.permissions import check_permission
from app.schemas_inteligencia_economica import CompararEscenariosIn, DimensionarIn, RecomendarPrecioValorIn
from app.services import economic_motor_service as motor_svc
from app.services import inteligencia_economica_service as svc

router = APIRouter(prefix="/api/inteligencia-economica", tags=["inteligencia-economica"])


def _org(db: Session, user: User, organization_id: str | None) -> str:
    return motor_svc.resolve_organization_id(db, user, organization_id)


@router.get("/auditoria")
def auditoria(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "inteligencia_economica.view", db)
    return svc.auditar_capacidades_existentes()


@router.get("/valor-empresarial")
def valor_empresarial(
    organization_id: str | None = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.view", db)
    return svc.valor_empresarial(db, _org(db, user, organization_id), period_days=period_days)


@router.get("/resultado-economico")
def resultado_economico(
    organization_id: str | None = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.view", db)
    return svc.resultado_economico(db, _org(db, user, organization_id), period_days=period_days)


@router.post("/escenarios/comparar")
def comparar_escenarios(
    body: CompararEscenariosIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.simulate", db)
    org_id = _org(db, user, organization_id)
    result = svc.comparar_escenarios(db, user, org_id, body.model_dump())
    db.commit()
    return result


@router.post("/dimensionar")
def dimensionar(
    body: DimensionarIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.simulate", db)
    return svc.dimensionar_capacidad(db, _org(db, user, organization_id), body.model_dump())


@router.get("/empleados/{employee_id}/economia")
def economia_empleado(
    employee_id: str,
    days: int = Query(30, ge=1, le=365),
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.view", db)
    try:
        return svc.economia_empleado(db, _org(db, user, organization_id), employee_id, days=days)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/empresa")
def economia_empresa(
    organization_id: str | None = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.view", db)
    return svc.economia_empresa(db, _org(db, user, organization_id), period_days=period_days)


@router.get("/comercial-interna")
def comercial_interna(
    proposal_id: str | None = Query(None),
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.private", db)
    return svc.inteligencia_comercial_interna(db, _org(db, user, organization_id), user, proposal_id=proposal_id)


@router.post("/precio-recomendado-valor")
def precio_recomendado_valor(
    body: RecomendarPrecioValorIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.private", db)
    org_id = _org(db, user, organization_id)
    result = svc.recomendar_precio_valor(
        db,
        user,
        org_id,
        fraccion_valor=body.fraccion_valor,
        attributable_value=body.attributable_value,
        proposal_id=body.proposal_id,
        margen_min=body.margen_min,
    )
    db.commit()
    return result


@router.get("/escenarios/runs")
def listar_runs(
    organization_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "inteligencia_economica.view", db)
    org_id = _org(db, user, organization_id)
    rows = (
        db.query(EconomicScenarioRun)
        .filter(EconomicScenarioRun.organization_id == org_id)
        .order_by(EconomicScenarioRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "codigo": r.codigo,
            "titulo": r.titulo,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resultados": svc.parse_run_resultados(r.resultados_json),
        }
        for r in rows
    ]
