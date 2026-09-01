"""MB-11 EIAAX — Centro de Información, comunicaciones e integración con Resultados."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.communications_models import CommChannel, CommEntregaInforme, CommMessage
from app.config import settings
from app.events.bus import EventMessage, publish
from app.models import Organization, User
from app.security import hash_password
from app.services import communications_service as comm_svc
from app.services import resultados_service as res_svc
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _admin(db) -> User:
    return db.query(User).filter(User.username == settings.bootstrap_admin_username).one()


def _org_user(db, prefix: str = "mb11e") -> tuple[Organization, User]:
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


def _channel(db, org_id: str, tipo: str = "INTERNO_PLATAFORMA") -> CommChannel:
    ch = CommChannel(organization_id=org_id, tipo=tipo, nombre=f"Canal-{uuid.uuid4().hex[:4]}", activo=True)
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def _expediente_y_informe(client: TestClient, headers: dict) -> tuple[str, str]:
    exp = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Eval comunicaciones",
            "entidad_nombre": "IPS Comunicaciones",
            "nivel": "PRELIMINAR",
        },
    ).json()
    inf = client.post(
        "/api/resultados/informes/generar",
        headers=headers,
        json={"expediente_id": exp["id"], "tipo": "IMPACTO", "visibilidad": "VISIBLE_ENTIDAD"},
    ).json()
    return exp["id"], inf["id"]


def test_caso1_informe_entrega_historial(client: TestClient, auth_headers):
    """CASO 1: resultado → informe → entregar → historial."""
    db = TestingSessionLocal()
    try:
        admin = _admin(db)
        comm_svc.bootstrap_default_comm_assets(db, admin.organization_id, admin)
        ch = _channel(db, admin.organization_id)
        channel_id = ch.id
        dest_id = admin.id
    finally:
        db.close()

    _, informe_id = _expediente_y_informe(client, auth_headers)
    entrega = client.post(
        f"/api/comunicaciones/informes/{informe_id}/entregar",
        headers=auth_headers,
        json={
            "channel_id": channel_id,
            "destinatario_tipo": "USUARIO",
            "destinatario_id": dest_id,
            "visibilidad_entrega": "VISIBLE_ENTIDAD",
        },
    )
    assert entrega.status_code == 200, entrega.text
    body = entrega.json()
    assert body["message"]["estado"] == "ENVIADA"
    assert body["entrega"]["informe_version"] >= 1

    historial = client.get(f"/api/comunicaciones/informes/entregas?informe_id={informe_id}", headers=auth_headers)
    assert historial.status_code == 200
    assert len(historial.json()) >= 1


def test_caso2_info_faltante_solicitud(client: TestClient, auth_headers):
    """CASO 2: expediente incompleto → solicitud → notificación."""
    db = TestingSessionLocal()
    try:
        admin = _admin(db)
        _channel(db, admin.organization_id)
        dest = admin.id
        org_id = admin.organization_id
    finally:
        db.close()

    exp = client.post(
        "/api/evaluaciones",
        headers=auth_headers,
        json={"titulo": "Incompleta", "entidad_nombre": "Demo", "nivel": "PRELIMINAR"},
    ).json()

    db2 = TestingSessionLocal()
    try:
        publish(
            EventMessage(
                event_type="EVALUACION_INFO_FALTANTE",
                organization_id=org_id,
                payload={
                    "expediente_id": exp["id"],
                    "responsable_id": dest,
                    "porcentaje_informacion": 35,
                },
            ),
            db2,
        )
        db2.commit()
    finally:
        db2.close()

    msgs = client.get("/api/comunicaciones/mensajes", headers=auth_headers).json()
    assert any(m["tipo_comunicacion"] == "SOLICITUD" for m in msgs)


def test_caso3_fallo_canal_externo(client: TestClient, auth_headers):
    """CASO 3: canal externo mal configurado → FALLIDA, sin simular entrega."""
    db = TestingSessionLocal()
    try:
        admin = _admin(db)
        ch = CommChannel(
            organization_id=admin.organization_id,
            tipo="WEBHOOK",
            nombre=f"Roto-{uuid.uuid4().hex[:4]}",
            activo=True,
            config_json='{"webhook_url":""}',
        )
        db.add(ch)
        db.commit()
        db.refresh(ch)
        channel_id = ch.id
        dest_id = admin.id
    finally:
        db.close()

    _, informe_id = _expediente_y_informe(client, auth_headers)
    entrega = client.post(
        f"/api/resultados/informes/{informe_id}/entregar",
        headers=auth_headers,
        json={"channel_id": channel_id, "destinatario_tipo": "USUARIO", "destinatario_id": dest_id},
    )
    assert entrega.status_code == 200
    assert entrega.json()["message"]["estado"] in ("FALLIDA", "PENDIENTE_ENVIO")
    assert entrega.json()["message"]["entregada_at"] is None


def test_caso4_privacidad_informe_interno(client: TestClient, auth_headers):
    """CASO 4: informe INTERNO no puede publicarse como visible entidad."""
    exp = client.post(
        "/api/evaluaciones",
        headers=auth_headers,
        json={"titulo": "Privado", "entidad_nombre": "Interna", "nivel": "PRELIMINAR"},
    ).json()
    inf = client.post(
        "/api/resultados/informes/generar",
        headers=auth_headers,
        json={"expediente_id": exp["id"], "visibilidad": "INTERNO"},
    ).json()

    db = TestingSessionLocal()
    try:
        ch = _channel(db, _admin(db).organization_id)
        channel_id = ch.id
        dest = _admin(db).id
    finally:
        db.close()

    rechazo = client.post(
        f"/api/comunicaciones/informes/{inf['id']}/entregar",
        headers=auth_headers,
        json={
            "channel_id": channel_id,
            "destinatario_tipo": "USUARIO",
            "destinatario_id": dest,
            "visibilidad_entrega": "VISIBLE_ENTIDAD",
        },
    )
    assert rechazo.status_code == 422


def test_caso5_multitenant_comunicaciones(client: TestClient, auth_headers):
    """CASO 5: tenant A no ve comunicaciones de tenant B."""
    db = TestingSessionLocal()
    try:
        org_b, user_b = _org_user(db, "orgc")
        ch_b = _channel(db, org_b.id)
        msg_b = CommMessage(
            organization_id=org_b.id,
            estado="ENVIADA",
            tipo_comunicacion="OPERATIVA",
            channel_id=ch_b.id,
            destinatario_tipo="USUARIO",
            destinatario_id=user_b.id,
            contenido="Secreto B",
            origen="MANUAL",
        )
        db.add(msg_b)
        db.commit()
        msg_b_id = msg_b.id
        uname_b = user_b.username
    finally:
        db.close()

    token_b = client.post("/api/auth/login", json={"username": uname_b, "password": "Admin2026*"}).json()["access_token"]
    headers_b = auth_header(token_b)

    forbidden = client.get(f"/api/comunicaciones/mensajes/{msg_b_id}", headers=auth_headers)
    assert forbidden.status_code == 404

    ids_a = {m["id"] for m in client.get("/api/comunicaciones/mensajes", headers=auth_headers).json()}
    ids_b = {m["id"] for m in client.get("/api/comunicaciones/mensajes", headers=headers_b).json()}
    assert msg_b_id in ids_b
    assert msg_b_id not in ids_a


def test_version_informe_fijada_en_entrega(client: TestClient, auth_headers):
    """Versión entregada no cambia si se genera nueva versión del informe."""
    db = TestingSessionLocal()
    try:
        admin = _admin(db)
        ch = _channel(db, admin.organization_id)
        channel_id = ch.id
        dest = admin.id
    finally:
        db.close()

    exp_res = client.post(
        "/api/evaluaciones",
        headers=auth_headers,
        json={"titulo": "Versiones informe", "entidad_nombre": "Entidad Versiones", "nivel": "PRELIMINAR"},
    )
    assert exp_res.status_code == 201, exp_res.text
    exp = exp_res.json()
    inf1 = client.post(
        "/api/resultados/informes/generar",
        headers=auth_headers,
        json={"expediente_id": exp["id"], "visibilidad": "VISIBLE_ENTIDAD"},
    ).json()
    entrega = client.post(
        f"/api/comunicaciones/informes/{inf1['id']}/entregar",
        headers=auth_headers,
        json={"channel_id": channel_id, "destinatario_tipo": "USUARIO", "destinatario_id": dest},
    ).json()
    v_entregada = entrega["entrega"]["informe_version"]

    inf2 = client.post(
        "/api/resultados/informes/generar",
        headers=auth_headers,
        json={"expediente_id": exp["id"], "visibilidad": "VISIBLE_ENTIDAD"},
    ).json()
    assert inf2["version"] > v_entregada

    hist = client.get(f"/api/comunicaciones/informes/entregas?informe_id={inf1['id']}", headers=auth_headers).json()
    assert hist[0]["informe_version"] == v_entregada


def test_regression_resultados_inteligencia(client: TestClient, auth_headers):
    """Regresión: bloque 1410 sigue operativo."""
    res = client.get("/api/resultados/antes-proyectado-real", headers=auth_headers)
    assert res.status_code == 200
