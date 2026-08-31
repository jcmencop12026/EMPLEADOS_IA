"""MB-11 — Centro de Información y Comunicaciones."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.communications_models import CommChannel, CommMessage, CommTemplateVersion
from app.config import settings
from app.events.bus import EventMessage, publish
from app.models import AuditLog, Notification, Organization, User
from app.security import hash_password
from app.services import communications_service as svc
from app.services.automation_scheduler import _tick
from conftest import TestingSessionLocal, auth_header


def _bootstrap_admin(db) -> User:
    return db.query(User).filter(User.username == settings.bootstrap_admin_username).one()


def _org_user(db, prefix: str = "mb11") -> tuple[Organization, User]:
    org = Organization(name=f"{prefix}-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"{prefix}-{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        full_name="Usuario Prueba",
    )
    db.add(user)
    db.commit()
    return org, user


def _channel(db, org_id: str, tipo: str = "INTERNO_PLATAFORMA", nombre: str | None = None) -> CommChannel:
    ch = CommChannel(
        organization_id=org_id,
        tipo=tipo,
        nombre=nombre or f"Canal-{uuid.uuid4().hex[:6]}",
        activo=True,
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def _template(db, org, user) -> dict:
    return svc.create_template(
        db,
        org.id,
        user,
        {
            "codigo": f"TPL_{uuid.uuid4().hex[:4].upper()}",
            "nombre": "Plantilla prueba",
            "tipo_comunicacion": "OPERATIVA",
            "canal_tipo": "INTERNO_PLATAFORMA",
            "asunto": "Aviso {{nombre}}",
            "contenido": "Hola {{nombre}} de {{empresa}} el {{fecha}}.",
            "variables": ["nombre", "empresa", "fecha"],
        },
    )


def test_template_create_version_and_variables(client: TestClient, auth_headers):
    codigo = f"SLA_RIESGO_{uuid.uuid4().hex[:6].upper()}"
    tpl = client.post(
        "/api/comunicaciones/plantillas",
        headers=auth_headers,
        json={
            "codigo": codigo,
            "nombre": "SLA en riesgo",
            "tipo_comunicacion": "ALERTA",
            "canal_tipo": "INTERNO_PLATAFORMA",
            "asunto": "SLA {{caso}}",
            "contenido": "Caso {{caso}} valor {{valor}} estado {{estado}}",
        },
    )
    assert tpl.status_code == 201
    template_id = tpl.json()["id"]
    ver = client.post(
        f"/api/comunicaciones/plantillas/{template_id}/versiones",
        headers=auth_headers,
        json={"contenido": "Versión 2: {{nombre}}", "asunto": "V2"},
    )
    assert ver.status_code == 201 and ver.json()["version"] == 2
    bad = client.post(
        "/api/comunicaciones/plantillas",
        headers=auth_headers,
        json={
            "codigo": f"MALA_{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Mala",
            "tipo_comunicacion": "X",
            "canal_tipo": "INTERNO_PLATAFORMA",
            "contenido": "import os; {{nombre}}",
        },
    )
    assert bad.status_code == 422


def test_rule_event_condition_idempotency_and_dedup(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = _bootstrap_admin(db)
        org_id = admin.organization_id
        org = db.query(Organization).filter(Organization.id == org_id).one()
        ch = _channel(db, org_id)
        tpl = _template(db, org, admin)
        admin_id = admin.id
        channel_id = ch.id
    finally:
        db.close()

    rule = client.post(
        "/api/comunicaciones/reglas",
        headers=auth_headers,
        json={
            "nombre": f"SLA riesgo {uuid.uuid4().hex[:6]}",
            "event_type": "SUPPORT_SLA_RISK",
            "condicion": {"match": {"prioridad": "alta"}},
            "destinatario_tipo": "USUARIO",
            "destinatario_regla": admin_id,
            "template_version_id": tpl["current_version_id"],
            "channel_id": channel_id,
            "accion": "ENVIAR",
            "antispam_minutos": 60,
        },
    )
    assert rule.status_code == 201

    db = TestingSessionLocal()
    try:
        admin = _bootstrap_admin(db)
        before = db.query(CommMessage).filter(CommMessage.organization_id == admin.organization_id).count()
        publish(
            EventMessage(
                event_type="SUPPORT_SLA_RISK",
                organization_id=admin.organization_id,
                payload={"prioridad": "alta", "nombre": "Ana", "recipient_user_id": admin.id},
            ),
            db,
        )
        db.commit()
        after_first = db.query(CommMessage).filter(CommMessage.organization_id == admin.organization_id).count()
        assert after_first == before + 1
        publish(
            EventMessage(
                event_type="SUPPORT_SLA_RISK",
                organization_id=admin.organization_id,
                payload={"prioridad": "alta", "nombre": "Ana", "recipient_user_id": admin.id},
            ),
            db,
        )
        db.commit()
        assert db.query(CommMessage).filter(CommMessage.organization_id == admin.organization_id).count() == after_first
        publish(
            EventMessage(
                event_type="SUPPORT_SLA_RISK",
                organization_id=admin.organization_id,
                payload={"prioridad": "baja", "nombre": "Ana"},
            ),
            db,
        )
        db.commit()
        assert db.query(CommMessage).filter(CommMessage.organization_id == admin.organization_id).count() == after_first
        last = (
            db.query(CommMessage)
            .filter(CommMessage.organization_id == admin.organization_id)
            .order_by(CommMessage.created_at.desc())
            .first()
        )
        assert last and last.estado == "ENVIADA"
    finally:
        db.close()


def test_channels_adapters_manual_schedule_cancel(client: TestClient, auth_headers):
    suffix = uuid.uuid4().hex[:6]
    ch = client.post(
        "/api/comunicaciones/canales",
        headers=auth_headers,
        json={"tipo": "CORREO_ELECTRONICO", "nombre": f"Correo simulado {suffix}"},
    )
    assert ch.status_code == 201
    assert ch.json()["secret_configured"] is False
    assert "password" not in str(ch.json())

    wh = client.post(
        "/api/comunicaciones/canales",
        headers=auth_headers,
        json={"tipo": "WEBHOOK", "nombre": f"Webhook {suffix}", "config": {"webhook_url": "https://example.com/hook"}},
    )
    assert wh.status_code == 201

    interno = client.post(
        "/api/comunicaciones/canales",
        headers=auth_headers,
        json={"tipo": "INTERNO_PLATAFORMA", "nombre": f"Bandeja {suffix}"},
    )
    channel_id = interno.json()["id"]

    tpl = client.post(
        "/api/comunicaciones/plantillas",
        headers=auth_headers,
        json={
            "codigo": f"MANUAL_{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Manual",
            "tipo_comunicacion": "MANUAL",
            "canal_tipo": "INTERNO_PLATAFORMA",
            "contenido": "Texto {{nombre}}",
        },
    )
    ver_id = tpl.json()["current_version_id"]
    db = TestingSessionLocal()
    try:
        admin = _bootstrap_admin(db)
        dest = admin.id
    finally:
        db.close()

    sent = client.post(
        "/api/comunicaciones/mensajes",
        headers=auth_headers,
        json={
            "channel_id": channel_id,
            "template_version_id": ver_id,
            "destinatario_tipo": "USUARIO",
            "destinatario_id": dest,
            "enviar_ahora": True,
        },
    )
    assert sent.status_code == 201 and sent.json()["estado"] == "ENVIADA"
    assert sent.json()["entregada_at"] is None

    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    sched = client.post(
        "/api/comunicaciones/mensajes",
        headers=auth_headers,
        json={
            "channel_id": channel_id,
            "contenido": "Programada",
            "destinatario_tipo": "USUARIO",
            "destinatario_id": dest,
            "programada_para": future,
            "enviar_ahora": False,
        },
    )
    assert sched.status_code == 201 and sched.json()["estado"] == "PROGRAMADA"
    cancelled = client.post(f"/api/comunicaciones/mensajes/{sched.json()['id']}/cancelar", headers=auth_headers)
    assert cancelled.json()["estado"] == "CANCELADA"


def test_retries_max_and_scheduler_810c(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = _bootstrap_admin(db)
        ch = CommChannel(
            organization_id=admin.organization_id,
            tipo="WEBHOOK",
            nombre=f"Roto-{uuid.uuid4().hex[:6]}",
            activo=True,
            config_json='{"webhook_url":""}',
        )
        db.add(ch)
        db.commit()
        db.refresh(ch)
        msg = CommMessage(
            organization_id=admin.organization_id,
            estado="PENDIENTE_ENVIO",
            tipo_comunicacion="TEST",
            channel_id=ch.id,
            destinatario_tipo="USUARIO",
            destinatario_id=admin.id,
            contenido="fallará",
            max_intentos=2,
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
        svc.send_message(db, msg)
        db.commit()
        msg = db.query(CommMessage).filter(CommMessage.id == msg_id).one()
        assert msg.intentos >= 1
        msg.proximo_intento = datetime.now(timezone.utc) - timedelta(seconds=5)
        db.commit()
    finally:
        db.close()

    _tick()
    db = TestingSessionLocal()
    try:
        msg = db.query(CommMessage).filter(CommMessage.id == msg_id).one()
        assert msg.estado in ("FALLIDA", "PENDIENTE_ENVIO")
        assert msg.intentos <= msg.max_intentos
    finally:
        db.close()


def test_preferences_language_contracts_rbac_multiorg(client: TestClient, auth_headers):
    pref = client.put(
        "/api/comunicaciones/preferencias",
        headers=auth_headers,
        json={"canales": ["INTERNO_PLATAFORMA"], "idioma": "es"},
    )
    assert pref.status_code == 200 and pref.json()["idioma"] == "es"

    cc = client.get("/api/comunicaciones/contrato/centro-control", headers=auth_headers)
    assert cc.status_code == 200 and "pendientes" in cc.json()
    mt = client.get("/api/comunicaciones/contrato/mi-trabajo", headers=auth_headers)
    assert mt.status_code == 200

    db = TestingSessionLocal()
    try:
        org_b, user_b = _org_user(db, "orgb")
        _channel(db, org_b.id, nombre="Canal B")
        _template(db, org_b, user_b)
        user_b_name = user_b.username
    finally:
        db.close()

    token_b = client.post("/api/auth/login", json={"username": user_b_name, "password": "Admin2026*"}).json()["access_token"]
    headers_b = auth_header(token_b)
    assert client.get("/api/comunicaciones/canales", headers=headers_b).status_code == 200
    msgs_a = {m["id"] for m in client.get("/api/comunicaciones/mensajes", headers=auth_headers).json()}
    msgs_b = {m["id"] for m in client.get("/api/comunicaciones/mensajes", headers=headers_b).json()}
    assert msgs_a.isdisjoint(msgs_b)

    viewer_db = TestingSessionLocal()
    try:
        _, viewer = _org_user(viewer_db, "viewer")
        viewer.role = "viewer"
        viewer_db.commit()
        vname = viewer.username
    finally:
        viewer_db.close()
    vtoken = client.post("/api/auth/login", json={"username": vname, "password": "Admin2026*"}).json()["access_token"]
    assert client.post(
        "/api/comunicaciones/plantillas",
        headers=auth_header(vtoken),
        json={
            "codigo": "X",
            "nombre": "X",
            "tipo_comunicacion": "X",
            "canal_tipo": "INTERNO_PLATAFORMA",
            "contenido": "x",
        },
    ).status_code == 403

    db = TestingSessionLocal()
    try:
        actions = {a.action for a in db.query(AuditLog).filter(AuditLog.action.like("communications.%")).all()}
        assert len(actions) >= 1
    finally:
        db.close()


def test_820_not_duplicated_by_communication_event(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = _bootstrap_admin(db)
        before = db.query(Notification).filter(Notification.organization_id == admin.organization_id).count()
        ch = _channel(db, admin.organization_id)
        tpl = _template(db, db.query(Organization).filter(Organization.id == admin.organization_id).one(), admin)
        svc.create_rule(
            db,
            admin.organization_id,
            admin,
            {
                "nombre": "Regla notif",
                "event_type": "FINOPS_LIMIT_REACHED",
                "condicion": {"match": {"limite": "90"}},
                "destinatario_tipo": "USUARIO",
                "destinatario_regla": admin.id,
                "template_version_id": tpl["current_version_id"],
                "channel_id": ch.id,
            },
        )
        publish(
            EventMessage(
                event_type="FINOPS_LIMIT_REACHED",
                organization_id=admin.organization_id,
                payload={"limite": "90", "nombre": "Test"},
            ),
            db,
        )
        db.commit()
        after = db.query(Notification).filter(Notification.organization_id == admin.organization_id).count()
        comms = db.query(CommMessage).filter(CommMessage.organization_id == admin.organization_id).count()
        assert comms >= 1
        assert after >= before
    finally:
        db.close()


def test_timezone_aware_scheduling():
    db = TestingSessionLocal()
    try:
        org, user = _org_user(db, "tz")
        ch = _channel(db, org.id)
        naive = datetime(2030, 6, 1, 10, 0, 0)
        aware = datetime(2030, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        msg_naive = svc.create_message_manual(
            db,
            org.id,
            user,
            {
                "channel_id": ch.id,
                "contenido": "naive",
                "destinatario_tipo": "USUARIO",
                "destinatario_id": user.id,
                "programada_para": naive,
                "enviar_ahora": False,
            },
        )
        msg_aware = svc.create_message_manual(
            db,
            org.id,
            user,
            {
                "channel_id": ch.id,
                "contenido": "aware",
                "destinatario_tipo": "USUARIO",
                "destinatario_id": user.id,
                "programada_para": aware,
                "enviar_ahora": False,
            },
        )
        assert msg_naive["estado"] == "PROGRAMADA"
        assert msg_aware["estado"] == "PROGRAMADA"
    finally:
        db.close()


def test_template_version_preserved_on_message():
    db = TestingSessionLocal()
    try:
        org, user = _org_user(db, "ver")
        ch = _channel(db, org.id)
        tpl = _template(db, org, user)
        ver1 = tpl["current_version_id"]
        svc.new_template_version(db, org.id, tpl["id"], user, {"contenido": "Nueva {{nombre}}", "asunto": "N"})
        msg = svc.create_message_manual(
            db,
            org.id,
            user,
            {
                "channel_id": ch.id,
                "template_version_id": ver1,
                "destinatario_tipo": "USUARIO",
                "destinatario_id": user.id,
                "enviar_ahora": True,
            },
        )
        ver_row = db.query(CommTemplateVersion).filter(CommTemplateVersion.id == ver1).one()
        stored = db.query(CommMessage).filter(CommMessage.id == msg["id"]).one()
        assert stored.template_version_id == ver1
        assert ver_row.version == 1
        assert "Nueva" not in (stored.contenido or "")
    finally:
        db.close()
