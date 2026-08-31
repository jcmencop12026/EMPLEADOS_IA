"""Router — Centro de Información y Comunicaciones (MB-11)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.communications_enums import ALLOWED_TEMPLATE_VARIABLES, CANAL_TIPOS, COMUNICACION_ESTADOS
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_communications import (
    CommChannelCreate,
    CommChannelOut,
    CommCentroInformacionResumen,
    CommContratoMiTrabajo,
    CommEntregaInformeCreate,
    CommEntregaInformeOut,
    CommMessageCreate,
    CommMessageDetailOut,
    CommMessageOut,
    CommPreferenceOut,
    CommPreferenceUpdate,
    CommResumenCentroControl,
    CommRuleCreate,
    CommRuleOut,
    CommSolicitudInfoFaltante,
    CommTemplateCreate,
    CommTemplateOut,
    CommTemplateVersionCreate,
    CommTemplateVersionOut,
)
from app.services import communications_service as svc

router = APIRouter(prefix="/api/comunicaciones", tags=["comunicaciones"])


@router.get("/catalogo/variables")
def catalog_variables(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return {"variables": sorted(ALLOWED_TEMPLATE_VARIABLES), "canales": list(CANAL_TIPOS), "estados": list(COMUNICACION_ESTADOS)}


@router.get("/canales", response_model=list[CommChannelOut])
def list_channels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return svc.list_channels(db, user.organization_id)


@router.post("/canales", response_model=CommChannelOut, status_code=status.HTTP_201_CREATED)
def create_channel(body: CommChannelCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.channel.manage", db)
    try:
        return svc.create_channel(db, user.organization_id, user, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/plantillas", response_model=list[CommTemplateOut])
def list_templates(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return svc.list_templates(db, user.organization_id)


@router.post("/plantillas", response_model=CommTemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(body: CommTemplateCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.template.manage", db)
    try:
        return svc.create_template(db, user.organization_id, user, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/plantillas/{template_id}/versiones", response_model=CommTemplateVersionOut, status_code=status.HTTP_201_CREATED)
def create_template_version(
    template_id: str,
    body: CommTemplateVersionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_permission(user, "communications.template.manage", db)
    try:
        return svc.new_template_version(db, user.organization_id, template_id, user, body.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/reglas", response_model=list[CommRuleOut])
def list_rules(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return svc.list_rules(db, user.organization_id)


@router.post("/reglas", response_model=CommRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(body: CommRuleCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.rule.manage", db)
    return svc.create_rule(db, user.organization_id, user, body.model_dump())


@router.get("/mensajes", response_model=list[CommMessageOut])
def list_messages(
    estado: str | None = None,
    canal_tipo: str | None = None,
    q: str | None = None,
    programadas: bool | None = None,
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_permission(user, "communications.view", db)
    if programadas:
        estado = "PROGRAMADA"
    return svc.list_messages(
        db,
        user.organization_id,
        estado=estado,
        canal_tipo=canal_tipo,
        q=q,
        limit=limit,
    )


@router.get("/mensajes/{message_id}", response_model=CommMessageDetailOut)
def get_message(message_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.history.view", db)
    try:
        return svc.get_message_detail(db, user.organization_id, message_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/mensajes", response_model=CommMessageOut, status_code=status.HTTP_201_CREATED)
def create_message(body: CommMessageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    permission = "communications.schedule" if body.programada_para and not body.enviar_ahora else "communications.send"
    check_permission(user, permission, db)
    if body.programada_para:
        check_permission(user, "communications.schedule", db)
    try:
        return svc.create_message_manual(db, user.organization_id, user, body.model_dump())
    except (LookupError, ValueError) as exc:
        status_code = 404 if isinstance(exc, LookupError) else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/mensajes/{message_id}/cancelar", response_model=CommMessageOut)
def cancel_message(message_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.schedule", db)
    try:
        return svc.cancel_message(db, user.organization_id, message_id, user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/preferencias", response_model=CommPreferenceOut)
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return svc.get_preferences(db, user.organization_id, user)


@router.put("/preferencias", response_model=CommPreferenceOut)
def update_preferences(
    body: CommPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_permission(user, "communications.view", db)
    return svc.upsert_preference(db, user.organization_id, user, body.model_dump(exclude_none=True))


@router.get("/contrato/centro-control", response_model=CommResumenCentroControl)
def contrato_centro_control(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return svc.contrato_centro_control(db, user.organization_id)


@router.get("/contrato/mi-trabajo", response_model=CommContratoMiTrabajo)
def contrato_mi_trabajo(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return svc.contrato_mi_trabajo(db, user.organization_id)


@router.get("/centro-informacion/resumen", response_model=CommCentroInformacionResumen)
def centro_informacion_resumen(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.view", db)
    return svc.get_centro_informacion_resumen(db, user.organization_id)


@router.post("/informes/{informe_id}/entregar")
def entregar_informe(
    informe_id: str,
    body: CommEntregaInformeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_permission(user, "communications.send", db)
    try:
        return svc.deliver_informe_impacto(
            db,
            user.organization_id,
            user,
            informe_id=informe_id,
            **body.model_dump(),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/informes/entregas", response_model=list[CommEntregaInformeOut])
def list_entregas_informe(
    informe_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_permission(user, "communications.history.view", db)
    return svc.list_entregas_informe(db, user.organization_id, informe_id=informe_id)


@router.post("/evaluaciones/solicitud-informacion", response_model=CommMessageOut, status_code=status.HTTP_201_CREATED)
def solicitud_informacion_faltante(
    body: CommSolicitudInfoFaltante,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_permission(user, "communications.send", db)
    try:
        return svc.send_solicitud_informacion_faltante(
            db,
            user.organization_id,
            user,
            expediente_id=body.expediente_id,
            destinatario_id=body.destinatario_id,
        )
    except (LookupError, ValueError) as exc:
        code = 404 if isinstance(exc, LookupError) else 422
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.post("/bootstrap-defaults")
def bootstrap_defaults(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "communications.template.manage", db)
    svc.bootstrap_default_comm_assets(db, user.organization_id, user)
    db.commit()
    return {"ok": True, "message": "Plantillas y canal por defecto listos."}
