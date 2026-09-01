"""Centro de Control Estratégico V1 — tests RBAC, lecturas, privacidad."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, Permission, Role, RolePermission, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


def _create_user_with_permissions(client: TestClient, *, permission_codes: set[str]) -> str:
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        org = Organization(name=f"Strat-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        role = Role(organization_id=org.id, code=f"strat_{uuid.uuid4().hex[:6]}", name="Strat", is_system=False)
        db.add(role)
        db.flush()
        for code in permission_codes:
            perm = db.query(Permission).filter(Permission.code == code).first()
            assert perm is not None, code
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        username = f"stv_{uuid.uuid4().hex[:6]}"
        password = "testpass123"
        db.add(
            User(
                organization_id=org.id,
                username=username,
                password_hash=hash_password(password),
                role=role.code,
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_cockpit_estructura_y_lecturas(client: TestClient, auth_headers):
    res = client.get("/api/centro-estrategico/cockpit?lectura=resumen", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["mismo_dossier"] is True
    assert body["lectura_activa"] == "resumen"
    assert len(body["lecturas"]) == 5
    assert "separacion_mb08" in body
    assert body["enlaces"]["operacional_mb08"] == "/centro-control"


def test_lecturas_comparten_dossier(client: TestClient, auth_headers):
    org_ids = []
    dossier_ids = []
    for lectura in ("resumen", "gerencia", "financiero"):
        r = client.get(f"/api/centro-estrategico/cockpit?lectura={lectura}", headers=auth_headers).json()
        org_ids.append(r.get("organization_id"))
        dossier_ids.append(r.get("dossier_id"))
    assert org_ids[0] == org_ids[1] == org_ids[2]
    assert dossier_ids[0] == dossier_ids[1] == dossier_ids[2]


def test_modo_comite(client: TestClient, auth_headers):
    res = client.get("/api/centro-estrategico/cockpit?modo_comite=true", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["modo_comite"] is True
    assert "lecturas_preview" in res.json()


def test_semantica_antes_proyectado_real(client: TestClient, auth_headers):
    res = client.get("/api/centro-estrategico/lecturas", headers=auth_headers)
    assert res.status_code == 200
    sem = res.json()["semantica"]
    assert "PROYECTADO" in sem
    assert "REAL" in sem
    assert "realizado" in sem["nota"].lower() or "proyectado" in sem["nota"].lower()


def test_economia_privada_restringida_sin_permiso(client: TestClient, token):
    """Viewer sin economia_privada no ve bloque interno."""
    tok = _create_user_with_permissions(
        client,
        permission_codes={"strategic_control.view", "transformacion.view"},
    )

    fin = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok)).json()
    eco = fin["contenido"].get("economia_privada", {})
    assert eco.get("restringido") is True or eco.get("visible_interno") is False


def test_multitenant_aislamiento(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b = Organization(name=f"StratB-{uuid.uuid4().hex[:6]}")
        db.add(org_b)
        db.flush()
        user_b = User(
            organization_id=org_b.id,
            username=f"stb_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("testpass123"),
            role="admin",
            is_active=True,
        )
        db.add(user_b)
        db.commit()
        tok_b = client.post("/api/auth/login", json={"username": user_b.username, "password": "testpass123"}).json()["access_token"]
    finally:
        db.close()

    org_a = client.get("/api/centro-estrategico/cockpit", headers=auth_headers).json()["organization_id"]
    org_b_res = client.get("/api/centro-estrategico/cockpit", headers=auth_header(tok_b)).json()["organization_id"]
    assert org_a != org_b_res


def test_sin_permiso_denegado(client: TestClient, token):
    tok = _create_user_with_permissions(client, permission_codes={"employee.view"})

    denied = client.get("/api/centro-estrategico/cockpit", headers=auth_header(tok))
    assert denied.status_code in (403, 401)


def test_mb08_no_sustituido(client: TestClient, auth_headers):
    """MB-08 operacional sigue disponible en ruta separada."""
    ops = client.get("/api/centro-control/operacional", headers=auth_headers)
    strat = client.get("/api/centro-estrategico/cockpit", headers=auth_headers)
    assert ops.status_code == 200
    assert strat.status_code == 200
    assert "fuerza_laboral" in ops.json()
    assert "fuerza_laboral" not in strat.json()
