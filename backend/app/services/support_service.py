"""Servicio — Mesa de Ayuda y Soporte (MB-12)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.notifications import emit_event
from app.support_enums import (
    ESCALAMIENTO_MOTIVOS,
    ESTADOS_ABIERTOS,
    ESTADOS_CASO,
    EVIDENCIA_TIPOS,
    SLA_ESTADOS,
    TIPOS_CASO,
    suggest_priority,
)
from app.support_models import (
    SupportAutoDedup,
    SupportCase,
    SupportCaseComment,
    SupportCaseEvidence,
    SupportCaseHistory,
    SupportKnowledgeProposal,
    SupportPostReview,
    SupportProblem,
    SupportSlaPolicy,
)

DEDUP_WINDOW_HOURS = 4
_SECRET_PATTERNS = re.compile(
    r"(password|contraseña|api[_-]?key|token|secret|bearer)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def sanitize_text(text: str) -> str:
    """Elimina patrones de secretos del texto visible."""
    return _SECRET_PATTERNS.sub("[dato sensible omitido]", text or "")


def _next_case_number(db: Session, org_id: str) -> int:
    current = (
        db.query(func.max(SupportCase.numero))
        .filter(SupportCase.organization_id == org_id)
        .scalar()
    )
    return int(current or 0) + 1


def _find_sla_policy(
    db: Session,
    org_id: str,
    prioridad: str,
    *,
    tipo_caso: str | None = None,
    servicio: str | None = None,
) -> SupportSlaPolicy | None:
    q = db.query(SupportSlaPolicy).filter(
        SupportSlaPolicy.organization_id == org_id,
        SupportSlaPolicy.prioridad == prioridad,
        SupportSlaPolicy.is_active.is_(True),
    )
    if tipo_caso:
        q = q.filter(
            (SupportSlaPolicy.tipo_caso == tipo_caso) | (SupportSlaPolicy.tipo_caso.is_(None))
        )
    if servicio:
        q = q.filter(
            (SupportSlaPolicy.servicio == servicio) | (SupportSlaPolicy.servicio.is_(None))
        )
    return q.order_by(
        SupportSlaPolicy.tipo_caso.desc().nullslast(),
        SupportSlaPolicy.servicio.desc().nullslast(),
        SupportSlaPolicy.created_at.desc(),
    ).first()


def _apply_sla_limits(case: SupportCase, policy: SupportSlaPolicy | None, now: datetime) -> None:
    if not policy:
        case.fecha_limite = None
        case.primera_respuesta_limite = None
        case.resolucion_limite = None
        return
    if policy.minutos_primera_respuesta:
        case.primera_respuesta_limite = now + timedelta(minutes=policy.minutos_primera_respuesta)
    if policy.minutos_resolucion:
        case.resolucion_limite = now + timedelta(minutes=policy.minutos_resolucion)
        case.fecha_limite = case.resolucion_limite
    case.sla_policy_id = policy.id


def compute_sla_estado(case: SupportCase, now: datetime | None = None) -> str:
    now = _as_utc(now or _utcnow())
    if case.estado in ("CERRADO", "CANCELADO", "RESUELTO"):
        return "NO_APLICA"
    limite = case.resolucion_limite or case.fecha_limite
    if not limite:
        return "NO_APLICA"
    limite = _as_utc(limite)
    if now > limite:
        return "VENCIDO"
    if now > limite - timedelta(minutes=60):
        return "PROXIMO"
    return "DENTRO"


def _record_history(
    db: Session,
    *,
    org_id: str,
    case_id: str,
    accion: str,
    user_id: str | None,
    detalle: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> None:
    db.add(
        SupportCaseHistory(
            organization_id=org_id,
            case_id=case_id,
            accion=accion,
            usuario_id=user_id,
            detalle_json=json.dumps(detalle, ensure_ascii=False) if detalle else None,
            correlation_id=correlation_id,
        )
    )


def _publish_comm_event(
    db: Session,
    *,
    event_type: str,
    org_id: str,
    case: SupportCase,
    payload: dict[str, Any],
) -> None:
    """Publica evento al bus MB-11 sin romper la transacción principal."""
    try:
        from app.events.bus import EventMessage, publish

        body = {
            **payload,
            "case_id": case.id,
            "case_numero": case.numero,
            "correlation_id": case.correlation_id,
            "solicitante_id": case.solicitante_id,
            "responsable_id": case.responsable_id,
            "estado": case.estado,
            "asunto": case.asunto,
        }
        publish(
            EventMessage(
                event_type=event_type,
                organization_id=org_id,
                payload=body,
            ),
            db,
        )
    except Exception:
        pass


def _notify(
    db: Session,
    *,
    event_type: str,
    org_id: str,
    case: SupportCase,
    title: str,
    message: str,
    recipient_user_id: str | None = None,
) -> None:
    payload = {
        "title": title,
        "message": sanitize_text(message),
        "recipient_user_id": recipient_user_id,
        "notification_type": "WARNING" if "SLA" in event_type or "ESCALATED" in event_type else "INFO",
        "correlation_id": case.correlation_id,
        "case_id": case.id,
        "case_numero": case.numero,
    }
    emit_event(
        event_type,
        org_id,
        source_type="support_case",
        source_id=case.id,
        payload=payload,
        db=db,
    )
    _publish_comm_event(db, event_type=event_type, org_id=org_id, case=case, payload=payload)


def case_to_dict(case: SupportCase, *, include_description: bool = True) -> dict[str, Any]:
    return {
        "id": case.id,
        "organization_id": case.organization_id,
        "numero": case.numero,
        "referencia": f"SUP-{case.numero:05d}",
        "tipo": case.tipo,
        "categoria": case.categoria,
        "asunto": case.asunto,
        "descripcion": sanitize_text(case.descripcion) if include_description else None,
        "prioridad": case.prioridad,
        "prioridad_sugerida": case.prioridad_sugerida,
        "impacto": case.impacto,
        "urgencia": case.urgencia,
        "estado": case.estado,
        "solicitante_id": case.solicitante_id,
        "responsable_id": case.responsable_id,
        "responsable_tecnico_id": case.responsable_tecnico_id,
        "responsable_funcional_id": case.responsable_funcional_id,
        "coordinador_id": case.coordinador_id,
        "grupo": case.grupo,
        "modulo_relacionado": case.modulo_relacionado,
        "entidad_relacionada": case.entidad_relacionada,
        "servicio_componente": case.servicio_componente,
        "problema_id": case.problema_id,
        "es_incidente_mayor": case.es_incidente_mayor,
        "correlation_id": case.correlation_id,
        "origen": case.origen,
        "origen_tipo": case.origen_tipo,
        "origen_id": case.origen_id,
        "resolucion": sanitize_text(case.resolucion) if case.resolucion else None,
        "sintoma": sanitize_text(case.sintoma) if case.sintoma else None,
        "hipotesis": sanitize_text(case.hipotesis) if case.hipotesis else None,
        "causa_probable": sanitize_text(case.causa_probable) if case.causa_probable else None,
        "causa_validada": sanitize_text(case.causa_validada) if case.causa_validada else None,
        "validacion_solicitante": case.validacion_solicitante,
        "validacion_at": case.validacion_at,
        "escalamiento_nivel": case.escalamiento_nivel,
        "sla_estado": compute_sla_estado(case),
        "primera_respuesta_limite": case.primera_respuesta_limite,
        "resolucion_limite": case.resolucion_limite,
        "fecha_limite": case.fecha_limite,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "resuelto_at": case.resuelto_at,
        "cerrado_at": case.cerrado_at,
        "clasificado_at": case.clasificado_at,
    }


def get_case(db: Session, org_id: str, case_id: str) -> SupportCase | None:
    return (
        db.query(SupportCase)
        .filter(SupportCase.id == case_id, SupportCase.organization_id == org_id)
        .first()
    )


def list_assignable_agents(db: Session, org_id: str) -> list[dict[str, Any]]:
    """Usuarios de la organización autorizados para asignación de casos de soporte."""
    from app.permissions import user_permissions

    assign_perms = frozenset({"support.assign", "support.view", "support.admin", "support.update"})
    users = (
        db.query(User)
        .filter(User.organization_id == org_id, User.is_active.is_(True), User.status == "ACTIVE")
        .order_by(User.full_name.asc().nullslast(), User.username.asc())
        .all()
    )
    agents: list[dict[str, Any]] = []
    for u in users:
        perms = user_permissions(u, db)
        if not perms.intersection(assign_perms):
            continue
        label = u.full_name or u.username
        agents.append({
            "id": u.id,
            "nombre": label,
            "username": u.username,
            "email": u.email,
            "rol": u.role,
            "etiqueta": f"{label} ({u.username})" + (f" — {u.email}" if u.email else ""),
        })
    return agents


def list_cases(
    db: Session,
    org_id: str,
    *,
    user: User,
    can_view_all: bool,
    estado: str | None = None,
    tipo: str | None = None,
    prioridad: str | None = None,
    sla_estado: str | None = None,
    q: str | None = None,
    solo_mios: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = db.query(SupportCase).filter(SupportCase.organization_id == org_id)
    if not can_view_all or solo_mios:
        query = query.filter(
            (SupportCase.solicitante_id == user.id) | (SupportCase.responsable_id == user.id)
        )
    if estado:
        query = query.filter(SupportCase.estado == estado.upper())
    if tipo:
        query = query.filter(SupportCase.tipo == tipo.upper())
    if prioridad:
        query = query.filter(SupportCase.prioridad == prioridad.upper())
    if q:
        like = f"%{q}%"
        query = query.filter(
            (SupportCase.asunto.ilike(like)) | (SupportCase.descripcion.ilike(like))
        )
    rows = query.order_by(SupportCase.created_at.desc()).limit(min(limit, 500)).all()
    items = [case_to_dict(r) for r in rows]
    if sla_estado:
        items = [i for i in items if i.get("sla_estado") == sla_estado.upper()]
    return items


def create_case_manual(
    db: Session,
    org_id: str,
    user: User,
    data: dict[str, Any],
) -> dict[str, Any]:
    tipo = (data.get("tipo") or "SOLICITUD").upper()
    if tipo not in TIPOS_CASO:
        raise ValueError(f"Tipo de caso no válido: {tipo}")
    now = _utcnow()
    impacto = (data.get("impacto") or "MEDIO").upper()
    urgencia = (data.get("urgencia") or "MEDIA").upper()
    sugerida = suggest_priority(impacto, urgencia)
    prioridad = (data.get("prioridad") or sugerida).upper()
    policy = _find_sla_policy(
        db,
        org_id,
        prioridad,
        tipo_caso=tipo,
        servicio=data.get("servicio_componente"),
    )
    case = SupportCase(
        organization_id=org_id,
        numero=_next_case_number(db, org_id),
        tipo=tipo,
        categoria=data.get("categoria"),
        asunto=sanitize_text(data["asunto"]),
        descripcion=sanitize_text(data["descripcion"]),
        prioridad=prioridad,
        prioridad_sugerida=sugerida,
        impacto=impacto,
        urgencia=urgencia,
        estado="NUEVO",
        solicitante_id=user.id,
        modulo_relacionado=data.get("modulo_relacionado"),
        entidad_relacionada=data.get("entidad_relacionada"),
        servicio_componente=data.get("servicio_componente"),
        correlation_id=data.get("correlation_id"),
        evidencia_ref=data.get("evidencia_ref"),
        grupo=data.get("grupo"),
        origen="MANUAL",
        es_incidente_mayor=bool(data.get("es_incidente_mayor")),
    )
    _apply_sla_limits(case, policy, now)
    db.add(case)
    db.flush()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CREACION",
        user_id=user.id,
        detalle={"origen": "MANUAL", "tipo": tipo},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def _dedup_key(org_id: str, origen_tipo: str, origen_id: str) -> str:
    raw = f"{org_id}|{origen_tipo}|{origen_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_case_auto(
    db: Session,
    org_id: str,
    data: dict[str, Any],
    *,
    actor_id: str | None = None,
) -> dict[str, Any]:
    origen_tipo = data["origen_tipo"]
    origen_id = data["origen_id"]
    key = _dedup_key(org_id, origen_tipo, origen_id)
    now = _utcnow()
    existing = (
        db.query(SupportAutoDedup)
        .filter(
            SupportAutoDedup.organization_id == org_id,
            SupportAutoDedup.dedup_key == key,
            SupportAutoDedup.ventana_fin >= now,
        )
        .first()
    )
    if existing:
        case = get_case(db, org_id, existing.case_id)
        if case:
            return {**case_to_dict(case), "deduplicado": True}

    solicitante_id = data.get("solicitante_id")
    if not solicitante_id:
        admin = (
            db.query(User)
            .filter(User.organization_id == org_id, User.role == "admin", User.is_active.is_(True))
            .first()
        )
        solicitante_id = admin.id if admin else actor_id
    if not solicitante_id:
        raise ValueError("No se pudo determinar solicitante para caso automático.")

    policy = _find_sla_policy(
        db,
        org_id,
        (data.get("prioridad") or "MEDIA").upper(),
        tipo_caso=(data.get("tipo") or "INCIDENTE").upper(),
        servicio=data.get("servicio_componente"),
    )
    impacto = (data.get("impacto") or "MEDIO").upper()
    urgencia = (data.get("urgencia") or "MEDIA").upper()
    sugerida = suggest_priority(impacto, urgencia)
    case = SupportCase(
        organization_id=org_id,
        numero=_next_case_number(db, org_id),
        tipo=(data.get("tipo") or "INCIDENTE").upper(),
        asunto=sanitize_text(data["asunto"]),
        descripcion=sanitize_text(data["descripcion"]),
        prioridad=(data.get("prioridad") or sugerida).upper(),
        prioridad_sugerida=sugerida,
        impacto=impacto,
        urgencia=urgencia,
        estado="NUEVO",
        solicitante_id=solicitante_id,
        modulo_relacionado=data.get("modulo_relacionado"),
        entidad_relacionada=data.get("entidad_relacionada"),
        servicio_componente=data.get("servicio_componente"),
        correlation_id=data.get("correlation_id"),
        origen="AUTOMATICO",
        origen_tipo=origen_tipo,
        origen_id=origen_id,
    )
    _apply_sla_limits(case, policy, now)
    db.add(case)
    db.flush()
    db.add(
        SupportAutoDedup(
            organization_id=org_id,
            dedup_key=key,
            case_id=case.id,
            origen_tipo=origen_tipo,
            origen_id=origen_id,
            ventana_fin=now + timedelta(hours=DEDUP_WINDOW_HOURS),
        )
    )
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CREACION",
        user_id=actor_id,
        detalle={"origen": "AUTOMATICO", "origen_tipo": origen_tipo, "origen_id": origen_id},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def assign_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    responsable_id: str | None,
    grupo: str | None = None,
    responsable_tecnico_id: str | None = None,
    responsable_funcional_id: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    case.responsable_id = responsable_id
    if responsable_tecnico_id is not None:
        case.responsable_tecnico_id = responsable_tecnico_id
    if responsable_funcional_id is not None:
        case.responsable_funcional_id = responsable_funcional_id
    if grupo is not None:
        case.grupo = grupo
    if case.estado in ("NUEVO", "CLASIFICADO"):
        case.estado = "ASIGNADO"
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="ASIGNACION",
        user_id=user.id,
        detalle={
            "responsable_id": responsable_id,
            "grupo": grupo,
            "responsable_tecnico_id": responsable_tecnico_id,
            "responsable_funcional_id": responsable_funcional_id,
        },
        correlation_id=case.correlation_id,
    )
    db.commit()
    if responsable_id:
        _notify(
            db,
            event_type="SUPPORT_CASE_ASSIGNED",
            org_id=org_id,
            case=case,
            title=f"Caso {case.numero} asignado",
            message=f"Se le asignó el caso: {case.asunto}",
            recipient_user_id=responsable_id,
        )
        db.commit()
    db.refresh(case)
    return case_to_dict(case)


def update_status(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    estado: str,
    nota: str | None = None,
) -> dict[str, Any]:
    estado = estado.upper()
    if estado not in ESTADOS_CASO:
        raise ValueError(f"Estado no válido: {estado}")
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    prev = case.estado
    case.estado = estado
    case.updated_at = _utcnow()
    if estado == "RESUELTO":
        case.resuelto_at = _utcnow()
    if estado in ("CERRADO", "CANCELADO"):
        case.cerrado_at = _utcnow()
    if not case.primera_respuesta_at and estado in (
        "EN_PROCESO",
        "EN_ANALISIS",
        "PENDIENTE_USUARIO",
        "RESUELTO",
    ):
        case.primera_respuesta_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CAMBIO_ESTADO",
        user_id=user.id,
        detalle={"de": prev, "a": estado, "nota": sanitize_text(nota) if nota else None},
        correlation_id=case.correlation_id,
    )
    _notify(
        db,
        event_type="SUPPORT_CASE_STATUS",
        org_id=org_id,
        case=case,
        title=f"Caso {case.numero}: {estado}",
        message=nota or f"El caso cambió de {prev} a {estado}.",
        recipient_user_id=case.solicitante_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def resolve_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    resolucion: str,
    cerrar: bool = False,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    case.resolucion = sanitize_text(resolucion)
    case.estado = "CERRADO" if cerrar else "RESUELTO"
    case.resuelto_at = _utcnow()
    if cerrar:
        case.cerrado_at = _utcnow()
        case.validacion_solicitante = "ACEPTADA"
        case.validacion_at = _utcnow()
    else:
        case.validacion_solicitante = "PENDIENTE"
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="RESOLUCION",
        user_id=user.id,
        detalle={"resolucion": case.resolucion, "cerrar": cerrar},
        correlation_id=case.correlation_id,
    )
    _notify(
        db,
        event_type="SUPPORT_CASE_RESOLVED",
        org_id=org_id,
        case=case,
        title=f"Caso {case.numero} resuelto",
        message=case.resolucion or "Su caso fue resuelto.",
        recipient_user_id=case.solicitante_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def close_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    nota: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    case.estado = "CERRADO"
    case.cerrado_at = _utcnow()
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CIERRE",
        user_id=user.id,
        detalle={"nota": sanitize_text(nota) if nota else None},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def add_comment(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    cuerpo: str,
    es_interno: bool = False,
    evidencia_ref: str | None = None,
    can_view_internal: bool = False,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    if es_interno and not can_view_internal:
        raise PermissionError("No puede crear comentarios internos.")
    comment = SupportCaseComment(
        organization_id=org_id,
        case_id=case_id,
        usuario_id=user.id,
        cuerpo=sanitize_text(cuerpo),
        es_interno=es_interno,
        evidencia_ref=evidencia_ref,
    )
    db.add(comment)
    if not case.primera_respuesta_at and user.id != case.solicitante_id:
        case.primera_respuesta_at = _utcnow()
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="COMENTARIO",
        user_id=user.id,
        detalle={"es_interno": es_interno},
        correlation_id=case.correlation_id,
    )
    recipient = case.responsable_id if user.id == case.solicitante_id else case.solicitante_id
    if recipient and not es_interno:
        _notify(
            db,
            event_type="SUPPORT_CASE_COMMENT",
            org_id=org_id,
            case=case,
            title=f"Nuevo comentario en caso {case.numero}",
            message=cuerpo[:200],
            recipient_user_id=recipient,
        )
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "usuario_id": comment.usuario_id,
        "cuerpo": comment.cuerpo,
        "es_interno": comment.es_interno,
        "evidencia_ref": comment.evidencia_ref,
        "created_at": comment.created_at,
    }


def get_case_detail(
    db: Session,
    org_id: str,
    case_id: str,
    *,
    can_view_internal: bool,
) -> dict[str, Any] | None:
    case = get_case(db, org_id, case_id)
    if not case:
        return None
    hist = (
        db.query(SupportCaseHistory)
        .filter(SupportCaseHistory.case_id == case_id)
        .order_by(SupportCaseHistory.created_at.asc())
        .all()
    )
    comments_q = db.query(SupportCaseComment).filter(SupportCaseComment.case_id == case_id)
    if not can_view_internal:
        comments_q = comments_q.filter(SupportCaseComment.es_interno.is_(False))
    comments = comments_q.order_by(SupportCaseComment.created_at.asc()).all()
    detail = case_to_dict(case)
    if case.responsable_id:
        resp = db.query(User).filter(User.id == case.responsable_id, User.organization_id == org_id).first()
        if resp:
            detail["responsable_nombre"] = resp.full_name or resp.username
            detail["responsable_email"] = resp.email
    detail["historial"] = [
        {
            "id": h.id,
            "accion": h.accion,
            "usuario_id": h.usuario_id,
            "detalle": json.loads(h.detalle_json) if h.detalle_json else None,
            "correlation_id": h.correlation_id,
            "created_at": h.created_at,
        }
        for h in hist
    ]
    detail["comentarios"] = [
        {
            "id": c.id,
            "usuario_id": c.usuario_id,
            "cuerpo": c.cuerpo,
            "es_interno": c.es_interno,
            "evidencia_ref": c.evidencia_ref,
            "created_at": c.created_at,
        }
        for c in comments
    ]
    evidences = (
        db.query(SupportCaseEvidence)
        .filter(SupportCaseEvidence.case_id == case_id)
        .order_by(SupportCaseEvidence.created_at.asc())
        .all()
    )
    detail["evidencias"] = [
        {
            "id": e.id,
            "tipo": e.tipo,
            "referencia": e.referencia,
            "descripcion": e.descripcion,
            "usuario_id": e.usuario_id,
            "created_at": e.created_at,
        }
        for e in evidences
    ]
    if case.problema_id:
        prob = db.query(SupportProblem).filter(
            SupportProblem.id == case.problema_id,
            SupportProblem.organization_id == org_id,
        ).first()
        if prob:
            detail["problema"] = problem_to_dict(prob)
    review = db.query(SupportPostReview).filter(SupportPostReview.case_id == case_id).first()
    if review:
        detail["revision_posterior"] = post_review_to_dict(review)
    return detail


def create_sla_policy(db: Session, org_id: str, data: dict[str, Any]) -> dict[str, Any]:
    row = SupportSlaPolicy(
        organization_id=org_id,
        nombre=data["nombre"],
        prioridad=(data.get("prioridad") or "MEDIA").upper(),
        tipo_caso=(data.get("tipo_caso") or "").upper() or None,
        servicio=data.get("servicio"),
        minutos_primera_respuesta=data.get("minutos_primera_respuesta"),
        minutos_resolucion=data.get("minutos_resolucion"),
        horario_servicio_json=json.dumps(data["horario_servicio_json"]) if data.get("horario_servicio_json") else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return sla_policy_to_dict(row)


def sla_policy_to_dict(row: SupportSlaPolicy) -> dict[str, Any]:
    return {
        "id": row.id,
        "nombre": row.nombre,
        "prioridad": row.prioridad,
        "tipo_caso": row.tipo_caso,
        "servicio": row.servicio,
        "minutos_primera_respuesta": row.minutos_primera_respuesta,
        "minutos_resolucion": row.minutos_resolucion,
        "is_active": row.is_active,
    }


def list_sla_policies(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(SupportSlaPolicy)
        .filter(SupportSlaPolicy.organization_id == org_id)
        .order_by(SupportSlaPolicy.prioridad.asc(), SupportSlaPolicy.nombre.asc())
        .all()
    )
    return [sla_policy_to_dict(r) for r in rows]


def suggest_priority_for_case(impacto: str, urgencia: str) -> dict[str, str]:
    sugerida = suggest_priority(impacto, urgencia)
    return {"prioridad_sugerida": sugerida, "impacto": impacto.upper(), "urgencia": urgencia.upper()}


def update_priority(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    prioridad: str,
    motivo: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    prev = case.prioridad
    case.prioridad = prioridad.upper()
    case.prioridad_ajuste_motivo = sanitize_text(motivo) if motivo else None
    case.prioridad_ajuste_por = user.id
    case.updated_at = _utcnow()
    policy = _find_sla_policy(
        db,
        org_id,
        case.prioridad,
        tipo_caso=case.tipo,
        servicio=case.servicio_componente,
    )
    _apply_sla_limits(case, policy, _utcnow())
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="PRIORIDAD",
        user_id=user.id,
        detalle={"de": prev, "a": case.prioridad, "motivo": case.prioridad_ajuste_motivo},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def classify_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    tipo: str | None = None,
    categoria: str | None = None,
    servicio_componente: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    if tipo:
        t = tipo.upper()
        if t not in TIPOS_CASO:
            raise ValueError(f"Tipo no válido: {tipo}")
        case.tipo = t
    if categoria is not None:
        case.categoria = categoria
    if servicio_componente is not None:
        case.servicio_componente = servicio_componente
    case.estado = "CLASIFICADO"
    case.clasificado_at = _utcnow()
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="CLASIFICACION",
        user_id=user.id,
        detalle={"tipo": case.tipo, "categoria": case.categoria, "servicio": case.servicio_componente},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def escalate_case(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    motivo: str,
    nota: str | None = None,
    coordinador_id: str | None = None,
) -> dict[str, Any]:
    motivo = motivo.upper()
    if motivo not in ESCALAMIENTO_MOTIVOS:
        raise ValueError(f"Motivo de escalamiento no válido: {motivo}")
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    case.escalamiento_nivel = (case.escalamiento_nivel or 0) + 1
    if coordinador_id:
        case.coordinador_id = coordinador_id
        case.es_incidente_mayor = case.es_incidente_mayor or case.escalamiento_nivel >= 2
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="ESCALAMIENTO",
        user_id=user.id,
        detalle={"motivo": motivo, "nota": sanitize_text(nota) if nota else None, "nivel": case.escalamiento_nivel},
        correlation_id=case.correlation_id,
    )
    recipient = case.coordinador_id or case.responsable_id
    _notify(
        db,
        event_type="SUPPORT_CASE_ESCALATED",
        org_id=org_id,
        case=case,
        title=f"Caso {case.numero} escalado ({motivo})",
        message=nota or f"Escalamiento nivel {case.escalamiento_nivel} por {motivo}.",
        recipient_user_id=recipient,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def update_diagnosis(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    sintoma: str | None = None,
    hipotesis: str | None = None,
    causa_probable: str | None = None,
    causa_validada: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    if sintoma is not None:
        case.sintoma = sanitize_text(sintoma)
    if hipotesis is not None:
        case.hipotesis = sanitize_text(hipotesis)
    if causa_probable is not None:
        case.causa_probable = sanitize_text(causa_probable)
    if causa_validada is not None:
        case.causa_validada = sanitize_text(causa_validada)
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="DIAGNOSTICO",
        user_id=user.id,
        detalle={
            "sintoma": bool(sintoma),
            "hipotesis": bool(hipotesis),
            "causa_probable": bool(causa_probable),
            "causa_validada": bool(causa_validada),
        },
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def add_evidence(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    tipo: str,
    referencia: str,
    descripcion: str | None = None,
) -> dict[str, Any]:
    tipo = tipo.upper()
    if tipo not in EVIDENCIA_TIPOS:
        raise ValueError(f"Tipo de evidencia no válido: {tipo}")
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    row = SupportCaseEvidence(
        organization_id=org_id,
        case_id=case_id,
        tipo=tipo,
        referencia=referencia[:500],
        descripcion=descripcion,
        usuario_id=user.id,
    )
    db.add(row)
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="EVIDENCIA",
        user_id=user.id,
        detalle={"tipo": tipo, "referencia": referencia[:120]},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "tipo": row.tipo,
        "referencia": row.referencia,
        "descripcion": row.descripcion,
        "created_at": row.created_at,
    }


def validate_resolution(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    *,
    aceptada: bool,
    comentario: str | None = None,
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    if case.estado != "RESUELTO":
        raise ValueError("Solo se puede validar un caso en estado RESUELTO.")
    case.validacion_at = _utcnow()
    if aceptada:
        case.validacion_solicitante = "ACEPTADA"
        case.estado = "CERRADO"
        case.cerrado_at = _utcnow()
    else:
        case.validacion_solicitante = "RECHAZADA"
        case.estado = "EN_PROCESO"
    case.updated_at = _utcnow()
    _record_history(
        db,
        org_id=org_id,
        case_id=case.id,
        accion="VALIDACION",
        user_id=user.id,
        detalle={"aceptada": aceptada, "comentario": sanitize_text(comentario) if comentario else None},
        correlation_id=case.correlation_id,
    )
    db.commit()
    db.refresh(case)
    return case_to_dict(case)


def _next_problem_number(db: Session, org_id: str) -> int:
    current = (
        db.query(func.max(SupportProblem.numero))
        .filter(SupportProblem.organization_id == org_id)
        .scalar()
    )
    return int(current or 0) + 1


def problem_to_dict(prob: SupportProblem) -> dict[str, Any]:
    return {
        "id": prob.id,
        "numero": prob.numero,
        "referencia": f"PRB-{prob.numero:05d}",
        "titulo": prob.titulo,
        "descripcion": sanitize_text(prob.descripcion),
        "estado": prob.estado,
        "causa_raiz": sanitize_text(prob.causa_raiz) if prob.causa_raiz else None,
        "solucion_temporal": sanitize_text(prob.solucion_temporal) if prob.solucion_temporal else None,
        "solucion_definitiva": sanitize_text(prob.solucion_definitiva) if prob.solucion_definitiva else None,
        "acciones_preventivas": sanitize_text(prob.acciones_preventivas) if prob.acciones_preventivas else None,
        "responsable_id": prob.responsable_id,
        "created_at": prob.created_at,
        "cerrado_at": prob.cerrado_at,
    }


def create_problem_from_cases(
    db: Session,
    org_id: str,
    user: User,
    *,
    titulo: str,
    descripcion: str,
    case_ids: list[str],
) -> dict[str, Any]:
    if not case_ids:
        raise ValueError("Se requiere al menos un incidente relacionado.")
    cases = (
        db.query(SupportCase)
        .filter(SupportCase.organization_id == org_id, SupportCase.id.in_(case_ids))
        .all()
    )
    if len(cases) != len(case_ids):
        raise LookupError("Uno o más casos no encontrados.")
    prob = SupportProblem(
        organization_id=org_id,
        numero=_next_problem_number(db, org_id),
        titulo=sanitize_text(titulo),
        descripcion=sanitize_text(descripcion),
        estado="ABIERTO",
        responsable_id=user.id,
    )
    db.add(prob)
    db.flush()
    for c in cases:
        c.problema_id = prob.id
        if c.tipo == "INCIDENTE":
            c.tipo = "INCIDENTE"
    db.commit()
    db.refresh(prob)
    return {
        **problem_to_dict(prob),
        "casos_vinculados": [c.id for c in cases],
    }


def list_problems(db: Session, org_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        db.query(SupportProblem)
        .filter(SupportProblem.organization_id == org_id)
        .order_by(SupportProblem.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    result = []
    for p in rows:
        d = problem_to_dict(p)
        d["incidentes"] = (
            db.query(SupportCase)
            .filter(SupportCase.problema_id == p.id)
            .count()
        )
        result.append(d)
    return result


def update_problem(
    db: Session,
    org_id: str,
    problem_id: str,
    user: User,
    data: dict[str, Any],
) -> dict[str, Any]:
    prob = (
        db.query(SupportProblem)
        .filter(SupportProblem.id == problem_id, SupportProblem.organization_id == org_id)
        .first()
    )
    if not prob:
        raise LookupError("Problema no encontrado.")
    for field in ("causa_raiz", "solucion_temporal", "solucion_definitiva", "acciones_preventivas", "estado"):
        if field in data and data[field] is not None:
            val = data[field]
            if field != "estado":
                val = sanitize_text(str(val))
            setattr(prob, field, val)
    prob.updated_at = _utcnow()
    if data.get("estado") == "CERRADO":
        prob.cerrado_at = _utcnow()
    db.commit()
    db.refresh(prob)
    return problem_to_dict(prob)


def propose_knowledge_article(
    db: Session,
    org_id: str,
    user: User,
    *,
    titulo: str,
    contenido: str,
    tipo_articulo: str = "PROCEDIMIENTO",
    case_id: str | None = None,
    problem_id: str | None = None,
) -> dict[str, Any]:
    row = SupportKnowledgeProposal(
        organization_id=org_id,
        case_id=case_id,
        problem_id=problem_id,
        titulo=sanitize_text(titulo),
        contenido=sanitize_text(contenido),
        tipo_articulo=tipo_articulo.upper(),
        estado="PENDIENTE",
        propuesto_por=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "titulo": row.titulo,
        "tipo_articulo": row.tipo_articulo,
        "estado": row.estado,
        "case_id": row.case_id,
        "problem_id": row.problem_id,
        "created_at": row.created_at,
    }


def post_review_to_dict(review: SupportPostReview) -> dict[str, Any]:
    return {
        "id": review.id,
        "que_ocurrio": sanitize_text(review.que_ocurrio) if review.que_ocurrio else None,
        "impacto": sanitize_text(review.impacto) if review.impacto else None,
        "causa": sanitize_text(review.causa) if review.causa else None,
        "que_se_hizo": sanitize_text(review.que_se_hizo) if review.que_se_hizo else None,
        "tiempos": review.tiempos,
        "que_funciono": sanitize_text(review.que_funciono) if review.que_funciono else None,
        "que_fallo": sanitize_text(review.que_fallo) if review.que_fallo else None,
        "accion_preventiva": sanitize_text(review.accion_preventiva) if review.accion_preventiva else None,
        "responsable_id": review.responsable_id,
        "fecha_objetivo": review.fecha_objetivo,
        "created_at": review.created_at,
    }


def upsert_post_review(
    db: Session,
    org_id: str,
    case_id: str,
    user: User,
    data: dict[str, Any],
) -> dict[str, Any]:
    case = get_case(db, org_id, case_id)
    if not case:
        raise LookupError("Caso no encontrado.")
    review = db.query(SupportPostReview).filter(SupportPostReview.case_id == case_id).first()
    if not review:
        review = SupportPostReview(
            organization_id=org_id,
            case_id=case_id,
            autor_id=user.id,
        )
        db.add(review)
    for field in (
        "que_ocurrio",
        "impacto",
        "causa",
        "que_se_hizo",
        "tiempos",
        "que_funciono",
        "que_fallo",
        "accion_preventiva",
        "responsable_id",
        "fecha_objetivo",
    ):
        if field in data:
            val = data[field]
            if val is not None and field != "fecha_objetivo" and field != "responsable_id":
                val = sanitize_text(str(val))
            setattr(review, field, val)
    review.updated_at = _utcnow()
    db.commit()
    db.refresh(review)
    return post_review_to_dict(review)


def autoservicio_buscar(
    db: Session,
    org_id: str,
    user: User,
    *,
    consulta: str,
    can_view_all: bool,
) -> dict[str, Any]:
    """Sugerencias antes de abrir un caso: conocimiento, casos existentes, prioridad."""
    consulta = (consulta or "").strip()
    sugerencias: list[dict[str, Any]] = []
    articulos: list[dict[str, Any]] = []
    if consulta:
        try:
            from app.services import knowledge_service as kb

            docs = kb.search_documents(db, org_id, consulta, limit=5)
            for d in docs:
                articulos.append({
                    "tipo": "KNOWLEDGE",
                    "titulo": d.get("original_filename") or d.get("title", "Documento"),
                    "referencia": d.get("id"),
                    "extracto": (d.get("snippet") or "")[:200],
                })
        except Exception:
            pass
        like = f"%{consulta}%"
        casos_q = db.query(SupportCase).filter(
            SupportCase.organization_id == org_id,
            (SupportCase.asunto.ilike(like)) | (SupportCase.descripcion.ilike(like)),
            SupportCase.estado.in_(list(ESTADOS_ABIERTOS)),
        )
        if not can_view_all:
            casos_q = casos_q.filter(
                (SupportCase.solicitante_id == user.id) | (SupportCase.responsable_id == user.id)
            )
        for c in casos_q.limit(5).all():
            sugerencias.append({
                "tipo": "CASO_EXISTENTE",
                "id": c.id,
                "referencia": f"SUP-{c.numero:05d}",
                "asunto": c.asunto,
                "estado": c.estado,
            })
    impacto = "MEDIO"
    urgencia = "MEDIA"
    if "critico" in consulta.lower() or "caído" in consulta.lower() or "caido" in consulta.lower():
        impacto, urgencia = "ALTO", "ALTA"
    prio = suggest_priority(impacto, urgencia)
    return {
        "consulta": consulta,
        "articulos": articulos,
        "casos_similares": sugerencias,
        "prioridad_sugerida": prio,
        "impacto_sugerido": impacto,
        "urgencia_sugerida": urgencia,
    }


def check_sla_warnings(db: Session, org_id: str) -> list[dict[str, Any]]:
    """Emite alertas SLA para casos próximos a vencer o vencidos."""
    now = _utcnow()
    abiertos = (
        db.query(SupportCase)
        .filter(
            SupportCase.organization_id == org_id,
            SupportCase.estado.in_(list(ESTADOS_ABIERTOS)),
            SupportCase.sla_warning_emitido.is_(False),
        )
        .all()
    )
    alertas: list[dict[str, Any]] = []
    for case in abiertos:
        estado = compute_sla_estado(case, now)
        if estado not in ("PROXIMO", "VENCIDO"):
            continue
        recipient = case.responsable_id or case.solicitante_id
        _notify(
            db,
            event_type="SUPPORT_SLA_WARNING",
            org_id=org_id,
            case=case,
            title=f"SLA {estado.lower()} — caso {case.numero}",
            message=f"El caso «{case.asunto}» está {estado.lower().replace('_', ' ')}.",
            recipient_user_id=recipient,
        )
        case.sla_warning_emitido = True
        alertas.append({"case_id": case.id, "sla_estado": estado})
    if alertas:
        db.commit()
    return alertas


def indicadores_soporte(db: Session, org_id: str) -> dict[str, Any]:
    """Indicadores reutilizables por Centro de Control e Inteligencia de Resultados."""
    cc = contrato_centro_control(db, org_id)
    total = db.query(SupportCase).filter(SupportCase.organization_id == org_id).count()
    cerrados = (
        db.query(SupportCase)
        .filter(SupportCase.organization_id == org_id, SupportCase.estado == "CERRADO")
        .count()
    )
    reaperturas = (
        db.query(SupportCaseHistory)
        .filter(
            SupportCaseHistory.organization_id == org_id,
            SupportCaseHistory.accion == "CAMBIO_ESTADO",
            SupportCaseHistory.detalle_json.ilike('%"a": "EN_PROCESO"%'),
        )
        .count()
    )
    problemas_abiertos = (
        db.query(SupportProblem)
        .filter(SupportProblem.organization_id == org_id, SupportProblem.estado != "CERRADO")
        .count()
    )
    return {
        **cc,
        "casos_totales": total,
        "casos_cerrados": cerrados,
        "reaperturas": reaperturas,
        "problemas_abiertos": problemas_abiertos,
        "endpoint": "/api/soporte/indicadores",
    }


def contrato_mi_trabajo(db: Session, org_id: str, user_id: str) -> dict[str, Any]:
    base = db.query(SupportCase).filter(
        SupportCase.organization_id == org_id,
        SupportCase.responsable_id == user_id,
        SupportCase.estado.in_(list(ESTADOS_ABIERTOS)),
    )
    asignados = base.count()
    vencidos = sum(1 for c in base.all() if compute_sla_estado(c) == "VENCIDO")
    accion = base.filter(SupportCase.estado.in_(["NUEVO", "ASIGNADO", "PENDIENTE_USUARIO"])).count()
    return {
        "casos_asignados": asignados,
        "casos_vencidos": vencidos,
        "casos_accion_requerida": accion,
        "endpoint": "/api/soporte/contrato/mi-trabajo",
    }


def contrato_centro_control(db: Session, org_id: str) -> dict[str, Any]:
    abiertos_q = db.query(SupportCase).filter(
        SupportCase.organization_id == org_id,
        SupportCase.estado.in_(list(ESTADOS_ABIERTOS)),
    )
    abiertos = abiertos_q.all()
    criticos = sum(1 for c in abiertos if c.prioridad in ("CRITICA", "ALTA"))
    vencidos = sum(1 for c in abiertos if compute_sla_estado(c) == "VENCIDO")
    categorias: dict[str, int] = {}
    for c in abiertos:
        cat = c.categoria or c.tipo
        categorias[cat] = categorias.get(cat, 0) + 1
    top_cats = sorted(categorias.items(), key=lambda x: -x[1])[:5]
    resueltos = (
        db.query(SupportCase)
        .filter(SupportCase.organization_id == org_id, SupportCase.resuelto_at.isnot(None))
        .order_by(SupportCase.resuelto_at.desc())
        .limit(50)
        .all()
    )
    tmr: list[float] = []
    tmo: list[float] = []
    for c in resueltos:
        if c.primera_respuesta_at and c.created_at:
            tmr.append((c.primera_respuesta_at - c.created_at).total_seconds() / 60)
        if c.resuelto_at and c.created_at:
            tmo.append((c.resuelto_at - c.created_at).total_seconds() / 60)
    return {
        "casos_abiertos": len(abiertos),
        "casos_criticos": criticos,
        "casos_vencidos": vencidos,
        "tiempo_medio_respuesta_min": round(sum(tmr) / len(tmr), 1) if tmr else None,
        "tiempo_medio_resolucion_min": round(sum(tmo) / len(tmo), 1) if tmo else None,
        "principales_categorias": [{"categoria": k, "cantidad": v} for k, v in top_cats],
        "endpoint": "/api/soporte/contrato/centro-control",
    }
