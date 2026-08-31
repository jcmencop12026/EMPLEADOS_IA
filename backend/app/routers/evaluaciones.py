"""API — Expediente de evaluación empresarial EIAAX (1405)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission, user_permissions
from app.services import evaluacion_service as svc
from app.services import evaluacion_accion_service as acc_svc
from app.services.evaluacion_proveedor_externo_service import listar_proveedores
from app.services.piiax_bridge_service import get_piiax_status, list_capacidades_catalog

router = APIRouter(prefix="/api/evaluaciones", tags=["Evaluaciones"])


class ExpedienteCreate(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=300)
    entidad_nombre: str = Field(..., min_length=2, max_length=200)
    entidad_ref: str | None = Field(None, max_length=120)
    necesidad: str | None = None
    objetivo: str | None = None
    area_proceso: str | None = Field(None, max_length=120)
    nivel: str = "PRELIMINAR"


class ExpedienteUpdate(BaseModel):
    titulo: str | None = Field(None, min_length=3, max_length=300)
    entidad_nombre: str | None = Field(None, min_length=2, max_length=200)
    entidad_ref: str | None = None
    necesidad: str | None = None
    objetivo: str | None = None
    area_proceso: str | None = None
    nivel: str | None = None
    estado: str | None = None
    notas_internas: str | None = None
    responsable_id: str | None = None
    valor_potencial: str | None = None


class InformacionUpdate(BaseModel):
    respuesta: str | None = None
    evidencia_ref: str | None = None
    estado: str | None = None


class HallazgoCreate(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=300)
    descripcion: str | None = None
    tipo_contenido: str = "INFERENCIA"
    confianza: str = "MEDIA"
    explicacion_confianza: str | None = None
    evidencia: str | None = None
    origen: str | None = None
    impacto_resumen: str | None = None
    visible_entidad: bool = False
    es_problema_original: bool = False


class VisibilidadBody(BaseModel):
    objeto_tipo: str = "hallazgo"
    objeto_id: str
    visible_entidad: bool


class VincularOportunidadBody(BaseModel):
    opportunity_id: str
    hallazgo_id: str | None = None


class CrearOportunidadBody(BaseModel):
    hallazgo_id: str
    dominio: str = "operaciones"


class PreguntarBody(BaseModel):
    mensaje: str = Field(..., min_length=2, max_length=2000)
    accion: str | None = None


class AccionCreate(BaseModel):
    capacidad: str
    tipo_accion: str = "LECTURA"
    titulo: str = Field(..., min_length=3, max_length=300)
    descripcion: str | None = None
    hallazgo_id: str | None = None
    parametros: dict[str, Any] | None = None
    solicitar: bool = False


class AccionAprobarBody(BaseModel):
    aprobado: bool = True
    motivo: str | None = None


class AccionResultadoBody(BaseModel):
    resultado_resumen: str
    evidencia_ref: str | None = None
    referencia_externa: str | None = None
    estado: str = "COMPLETADA"


class IndicadorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    unidad: str | None = None
    valor_antes: str | None = None
    valor_proyectado: str | None = None
    valor_real: str | None = None
    hallazgo_id: str | None = None
    visible_entidad: bool = False


@router.get("/capacidades")
def list_capacidades(user: User = Depends(require_permission("evaluacion.view"))):
    return {"capacidades": list_capacidades_catalog()}


@router.get("/integracion/piiax")
def estado_piiax(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return get_piiax_status(db, user.organization_id)


@router.get("/proveedores-externos")
def list_proveedores_externos(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return {"proveedores": listar_proveedores(db, user.organization_id)}


@router.get("")
def list_expedientes(
    estado: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return svc.list_expedientes(
        db, user.organization_id, estado=estado, q=q, limit=limit, offset=offset,
    )


@router.post("", status_code=201)
def create_expediente(
    body: ExpedienteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    exp = svc.create_expediente(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        titulo=body.titulo,
        entidad_nombre=body.entidad_nombre,
        entidad_ref=body.entidad_ref,
        necesidad=body.necesidad,
        objetivo=body.objetivo,
        area_proceso=body.area_proceso,
        nivel=body.nivel,
    )
    db.commit()
    return svc.expediente_to_detail(db, exp)


@router.get("/{expediente_id}")
def get_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    exp = svc._get_expediente(db, expediente_id, user.organization_id)  # noqa: SLF001
    return svc.expediente_to_detail(db, exp)


@router.patch("/{expediente_id}")
def update_expediente(
    expediente_id: str,
    body: ExpedienteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    exp = svc.update_expediente(
        db,
        expediente_id,
        user.organization_id,
        user_id=user.id,
        **body.model_dump(exclude_unset=True),
    )
    db.commit()
    return svc.expediente_to_detail(db, exp)


@router.post("/{expediente_id}/informacion/sync")
def sync_informacion(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    exp = svc._get_expediente(db, expediente_id, user.organization_id)  # noqa: SLF001
    svc.sync_informacion_adaptativa(db, exp, user_id=user.id)
    db.commit()
    return svc.expediente_to_detail(db, exp)


@router.patch("/{expediente_id}/informacion/{item_id}")
def update_informacion(
    expediente_id: str,
    item_id: str,
    body: InformacionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    svc.update_informacion_item(
        db,
        expediente_id,
        user.organization_id,
        item_id,
        respuesta=body.respuesta,
        evidencia_ref=body.evidencia_ref,
        estado=body.estado,
    )
    db.commit()
    exp = svc._get_expediente(db, expediente_id, user.organization_id)  # noqa: SLF001
    return svc.expediente_to_detail(db, exp)


@router.post("/{expediente_id}/evaluar")
def evaluar_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.evaluate")),
):
    result = svc.ejecutar_evaluacion_preliminar(
        db, expediente_id, user.organization_id, user_id=user.id,
    )
    db.commit()
    return result


@router.post("/{expediente_id}/hallazgos", status_code=201)
def create_hallazgo(
    expediente_id: str,
    body: HallazgoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.evaluate")),
):
    h = svc.create_hallazgo(
        db,
        expediente_id,
        user.organization_id,
        user_id=user.id,
        **body.model_dump(),
    )
    db.commit()
    return svc._hallazgo_dict(h)  # noqa: SLF001


@router.post("/{expediente_id}/visibilidad")
def set_visibilidad(
    expediente_id: str,
    body: VisibilidadBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.visibility")),
):
    result = svc.set_visibilidad(
        db,
        expediente_id,
        user.organization_id,
        objeto_tipo=body.objeto_tipo,
        objeto_id=body.objeto_id,
        visible_entidad=body.visible_entidad,
        user_id=user.id,
    )
    db.commit()
    return result


@router.get("/{expediente_id}/vista-entidad")
def vista_entidad(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.vista_entidad")),
):
    return svc.get_vista_entidad(db, expediente_id, user.organization_id)


@router.get("/{expediente_id}/trazabilidad")
def trazabilidad(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return svc.get_trazabilidad(db, expediente_id, user.organization_id)


@router.get("/{expediente_id}/impacto")
def impacto(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return svc.get_impacto_resumen(db, expediente_id, user.organization_id)


@router.post("/{expediente_id}/oportunidades/vincular", status_code=201)
def vincular_oportunidad(
    expediente_id: str,
    body: VincularOportunidadBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    link = svc.vincular_oportunidad(
        db,
        expediente_id,
        user.organization_id,
        opportunity_id=body.opportunity_id,
        hallazgo_id=body.hallazgo_id,
        user_id=user.id,
    )
    db.commit()
    return {"id": link.id, "opportunity_id": link.opportunity_id, "hallazgo_id": link.hallazgo_id}


@router.post("/{expediente_id}/oportunidades/crear", status_code=201)
def crear_oportunidad(
    expediente_id: str,
    body: CrearOportunidadBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    result = svc.crear_oportunidad_desde_hallazgo(
        db,
        expediente_id,
        user.organization_id,
        hallazgo_id=body.hallazgo_id,
        user_id=user.id,
        dominio=body.dominio,
    )
    db.commit()
    return result


@router.post("/{expediente_id}/preguntar")
def preguntar_eiaax(
    expediente_id: str,
    body: PreguntarBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return svc.ask_eiaax(
        db,
        expediente_id,
        user.organization_id,
        user_id=user.id,
        mensaje=body.mensaje,
        accion=body.accion,
    )


@router.get("/{expediente_id}/acciones")
def list_acciones(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return {"items": acc_svc.list_acciones(db, expediente_id, user.organization_id)}


@router.post("/{expediente_id}/acciones", status_code=201)
def crear_accion(
    expediente_id: str,
    body: AccionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.accion.request")),
):
    accion = acc_svc.crear_accion(
        db,
        expediente_id,
        user.organization_id,
        user_id=user.id,
        capacidad=body.capacidad,
        tipo_accion=body.tipo_accion,
        titulo=body.titulo,
        descripcion=body.descripcion,
        hallazgo_id=body.hallazgo_id,
        parametros=body.parametros,
        solicitar=body.solicitar,
    )
    db.commit()
    return acc_svc._accion_dict(db, accion, user.organization_id)  # noqa: SLF001


@router.post("/{expediente_id}/acciones/{accion_id}/solicitar")
def solicitar_accion(
    expediente_id: str,
    accion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.accion.request")),
):
    accion = acc_svc.solicitar_accion(db, accion_id, user.organization_id, user_id=user.id)
    db.commit()
    return acc_svc._accion_dict(db, accion, user.organization_id)  # noqa: SLF001


@router.post("/{expediente_id}/acciones/{accion_id}/aprobar")
def aprobar_accion(
    expediente_id: str,
    accion_id: str,
    body: AccionAprobarBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.accion.approve")),
):
    accion = acc_svc.aprobar_accion(
        db, accion_id, user.organization_id,
        user_id=user.id, aprobado=body.aprobado, motivo=body.motivo,
    )
    db.commit()
    return acc_svc._accion_dict(db, accion, user.organization_id)  # noqa: SLF001


@router.post("/{expediente_id}/acciones/{accion_id}/resultado")
def registrar_resultado_accion(
    expediente_id: str,
    accion_id: str,
    body: AccionResultadoBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.accion.request")),
):
    accion = acc_svc.registrar_resultado_compatible(
        db, accion_id, user.organization_id,
        user_id=user.id,
        resultado_resumen=body.resultado_resumen,
        evidencia_ref=body.evidencia_ref,
        referencia_externa=body.referencia_externa,
        estado=body.estado,
    )
    db.commit()
    return acc_svc._accion_dict(db, accion, user.organization_id)  # noqa: SLF001


@router.get("/{expediente_id}/indicadores")
def list_indicadores(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    return {"items": acc_svc.list_indicadores(db, expediente_id, user.organization_id)}


@router.post("/{expediente_id}/indicadores", status_code=201)
def crear_indicador(
    expediente_id: str,
    body: IndicadorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.indicadores.manage")),
):
    ind = acc_svc.crear_indicador(
        db, expediente_id, user.organization_id,
        user_id=user.id,
        nombre=body.nombre,
        unidad=body.unidad,
        valor_antes=body.valor_antes,
        valor_proyectado=body.valor_proyectado,
        valor_real=body.valor_real,
        hallazgo_id=body.hallazgo_id,
        visible_entidad=body.visible_entidad,
    )
    db.commit()
    return acc_svc._indicador_dict(ind)  # noqa: SLF001


@router.get("/{expediente_id}/siguiente-accion")
def get_siguiente_accion(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.view")),
):
    perms = user_permissions(user, db)
    resultado = svc.get_siguiente_accion(
        db, expediente_id, user.organization_id, permisos=perms, persistir=True,
    )
    db.commit()
    return resultado
