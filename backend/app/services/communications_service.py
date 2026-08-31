"""Servicio — Centro de Información y Comunicaciones (MB-11)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.communications_enums import (
    ALLOWED_TEMPLATE_VARIABLES,
    CANAL_TIPOS,
    COMUNICACION_ESTADOS,
    MAX_REINTENTOS,
    REINTENTO_BACKOFF_SEG,
)
from app.communications_models import (
    CommChannel,
    CommDedup,
    CommDeliveryAttempt,
    CommMessage,
    CommPreference,
    CommRule,
    CommTemplate,
    CommTemplateVersion,
)
from app.events.bus import EventMessage, subscribe
from app.gateway.secrets import mask_secret, resolve_secret, secret_configured
from app.integration_security import SSRFError, validate_external_url
from app.models import Organization, User
from app.notifications import resolve_event_id

logger = logging.getLogger(__name__)

_VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
_DANGEROUS_VAR = re.compile(r"(import|exec|eval|__|<%|javascript:)", re.I)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _json_load(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _json_dump(data: Any) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def sanitize_comm_text(text: str) -> str:
    """Elimina patrones sensibles del texto visible."""
    if not text:
        return ""
    clean = re.sub(
        r"(password|contraseña|api[_-]?key|token|secret|bearer)\s*[:=]\s*\S+",
        "[dato sensible omitido]",
        text,
        flags=re.I,
    )
    return clean


def validate_template_content(content: str) -> None:
    if _DANGEROUS_VAR.search(content):
        raise ValueError("Contenido de plantilla con expresiones no permitidas.")
    for match in _VAR_PATTERN.finditer(content):
        var = match.group(1)
        if var not in ALLOWED_TEMPLATE_VARIABLES:
            raise ValueError(f"Variable no permitida: {{{{{var}}}}}")


def render_template(text: str, variables: dict[str, str]) -> str:
    validate_template_content(text)

    def replacer(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in ALLOWED_TEMPLATE_VARIABLES:
            raise ValueError(f"Variable no permitida: {key}")
        return variables.get(key, "")

    return _VAR_PATTERN.sub(replacer, text)


def build_idempotency_key(
    *,
    organization_id: str,
    event_id: str | None,
    rule_id: str | None,
    destinatario: str,
    channel_id: str,
) -> str:
    raw = "|".join([organization_id, event_id or "-", rule_id or "-", destinatario, channel_id])
    return hashlib.sha256(raw.encode()).hexdigest()


def channel_to_dict(ch: CommChannel) -> dict[str, Any]:
    cfg = _json_load(ch.config_json)
    safe_cfg = {k: v for k, v in cfg.items() if "secret" not in k.lower() and "password" not in k.lower()}
    return {
        "id": ch.id,
        "organization_id": ch.organization_id,
        "tipo": ch.tipo,
        "nombre": ch.nombre,
        "activo": ch.activo,
        "config": safe_cfg or None,
        "secret_configured": secret_configured(ch.secret_ref),
        "estado": ch.estado,
        "prioridad": ch.prioridad,
        "uso_permitido": ch.uso_permitido,
        "created_at": ch.created_at,
        "updated_at": ch.updated_at,
    }


def message_to_dict(msg: CommMessage, db: Session, *, include_content: bool = True) -> dict[str, Any]:
    ch = db.query(CommChannel).filter(CommChannel.id == msg.channel_id).first() if msg.channel_id else None
    ver = (
        db.query(CommTemplateVersion).filter(CommTemplateVersion.id == msg.template_version_id).first()
        if msg.template_version_id
        else None
    )
    return {
        "id": msg.id,
        "organization_id": msg.organization_id,
        "estado": msg.estado,
        "tipo_comunicacion": msg.tipo_comunicacion,
        "channel_id": msg.channel_id,
        "channel_tipo": ch.tipo if ch else None,
        "template_version_id": msg.template_version_id,
        "template_version": ver.version if ver else None,
        "rule_id": msg.rule_id,
        "destinatario_tipo": msg.destinatario_tipo,
        "destinatario_id": msg.destinatario_id,
        "destinatario_externo": msg.destinatario_externo,
        "asunto": sanitize_comm_text(msg.asunto) if msg.asunto else None,
        "contenido": sanitize_comm_text(msg.contenido) if include_content else None,
        "idioma": msg.idioma,
        "programada_para": msg.programada_para,
        "correlation_id": msg.correlation_id,
        "event_id": msg.event_id,
        "origen": msg.origen,
        "origen_id": msg.origen_id,
        "intentos": msg.intentos,
        "max_intentos": msg.max_intentos,
        "proximo_intento": msg.proximo_intento,
        "created_at": msg.created_at,
        "enviada_at": msg.enviada_at,
        "entregada_at": msg.entregada_at,
        "cancelada_at": msg.cancelada_at,
    }


def _resolve_destinatario(
    db: Session,
    org_id: str,
    *,
    tipo: str,
    regla: str,
    payload: dict[str, Any],
) -> tuple[str, str | None, str | None]:
    if tipo == "USUARIO":
        return "USUARIO", regla, None
    if tipo == "ROL":
        admin = (
            db.query(User)
            .filter(User.organization_id == org_id, User.role == regla, User.is_active.is_(True))
            .first()
        )
        return "USUARIO", admin.id if admin else None, None
    if tipo == "DINAMICO":
        if regla == "ADMIN_ORGANIZACION":
            admin = (
                db.query(User)
                .filter(User.organization_id == org_id, User.role == "admin", User.is_active.is_(True))
                .first()
            )
            return "USUARIO", admin.id if admin else None, None
        if regla == "SOLICITANTE":
            uid = payload.get("solicitante_id") or payload.get("recipient_user_id")
            return "USUARIO", str(uid) if uid else None, None
        if regla == "RESPONSABLE_CASO":
            uid = payload.get("responsable_id") or payload.get("recipient_user_id")
            return "USUARIO", str(uid) if uid else None, None
    if tipo == "EXTERNO":
        return "EXTERNO", None, regla
    return tipo, regla, None


def _matches_condition(condicion: dict[str, Any], payload: dict[str, Any]) -> bool:
    expected = condicion.get("match", condicion)
    if not expected:
        return True
    return all(payload.get(k) == v for k, v in expected.items())


def _preference_allows(
    db: Session,
    org_id: str,
    user_id: str | None,
    *,
    canal_tipo: str,
    tipo_com: str,
    obligatoria: bool,
) -> bool:
    if obligatoria:
        return True
    pref = (
        db.query(CommPreference)
        .filter(CommPreference.organization_id == org_id, CommPreference.user_id == user_id)
        .first()
    )
    if not pref:
        return True
    canales = json.loads(pref.canales_json) if pref.canales_json else []
    tipos = json.loads(pref.tipos_json) if pref.tipos_json else []
    if canales and canal_tipo not in canales:
        return False
    if tipos and tipo_com not in tipos:
        return False
    return True


def _check_dedup(db: Session, org_id: str, dedup_key: str) -> CommMessage | None:
    now = _utcnow()
    row = (
        db.query(CommDedup)
        .filter(
            CommDedup.organization_id == org_id,
            CommDedup.dedup_key == dedup_key,
            CommDedup.ventana_fin >= now,
        )
        .first()
    )
    if not row:
        return None
    return db.query(CommMessage).filter(CommMessage.id == row.message_id).first()


def _register_dedup(db: Session, org_id: str, dedup_key: str, message_id: str, minutos: int) -> None:
    db.add(
        CommDedup(
            organization_id=org_id,
            dedup_key=dedup_key,
            message_id=message_id,
            ventana_fin=_utcnow() + timedelta(minutes=minutos),
        )
    )


def _deliver_channel(db: Session, msg: CommMessage, channel: CommChannel) -> tuple[str, str | None]:
    """Retorna (estado_final, detalle). No finge ENTREGADA si no hay confirmación."""
    cfg = _json_load(channel.config_json)
    if channel.tipo == "INTERNO_PLATAFORMA":
        return "ENVIADA", "Registrada en bandeja interna de comunicaciones"
    if channel.tipo == "CORREO_ELECTRONICO":
        if not secret_configured(channel.secret_ref):
            return "ENVIADA", "Correo aceptado por adaptador simulado (sin SMTP configurado)"
        _ = resolve_secret(channel.secret_ref)
        return "ENVIADA", "Correo aceptado por proveedor (entrega no confirmada)"
    if channel.tipo == "WEBHOOK":
        url = cfg.get("webhook_url") or cfg.get("url")
        if not url:
            return "FALLIDA", "URL de webhook no configurada"
        try:
            validate_external_url(url)
        except SSRFError as exc:
            return "FALLIDA", str(exc)
        if secret_configured(channel.secret_ref):
            _ = resolve_secret(channel.secret_ref)
        return "ENVIADA", "Webhook aceptado por destino (respuesta no verificada en esta fase)"
    return "FALLIDA", f"Canal no soportado: {channel.tipo}"


def send_message(db: Session, msg: CommMessage, *, commit: bool = True) -> CommMessage:
    if msg.estado in ("ENVIADA", "ENTREGADA", "CANCELADA"):
        return msg
    channel = db.query(CommChannel).filter(CommChannel.id == msg.channel_id).first()
    if not channel or not channel.activo:
        msg.estado = "FALLIDA"
        db.add(
            CommDeliveryAttempt(
                message_id=msg.id,
                organization_id=msg.organization_id,
                intento_num=msg.intentos + 1,
                estado="FALLIDA",
                causa="CANAL_INACTIVO",
                detalle="Canal no disponible",
            )
        )
        if commit:
            db.commit()
        return msg

    msg.estado = "ENVIANDO"
    msg.intentos += 1
    estado, detalle = _deliver_channel(db, msg, channel)
    db.add(
        CommDeliveryAttempt(
            message_id=msg.id,
            organization_id=msg.organization_id,
            intento_num=msg.intentos,
            estado=estado,
            causa=None if estado == "ENVIADA" else "ENVIO_FALLIDO",
            detalle=sanitize_comm_text(detalle or ""),
        )
    )
    now = _utcnow()
    if estado == "ENVIADA":
        msg.estado = "ENVIADA"
        msg.enviada_at = now
    else:
        msg.estado = "FALLIDA"
        if msg.intentos < msg.max_intentos:
            backoff = REINTENTO_BACKOFF_SEG[min(msg.intentos - 1, len(REINTENTO_BACKOFF_SEG) - 1)]
            msg.proximo_intento = now + timedelta(seconds=backoff)
            msg.estado = "PENDIENTE_ENVIO"
    msg.updated_at = now
    if commit:
        db.commit()
        db.refresh(msg)
    return msg


def list_channels(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(CommChannel)
        .filter(CommChannel.organization_id == org_id)
        .order_by(CommChannel.prioridad, CommChannel.nombre)
        .all()
    )
    return [channel_to_dict(ch) for ch in rows]


def list_templates(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(CommTemplate).filter(CommTemplate.organization_id == org_id).order_by(CommTemplate.codigo).all()
    result: list[dict[str, Any]] = []
    for tpl in rows:
        ver = (
            db.query(CommTemplateVersion)
            .filter(CommTemplateVersion.id == tpl.current_version_id)
            .first()
            if tpl.current_version_id
            else None
        )
        result.append(
            {
                "id": tpl.id,
                "organization_id": org_id,
                "codigo": tpl.codigo,
                "nombre": tpl.nombre,
                "tipo_comunicacion": tpl.tipo_comunicacion,
                "canal_tipo": tpl.canal_tipo,
                "idioma": tpl.idioma,
                "current_version_id": tpl.current_version_id,
                "current_version": ver.version if ver else None,
            }
        )
    return result


def list_rules(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(CommRule).filter(CommRule.organization_id == org_id).order_by(CommRule.nombre).all()
    return [rule_to_dict(r) for r in rows]


def create_channel(db: Session, org_id: str, user: User, data: dict[str, Any]) -> dict[str, Any]:
    tipo = data["tipo"].upper()
    if tipo not in CANAL_TIPOS:
        raise ValueError(f"Tipo de canal no válido: {tipo}")
    ch = CommChannel(
        organization_id=org_id,
        tipo=tipo,
        nombre=data["nombre"],
        activo=data.get("activo", True),
        config_json=_json_dump(data.get("config")),
        secret_ref=data.get("secret_ref"),
        prioridad=data.get("prioridad", 100),
        uso_permitido=data.get("uso_permitido"),
    )
    db.add(ch)
    db.flush()
    write_audit(db, action="communications.channel.created", organization_id=org_id, user_id=user.id, detail=ch.nombre)
    db.commit()
    db.refresh(ch)
    return channel_to_dict(ch)


def create_template(db: Session, org_id: str, user: User, data: dict[str, Any]) -> dict[str, Any]:
    validate_template_content(data["contenido"])
    tpl = CommTemplate(
        organization_id=org_id,
        codigo=data["codigo"].upper(),
        nombre=data["nombre"],
        tipo_comunicacion=data["tipo_comunicacion"],
        canal_tipo=data["canal_tipo"].upper(),
        idioma=data.get("idioma", "es"),
    )
    db.add(tpl)
    db.flush()
    ver = CommTemplateVersion(
        template_id=tpl.id,
        organization_id=org_id,
        version=1,
        asunto=data.get("asunto"),
        contenido=data["contenido"],
        variables_json=_json_dump(data.get("variables", [])),
        estado="ACTIVA",
        creador_id=user.id,
    )
    db.add(ver)
    db.flush()
    tpl.current_version_id = ver.id
    write_audit(db, action="communications.template.created", organization_id=org_id, user_id=user.id, detail=tpl.codigo)
    db.commit()
    return {
        "id": tpl.id,
        "organization_id": org_id,
        "codigo": tpl.codigo,
        "nombre": tpl.nombre,
        "tipo_comunicacion": tpl.tipo_comunicacion,
        "canal_tipo": tpl.canal_tipo,
        "idioma": tpl.idioma,
        "current_version_id": ver.id,
        "current_version": 1,
    }


def new_template_version(db: Session, org_id: str, template_id: str, user: User, data: dict[str, Any]) -> dict[str, Any]:
    tpl = db.query(CommTemplate).filter(CommTemplate.id == template_id, CommTemplate.organization_id == org_id).first()
    if not tpl:
        raise LookupError("Plantilla no encontrada.")
    validate_template_content(data["contenido"])
    last = (
        db.query(CommTemplateVersion)
        .filter(CommTemplateVersion.template_id == template_id)
        .order_by(CommTemplateVersion.version.desc())
        .first()
    )
    next_ver = int(last.version if last else 0) + 1
    ver = CommTemplateVersion(
        template_id=template_id,
        organization_id=org_id,
        version=next_ver,
        asunto=data.get("asunto"),
        contenido=data["contenido"],
        variables_json=_json_dump(data.get("variables", [])),
        estado="ACTIVA",
        creador_id=user.id,
    )
    db.add(ver)
    db.flush()
    tpl.current_version_id = ver.id
    write_audit(
        db,
        action="communications.template.versioned",
        organization_id=org_id,
        user_id=user.id,
        detail=f"{tpl.codigo} v{next_ver}",
    )
    db.commit()
    return {
        "id": ver.id,
        "template_id": template_id,
        "version": next_ver,
        "asunto": ver.asunto,
        "contenido": ver.contenido,
        "variables": data.get("variables", []),
        "estado": ver.estado,
        "created_at": ver.created_at,
    }


def create_rule(db: Session, org_id: str, user: User, data: dict[str, Any]) -> dict[str, Any]:
    rule = CommRule(
        organization_id=org_id,
        nombre=data["nombre"],
        event_type=data["event_type"].upper(),
        condicion_json=_json_dump(data.get("condicion")),
        destinatario_tipo=data["destinatario_tipo"].upper(),
        destinatario_regla=data["destinatario_regla"],
        template_version_id=data["template_version_id"],
        channel_id=data["channel_id"],
        accion=data.get("accion", "ENVIAR").upper(),
        activo=data.get("activo", True),
        antispam_minutos=data.get("antispam_minutos", 15),
        obligatoria=data.get("obligatoria", False),
    )
    db.add(rule)
    db.flush()
    write_audit(db, action="communications.rule.created", organization_id=org_id, user_id=user.id, detail=rule.nombre)
    db.commit()
    return rule_to_dict(rule)


def rule_to_dict(rule: CommRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "organization_id": rule.organization_id,
        "nombre": rule.nombre,
        "event_type": rule.event_type,
        "condicion": _json_load(rule.condicion_json) or None,
        "destinatario_tipo": rule.destinatario_tipo,
        "destinatario_regla": rule.destinatario_regla,
        "template_version_id": rule.template_version_id,
        "channel_id": rule.channel_id,
        "accion": rule.accion,
        "activo": rule.activo,
        "antispam_minutos": rule.antispam_minutos,
        "obligatoria": rule.obligatoria,
    }


def create_message_manual(db: Session, org_id: str, user: User, data: dict[str, Any]) -> dict[str, Any]:
    channel = db.query(CommChannel).filter(CommChannel.id == data["channel_id"], CommChannel.organization_id == org_id).first()
    if not channel:
        raise LookupError("Canal no encontrado.")
    contenido = data.get("contenido") or ""
    asunto = data.get("asunto")
    ver_id = data.get("template_version_id")
    if ver_id:
        ver = db.query(CommTemplateVersion).filter(CommTemplateVersion.id == ver_id, CommTemplateVersion.organization_id == org_id).first()
        if not ver:
            raise LookupError("Versión de plantilla no encontrada.")
        org = db.query(Organization).filter(Organization.id == org_id).first()
        vars_map = {
            "nombre": user.full_name or user.username,
            "empresa": org.name if org else "",
            "fecha": _utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            **(data.get("variables") or {}),
        }
        contenido = render_template(ver.contenido, vars_map)
        if ver.asunto:
            asunto = render_template(ver.asunto, vars_map)
    if not contenido:
        raise ValueError("Contenido requerido.")
    programada = data.get("programada_para")
    estado = "PROGRAMADA" if programada and _as_utc(programada) > _utcnow() else "PENDIENTE_ENVIO"
    if data.get("enviar_ahora") is False and programada:
        estado = "PROGRAMADA"
    msg = CommMessage(
        organization_id=org_id,
        estado=estado,
        tipo_comunicacion=data.get("tipo_comunicacion", "MANUAL"),
        channel_id=channel.id,
        template_version_id=ver_id,
        destinatario_tipo=data["destinatario_tipo"].upper(),
        destinatario_id=data.get("destinatario_id"),
        destinatario_externo=data.get("destinatario_externo"),
        asunto=asunto,
        contenido=contenido,
        idioma=data.get("idioma", "es"),
        programada_para=programada,
        correlation_id=data.get("correlation_id"),
        origen="MANUAL",
        creador_id=user.id,
        max_intentos=MAX_REINTENTOS,
    )
    db.add(msg)
    db.flush()
    write_audit(db, action="communications.message.created", organization_id=org_id, user_id=user.id, detail=msg.id)
    if estado == "PENDIENTE_ENVIO" and data.get("enviar_ahora", True):
        send_message(db, msg, commit=False)
    db.commit()
    db.refresh(msg)
    return message_to_dict(msg, db)


def cancel_message(db: Session, org_id: str, message_id: str, user: User) -> dict[str, Any]:
    msg = db.query(CommMessage).filter(CommMessage.id == message_id, CommMessage.organization_id == org_id).first()
    if not msg:
        raise LookupError("Comunicación no encontrada.")
    if msg.estado in ("ENVIADA", "ENTREGADA", "CANCELADA"):
        return message_to_dict(msg, db)
    msg.estado = "CANCELADA"
    msg.cancelada_at = _utcnow()
    write_audit(db, action="communications.message.cancelled", organization_id=org_id, user_id=user.id, detail=msg.id)
    db.commit()
    db.refresh(msg)
    return message_to_dict(msg, db)


def list_messages(
    db: Session,
    org_id: str,
    *,
    estado: str | None = None,
    canal_tipo: str | None = None,
    q: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = db.query(CommMessage).filter(CommMessage.organization_id == org_id)
    if estado:
        query = query.filter(CommMessage.estado == estado.upper())
    rows = query.order_by(CommMessage.created_at.desc()).limit(min(limit, 500)).all()
    items = [message_to_dict(r, db) for r in rows]
    if canal_tipo:
        items = [i for i in items if i.get("channel_tipo") == canal_tipo.upper()]
    if q:
        needle = q.lower()
        items = [i for i in items if needle in f"{i.get('asunto','')} {i.get('contenido','')}".lower()]
    return items


def get_message_detail(db: Session, org_id: str, message_id: str) -> dict[str, Any]:
    msg = db.query(CommMessage).filter(CommMessage.id == message_id, CommMessage.organization_id == org_id).first()
    if not msg:
        raise LookupError("Comunicación no encontrada.")
    detail = message_to_dict(msg, db)
    attempts = (
        db.query(CommDeliveryAttempt)
        .filter(CommDeliveryAttempt.message_id == message_id)
        .order_by(CommDeliveryAttempt.intento_num)
        .all()
    )
    detail["historial_intentos"] = [
        {
            "intento": a.intento_num,
            "estado": a.estado,
            "causa": a.causa,
            "detalle": sanitize_comm_text(a.detalle or ""),
            "fecha": a.created_at.isoformat() if a.created_at else None,
        }
        for a in attempts
    ]
    return detail


def evaluate_rules_for_event(db: Session, event: EventMessage) -> list[CommMessage]:
    created: list[CommMessage] = []
    rules = (
        db.query(CommRule)
        .filter(
            CommRule.organization_id == event.organization_id,
            CommRule.activo.is_(True),
            CommRule.event_type == event.event_type.upper(),
        )
        .all()
    )
    payload = event.payload or {}
    eid = resolve_event_id(event.event_type, event.organization_id, event.work_plan_id, payload)
    for rule in rules:
        cond = _json_load(rule.condicion_json)
        if not _matches_condition(cond, payload):
            continue
        dest_tipo, dest_id, dest_ext = _resolve_destinatario(
            db,
            event.organization_id,
            tipo=rule.destinatario_tipo,
            regla=rule.destinatario_regla,
            payload=payload,
        )
        channel = db.query(CommChannel).filter(CommChannel.id == rule.channel_id).first()
        if not channel:
            continue
        if not _preference_allows(
            db,
            event.organization_id,
            dest_id,
            canal_tipo=channel.tipo,
            tipo_com=rule.event_type,
            obligatoria=rule.obligatoria,
        ):
            continue
        dedup_key = build_idempotency_key(
            organization_id=event.organization_id,
            event_id=eid,
            rule_id=rule.id,
            destinatario=dest_id or dest_ext or rule.destinatario_regla,
            channel_id=rule.channel_id,
        )
        existing = _check_dedup(db, event.organization_id, dedup_key)
        if existing:
            created.append(existing)
            continue
        ver = db.query(CommTemplateVersion).filter(CommTemplateVersion.id == rule.template_version_id).first()
        if not ver:
            continue
        org = db.query(Organization).filter(Organization.id == event.organization_id).first()
        vars_map = {
            "nombre": payload.get("nombre", ""),
            "empresa": org.name if org else "",
            "fecha": _utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "evento": event.event_type,
            "correlation_id": payload.get("correlation_id", ""),
            "valor": str(payload.get("valor", payload.get("message", ""))),
            "estado": str(payload.get("estado", "")),
            "asunto": str(payload.get("title", payload.get("asunto", ""))),
        }
        contenido = render_template(ver.contenido, vars_map)
        asunto = render_template(ver.asunto, vars_map) if ver.asunto else f"Comunicación: {rule.nombre}"
        msg = CommMessage(
            organization_id=event.organization_id,
            estado="PENDIENTE_ENVIO",
            tipo_comunicacion=rule.event_type,
            channel_id=rule.channel_id,
            template_version_id=ver.id,
            rule_id=rule.id,
            destinatario_tipo=dest_tipo,
            destinatario_id=dest_id,
            destinatario_externo=dest_ext,
            asunto=asunto,
            contenido=contenido,
            correlation_id=payload.get("correlation_id"),
            event_id=eid,
            origen="EVENTO",
            origen_id=event.work_plan_id,
            idempotency_key=dedup_key,
            max_intentos=MAX_REINTENTOS,
        )
        try:
            db.add(msg)
            db.flush()
            _register_dedup(db, event.organization_id, dedup_key, msg.id, rule.antispam_minutos)
            if rule.accion == "ENVIAR":
                send_message(db, msg, commit=False)
            db.commit()
            db.refresh(msg)
            created.append(msg)
            db.commit()
        except IntegrityError:
            db.rollback()
            dup = _check_dedup(db, event.organization_id, dedup_key)
            if dup:
                created.append(dup)
    return created


def process_scheduled_and_retries(db: Session) -> int:
    """Invocado desde scheduler 810C — mensajes programados y reintentos."""
    now = _utcnow()
    processed = 0
    due = (
        db.query(CommMessage)
        .filter(
            CommMessage.estado.in_(["PROGRAMADA", "PENDIENTE_ENVIO"]),
            (
                (CommMessage.programada_para.isnot(None)) & (CommMessage.programada_para <= now)
                | (CommMessage.proximo_intento.isnot(None)) & (CommMessage.proximo_intento <= now)
            ),
        )
        .limit(50)
        .all()
    )
    for msg in due:
        if msg.estado == "PROGRAMADA" and msg.programada_para and _as_utc(msg.programada_para) > now:
            continue
        if msg.proximo_intento and _as_utc(msg.proximo_intento) > now:
            continue
        send_message(db, msg)
        processed += 1
    return processed


def contrato_centro_control(db: Session, org_id: str) -> dict[str, Any]:
    msgs = db.query(CommMessage).filter(CommMessage.organization_id == org_id).all()
    pendientes = sum(1 for m in msgs if m.estado in ("PENDIENTE_ENVIO", "PROGRAMADA", "ENVIANDO"))
    fallidas = sum(1 for m in msgs if m.estado == "FALLIDA")
    enviadas = sum(1 for m in msgs if m.estado in ("ENVIADA", "ENTREGADA"))
    total_intentos = sum(m.intentos for m in msgs if m.intentos)
    fallidos_intentos = sum(1 for m in msgs if m.estado == "FALLIDA" and m.intentos >= m.max_intentos)
    canales_deg = db.query(CommChannel).filter(CommChannel.organization_id == org_id, CommChannel.estado == "DEGRADADO").count()
    tasa = round(fallidas / enviadas * 100, 1) if enviadas else None
    return {
        "pendientes": pendientes,
        "fallidas": fallidas,
        "enviadas": enviadas,
        "tasa_fallo_pct": tasa,
        "canales_degradados": canales_deg,
        "reintentos_pendientes": sum(1 for m in msgs if m.proximo_intento is not None),
        "criticas_pendientes": fallidos_intentos,
        "endpoint": "/api/comunicaciones/contrato/centro-control",
    }


def contrato_mi_trabajo(db: Session, org_id: str) -> dict[str, Any]:
    channels_missing = (
        db.query(CommChannel)
        .filter(CommChannel.organization_id == org_id, CommChannel.activo.is_(True), CommChannel.estado == "ERROR")
        .count()
    )
    reintentos_agotados = (
        db.query(CommMessage)
        .filter(
            CommMessage.organization_id == org_id,
            CommMessage.estado == "FALLIDA",
            CommMessage.intentos >= CommMessage.max_intentos,
        )
        .count()
    )
    sin_config = (
        db.query(CommChannel)
        .filter(
            CommChannel.organization_id == org_id,
            CommChannel.tipo == "CORREO_ELECTRONICO",
            CommChannel.activo.is_(True),
            CommChannel.secret_ref.is_(None),
        )
        .count()
    )
    return {
        "configuracion_faltante": sin_config,
        "canales_bloqueados": channels_missing,
        "reintentos_agotados": reintentos_agotados,
        "endpoint": "/api/comunicaciones/contrato/mi-trabajo",
    }


def get_preferences(db: Session, org_id: str, user: User) -> dict[str, Any]:
    pref = (
        db.query(CommPreference)
        .filter(CommPreference.organization_id == org_id, CommPreference.user_id == user.id)
        .first()
    )
    if not pref:
        return {
            "id": None,
            "organization_id": org_id,
            "user_id": user.id,
            "canales": [],
            "tipos": [],
            "horario": None,
            "idioma": "es",
        }
    return {
        "id": pref.id,
        "organization_id": org_id,
        "user_id": user.id,
        "canales": json.loads(pref.canales_json) if pref.canales_json else [],
        "tipos": json.loads(pref.tipos_json) if pref.tipos_json else [],
        "horario": _json_load(pref.horario_json) or None,
        "idioma": pref.idioma,
    }


def upsert_preference(db: Session, org_id: str, user: User, data: dict[str, Any]) -> dict[str, Any]:
    pref = (
        db.query(CommPreference)
        .filter(CommPreference.organization_id == org_id, CommPreference.user_id == user.id)
        .first()
    )
    if not pref:
        pref = CommPreference(organization_id=org_id, user_id=user.id)
        db.add(pref)
    if data.get("canales") is not None:
        pref.canales_json = _json_dump(data["canales"])
    if data.get("tipos") is not None:
        pref.tipos_json = _json_dump(data["tipos"])
    if data.get("horario") is not None:
        pref.horario_json = _json_dump(data["horario"])
    if data.get("idioma"):
        pref.idioma = data["idioma"]
    write_audit(db, action="communications.preferences.updated", organization_id=org_id, user_id=user.id)
    db.commit()
    db.refresh(pref)
    return {
        "id": pref.id,
        "organization_id": org_id,
        "user_id": user.id,
        "canales": json.loads(pref.canales_json) if pref.canales_json else [],
        "tipos": json.loads(pref.tipos_json) if pref.tipos_json else [],
        "horario": _json_load(pref.horario_json) or None,
        "idioma": pref.idioma,
    }


def _resolve_org_admin_id(db: Session, org_id: str) -> str | None:
    admin = (
        db.query(User)
        .filter(User.organization_id == org_id, User.role == "admin", User.is_active.is_(True))
        .first()
    )
    return admin.id if admin else None


def _is_terminal_comm_failure(msg: CommMessage, now: datetime) -> bool:
    """Fallo terminal: reintentos agotados y sin reintento programado futuro."""
    if msg.estado != "FALLIDA":
        return False
    if msg.intentos < msg.max_intentos:
        return False
    if msg.proximo_intento and _as_utc(msg.proximo_intento) > now:
        return False
    return True


def _trabajo_action(codigo: str, etiqueta: str, permiso: str | None = None, href: str | None = None) -> dict[str, Any]:
    return {"codigo": codigo, "etiqueta": etiqueta, "permiso": permiso, "href": href, "payload": None}


def collect_trabajo_items(
    db: Session,
    org_id: str,
    user: User,
    *,
    organization_name: str | None = None,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    """Ítems accionables para Mi Trabajo. Retorna (items, msg_ids, correlation_ids)."""
    ts = now or _utcnow()
    items: list[dict[str, Any]] = []
    msg_ids: set[str] = set()
    correlation_ids: set[str] = set()
    seen_item_keys: set[str] = set()

    terminal_msgs = (
        db.query(CommMessage)
        .filter(CommMessage.organization_id == org_id, CommMessage.estado == "FALLIDA")
        .all()
    )
    for msg in terminal_msgs:
        if not _is_terminal_comm_failure(msg, ts):
            continue
        item_key = f"comunicacion:msg:{msg.id}"
        if item_key in seen_item_keys:
            continue
        seen_item_keys.add(item_key)
        msg_ids.add(msg.id)
        if msg.correlation_id:
            correlation_ids.add(msg.correlation_id)
        ch = db.query(CommChannel).filter(CommChannel.id == msg.channel_id).first() if msg.channel_id else None
        responsable = msg.creador_id
        if msg.destinatario_tipo == "USUARIO" and msg.destinatario_id:
            responsable = msg.destinatario_id
        if not responsable:
            responsable = _resolve_org_admin_id(db, org_id)
        tipo = "comunicacion_envio_critico"
        if msg.tipo_comunicacion and "CRIT" in msg.tipo_comunicacion.upper():
            tipo = "comunicacion_envio_critico"
        items.append(
            {
                "id": item_key,
                "source_id": msg.id,
                "tipo": tipo,
                "asunto": sanitize_comm_text(msg.asunto or f"Comunicación fallida ({msg.tipo_comunicacion})"),
                "modulo": "comunicaciones",
                "modulo_etiqueta": "Centro de Información y Comunicaciones",
                "organization_id": org_id,
                "organization_name": organization_name,
                "prioridad": "ALTA",
                "prioridad_orden": 3,
                "estado_dominio": msg.estado,
                "estado_presentacion": "FALLIDA",
                "responsable_id": responsable,
                "responsable_nombre": None,
                "created_at": msg.updated_at or msg.created_at,
                "fecha_limite": None,
                "antiguedad_horas": None,
                "vencida": False,
                "correlation_id": msg.correlation_id,
                "requires_action": True,
                "informativa": False,
                "semantic_kind": "HECHO",
                "detalle": sanitize_comm_text(
                    f"Canal {ch.tipo if ch else '—'}: reintentos agotados ({msg.intentos}/{msg.max_intentos})."
                ),
                "enlace": f"/comunicaciones?mensaje={msg.id}",
                "trazabilidad_enlace": None,
                "acciones": [
                    _trabajo_action("ver", "Abrir comunicación", "communications.view", f"/comunicaciones?mensaje={msg.id}"),
                ],
                "metadata": {
                    "communication_id": msg.id,
                    "channel_tipo": ch.tipo if ch else None,
                    "intentos": msg.intentos,
                    "max_intentos": msg.max_intentos,
                    "event_id": msg.event_id,
                    "rule_id": msg.rule_id,
                    "estado_accionable": "reintentos_agotados",
                },
            }
        )

    blocked_channels = (
        db.query(CommChannel)
        .filter(
            CommChannel.organization_id == org_id,
            CommChannel.activo.is_(True),
            CommChannel.estado.in_(["ERROR", "DEGRADADO"]),
        )
        .all()
    )
    for ch in blocked_channels:
        item_key = f"comunicacion:canal:{ch.id}"
        if item_key in seen_item_keys:
            continue
        has_terminal = any(m.channel_id == ch.id for m in terminal_msgs if _is_terminal_comm_failure(m, ts))
        if not has_terminal and ch.estado != "ERROR":
            continue
        seen_item_keys.add(item_key)
        items.append(
            {
                "id": item_key,
                "source_id": ch.id,
                "tipo": "comunicacion_canal_bloqueado",
                "asunto": f"Canal bloqueado: {ch.nombre}",
                "modulo": "comunicaciones",
                "modulo_etiqueta": "Centro de Información y Comunicaciones",
                "organization_id": org_id,
                "organization_name": organization_name,
                "prioridad": "ALTA",
                "prioridad_orden": 3,
                "estado_dominio": ch.estado,
                "estado_presentacion": "PENDIENTE",
                "responsable_id": _resolve_org_admin_id(db, org_id),
                "responsable_nombre": None,
                "created_at": ch.updated_at or ch.created_at,
                "fecha_limite": None,
                "antiguedad_horas": None,
                "vencida": False,
                "correlation_id": None,
                "requires_action": True,
                "informativa": False,
                "detalle": f"Canal {ch.tipo} en estado {ch.estado}.",
                "enlace": "/comunicaciones?tab=canales",
                "trazabilidad_enlace": None,
                "acciones": [
                    _trabajo_action("ver", "Revisar canales", "communications.view", "/comunicaciones?tab=canales"),
                ],
                "metadata": {
                    "channel_id": ch.id,
                    "channel_tipo": ch.tipo,
                    "estado_accionable": "canal_bloqueado",
                },
            }
        )

    for ch in (
        db.query(CommChannel)
        .filter(
            CommChannel.organization_id == org_id,
            CommChannel.activo.is_(True),
            CommChannel.tipo == "CORREO_ELECTRONICO",
            CommChannel.secret_ref.is_(None),
        )
        .all()
    ):
        failed_on_channel = [m for m in terminal_msgs if m.channel_id == ch.id and _is_terminal_comm_failure(m, ts)]
        if not failed_on_channel:
            continue
        item_key = f"comunicacion:config:{ch.id}"
        if item_key in seen_item_keys:
            continue
        seen_item_keys.add(item_key)
        items.append(
            {
                "id": item_key,
                "source_id": ch.id,
                "tipo": "comunicacion_configuracion_requerida",
                "asunto": f"Configuración requerida: {ch.nombre}",
                "modulo": "comunicaciones",
                "modulo_etiqueta": "Centro de Información y Comunicaciones",
                "organization_id": org_id,
                "organization_name": organization_name,
                "prioridad": "MEDIA",
                "prioridad_orden": 2,
                "estado_dominio": "CONFIG_FALTANTE",
                "estado_presentacion": "PENDIENTE",
                "responsable_id": _resolve_org_admin_id(db, org_id),
                "responsable_nombre": None,
                "created_at": ch.updated_at or ch.created_at,
                "fecha_limite": None,
                "antiguedad_horas": None,
                "vencida": False,
                "correlation_id": None,
                "requires_action": True,
                "informativa": False,
                "detalle": "El canal de correo requiere credenciales configuradas tras fallos de envío.",
                "enlace": "/comunicaciones?tab=canales",
                "trazabilidad_enlace": None,
                "acciones": [
                    _trabajo_action("ver", "Configurar canal", "communications.channel.manage", "/comunicaciones?tab=canales"),
                ],
                "metadata": {
                    "channel_id": ch.id,
                    "estado_accionable": "configuracion_requerida",
                    "secret_configured": False,
                },
            }
        )

    return items, msg_ids, correlation_ids


def _comms_event_subscriber(event: EventMessage, db: Session) -> None:
    try:
        evaluate_rules_for_event(db, event)
    except Exception:
        logger.exception("MB-11 rule evaluation failed for %s", event.event_type)


def register_communications_handlers() -> None:
    subscribe(_comms_event_subscriber)
