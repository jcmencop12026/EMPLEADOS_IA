"""API transversal — seguridad, gobierno de datos, trazabilidad y evidencia."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_empresa_seguridad import (
    AuditoriaConsultaOut,
    CentroConfianzaEmpresarialOut,
    ClasificacionAsignarIn,
    ClasificacionOut,
    EvidenciaVinculoIn,
    EvidenciaVinculoOut,
    GobiernoObjetoOut,
    TrazabilidadOut,
    VisibilidadNivelIn,
)
from app.services import empresa_seguridad_service as svc
from app.services.governance_service import list_classification_levels

router = APIRouter(prefix="/api/empresa-seguridad", tags=["empresa-seguridad"])


@router.get("/clasificaciones/niveles")
def niveles_clasificacion(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "gobierno.clasificacion.view", db)
    return list_classification_levels(db, user.organization_id)


@router.post("/clasificaciones", response_model=ClasificacionOut, status_code=201)
def asignar_clasificacion(
    body: ClasificacionAsignarIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.clasificacion.assign", db)
    result = svc.asignar_clasificacion(
        db,
        user.organization_id,
        user.id,
        objeto_tipo=body.objeto_tipo,
        objeto_id=body.objeto_id,
        codigo_clasificacion=body.codigo_clasificacion,
        motivo=body.motivo,
        catalog_entry_id=body.catalog_entry_id,
    )
    db.commit()
    return result


@router.get("/clasificaciones", response_model=list[ClasificacionOut])
def listar_clasificaciones(
    objeto_tipo: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.clasificacion.view", db)
    return svc.listar_clasificaciones_objeto(db, user.organization_id, objeto_tipo=objeto_tipo, limit=limit)


@router.get("/clasificaciones/{objeto_tipo}/{objeto_id}", response_model=ClasificacionOut | None)
def obtener_clasificacion(
    objeto_tipo: str,
    objeto_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.clasificacion.view", db)
    return svc.obtener_clasificacion(db, user.organization_id, objeto_tipo, objeto_id)


@router.post("/visibilidad", status_code=201)
def set_visibilidad_nivel(
    body: VisibilidadNivelIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.visibility", db)
    result = svc.set_visibilidad_nivel(
        db,
        user.organization_id,
        user.id,
        dominio=body.dominio,
        contexto_id=body.contexto_id,
        objeto_tipo=body.objeto_tipo,
        objeto_id=body.objeto_id,
        nivel_visibilidad=body.nivel_visibilidad,
        motivo=body.motivo,
        correlation_id=body.correlation_id,
    )
    db.commit()
    return result


@router.post("/evidencias", response_model=EvidenciaVinculoOut, status_code=201)
def vincular_evidencia(
    body: EvidenciaVinculoIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.evidencia.link", db)
    result = svc.vincular_evidencia(
        db,
        user.organization_id,
        user.id,
        tipo_evidencia=body.tipo_evidencia,
        referencia=body.referencia,
        objeto_tipo=body.objeto_tipo,
        objeto_id=body.objeto_id,
        rol_vinculo=body.rol_vinculo,
        descripcion=body.descripcion,
        correlation_id=body.correlation_id,
    )
    db.commit()
    return result


@router.get("/evidencias", response_model=list[EvidenciaVinculoOut])
def listar_evidencias(
    objeto_tipo: str | None = None,
    objeto_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.evidencia.view", db)
    return svc.listar_evidencias(
        db,
        user.organization_id,
        objeto_tipo=objeto_tipo,
        objeto_id=objeto_id,
        correlation_id=correlation_id,
        limit=limit,
    )


@router.get("/auditoria/consulta", response_model=list[AuditoriaConsultaOut])
def consultar_auditoria(
    accion: str | None = None,
    user_id: str | None = None,
    correlation_id: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.auditoria.consulta", db)
    return svc.consultar_auditoria(
        db,
        user.organization_id,
        accion=accion,
        user_id=user_id,
        correlation_id=correlation_id,
        desde=desde,
        hasta=hasta,
        limit=limit,
    )


@router.get("/trazabilidad/{correlation_id}", response_model=TrazabilidadOut)
def obtener_trazabilidad(
    correlation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.trazabilidad.view", db)
    return svc.obtener_trazabilidad(db, user.organization_id, correlation_id)


@router.get("/confianza", response_model=CentroConfianzaEmpresarialOut)
def centro_confianza_empresarial(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "gobierno.confianza.view", db)
    return svc.get_centro_confianza_empresarial(db, user.organization_id)


@router.get("/objetos/{objeto_tipo}/{objeto_id}", response_model=GobiernoObjetoOut)
def gobierno_objeto(
    objeto_tipo: str,
    objeto_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.view", db)
    return svc.obtener_gobierno_objeto(db, user.organization_id, objeto_tipo, objeto_id)


@router.get("/exportar")
def exportar_gobierno(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.auditoria.consulta", db)
    data = svc.exportar_evidencia_gobierno(db, user.organization_id, limit=limit)
    return JSONResponse(content=data)
