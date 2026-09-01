"""Pruebas Bloque C1 — base segura convergencia V1+V2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "backend" / "alembic" / "migration_ledger.json"
MAIN_PY = ROOT / "backend" / "app" / "main.py"

V2_HEAD = "1341a1b2c3d4e"
V1_HEAD = "d1e2f3a4b5c6"


def _second_org_token(client: TestClient) -> str:
    db = TestingSessionLocal()
    org = Organization(name="Org C1 B", slug="org-c1-b")
    db.add(org)
    db.flush()
    db.add(
        User(
            organization_id=org.id,
            username="user_c1_b",
            password_hash=hash_password("TenantC1B*Test"),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
    )
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": "user_c1_b", "password": "TenantC1B*Test"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_alembic_single_head_c1():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["baseline_head"] == V2_HEAD
    assert V2_HEAD in data["protected_revisions"]
    assert V1_HEAD in data["protected_revisions"]


def test_v2_routers_preserved_after_c1():
    src = MAIN_PY.read_text(encoding="utf-8")
    for marker in (
        "control_center.router",
        "comunicaciones.router",
        "trabajo.router",
        "security.router",
        "identidad.router",
        "scim.router",
    ):
        assert marker in src, f"router V2 perdido: {marker}"


def test_knowledge_download_requires_auth(client: TestClient, token: str):
    created = client.post(
        "/api/knowledge/text",
        headers=auth_header(token),
        json={"name": "C1 doc", "content": "contenido"},
    )
    assert created.status_code == 201
    doc_id = created.json()["id"]
    denied = client.get(f"/api/knowledge/{doc_id}/download")
    assert denied.status_code == 401
    ok = client.get(f"/api/knowledge/{doc_id}/download", headers=auth_header(token))
    assert ok.status_code == 200


def test_multitenant_org_isolation_still_enforced(client: TestClient, token: str):
    me_a = client.get("/api/auth/me", headers=auth_header(token)).json()
    token_b = _second_org_token(client)
    me_b = client.get("/api/auth/me", headers=auth_header(token_b)).json()
    assert me_a["organization_id"] != me_b["organization_id"]

    created = client.post(
        "/api/knowledge/text",
        headers=auth_header(token),
        json={"name": "Org A only", "content": "x"},
    )
    doc_id = created.json()["id"]
    denied = client.get(f"/api/knowledge/{doc_id}/download", headers=auth_header(token_b))
    assert denied.status_code in (403, 404)


def test_auth_me_returns_permissions(client: TestClient, token: str):
    me = client.get("/api/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    body = me.json()
    assert body["role"] == "superadmin"
    assert isinstance(body["permissions"], list)
    assert len(body["permissions"]) > 0
