"""Router — TCO y ecosistema de aliados (1320)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_tco import (
    AlianzaCreate,
    AlianzaEstadoUpdate,
    CategoriaCostoCreate,
    CompararProveedoresRequest,
    ContratoCondicionCreate,
    CostoCreate,
    CostoUpdate,
    DistribucionCreate,
    MakeOrBuyRequest,
    ProveedorAliadoCreate,
    RentabilidadRequest,
    RiesgoProveedorUpdate,
    SimulacionRequest,
    SustitucionProveedorRequest,
    TarifaCreate,
    TcoCalcularRequest,
)
from app.services import tco_service as svc

router = APIRouter(prefix="/api/tco", tags=["tco"])


def _handle_validation(exc: svc.TcoValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# --- Categorías ---

@router.get("/categorias")
def list_categorias(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    svc.bootstrap_categorias_default(db, user.organization_id)
    db.commit()
    return [svc.categoria_to_dict(c) for c in svc.list_categorias(db, user.organization_id)]


@router.post("/categorias", status_code=status.HTTP_201_CREATED)
def create_categoria(body: CategoriaCostoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.manage", db)
    try:
        row = svc.create_categoria(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return svc.categoria_to_dict(row)
    except svc.TcoValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


# --- Proveedores ---

@router.get("/proveedores")
def list_proveedores(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return [svc.proveedor_to_dict(p) for p in svc.list_proveedores(db, user.organization_id)]


@router.post("/proveedores", status_code=status.HTTP_201_CREATED)
def create_proveedor(body: ProveedorAliadoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "proveedores.manage", db)
    try:
        row = svc.create_proveedor(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return svc.proveedor_to_dict(row)
    except svc.TcoValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.patch("/proveedores/{proveedor_id}/riesgo")
def update_riesgo(proveedor_id: str, body: RiesgoProveedorUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "proveedores.manage", db)
    row = svc.update_riesgo_proveedor(db, user.organization_id, proveedor_id, body.model_dump(), user.id)
    db.commit()
    return svc.proveedor_to_dict(row)


# --- Contratos ---

@router.get("/contratos")
def list_contratos(proveedor_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return [svc.contrato_to_dict(c) for c in svc.list_contratos(db, user.organization_id, proveedor_id)]


@router.post("/contratos", status_code=status.HTTP_201_CREATED)
def create_contrato(body: ContratoCondicionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "proveedores.manage", db)
    row = svc.create_contrato(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return svc.contrato_to_dict(row)


# --- Tarifas ---

@router.get("/tarifas")
def list_tarifas(proveedor_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return svc.list_tarifas(db, user.organization_id, proveedor_id)


@router.post("/tarifas", status_code=status.HTTP_201_CREATED)
def create_tarifa(body: TarifaCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "proveedores.manage", db)
    row = svc.create_tarifa(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return svc.tarifa_to_dict(db, row)


@router.post("/tarifas/calcular")
def calcular_tarifa(unidades: float, tramos: list[dict], user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    from decimal import Decimal
    return svc.calcular_tarifa_volumen(tramos, Decimal(str(unidades)))


# --- Costos ---

@router.get("/costos")
def list_costos(naturaleza: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return svc.list_costos(db, user.organization_id, naturaleza)


@router.post("/costos", status_code=status.HTTP_201_CREATED)
def create_costo(body: CostoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.manage", db)
    try:
        row = svc.create_costo(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return svc.costo_to_dict(row)
    except svc.TcoValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.patch("/costos/{costo_id}")
def update_costo(costo_id: str, body: CostoUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.manage", db)
    row = svc.update_costo(db, user.organization_id, costo_id, body.model_dump(exclude_unset=True), user.id)
    db.commit()
    return svc.costo_to_dict(row)


# --- Distribución ---

@router.post("/distribuciones", status_code=status.HTTP_201_CREATED)
def create_distribucion(body: DistribucionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.manage", db)
    try:
        row = svc.create_distribucion(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return svc.distribucion_to_dict(row)
    except svc.TcoValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


# --- TCO ---

@router.post("/calcular")
def calcular_tco(body: TcoCalcularRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    result = svc.calcular_tco(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return result


@router.get("/desviacion")
def desviacion(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return svc.calcular_desviacion(db, user.organization_id)


@router.get("/tablero")
def tablero(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return svc.centro_control_resumen(db, user.organization_id)


# --- Rentabilidad ---

@router.post("/rentabilidad")
def rentabilidad(body: RentabilidadRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return svc.calcular_rentabilidad(db, user.organization_id, body.model_dump())


# --- Simulaciones ---

@router.post("/simular")
def simular(body: SimulacionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.simulate", db)
    try:
        result = svc.simular(db, user.organization_id, body.tipo, body.parametros, user.id)
        db.commit()
        return result
    except svc.TcoValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.post("/simular/make-or-buy")
def simular_make_or_buy(body: MakeOrBuyRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.simulate", db)
    from app.tco_enums import TipoSimulacion
    result = svc.simular(db, user.organization_id, TipoSimulacion.MAKE_OR_BUY, body.model_dump(), user.id)
    db.commit()
    return result


@router.post("/simular/sustitucion-proveedor")
def simular_sustitucion(body: SustitucionProveedorRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.simulate", db)
    from app.tco_enums import TipoSimulacion
    result = svc.simular(db, user.organization_id, TipoSimulacion.SUSTITUCION_PROVEEDOR, body.model_dump(), user.id)
    db.commit()
    return result


@router.post("/comparar-proveedores")
def comparar_proveedores(body: CompararProveedoresRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.simulate", db)
    return svc.comparar_proveedores(db, user.organization_id, body.proveedor_ids, body.unidades)


# --- Alianzas ---

@router.get("/alianzas")
def list_alianzas(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "alianzas.view", db)
    return svc.list_alianzas(db, user.organization_id)


@router.post("/alianzas", status_code=status.HTTP_201_CREATED)
def create_alianza(body: AlianzaCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "alianzas.manage", db)
    row = svc.create_alianza(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return svc.alianza_to_dict(row)


@router.patch("/alianzas/{alianza_id}/estado")
def update_alianza_estado(alianza_id: str, body: AlianzaEstadoUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "alianzas.manage", db)
    row = svc.update_alianza_estado(db, user.organization_id, alianza_id, body.estado, user.id, body.justificacion)
    db.commit()
    return svc.alianza_to_dict(row)


# --- Historial ---

@router.get("/historial")
def historial(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "tco.view", db)
    return svc.list_historial(db, user.organization_id)
