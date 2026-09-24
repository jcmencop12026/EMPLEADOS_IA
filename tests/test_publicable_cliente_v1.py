"""Pruebas backend — Publicable cliente (V1) fail-closed."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User
from app.security import hash_password
from app.services import resultados_service as res_svc
from app.services.publicable_cliente_service import (
    FORBIDDEN_PAYLOAD_KEYS,
    assert_payload_publicable,
)
from conftest import TestingSessionLocal, auth_header


FORBIDDEN_IN_RESPONSE = FORBIDDEN_PAYLOAD_KEYS | {
    "prompt",
    "margen",
    "finops",
    "scoring",
    "costo_interno",
    "precio_sugerido",
    "notas_internas",
}


def _create_expediente(client: TestClient, headers: dict, **extra) -> dict:
    payload = {
        "titulo": extra.pop("titulo", "Eval publicable"),
        "entidad_nombre": extra.pop("entidad_nombre", "Empresa Publicable Test"),
        "nivel": "PRELIMINAR",
        **extra,
    }
    res = client.post("/api/evaluaciones", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def _admin_user_id() -> str:
    db = TestingSessionLocal()
    try:
        from app.config import settings

        user = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        assert user is not None
        return user.id
    finally:
        db.close()


def _collect_keys(obj: object, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            full = f"{prefix}.{k}" if prefix else str(k)
            keys.add(str(k).lower())
            keys.update(_collect_keys(v, full))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(_collect_keys(item, prefix))
    return keys


def test_publicable_cliente_endpoint_filtra_payload(client: TestClient, auth_headers: dict):
    exp = _create_expediente(client, auth_headers, entidad_nombre="Pub Cliente SA")
    res = client.get(f"/api/evaluaciones/{exp['id']}/informe-publicable-cliente", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("audiencia") == "PUBLICABLE_CLIENTE"
    payload_keys = _collect_keys(body)
    for key in FORBIDDEN_IN_RESPONSE:
        assert key not in payload_keys, f"Campo prohibido en publicable cliente: {key}"
    assert "valor_potencial" not in body
    assert_payload_publicable(body)


def test_publicable_cliente_aislamiento_org_b(client: TestClient, auth_headers: dict):
    exp = _create_expediente(client, auth_headers, entidad_nombre="Org A exclusiva pub")
    db = TestingSessionLocal()
    try:
        org_b = Organization(name="Org Pub B", slug=f"pub-b-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(org_b)
        db.flush()
        user_b = User(
            organization_id=org_b.id,
            username=f"pub_b_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("TestB2026!"),
            role="admin",
            is_active=True,
        )
        db.add(user_b)
        db.commit()
        login = client.post("/api/auth/login", json={"username": user_b.username, "password": "TestB2026!"})
        headers_b = auth_header(login.json()["access_token"])
    finally:
        db.close()

    forbidden = client.get(f"/api/evaluaciones/{exp['id']}/informe-publicable-cliente", headers=headers_b)
    assert forbidden.status_code in (403, 404)


def test_publicable_cliente_expediente_otra_org_no_filtra_por_id(client: TestClient, auth_headers: dict):
    """Cambiar ID de expediente no debe exponer datos de otra organización."""
    exp_a = _create_expediente(client, auth_headers, entidad_nombre="Exp A pub")
    db = TestingSessionLocal()
    try:
        org_b = Organization(name="Org Pub D", slug=f"pub-d-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(org_b)
        db.flush()
        user_b = User(
            organization_id=org_b.id,
            username=f"pub_d_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("TestD2026!"),
            role="admin",
            is_active=True,
        )
        db.add(user_b)
        db.commit()
        login = client.post("/api/auth/login", json={"username": user_b.username, "password": "TestD2026!"})
        headers_b = auth_header(login.json()["access_token"])
    finally:
        db.close()

    denied = client.get(f"/api/evaluaciones/{exp_a['id']}/informe-publicable-cliente", headers=headers_b)
    assert denied.status_code in (403, 404)
    if denied.status_code == 200:
        assert denied.json().get("expediente_id") != exp_a["id"]


def test_impacto_vista_entidad_requiere_permiso(client: TestClient, auth_headers: dict):
    exp = _create_expediente(client, auth_headers, entidad_nombre="Impacto vista entidad")
    ok = client.get(f"/api/evaluaciones/{exp['id']}/impacto?vista_entidad=true", headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json().get("valor_potencial") is None

    db = TestingSessionLocal()
    try:
        org = Organization(name="Org Pub C", slug=f"pub-c-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(org)
        db.flush()
        viewer = User(
            organization_id=org.id,
            username=f"pub_c_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("View2026!"),
            role="viewer",
            is_active=True,
        )
        db.add(viewer)
        db.commit()
        login = client.post("/api/auth/login", json={"username": viewer.username, "password": "View2026!"})
        headers_v = auth_header(login.json()["access_token"])
    finally:
        db.close()

    denied = client.get(f"/api/evaluaciones/{exp['id']}/impacto?vista_entidad=true", headers=headers_v)
    assert denied.status_code == 403


def test_informe_interno_no_en_publicable(client: TestClient, auth_headers: dict):
    """Informes INTERNO no deben aparecer en lista publicable."""
    exp = _create_expediente(client, auth_headers, entidad_nombre="Informes visibilidad")
    db = TestingSessionLocal()
    try:
        org_id = db.query(User).filter(User.username == "admin").first().organization_id
        user_id = _admin_user_id()
        res_svc.generate_informe_impacto(
            db, org_id, user_id, expediente_id=exp["id"], visibilidad="INTERNO",
        )
        res_svc.generate_informe_impacto(
            db, org_id, user_id, expediente_id=exp["id"], visibilidad="VISIBLE_ENTIDAD",
        )
        db.commit()
    finally:
        db.close()

    res = client.get(f"/api/evaluaciones/{exp['id']}/informe-publicable-cliente", headers=auth_headers)
    assert res.status_code == 200
    informes = res.json().get("informes_publicables") or []
    assert all(i.get("visibilidad") == "VISIBLE_ENTIDAD" for i in informes)
    assert len(informes) >= 1


def test_contenido_no_publicado_marca_aviso(client: TestClient, auth_headers: dict):
    """Expediente no publicado debe indicarlo sin exponer campos internos."""
    exp = _create_expediente(client, auth_headers, entidad_nombre="No publicado SA")
    res = client.get(f"/api/evaluaciones/{exp['id']}/informe-publicable-cliente", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body.get("publicado") is False
    assert body.get("aviso")
    assert_payload_publicable(body)


def test_permiso_insuficiente_rechaza_publicable(client: TestClient, auth_headers: dict):
    exp = _create_expediente(client, auth_headers, entidad_nombre="Permiso viewer")
    db = TestingSessionLocal()
    try:
        from app.config import settings

        org = db.query(Organization).filter(Organization.name == settings.bootstrap_org_name).first()
        viewer = User(
            organization_id=org.id,
            username=f"viewer_pub_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("ViewerPub2026!"),
            role="viewer",
            is_active=True,
        )
        db.add(viewer)
        db.commit()
        login = client.post("/api/auth/login", json={"username": viewer.username, "password": "ViewerPub2026!"})
        headers_v = auth_header(login.json()["access_token"])
    finally:
        db.close()

    denied = client.get(f"/api/evaluaciones/{exp['id']}/informe-publicable-cliente", headers=headers_v)
    assert denied.status_code == 403


def test_assert_payload_publicable_detecta_violaciones():
    with pytest.raises(Exception):
        assert_payload_publicable({"margen": 10, "audiencia": "PUBLICABLE_CLIENTE"})
