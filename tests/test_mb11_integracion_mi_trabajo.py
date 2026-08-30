"""MB-11 ↔ Mi Trabajo — integración portable."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.communications_models import CommChannel, CommMessage
from app.models import Notification, Organization, User
from app.security import hash_password
from app.services import communications_service as comm_svc
from app.services.automation_scheduler import _tick
from conftest import TestingSessionLocal, auth_header


def _org_user(db, prefix: str = "int") -> tuple[Organization, User]:
    org = Organization(name=f"{prefix}-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"{prefix}-{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        full_name="Admin Integración",
    )
    db.add(user)
    db.commit()
    return org, user


def _channel(db, org_id: str, **kwargs) -> CommChannel:
    ch = CommChannel(
        organization_id=org_id,
        tipo=kwargs.get("tipo", "INTERNO_PLATAFORMA"),
        nombre=kwargs.get("nombre", f"Canal-{uuid.uuid4().hex[:6]}"),
        activo=kwargs.get("activo", True),
        estado=kwargs.get("estado", "ACTIVO"),
        config_json=kwargs.get("config_json"),
        secret_ref=kwargs.get("secret_ref"),
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def test_recoverable_failure_not_in_trabajo(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        ch = _channel(db, admin.organization_id, tipo="WEBHOOK", config_json='{"webhook_url":""}')
        msg = CommMessage(
            organization_id=admin.organization_id,
            estado="FALLIDA",
            tipo_comunicacion="TEST",
            channel_id=ch.id,
            destinatario_tipo="USUARIO",
            destinatario_id=admin.id,
            contenido="fallo recuperable",
            intentos=1,
            max_intentos=3,
            proximo_intento=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
    finally:
        db.close()

    items = client.get("/api/trabajo/items?modulo=comunicaciones", headers=auth_headers).json()["items"]
    assert not any(i.get("metadata", {}).get("communication_id") == msg_id for i in items)


def test_terminal_failure_appears_once(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        ch = _channel(db, admin.organization_id, tipo="WEBHOOK", config_json='{"webhook_url":""}')
        msg = CommMessage(
            organization_id=admin.organization_id,
            estado="FALLIDA",
            tipo_comunicacion="CRITICA",
            channel_id=ch.id,
            destinatario_tipo="USUARIO",
            destinatario_id=admin.id,
            contenido="fallo terminal",
            intentos=3,
            max_intentos=3,
            correlation_id=f"corr-{uuid.uuid4().hex[:8]}",
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
        corr = msg.correlation_id
    finally:
        db.close()

    r1 = client.get("/api/trabajo/items?modulo=comunicaciones", headers=auth_headers).json()["items"]
    r2 = client.get("/api/trabajo/items?modulo=comunicaciones", headers=auth_headers).json()["items"]
    matches = [i for i in r1 if i.get("metadata", {}).get("communication_id") == msg_id]
    assert len(matches) == 1
    assert matches[0]["tipo"] == "comunicacion_envio_critico"
    assert matches[0]["modulo"] == "comunicaciones"
    assert len([i for i in r2 if i.get("metadata", {}).get("communication_id") == msg_id]) == 1

    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        db.add(
            Notification(
                organization_id=admin.organization_id,
                type="WARNING",
                severity="HIGH",
                title="Duplicado comunicación",
                message="No debe duplicar obligación humana",
                source_type="communication",
                source_id=msg_id,
                status="NEW",
                channel="IN_APP",
                event_id=corr,
                metadata_json=f'{{"communication_id":"{msg_id}","correlation_id":"{corr}"}}',
            )
        )
        db.commit()
    finally:
        db.close()

    all_items = client.get("/api/trabajo/items", headers=auth_headers).json()["items"]
    comm_human = [i for i in all_items if i.get("metadata", {}).get("communication_id") == msg_id]
    notif_dup = [i for i in all_items if i.get("tipo") == "notificacion" and i.get("source_id") == msg_id]
    assert len(comm_human) == 1
    assert len(notif_dup) == 0


def test_resolved_failure_disappears(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        ch = _channel(db, admin.organization_id)
        msg = CommMessage(
            organization_id=admin.organization_id,
            estado="FALLIDA",
            tipo_comunicacion="TEST",
            channel_id=ch.id,
            destinatario_tipo="USUARIO",
            destinatario_id=admin.id,
            contenido="x",
            intentos=3,
            max_intentos=3,
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
    finally:
        db.close()

    assert any(
        i.get("metadata", {}).get("communication_id") == msg_id
        for i in client.get("/api/trabajo/items?modulo=comunicaciones", headers=auth_headers).json()["items"]
    )

    db = TestingSessionLocal()
    try:
        msg = db.query(CommMessage).filter(CommMessage.id == msg_id).one()
        msg.estado = "ENVIADA"
        msg.enviada_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()

    assert not any(
        i.get("metadata", {}).get("communication_id") == msg_id
        for i in client.get("/api/trabajo/items?modulo=comunicaciones", headers=auth_headers).json()["items"]
    )


def test_scheduler_retry_no_premature_trabajo(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        ch = _channel(db, admin.organization_id, tipo="WEBHOOK", config_json='{"webhook_url":""}')
        msg = CommMessage(
            organization_id=admin.organization_id,
            estado="PENDIENTE_ENVIO",
            tipo_comunicacion="TEST",
            channel_id=ch.id,
            destinatario_tipo="USUARIO",
            destinatario_id=admin.id,
            contenido="reintento",
            intentos=1,
            max_intentos=3,
            proximo_intento=datetime.now(timezone.utc) - timedelta(seconds=10),
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
    finally:
        db.close()

    _tick()
    items_before_terminal = client.get("/api/trabajo/items?modulo=comunicaciones", headers=auth_headers).json()["items"]
    assert not any(i.get("metadata", {}).get("communication_id") == msg_id for i in items_before_terminal)

    db = TestingSessionLocal()
    try:
        msg = db.query(CommMessage).filter(CommMessage.id == msg_id).one()
        msg.estado = "FALLIDA"
        msg.intentos = 3
        msg.proximo_intento = None
        db.commit()
    finally:
        db.close()

    items = client.get("/api/trabajo/items?modulo=comunicaciones", headers=auth_headers).json()["items"]
    assert any(i.get("metadata", {}).get("communication_id") == msg_id for i in items)


def test_resumen_filtros_navegacion_secretos(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        ch = _channel(
            db,
            admin.organization_id,
            tipo="CORREO_ELECTRONICO",
            secret_ref="vault/smtp/secret",
            config_json='{"smtp_password":"NO-MOSTRAR"}',
        )
        msg = CommMessage(
            organization_id=admin.organization_id,
            estado="FALLIDA",
            tipo_comunicacion="TEST",
            channel_id=ch.id,
            destinatario_tipo="USUARIO",
            destinatario_id=admin.id,
            contenido="smtp password=secreto123",
            intentos=3,
            max_intentos=3,
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
    finally:
        db.close()

    resumen = client.get("/api/trabajo/resumen", headers=auth_headers).json()
    assert resumen["pendientes"] >= 1

    filtered = client.get(f"/api/trabajo/items?communication_id={msg_id}", headers=auth_headers).json()
    assert filtered["total"] >= 1
    item = filtered["items"][0]
    assert item["enlace"].startswith("/comunicaciones")
    raw = str(item).lower()
    assert "vault/smtp" not in raw
    assert "secreto123" not in raw
    assert "no-mostrar" not in raw


def test_multiempresa_rbac(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b, user_b = _org_user(db, "orgb")
        ch = _channel(db, org_b.id)
        msg = CommMessage(
            organization_id=org_b.id,
            estado="FALLIDA",
            tipo_comunicacion="TEST",
            channel_id=ch.id,
            destinatario_tipo="USUARIO",
            destinatario_id=user_b.id,
            contenido="org b",
            intentos=3,
            max_intentos=3,
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
        uname = user_b.username
    finally:
        db.close()

    assert client.get(f"/api/trabajo/items?communication_id={msg_id}", headers=auth_headers).json()["total"] == 0
    token_b = client.post("/api/auth/login", json={"username": uname, "password": "Admin2026*"}).json()["access_token"]
    headers_b = auth_header(token_b)
    assert client.get(f"/api/trabajo/items?communication_id={msg_id}", headers=headers_b).json()["total"] == 1

    viewer_db = TestingSessionLocal()
    try:
        _, viewer = _org_user(viewer_db, "viewer")
        viewer.role = "viewer"
        viewer_db.commit()
        vname = viewer.username
    finally:
        viewer_db.close()
    vtoken = client.post("/api/auth/login", json={"username": vname, "password": "Admin2026*"}).json()["access_token"]
    vheaders = auth_header(vtoken)
    comm_items = client.get("/api/trabajo/items?modulo=comunicaciones", headers=vheaders).json()["items"]
    assert len(comm_items) == 0


def test_contrato_mi_trabajo_reused():
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        contract = comm_svc.contrato_mi_trabajo(db, admin.organization_id)
        items, _, _ = comm_svc.collect_trabajo_items(db, admin.organization_id, admin)
        assert "endpoint" in contract
        assert isinstance(items, list)
    finally:
        db.close()
