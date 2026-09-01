"""API — Espacio externo controlado empresa/prospecto/cliente V1."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import espacio_externo_service as svc

router = APIRouter(prefix="/api/espacio-externo", tags=["Espacio externo"])


class EntidadCreate(BaseModel):
    expediente_id: str
    contacto_email: str | None = None


class AccesoInvite(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)
    full_name: str = Field(..., min_length=2, max_length=200)
    rol_externo: str = "PROSPECTO"
    password: str | None = Field(None, min_length=8, max_length=120)


class PublicacionEstado(BaseModel):
    estado: str
    destinatario: str | None = None
    motivo: str | None = None
    audiencia: str | None = None


class PromoverCliente(BaseModel):
    contrato_ref: str | None = None
    capacidades: list[str] | None = None


class LinkProyecto(BaseModel):
    proyecto_id: str


class ConfigureContrato(BaseModel):
    capacidades: list[str]
    empleados_ia_ids: list[str] | None = None


class SoporteCasoCreate(BaseModel):
    asunto: str = Field(..., min_length=3, max_length=200)
    descripcion: str = Field(..., min_length=3)
    tipo: str = "SOLICITUD"
    prioridad: str = "MEDIA"


class SoporteComentarioCreate(BaseModel):
    cuerpo: str = Field(..., min_length=1)
    evidencia_ref: str | None = None


class SolicitudInformacion(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=200)
    descripcion: str | None = None
    informacion_item_id: str | None = None


class EntregaExterna(BaseModel):
    item_id: str | None = None
    entrega_id: str | None = None
    contenido: str = Field(..., min_length=1)
    evidencia_ref: str | None = None
    fuente_tipo: str = "SUMINISTRADA_EMPRESA"


class ValidarEntrega(BaseModel):
    estado: str
    marcar_suficiencia: bool = False


# --- Internal (EIAAX staff) ---

@router.get("/entidades")
def list_entidades(
    expediente_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    return svc.list_entidades(db, user.organization_id, expediente_id=expediente_id)


@router.post("/entidades", status_code=201)
def create_entidad(
    body: EntidadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    result = svc.create_entidad_from_expediente(
        db,
        user.organization_id,
        user.id,
        expediente_id=body.expediente_id,
        contacto_email=body.contacto_email,
    )
    db.commit()
    return result


@router.get("/entidades/{entidad_id}")
def get_entidad(
    entidad_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    return svc.get_entidad_detail(db, user.organization_id, entidad_id)


@router.post("/entidades/{entidad_id}/accesos", status_code=201)
def invite_acceso(
    entidad_id: str,
    body: AccesoInvite,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.acceso")),
):
    result = svc.invite_external_user(
        db,
        user.organization_id,
        user.id,
        entidad_id=entidad_id,
        email=body.email,
        full_name=body.full_name,
        rol_externo=body.rol_externo,
        password=body.password,
    )
    db.commit()
    return result


@router.delete("/accesos/{acceso_id}")
def revoke_acceso(
    acceso_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.acceso")),
):
    result = svc.revoke_access(db, user.organization_id, user.id, acceso_id)
    db.commit()
    return result


@router.post("/entidades/{entidad_id}/promover-cliente")
def promover_cliente(
    entidad_id: str,
    body: PromoverCliente,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    result = svc.promote_to_cliente(
        db,
        user.organization_id,
        user.id,
        entidad_id,
        contrato_ref=body.contrato_ref,
        capacidades=body.capacidades,
    )
    db.commit()
    return result


@router.post("/entidades/{entidad_id}/link-proyecto")
def link_proyecto(
    entidad_id: str,
    body: LinkProyecto,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    result = svc.link_proyecto(
        db,
        user.organization_id,
        user.id,
        entidad_id,
        proyecto_id=body.proyecto_id,
    )
    db.commit()
    return result


@router.patch("/entidades/{entidad_id}/contrato")
def configure_contrato(
    entidad_id: str,
    body: ConfigureContrato,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    result = svc.configure_contrato(
        db,
        user.organization_id,
        user.id,
        entidad_id,
        capacidades=body.capacidades,
        empleados_ia_ids=body.empleados_ia_ids,
    )
    db.commit()
    return result


@router.patch("/publicaciones/{publicacion_id}/estado")
def set_publicacion(
    publicacion_id: str,
    body: PublicacionEstado,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.publish")),
):
    result = svc.set_publicacion_estado(
        db,
        user.organization_id,
        user.id,
        publicacion_id=publicacion_id,
        estado=body.estado,
        destinatario=body.destinatario,
        motivo=body.motivo,
        audiencia=body.audiencia,
    )
    db.commit()
    return result


@router.get("/publicaciones/{publicacion_id}/historial")
def historial_publicacion(
    publicacion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    return svc.get_publicacion_historial(db, user.organization_id, publicacion_id)


@router.post("/entidades/{entidad_id}/solicitudes", status_code=201)
def crear_solicitud(
    entidad_id: str,
    body: SolicitudInformacion,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    result = svc.crear_solicitud_informacion(
        db,
        user.organization_id,
        user.id,
        entidad_id,
        titulo=body.titulo,
        descripcion=body.descripcion,
        informacion_item_id=body.informacion_item_id,
    )
    db.commit()
    return result


@router.post("/entregas/{entrega_id}/validar")
def validar_entrega(
    entrega_id: str,
    body: ValidarEntrega,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.manage")),
):
    result = svc.validar_entrega_interna(
        db,
        user.organization_id,
        user.id,
        entrega_id,
        estado=body.estado,
        marcar_suficiencia=body.marcar_suficiencia,
    )
    db.commit()
    return result


# --- Portal externo (usuario empresa/prospecto) ---

@router.get("/mi-espacio")
def mi_espacio(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_context(db, user)


@router.get("/mi-espacio/inicio")
def mi_inicio(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_inicio(db, user)


@router.get("/mi-espacio/informacion")
def mi_informacion(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_informacion(db, user)


@router.get("/mi-espacio/estado")
def mi_estado(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_estado(db, user)


@router.get("/mi-espacio/vista-entidad")
def mi_vista_entidad(
    paquete: str = "RESULTADOS",
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_vista_entidad(db, user, paquete=paquete)


@router.post("/mi-espacio/entregas", status_code=201)
def mi_entrega(
    body: EntregaExterna,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.entregar")),
):
    result = svc.external_entregar(
        db,
        user,
        item_id=body.item_id,
        entrega_id=body.entrega_id,
        contenido=body.contenido,
        evidencia_ref=body.evidencia_ref,
        fuente_tipo=body.fuente_tipo,
    )
    db.commit()
    return result


@router.get("/mi-espacio/implementacion")
def mi_implementacion(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_implementacion(db, user)


@router.get("/mi-espacio/empleados-ia")
def mi_empleados_ia(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_empleados_ia(db, user)


@router.get("/mi-espacio/empleados-ia/{employee_id}")
def mi_empleado_ia(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_empleado_ia(db, user, employee_id)


@router.get("/mi-espacio/informes")
def mi_informes(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_informes(db, user)


@router.get("/mi-espacio/informes/{message_id}")
def mi_informe(
    message_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_informe(db, user, message_id)


@router.get("/mi-espacio/soporte")
def mi_soporte(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_soporte(db, user)


@router.post("/mi-espacio/soporte/casos", status_code=201)
def mi_soporte_crear(
    body: SoporteCasoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    result = svc.create_portal_soporte_caso(
        db,
        user,
        asunto=body.asunto,
        descripcion=body.descripcion,
        tipo=body.tipo,
        prioridad=body.prioridad,
    )
    db.commit()
    return result


@router.get("/mi-espacio/soporte/casos/{case_id}")
def mi_soporte_caso(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    return svc.get_portal_soporte_caso(db, user, case_id)


@router.post("/mi-espacio/soporte/casos/{case_id}/comentarios", status_code=201)
def mi_soporte_comentario(
    case_id: str,
    body: SoporteComentarioCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("espacio_externo.portal")),
):
    result = svc.add_portal_soporte_comentario(
        db,
        user,
        case_id,
        cuerpo=body.cuerpo,
        evidencia_ref=body.evidencia_ref,
    )
    db.commit()
    return result
