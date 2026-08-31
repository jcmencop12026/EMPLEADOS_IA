"""API — Mesa de Ayuda y Soporte (MB-12)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission, require_permission, user_permissions
from app.schemas_support import (
    SupportAutoservicioQuery,
    SupportCaseAssign,
    SupportCaseAutoCreate,
    SupportCaseClose,
    SupportCaseCreate,
    SupportCaseDetailOut,
    SupportCaseOut,
    SupportCaseResolve,
    SupportCaseStatusUpdate,
    SupportAssigneeOut,
    SupportClassify,
    SupportCommentCreate,
    SupportContratoCentroControl,
    SupportContratoMiTrabajo,
    SupportDiagnosisUpdate,
    SupportEscalate,
    SupportEvidenceCreate,
    SupportKnowledgeProposalCreate,
    SupportPostReviewUpsert,
    SupportPrioritySuggest,
    SupportPriorityUpdate,
    SupportProblemCreate,
    SupportProblemUpdate,
    SupportSlaPolicyCreate,
    SupportValidateResolution,
)
from app.services import support_service as svc

router = APIRouter(prefix="/api/soporte", tags=["soporte"])


def _can_view_all(user: User, db: Session) -> bool:
    perms = user_permissions(user, db)
    return "support.view" in perms or "support.admin" in perms


def _http_value(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _http_lookup(exc: LookupError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@router.get("/casos", response_model=list[SupportCaseOut])
def list_cases(
    estado: str | None = None,
    tipo: str | None = None,
    prioridad: str | None = None,
    sla_estado: str | None = None,
    q: str | None = None,
    solo_mios: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    perms = user_permissions(user, db)
    if "support.view" not in perms:
        if "support.create" not in perms:
            raise HTTPException(status_code=403, detail="No autorizado.")
        solo_mios = True
    elif solo_mios is False:
        check_permission(user, "support.view", db)
    return svc.list_cases(
        db,
        user.organization_id,
        user=user,
        can_view_all=_can_view_all(user, db),
        estado=estado,
        tipo=tipo,
        prioridad=prioridad,
        sla_estado=sla_estado,
        q=q,
        solo_mios=solo_mios,
        limit=limit,
    )


@router.post("/casos", response_model=SupportCaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    body: SupportCaseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.create")),
):
    try:
        return svc.create_case_manual(db, user.organization_id, user, body.model_dump())
    except ValueError as exc:
        raise _http_value(exc) from exc


@router.post("/casos/auto", response_model=SupportCaseOut, status_code=status.HTTP_201_CREATED)
def create_case_auto(
    body: SupportCaseAutoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.admin")),
):
    try:
        return svc.create_case_auto(
            db,
            user.organization_id,
            body.model_dump(),
            actor_id=user.id,
        )
    except ValueError as exc:
        raise _http_value(exc) from exc


@router.get("/casos/{case_id}", response_model=SupportCaseDetailOut)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    perms = user_permissions(user, db)
    can_all = _can_view_all(user, db)
    detail = svc.get_case_detail(
        db,
        user.organization_id,
        case_id,
        can_view_internal="support.admin" in perms or "support.assign" in perms,
    )
    if not detail:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
    if not can_all and user.id not in (detail["solicitante_id"], detail.get("responsable_id")):
        raise HTTPException(status_code=403, detail="No autorizado para ver este caso.")
    return detail


@router.get("/agentes-asignables", response_model=list[SupportAssigneeOut])
def list_assignable_agents(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.assign")),
):
    return svc.list_assignable_agents(db, user.organization_id)


@router.post("/casos/{case_id}/asignar", response_model=SupportCaseOut)
def assign_case(
    case_id: str,
    body: SupportCaseAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.assign")),
):
    try:
        return svc.assign_case(
            db,
            user.organization_id,
            case_id,
            user,
            responsable_id=body.responsable_id,
            grupo=body.grupo,
            responsable_tecnico_id=body.responsable_tecnico_id,
            responsable_funcional_id=body.responsable_funcional_id,
        )
    except LookupError as exc:
        raise _http_lookup(exc) from exc


@router.patch("/casos/{case_id}/estado", response_model=SupportCaseOut)
def update_status(
    case_id: str,
    body: SupportCaseStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.update")),
):
    try:
        return svc.update_status(
            db,
            user.organization_id,
            case_id,
            user,
            estado=body.estado,
            nota=body.nota,
        )
    except (LookupError, ValueError) as exc:
        if isinstance(exc, LookupError):
            raise _http_lookup(exc) from exc
        raise _http_value(exc) from exc


@router.post("/casos/{case_id}/clasificar", response_model=SupportCaseOut)
def classify_case(
    case_id: str,
    body: SupportClassify,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.update")),
):
    try:
        return svc.classify_case(
            db,
            user.organization_id,
            case_id,
            user,
            tipo=body.tipo,
            categoria=body.categoria,
            servicio_componente=body.servicio_componente,
        )
    except (LookupError, ValueError) as exc:
        if isinstance(exc, LookupError):
            raise _http_lookup(exc) from exc
        raise _http_value(exc) from exc


@router.post("/casos/{case_id}/prioridad", response_model=SupportCaseOut)
def update_priority(
    case_id: str,
    body: SupportPriorityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.update")),
):
    try:
        return svc.update_priority(
            db,
            user.organization_id,
            case_id,
            user,
            prioridad=body.prioridad,
            motivo=body.motivo,
        )
    except LookupError as exc:
        raise _http_lookup(exc) from exc


@router.post("/casos/{case_id}/escalar", response_model=SupportCaseOut)
def escalate_case(
    case_id: str,
    body: SupportEscalate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.update")),
):
    try:
        return svc.escalate_case(
            db,
            user.organization_id,
            case_id,
            user,
            motivo=body.motivo,
            nota=body.nota,
            coordinador_id=body.coordinador_id,
        )
    except (LookupError, ValueError) as exc:
        if isinstance(exc, LookupError):
            raise _http_lookup(exc) from exc
        raise _http_value(exc) from exc


@router.patch("/casos/{case_id}/diagnostico", response_model=SupportCaseOut)
def update_diagnosis(
    case_id: str,
    body: SupportDiagnosisUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.update")),
):
    try:
        return svc.update_diagnosis(
            db,
            user.organization_id,
            case_id,
            user,
            sintoma=body.sintoma,
            hipotesis=body.hipotesis,
            causa_probable=body.causa_probable,
            causa_validada=body.causa_validada,
        )
    except LookupError as exc:
        raise _http_lookup(exc) from exc


@router.post("/casos/{case_id}/evidencias")
def add_evidence(
    case_id: str,
    body: SupportEvidenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    perms = user_permissions(user, db)
    if "support.update" not in perms and "support.create" not in perms:
        case = svc.get_case(db, user.organization_id, case_id)
        if not case or case.solicitante_id != user.id:
            raise HTTPException(status_code=403, detail="No autorizado.")
    try:
        return svc.add_evidence(
            db,
            user.organization_id,
            case_id,
            user,
            tipo=body.tipo,
            referencia=body.referencia,
            descripcion=body.descripcion,
        )
    except (LookupError, ValueError) as exc:
        if isinstance(exc, LookupError):
            raise _http_lookup(exc) from exc
        raise _http_value(exc) from exc


@router.post("/casos/{case_id}/validar", response_model=SupportCaseOut)
def validate_resolution(
    case_id: str,
    body: SupportValidateResolution,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case = svc.get_case(db, user.organization_id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
    perms = user_permissions(user, db)
    if case.solicitante_id != user.id and "support.close" not in perms:
        raise HTTPException(status_code=403, detail="No autorizado.")
    try:
        return svc.validate_resolution(
            db,
            user.organization_id,
            case_id,
            user,
            aceptada=body.aceptada,
            comentario=body.comentario,
        )
    except (LookupError, ValueError) as exc:
        if isinstance(exc, LookupError):
            raise _http_lookup(exc) from exc
        raise _http_value(exc) from exc


@router.post("/casos/{case_id}/resolver", response_model=SupportCaseOut)
def resolve_case(
    case_id: str,
    body: SupportCaseResolve,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.resolve")),
):
    try:
        return svc.resolve_case(
            db,
            user.organization_id,
            case_id,
            user,
            resolucion=body.resolucion,
            cerrar=body.cerrar,
        )
    except LookupError as exc:
        raise _http_lookup(exc) from exc


@router.post("/casos/{case_id}/cerrar", response_model=SupportCaseOut)
def close_case(
    case_id: str,
    body: SupportCaseClose,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.close")),
):
    try:
        return svc.close_case(db, user.organization_id, case_id, user, nota=body.nota)
    except LookupError as exc:
        raise _http_lookup(exc) from exc


@router.post("/casos/{case_id}/comentarios")
def add_comment(
    case_id: str,
    body: SupportCommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    perms = user_permissions(user, db)
    can_internal = "support.assign" in perms or "support.admin" in perms
    if "support.create" not in perms and "support.update" not in perms:
        case = svc.get_case(db, user.organization_id, case_id)
        if not case or case.solicitante_id != user.id:
            raise HTTPException(status_code=403, detail="No autorizado.")
    try:
        return svc.add_comment(
            db,
            user.organization_id,
            case_id,
            user,
            cuerpo=body.cuerpo,
            es_interno=body.es_interno,
            evidencia_ref=body.evidencia_ref,
            can_view_internal=can_internal,
        )
    except (LookupError, PermissionError) as exc:
        if isinstance(exc, PermissionError):
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        raise _http_lookup(exc) from exc


@router.put("/casos/{case_id}/revision-posterior")
def upsert_post_review(
    case_id: str,
    body: SupportPostReviewUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.admin")),
):
    try:
        return svc.upsert_post_review(
            db,
            user.organization_id,
            case_id,
            user,
            body.model_dump(exclude_unset=True),
        )
    except LookupError as exc:
        raise _http_lookup(exc) from exc


@router.post("/sla", status_code=status.HTTP_201_CREATED)
def create_sla(
    body: SupportSlaPolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.admin")),
):
    return svc.create_sla_policy(db, user.organization_id, body.model_dump())


@router.get("/sla")
def list_sla(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.view")),
):
    return svc.list_sla_policies(db, user.organization_id)


@router.post("/prioridad/sugerir")
def suggest_priority(body: SupportPrioritySuggest):
    return svc.suggest_priority_for_case(body.impacto, body.urgencia)


@router.post("/autoservicio")
def autoservicio(
    body: SupportAutoservicioQuery,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.autoservicio_buscar(
        db,
        user.organization_id,
        user,
        consulta=body.consulta,
        can_view_all=_can_view_all(user, db),
    )


@router.get("/problemas")
def list_problems(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.view")),
):
    return svc.list_problems(db, user.organization_id)


@router.post("/problemas", status_code=status.HTTP_201_CREATED)
def create_problem(
    body: SupportProblemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.admin")),
):
    try:
        return svc.create_problem_from_cases(
            db,
            user.organization_id,
            user,
            titulo=body.titulo,
            descripcion=body.descripcion,
            case_ids=body.case_ids,
        )
    except (LookupError, ValueError) as exc:
        if isinstance(exc, LookupError):
            raise _http_lookup(exc) from exc
        raise _http_value(exc) from exc


@router.patch("/problemas/{problem_id}")
def update_problem(
    problem_id: str,
    body: SupportProblemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.admin")),
):
    try:
        return svc.update_problem(
            db,
            user.organization_id,
            problem_id,
            user,
            body.model_dump(exclude_unset=True),
        )
    except LookupError as exc:
        raise _http_lookup(exc) from exc


@router.post("/conocimiento/proponer", status_code=status.HTTP_201_CREATED)
def propose_knowledge(
    body: SupportKnowledgeProposalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.resolve")),
):
    return svc.propose_knowledge_article(
        db,
        user.organization_id,
        user,
        titulo=body.titulo,
        contenido=body.contenido,
        tipo_articulo=body.tipo_articulo,
        case_id=body.case_id,
        problem_id=body.problem_id,
    )


@router.post("/sla/verificar-alertas")
def check_sla_warnings(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.admin")),
):
    return svc.check_sla_warnings(db, user.organization_id)


@router.get("/contrato/mi-trabajo", response_model=SupportContratoMiTrabajo)
def contrato_mi_trabajo(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.contrato_mi_trabajo(db, user.organization_id, user.id)


@router.get("/contrato/centro-control", response_model=SupportContratoCentroControl)
def contrato_centro_control(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.view")),
):
    return svc.contrato_centro_control(db, user.organization_id)


@router.get("/indicadores")
def indicadores(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("support.view")),
):
    return svc.indicadores_soporte(db, user.organization_id)


@router.get("/tipos")
def list_tipos():
    from app.support_enums import (
        ESCALAMIENTO_MOTIVOS,
        ESTADOS_CASO,
        ESTADO_ETIQUETAS,
        EVIDENCIA_TIPOS,
        PRIORIDADES,
        SLA_ETIQUETAS,
        TIPOS_CASO,
    )

    return {
        "tipos": list(TIPOS_CASO),
        "estados": list(ESTADOS_CASO),
        "estado_etiquetas": ESTADO_ETIQUETAS,
        "prioridades": list(PRIORIDADES),
        "sla_etiquetas": SLA_ETIQUETAS,
        "escalamiento_motivos": list(ESCALAMIENTO_MOTIVOS),
        "evidencia_tipos": list(EVIDENCIA_TIPOS),
    }
