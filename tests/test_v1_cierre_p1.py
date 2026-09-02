"""Cierre P1 V1 — identidad E2E, entitlements RBAC y multiempresa."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations, pytest.mark.tenant]


def _admin_token(client: TestClient) -> tuple[str, str]:
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        org = Organization(name=f"V1P1-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        username = f"admin-{uuid.uuid4().hex[:6]}"
        password = "AdminV1P1*Pass"
        db.add(
            User(
                organization_id=org.id,
                username=username,
                password_hash=hash_password(password),
                role="admin",
                status="ACTIVE",
                is_active=True,
            )
        )
        db.commit()
        org_id = org.id
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    return org_id, login.json()["access_token"]


def _viewer_token(client: TestClient, org_id: str) -> str:
    db = TestingSessionLocal()
    try:
        username = f"viewer-{uuid.uuid4().hex[:6]}"
        password = "ViewerV1P1*Pass"
        db.add(
            User(
                organization_id=org_id,
                username=username,
                password_hash=hash_password(password),
                role="viewer",
                status="ACTIVE",
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def test_identity_branding_persists_across_reads(client: TestClient, auth_headers):
    """Identidad empresarial: guardar → releer → persiste."""
    payload = {
        "enterprise_display_name": "Empresa Persistente V1",
        "enterprise_logo_url": "https://cdn.test/logo.svg",
        "enterprise_logo_compact_url": "https://cdn.test/logo-sm.svg",
        "enterprise_accent_color": "#0f766e",
    }
    put = client.put("/api/admin/config", headers=auth_headers, json=payload)
    assert put.status_code == 200, put.text
    body = put.json()
    assert body["enterprise_display_name"] == payload["enterprise_display_name"]
    assert body["enterprise_logo_url"] == payload["enterprise_logo_url"]
    assert body["enterprise_logo_compact_url"] == payload["enterprise_logo_compact_url"]

    get1 = client.get("/api/admin/config", headers=auth_headers)
    assert get1.status_code == 200
    assert get1.json()["enterprise_display_name"] == payload["enterprise_display_name"]

    get2 = client.get("/api/admin/config", headers=auth_headers)
    assert get2.status_code == 200
    reread = get2.json()
    assert reread["enterprise_display_name"] == payload["enterprise_display_name"]
    assert reread["enterprise_logo_url"] == payload["enterprise_logo_url"]
    assert reread["enterprise_accent_color"] == payload["enterprise_accent_color"]


def test_entitlements_viewer_denied_espacio_externo_publish(client: TestClient):
    """Capacidad deshabilitada: viewer no puede publicar a empresa."""
    org_id, admin_token = _admin_token(client)
    viewer_token = _viewer_token(client, org_id)

    exp = client.post(
        "/api/evaluaciones",
        headers=auth_header(admin_token),
        json={"titulo": "Exp pub", "entidad_nombre": "Ent A", "nivel": "PRELIMINAR"},
    )
    assert exp.status_code == 201
    expediente_id = exp.json()["id"]

    ent = client.post(
        "/api/espacio-externo/entidades",
        headers=auth_header(admin_token),
        json={"expediente_id": expediente_id},
    )
    assert ent.status_code == 201
    detail = client.get(
        f"/api/espacio-externo/entidades/{ent.json()['entidad']['id']}",
        headers=auth_header(admin_token),
    )
    pub_id = detail.json()["publicaciones"][0]["id"]

    denied = client.patch(
        f"/api/espacio-externo/publicaciones/{pub_id}/estado",
        headers=auth_header(viewer_token),
        json={"estado": "PUBLICADO_EMPRESA", "destinatario": "x@test", "motivo": "no"},
    )
    assert denied.status_code == 403


def test_entitlements_viewer_denied_evaluacion_access(client: TestClient):
    """Viewer sin evaluacion.view no accede a expedientes."""
    org_id, admin_token = _admin_token(client)
    viewer_token = _viewer_token(client, org_id)

    create = client.post(
        "/api/evaluaciones",
        headers=auth_header(admin_token),
        json={"titulo": "Exp V1", "entidad_nombre": "Ent A", "nivel": "PRELIMINAR"},
    )
    assert create.status_code == 201

    list_denied = client.get("/api/evaluaciones", headers=auth_header(viewer_token))
    assert list_denied.status_code == 403


def test_entitlements_viewer_denied_evaluacion_manage(client: TestClient):
    """Viewer no puede gestionar evaluaciones."""
    org_id, admin_token = _admin_token(client)
    viewer_token = _viewer_token(client, org_id)

    create = client.post(
        "/api/evaluaciones",
        headers=auth_header(admin_token),
        json={"titulo": "Exp V1", "entidad_nombre": "Ent A", "nivel": "PRELIMINAR"},
    )
    assert create.status_code == 201
    exp_id = create.json()["id"]

    denied = client.patch(
        f"/api/evaluaciones/{exp_id}",
        headers=auth_header(viewer_token),
        json={"titulo": "Intento no autorizado"},
    )
    assert denied.status_code in (403, 404)


def test_multiempresa_evaluacion_aislamiento(client: TestClient):
    """Empresa A no puede leer expediente de empresa B."""
    _, token_a = _admin_token(client)
    _, token_b = _admin_token(client)

    exp_a = client.post(
        "/api/evaluaciones",
        headers=auth_header(token_a),
        json={"titulo": "Privado A", "entidad_nombre": "Org A", "nivel": "PRELIMINAR"},
    )
    assert exp_a.status_code == 201
    exp_id = exp_a.json()["id"]

    cross = client.get(f"/api/evaluaciones/{exp_id}", headers=auth_header(token_b))
    assert cross.status_code == 404


def test_publicacion_estados_espacio_externo(client: TestClient, auth_headers):
    """Flujo publicación: privado → preparado → publicado."""
    exp = client.post(
        "/api/evaluaciones",
        headers=auth_headers,
        json={"titulo": "Pub V1", "entidad_nombre": "Cliente Ext", "nivel": "PRELIMINAR"},
    )
    assert exp.status_code == 201
    expediente_id = exp.json()["id"]

    ent = client.post(
        "/api/espacio-externo/entidades",
        headers=auth_headers,
        json={"expediente_id": expediente_id},
    )
    assert ent.status_code == 201, ent.text
    entidad_id = ent.json()["entidad"]["id"]

    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers)
    assert detail.status_code == 200
    pubs = detail.json().get("publicaciones") or []
    assert len(pubs) >= 1
    pub_id = pubs[0]["id"]

    prep = client.patch(
        f"/api/espacio-externo/publicaciones/{pub_id}/estado",
        headers=auth_headers,
        json={"estado": "PREPARADO_PRESENTAR", "destinatario": "admin@test", "motivo": "V1 prep"},
    )
    assert prep.status_code == 200, prep.text
    assert prep.json()["estado"] == "PREPARADO_PRESENTAR"

    pub = client.patch(
        f"/api/espacio-externo/publicaciones/{pub_id}/estado",
        headers=auth_headers,
        json={"estado": "PUBLICADO_EMPRESA", "destinatario": "admin@test", "motivo": "V1 pub"},
    )
    assert pub.status_code == 200, pub.text
    assert pub.json()["estado"] == "PUBLICADO_EMPRESA"
