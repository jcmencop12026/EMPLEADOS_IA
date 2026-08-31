"""API — Continuidad operativa y resiliencia (1360)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.schemas_continuidad import (
    AccionCorrectivaCreate,
    BackupEjecucionCreate,
    BackupPoliticaCreate,
    BackupVerificacionCreate,
    ContingenciaActivar,
    DependenciaCreate,
    DisponibilidadCreate,
    EscalamientoCreate,
    FallbackCreate,
    IncidenteCreate,
    IncidenteEstadoUpdate,
    ModoDegradadoCreate,
    PlanCreate,
    PostIncidenteCreate,
    PruebaCreate,
    RestorePruebaCreate,
    RunbookCreate,
    ServicioCreate,
    SloCreate,
    SloMedir,
)
from app.services import continuidad_service as svc

router = APIRouter(prefix="/api/continuidad", tags=["Continuidad"])


def _validation_error(exc: svc.ContinuidadValidationError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/tablero")
def get_tablero(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    return svc.tablero(db, user.organization_id)


@router.get("/centro-control-resumen")
def get_centro_control(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    return svc.centro_control_resumen(db, user.organization_id)


@router.get("/servicios")
def list_servicios(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    return svc.list_servicios(db, user.organization_id)


@router.post("/servicios", status_code=201)
def create_servicio(
    body: ServicioCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    try:
        row = svc.create_servicio(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return svc.servicio_to_dict(row)
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.patch("/servicios/{servicio_id}/estado")
def update_estado_servicio(
    servicio_id: str,
    estado: str,
    mensaje: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    try:
        row = svc.update_estado_servicio(db, user.organization_id, servicio_id, estado, mensaje)
        db.commit()
        return svc.servicio_to_dict(row)
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.post("/servicios/{servicio_id}/evaluar-rto-rpo")
def evaluar_rto_rpo(
    servicio_id: str,
    tiempo_recuperacion_min: float,
    perdida_datos_min: float,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    result = svc.evaluar_rto_rpo(db, user.organization_id, servicio_id, tiempo_recuperacion_min, perdida_datos_min)
    db.commit()
    return result


@router.post("/servicios/{servicio_id}/reportar-salud")
def reportar_salud(
    servicio_id: str,
    estado: str,
    mensaje: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    """Adaptador preparado para integración 1330 — reporte de salud de conectores."""
    try:
        row = svc.update_estado_servicio(db, user.organization_id, servicio_id, estado, mensaje)
        db.commit()
        return {"servicio_id": row.id, "estado_operacional": row.estado_operacional, "integracion_1330": True}
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.post("/dependencias", status_code=201)
def create_dependencia(
    body: DependenciaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    row = svc.create_dependencia(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "critica": row.critica}


@router.get("/dependencias/analisis")
def analizar_dependencias(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    return svc.analizar_dependencias(db, user.organization_id)


@router.get("/planes")
def list_planes(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    return svc.list_planes(db, user.organization_id)


@router.post("/planes", status_code=201)
def create_plan(
    body: PlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    row = svc.create_plan(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return svc.plan_to_dict(row)


@router.post("/planes/{plan_id}/activar", status_code=201)
def activar_plan(
    plan_id: str,
    body: ContingenciaActivar,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.activate")),
):
    row = svc.activar_plan(db, user.organization_id, plan_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "plan_id": row.plan_id, "estado": "ACTIVADO"}


@router.post("/backups/politicas", status_code=201)
def create_politica_backup(
    body: BackupPoliticaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("backups.manage")),
):
    row = svc.create_politica_backup(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "recurso": row.recurso, "estado": row.estado}


@router.post("/backups/ejecuciones", status_code=201)
def registrar_ejecucion_backup(
    body: BackupEjecucionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("backups.manage")),
):
    try:
        row = svc.registrar_ejecucion_backup(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "resultado": row.resultado, "estado_registro": row.estado_registro}
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.post("/backups/verificaciones", status_code=201)
def verificar_backup(
    body: BackupVerificacionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("backups.verify")),
):
    row = svc.verificar_backup(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "explicacion": row.explicacion}


@router.post("/backups/restores", status_code=201)
def registrar_restore(
    body: RestorePruebaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.test")),
):
    try:
        row = svc.registrar_restore(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "tipo": row.tipo, "entorno_destino": row.entorno_destino}
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.get("/incidentes")
def list_incidentes(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("incidentes.view")),
):
    return svc.list_incidentes(db, user.organization_id)


@router.post("/incidentes", status_code=201)
def create_incidente(
    body: IncidenteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("incidentes.manage")),
):
    try:
        row = svc.create_incidente(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return svc.incidente_to_dict(row)
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.patch("/incidentes/{incidente_id}/estado")
def update_incidente_estado(
    incidente_id: str,
    body: IncidenteEstadoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("incidentes.manage")),
):
    try:
        row = svc.update_incidente_estado(db, user.organization_id, incidente_id, body.model_dump(), user.id)
        db.commit()
        return svc.incidente_to_dict(row)
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.post("/incidentes/{incidente_id}/cerrar")
def cerrar_incidente(
    incidente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("incidentes.close")),
):
    row = svc.cerrar_incidente(db, user.organization_id, incidente_id, user.id)
    db.commit()
    return svc.incidente_to_dict(row)


@router.post("/modo-degradado", status_code=201)
def create_modo_degradado(
    body: ModoDegradadoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    row = svc.create_modo_degradado(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "activo": row.activo}


@router.post("/fallbacks", status_code=201)
def create_fallback(
    body: FallbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    row = svc.create_fallback(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id}


@router.post("/slos", status_code=201)
def create_slo(
    body: SloCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    row = svc.create_slo(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "objetivo_pct": float(row.objetivo_pct)}


@router.post("/slos/{slo_id}/medir")
def medir_slo(
    slo_id: str,
    body: SloMedir,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    row = svc.medir_slo(db, user.organization_id, slo_id, body.medido_pct, user.id)
    db.commit()
    return {"id": row.id, "medido_pct": float(row.medido_pct) if row.medido_pct else None, "incumplido": row.incumplido}


@router.post("/disponibilidad", status_code=201)
def registrar_disponibilidad(
    body: DisponibilidadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    row = svc.registrar_disponibilidad(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {
        "id": row.id,
        "disponibilidad_pct": float(row.disponibilidad_pct),
        "tiempo_disponible_min": float(row.tiempo_disponible_min),
        "tiempo_caido_min": float(row.tiempo_caido_min),
    }


@router.post("/escalamientos", status_code=201)
def create_escalamiento(
    body: EscalamientoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    try:
        row = svc.create_escalamiento(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "severidad": row.severidad, "nivel": row.nivel}
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.post("/runbooks", status_code=201)
def create_runbook(
    body: RunbookCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.manage")),
):
    try:
        row = svc.create_runbook(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return svc.runbook_to_dict(row)
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.post("/pruebas", status_code=201)
def create_prueba(
    body: PruebaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.test")),
):
    row = svc.create_prueba(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "escenario": row.escenario, "tipo": row.tipo}


@router.post("/post-incidentes", status_code=201)
def create_post_incidente(
    body: PostIncidenteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("incidentes.manage")),
):
    try:
        row = svc.create_post_incidente(db, user.organization_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "aprendizaje_ref": row.aprendizaje_ref, "integracion_1260_prep": True}
    except svc.ContinuidadValidationError as exc:
        raise _validation_error(exc) from exc


@router.post("/acciones-correctivas", status_code=201)
def create_accion_correctiva(
    body: AccionCorrectivaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("incidentes.manage")),
):
    row = svc.create_accion_correctiva(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "estado": row.estado}


@router.get("/alertas")
def list_alertas(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("continuidad.view")),
):
    return svc.list_alertas(db, user.organization_id)
