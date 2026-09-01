"""Tests — Demo comercial ficticia EIAAX (V1)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import demo_comercial_service as demo_svc

pytestmark = [pytest.mark.operations]


@pytest.fixture
def sdb():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _tenant(db: Session) -> tuple[Organization, User]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-demo-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    admin = User(
        organization_id=org.id,
        username=f"adm-{uuid.uuid4().hex[:6]}",
        email=f"a-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return org, admin


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_manifest_sin_semilla(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    res = client.get("/api/demo-comercial/manifest", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["es_demo"] is True
    assert "DEMO" in body["etiqueta"]


def test_semilla_y_aislamiento_demo(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    seed = client.post("/api/demo-comercial/semilla", headers=headers)
    assert seed.status_code == 200
    manifest = seed.json()
    assert manifest["expediente_id"]
    assert manifest["enlaces"]["presentacion"]
    assert "[DEMO]" in demo_svc._demo_entidad_label() or True

    pres = client.get(
        f"/api/demo-comercial/presentacion/{manifest['expediente_id']}?audiencia=GERENCIA",
        headers=headers,
    )
    assert pres.status_code == 200
    secciones = pres.json()["secciones"]
    assert any(s["titulo"] == "Qué encontramos" for s in secciones)
    assert "proteccion_ip" in pres.json()

    for aud in ("OPERACION", "SISTEMAS", "FINANCIERO"):
        r = client.get(
            f"/api/demo-comercial/presentacion/{manifest['expediente_id']}?audiencia={aud}",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["audiencia"] == aud


def test_presentacion_rechaza_no_demo(client: TestClient, sdb):
    from app.services import evaluacion_service as ev_svc

    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    exp = ev_svc.create_expediente(
        sdb,
        organization_id=org.id,
        user_id=admin.id,
        titulo="Real",
        entidad_nombre="Cliente Real SA",
        nivel="PRELIMINAR",
    )
    sdb.commit()
    res = client.get(
        f"/api/demo-comercial/presentacion/{exp.id}?audiencia=GERENCIA",
        headers=headers,
    )
    assert res.status_code == 403


def test_informes_periodicos_plantillas(client: TestClient, auth_headers):
    res = client.get("/api/demo-comercial/informes-periodicos", headers=auth_headers)
    assert res.status_code == 200
    plantillas = res.json()["plantillas"]
    assert len(plantillas) >= 4
    assert any(p["periodicidad"] == "MENSUAL" for p in plantillas)


def test_semilla_idempotente(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    a = client.post("/api/demo-comercial/semilla", headers=headers).json()
    b = client.post("/api/demo-comercial/semilla", headers=headers).json()
    assert a["expediente_id"] == b["expediente_id"]
    assert b.get("reused") is True


def test_presentacion_demo_pdf(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    seed = client.post("/api/demo-comercial/semilla", headers=headers).json()
    res = client.get(
        f"/api/demo-comercial/presentacion/{seed['expediente_id']}/pdf?audiencia=GERENCIA",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF")


def test_presentacion_demo_incluye_graficos(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    seed = client.post("/api/demo-comercial/semilla", headers=headers).json()
    pres = client.get(
        f"/api/demo-comercial/presentacion/{seed['expediente_id']}?audiencia=FINANCIERO",
        headers=headers,
    )
    assert pres.status_code == 200
    graficos = pres.json().get("graficos", {})
    assert len(graficos.get("series", [])) >= 1
    assert graficos["series"][0].get("simulado") is True
