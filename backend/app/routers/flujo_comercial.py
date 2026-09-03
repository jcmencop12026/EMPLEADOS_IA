"""Router — Flujo comercial V1 EIAAX (1730)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.evaluacion_models import EvaluacionInformacionItem
from app.flujo_comercial_models import ComercialCompromisoGarantia, ComercialInstrumentoContractual, ComercialPresentacionEjecutiva
from app.models import User
from app.opportunity_models import Opportunity
from app.permissions import check_permission
from app.schemas_flujo_comercial import (
    CompromisoGarantiaCreate,
    DemoIniciar,
    InstrumentoCreate,
    OportunidadClasificacionUpdate,
    PresentacionEjecutivaCreate,
    PropuestaDesdeDossier,
    SeleccionOportunidades,
)
from app.services import evaluacion_service as eval_svc
from app.services import flujo_comercial_service as svc

router = APIRouter(prefix="/api/flujo-comercial", tags=["flujo-comercial"])


@router.post("/demo/recorrido")
def demo_recorrido(
    body: DemoIniciar,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.manage", db)
    result = svc.recorrido_demo(db, user, user.organization_id, sector=body.sector, area=body.area)
    db.commit()
    return result


@router.get("/expedientes/{evaluacion_id}/catalogo-informacion")
def catalogo_informacion(
    evaluacion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "evaluacion.view", db)
    exp = eval_svc._get_expediente(db, evaluacion_id, user.organization_id)
    return {
        "base": [c for c in eval_svc._INFO_CATALOGO if exp.nivel in c["niveles"]],
        "contextual": svc.resolve_catalogo_contextual(exp),
        "aplicable": svc.merge_catalogo_aplicable(exp),
    }


@router.post("/expedientes/{evaluacion_id}/sync-informacion")
def sync_informacion(
    evaluacion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "evaluacion.manage", db)
    exp = eval_svc._get_expediente(db, evaluacion_id, user.organization_id)
    items = svc.sync_informacion_contextual(db, exp, user_id=user.id)
    db.commit()
    return {"items": len(items)}


@router.get("/expedientes/{evaluacion_id}/suficiencia")
def validar_suficiencia(
    evaluacion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "evaluacion.view", db)
    exp = eval_svc._get_expediente(db, evaluacion_id, user.organization_id)
    items = db.query(EvaluacionInformacionItem).filter(EvaluacionInformacionItem.expediente_id == evaluacion_id).all()
    return svc.evaluar_suficiencia(exp, items)


@router.post("/expedientes/{evaluacion_id}/importar-inteligencia-externa")
def importar_inteligencia(
    evaluacion_id: str,
    limite: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "evaluacion.evaluate", db)
    result = svc.importar_inteligencia_externa(db, user, user.organization_id, evaluacion_id, limite=limite)
    db.commit()
    return {"importados": result}


@router.post("/expedientes/{evaluacion_id}/importar-diagnostico")
def importar_diagnostico(
    evaluacion_id: str,
    diagnostic_id: str | None = Query(None),
    limite: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "evaluacion.evaluate", db)
    result = svc.importar_hallazgos_diagnostico(
        db,
        user,
        user.organization_id,
        evaluacion_id,
        diagnostic_id=diagnostic_id,
        limite=limite,
    )
    db.commit()
    return result


@router.get("/expedientes/{evaluacion_id}/oportunidades")
def listar_oportunidades(
    evaluacion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.view", db)
    return svc.listar_oportunidades_expediente(db, user.organization_id, evaluacion_id)


@router.post("/expedientes/{evaluacion_id}/oportunidades/seleccion-presentacion")
def seleccion_presentacion(
    evaluacion_id: str,
    body: SeleccionOportunidades,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.manage", db)
    result = svc.seleccionar_oportunidades_presentacion(
        db, user, user.organization_id, evaluacion_id, body.opportunity_ids, presentar=body.presentar
    )
    db.commit()
    return result


@router.patch("/oportunidades/{opportunity_id}/clasificacion")
def actualizar_clasificacion(
    opportunity_id: str,
    body: OportunidadClasificacionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.manage", db)
    opp = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id, Opportunity.organization_id == user.organization_id
    ).first()
    if not opp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    if body.origen_comercial is not None:
        opp.origen_comercial = body.origen_comercial
    if body.presentar_cliente is not None:
        opp.presentar_cliente = body.presentar_cliente
    if body.clasificacion_valor is not None:
        opp.valor_potencial_certidumbre = body.clasificacion_valor
    db.commit()
    return {
        "id": opp.id,
        "origen_comercial": opp.origen_comercial,
        "presentar_cliente": opp.presentar_cliente,
        "clasificacion_valor": opp.valor_potencial_certidumbre,
    }


@router.post("/expedientes/{evaluacion_id}/presentacion-ejecutiva")
def crear_presentacion(
    evaluacion_id: str,
    body: PresentacionEjecutivaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.manage", db)
    row = svc.crear_presentacion_ejecutiva(db, user, user.organization_id, evaluacion_id, body.model_dump())
    db.commit()
    return svc.presentacion_to_dict(row)


@router.get("/expedientes/{evaluacion_id}/presentacion-ejecutiva")
def obtener_presentacion(
    evaluacion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.view", db)
    row = (
        db.query(ComercialPresentacionEjecutiva)
        .filter(
            ComercialPresentacionEjecutiva.evaluacion_id == evaluacion_id,
            ComercialPresentacionEjecutiva.organization_id == user.organization_id,
        )
        .order_by(ComercialPresentacionEjecutiva.created_at.desc())
        .first()
    )
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sin presentación ejecutiva")
    return svc.presentacion_to_dict(row)


@router.post("/expedientes/{evaluacion_id}/generar-propuesta")
def generar_propuesta(
    evaluacion_id: str,
    body: PropuestaDesdeDossier,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.manage", db)
    result = svc.generar_propuesta_desde_dossier(
        db,
        user,
        user.organization_id,
        evaluacion_id,
        opportunity_id=body.opportunity_id,
        titulo=body.titulo,
        exigir_suficiencia=body.exigir_suficiencia,
        presentacion_id=body.presentacion_id,
    )
    db.commit()
    return result


@router.get("/instrumentos/catalogo")
def catalogo_instrumentos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "flujo_comercial.view", db)
    return svc.listar_instrumentos_modulares()


@router.get("/propuestas/{proposal_id}/instrumentos")
def listar_instrumentos(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.view", db)
    rows = (
        db.query(ComercialInstrumentoContractual)
        .filter(
            ComercialInstrumentoContractual.proposal_id == proposal_id,
            ComercialInstrumentoContractual.organization_id == user.organization_id,
        )
        .all()
    )
    return [svc.instrumento_to_dict(r) for r in rows]


@router.post("/propuestas/{proposal_id}/instrumentos")
def crear_instrumento(
    proposal_id: str,
    body: InstrumentoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.manage", db)
    row = svc.crear_instrumento(db, user, user.organization_id, proposal_id, body.model_dump())
    db.commit()
    return svc.instrumento_to_dict(row)


@router.get("/propuestas/{proposal_id}/compromisos-garantia")
def listar_compromisos(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.view", db)
    rows = (
        db.query(ComercialCompromisoGarantia)
        .filter(
            ComercialCompromisoGarantia.proposal_id == proposal_id,
            ComercialCompromisoGarantia.organization_id == user.organization_id,
        )
        .all()
    )
    return [svc.compromiso_to_dict(r) for r in rows]


@router.post("/propuestas/{proposal_id}/compromisos-garantia")
def crear_compromiso(
    proposal_id: str,
    body: CompromisoGarantiaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "flujo_comercial.manage", db)
    row = svc.crear_compromiso_garantia(db, user, user.organization_id, proposal_id, body.model_dump())
    db.commit()
    return svc.compromiso_to_dict(row)
