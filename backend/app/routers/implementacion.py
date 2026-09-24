"""Router — Implementación y éxito del cliente (1340)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_implementacion import (
    AdopcionCreate,
    BloqueadorCreate,
    BloqueadorResolver,
    CapacitacionCreate,
    EntregableCreate,
    EntregableUpdate,
    ExitoObjetivoCreate,
    ExitoObjetivoMedir,
    ExitoPlanAccionCreate,
    ExitoPlanCreate,
    ExitoRevisionCreate,
    ExpansionCreate,
    FaseCreate,
    GoLiveAprobacion,
    HitoCompletar,
    HitoCreate,
    PilotoAprobarProduccion,
    PilotoCreate,
    PilotoResultado,
    PlanAdopcionCreate,
    ProyectoCreate,
    ProyectoUpdate,
    ReadinessCreate,
    RenovacionCreate,
    RequisitoCreate,
    RiesgoCreate,
    TareaCreate,
    TareaCompletar,
)
from app.schemas_continuidad_comercial import ExpansionContinuidadCreate, RenovacionContinuidadCreate
from app.services import implementacion_service as svc

router = APIRouter(prefix="/api/implementacion", tags=["implementacion"])


def _val(exc: svc.ImplementacionValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/proyectos")
def list_proyectos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.view", db)
    return svc.list_proyectos(db, user.organization_id)


@router.post("/proyectos", status_code=status.HTTP_201_CREATED)
def create_proyecto(body: ProyectoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_proyecto(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return svc.proyecto_to_dict(row)


@router.get("/proyectos/{proyecto_id}")
def get_proyecto(proyecto_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.view", db)
    return svc.detalle_proyecto(db, user.organization_id, proyecto_id)


@router.patch("/proyectos/{proyecto_id}")
def update_proyecto(proyecto_id: str, body: ProyectoUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    try:
        row = svc.update_proyecto(db, user.organization_id, proyecto_id, body.model_dump(exclude_unset=True), user.id)
        db.commit()
        return svc.proyecto_to_dict(row)
    except svc.ImplementacionValidationError as exc:
        db.rollback()
        raise _val(exc) from exc


@router.get("/proyectos/{proyecto_id}/tablero")
def tablero(proyecto_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.view", db)
    return svc.tablero_proyecto(db, user.organization_id, proyecto_id)


@router.post("/proyectos/{proyecto_id}/fases", status_code=status.HTTP_201_CREATED)
def create_fase(proyecto_id: str, body: FaseCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_fase(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return svc.fase_to_dict(row)


@router.post("/proyectos/{proyecto_id}/hitos", status_code=status.HTTP_201_CREATED)
def create_hito(proyecto_id: str, body: HitoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_hito(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "codigo": row.codigo, "nombre": row.nombre, "estado": row.estado}


@router.post("/hitos/{hito_id}/completar")
def completar_hito(hito_id: str, body: HitoCompletar, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.completar_hito(db, user.organization_id, hito_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "estado": row.estado}


@router.post("/proyectos/{proyecto_id}/tareas", status_code=status.HTTP_201_CREATED)
def create_tarea(proyecto_id: str, body: TareaCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_tarea(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return svc.tarea_to_dict(row)


@router.post("/tareas/{tarea_id}/completar")
def completar_tarea(tarea_id: str, body: TareaCompletar, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.completar_tarea(db, user.organization_id, tarea_id, body.model_dump(), user.id)
    db.commit()
    return svc.tarea_to_dict(row)


@router.post("/requisitos/{requisito_id}/completar")
def completar_requisito(requisito_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.completar_requisito(db, user.organization_id, requisito_id, user.id)
    db.commit()
    return svc.requisito_to_dict(row)


@router.post("/bloqueadores/{bloqueador_id}/resolver")
def resolver_bloqueador(bloqueador_id: str, body: BloqueadorResolver, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.resolver_bloqueador(db, user.organization_id, bloqueador_id, user.id, body.observaciones)
    db.commit()
    return svc.bloqueador_to_dict(row)


@router.get("/proyectos/{proyecto_id}/entregables")
def list_entregables(proyecto_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.view", db)
    return svc.list_entregables(db, user.organization_id, proyecto_id)


@router.post("/proyectos/{proyecto_id}/entregables", status_code=status.HTTP_201_CREATED)
def create_entregable(proyecto_id: str, body: EntregableCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_entregable(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return svc.entregable_to_dict(row)


@router.patch("/entregables/{entregable_id}")
def patch_entregable(entregable_id: str, body: EntregableUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.update_entregable(db, user.organization_id, entregable_id, body.model_dump(exclude_unset=True), user.id)
    db.commit()
    return svc.entregable_to_dict(row)


@router.post("/proyectos/{proyecto_id}/requisitos", status_code=status.HTTP_201_CREATED)
def create_requisito(proyecto_id: str, body: RequisitoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_requisito(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return svc.requisito_to_dict(row)


@router.post("/proyectos/{proyecto_id}/readiness", status_code=status.HTTP_201_CREATED)
def evaluar_readiness(proyecto_id: str, body: ReadinessCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.evaluar_readiness(db, user.organization_id, proyecto_id, body.dimensiones, user.id)
    db.commit()
    return {"resultado": row.resultado, "explicacion": row.explicacion}


@router.post("/proyectos/{proyecto_id}/bloqueadores", status_code=status.HTTP_201_CREATED)
def create_bloqueador(proyecto_id: str, body: BloqueadorCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    try:
        row = svc.create_bloqueador(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
        db.commit()
        return svc.bloqueador_to_dict(row)
    except svc.ImplementacionValidationError as exc:
        db.rollback()
        raise _val(exc) from exc


@router.post("/proyectos/{proyecto_id}/riesgos", status_code=status.HTTP_201_CREATED)
def create_riesgo(proyecto_id: str, body: RiesgoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_riesgo(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "nivel": row.nivel, "descripcion": row.descripcion}


@router.post("/proyectos/{proyecto_id}/pilotos", status_code=status.HTTP_201_CREATED)
def create_piloto(proyecto_id: str, body: PilotoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    row = svc.create_piloto(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "estado": row.estado}


@router.post("/pilotos/{piloto_id}/resultado")
def resultado_piloto(piloto_id: str, body: PilotoResultado, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.manage", db)
    try:
        row = svc.registrar_resultado_piloto(db, user.organization_id, piloto_id, body.model_dump(), user.id)
        db.commit()
        return {"resultado": row.resultado, "explicacion": row.resultado_explicacion}
    except svc.ImplementacionValidationError as exc:
        db.rollback()
        raise _val(exc) from exc


@router.post("/pilotos/{piloto_id}/aprobar-produccion")
def aprobar_piloto(piloto_id: str, body: PilotoAprobarProduccion, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.approve_go_live", db)
    try:
        row = svc.aprobar_piloto_produccion(db, user.organization_id, piloto_id, user.id, body.observaciones)
        db.commit()
        return {"aprobado": row.aprobado_produccion}
    except svc.ImplementacionValidationError as exc:
        db.rollback()
        raise _val(exc) from exc


@router.post("/proyectos/{proyecto_id}/go-live")
def go_live(proyecto_id: str, body: GoLiveAprobacion, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "implementacion.approve_go_live", db)
    try:
        row = svc.aprobar_go_live(db, user.organization_id, proyecto_id, body.checklist, user.id, body.observaciones)
        db.commit()
        return svc.proyecto_to_dict(row)
    except svc.ImplementacionValidationError as exc:
        db.rollback()
        raise _val(exc) from exc


@router.post("/proyectos/{proyecto_id}/adopcion", status_code=status.HTTP_201_CREATED)
def registrar_adopcion(proyecto_id: str, body: AdopcionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.registrar_adopcion(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "metricas": body.metricas}


@router.post("/proyectos/{proyecto_id}/plan-adopcion", status_code=status.HTTP_201_CREATED)
def plan_adopcion(proyecto_id: str, body: PlanAdopcionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.create_plan_adopcion(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "tipo_accion": row.tipo_accion}


@router.post("/proyectos/{proyecto_id}/capacitaciones", status_code=status.HTTP_201_CREATED)
def capacitacion(proyecto_id: str, body: CapacitacionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.create_capacitacion(db, user.organization_id, proyecto_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "tema": row.tema}


# --- Éxito del cliente ---

@router.post("/exito/planes", status_code=status.HTTP_201_CREATED)
def create_plan_exito(body: ExitoPlanCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.create_plan_exito(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "titulo": row.titulo}


@router.post("/exito/planes/{plan_id}/objetivos", status_code=status.HTTP_201_CREATED)
def create_objetivo(plan_id: str, body: ExitoObjetivoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.create_objetivo(db, user.organization_id, plan_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "nombre": row.nombre, "estado_valor": row.estado_valor}


@router.post("/exito/objetivos/{objetivo_id}/medir")
def medir_objetivo(objetivo_id: str, body: ExitoObjetivoMedir, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.medir_objetivo(db, user.organization_id, objetivo_id, body.valor_medido, user.id)
    db.commit()
    return {"estado_valor": row.estado_valor, "valor_medido": float(row.valor_medido) if row.valor_medido else None}


@router.post("/exito/planes/{plan_id}/acciones", status_code=status.HTTP_201_CREATED)
def plan_accion(plan_id: str, body: ExitoPlanAccionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    try:
        row = svc.create_plan_accion(db, user.organization_id, plan_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "causa": row.causa}
    except svc.ImplementacionValidationError as exc:
        db.rollback()
        raise _val(exc) from exc


@router.post("/exito/planes/{plan_id}/revisiones", status_code=status.HTTP_201_CREATED)
def revision(plan_id: str, body: ExitoRevisionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.review", db)
    row = svc.create_revision(db, user.organization_id, plan_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "fecha": row.fecha.isoformat()}


@router.post("/proyectos/{proyecto_id}/salud")
def salud(proyecto_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.view", db)
    result = svc.calcular_salud(db, user.organization_id, proyecto_id, user.id)
    db.commit()
    return result


@router.post("/exito/renovaciones", status_code=status.HTTP_201_CREATED)
def renovacion(body: RenovacionContinuidadCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.create_renovacion(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "estado": row.estado, "opportunity_id": row.opportunity_id}


@router.post("/exito/expansiones", status_code=status.HTTP_201_CREATED)
def expansion(body: ExpansionContinuidadCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "exito_cliente.manage", db)
    row = svc.create_expansion(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return {"id": row.id, "tipo": row.tipo, "recomendacion": row.recomendacion, "opportunity_id": row.opportunity_id}
