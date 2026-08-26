"""CURSOR-840 — Administración empresarial V1."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.permissions import user_permissions
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _create_org_admin(db: Session, org_name: str, username: str | None = None, role: str = "admin") -> tuple[Organization, User, str]:
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    uname = username or f"admin-{uuid.uuid4().hex[:6]}"
    password = "Admin840*Test"
    user = User(
        organization_id=org.id,
        username=uname,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    login = None
    return org, user, password


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_auth_me_includes_permissions(client: TestClient, token):
    res = client.get("/api/auth/me", headers=auth_header(token))
    assert res.status_code == 200
    body = res.json()
    assert "admin.user.view" in body["permissions"]
    assert body["status"] == "ACTIVE"


def test_inactive_user_cannot_login(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_org_admin(db, "Inactive Org")
        user.status = "INACTIVE"
        user.is_active = False
        db.commit()
        username = user.username
    finally:
        db.close()
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 401


def test_admin_create_list_users(client: TestClient, token, auth_headers):
    res = client.post(
        "/api/admin/users",
        headers=auth_headers,
        json={
            "username": f"op-{uuid.uuid4().hex[:6]}",
            "password": "Operator840*",
            "role": "operator",
            "full_name": "Operador Demo",
            "email": "op@demo.local",
        },
    )
    assert res.status_code == 201
    assert res.json()["status"] == "ACTIVE"

    listed = client.get("/api/admin/users", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 2


def test_viewer_denied_admin_users(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_org_admin(db, "Viewer Org 840", role="viewer")
        username = user.username
    finally:
        db.close()
    token = _token(client, username, password)
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_cross_tenant_user_access_blocked(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b, user_b, _ = _create_org_admin(db, "Org B 840", username=f"userb-{uuid.uuid4().hex[:6]}")
        user_b_id = user_b.id
    finally:
        db.close()
    res = client.get(f"/api/admin/users/{user_b_id}", headers=auth_headers)
    assert res.status_code == 404


def test_cross_tenant_user_update_blocked(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        _, user_b, _ = _create_org_admin(db, "Org B upd 840")
        user_b_id = user_b.id
    finally:
        db.close()
    res = client.put(
        f"/api/admin/users/{user_b_id}",
        headers=auth_headers,
        json={"full_name": "Hack"},
    )
    assert res.status_code == 404


def test_cross_tenant_deactivate_blocked(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        _, user_b, _ = _create_org_admin(db, "Org B deact 840")
        user_b_id = user_b.id
    finally:
        db.close()
    res = client.post(
        f"/api/admin/users/{user_b_id}/status",
        headers=auth_headers,
        json={"status": "INACTIVE"},
    )
    assert res.status_code == 404


def test_roles_and_permission_matrix(client: TestClient, auth_headers):
    roles = client.get("/api/admin/roles", headers=auth_headers)
    assert roles.status_code == 200
    codes = {r["code"] for r in roles.json()}
    assert {"admin", "operator", "viewer"}.issubset(codes)

    matrix = client.get("/api/admin/roles/permission-matrix", headers=auth_headers)
    assert matrix.status_code == 200
    assert matrix.json()["permissions"]
    assert matrix.json()["matrix"]


def test_organization_get_and_update(client: TestClient, auth_headers):
    res = client.get("/api/admin/organization", headers=auth_headers)
    assert res.status_code == 200
    org_id = res.json()["id"]

    upd = client.put(
        "/api/admin/organization",
        headers=auth_headers,
        json={"name": "Empresa Actualizada 840", "timezone": "America/Bogota"},
    )
    assert upd.status_code == 200
    assert upd.json()["timezone"] == "America/Bogota"

    cross = client.put(
        "/api/admin/organization",
        headers=auth_headers,
        json={"name": "Otra"},
    )
    assert cross.json()["id"] == org_id


def test_cross_tenant_organization_blocked(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pass_a = _create_org_admin(db, "Org A iso 840", username=f"a-{uuid.uuid4().hex[:6]}")
        org_b, user_b, _ = _create_org_admin(db, "Org B iso 840", username=f"b-{uuid.uuid4().hex[:6]}")
        org_a_id = org_a.id
        token_a = _token(client, user_a.username, pass_a)
        user_b_id = user_b.id
        org_b_id = org_b.id
    finally:
        db.close()

    res = client.get(f"/api/admin/users/{user_b_id}", headers=auth_header(token_a))
    assert res.status_code == 404

    listed = client.get("/api/admin/users", headers=auth_header(token_a))
    ids = {u["id"] for u in listed.json()}
    assert user_b_id not in ids
    assert org_b_id != org_a_id


def test_config_get_update(client: TestClient, auth_headers):
    cfg = client.get("/api/admin/config", headers=auth_headers)
    assert cfg.status_code == 200
    assert cfg.json()["language"] == "es"

    upd = client.put(
        "/api/admin/config",
        headers=auth_headers,
        json={"date_format": "YYYY-MM-DD", "time_format": "12h"},
    )
    assert upd.status_code == 200
    assert upd.json()["date_format"] == "YYYY-MM-DD"


def test_invalid_timezone_rejected(client: TestClient, auth_headers):
    res = client.put(
        "/api/admin/organization",
        headers=auth_headers,
        json={"timezone": "Not/A_Real_Zone"},
    )
    assert res.status_code == 422


def test_security_summary(client: TestClient, auth_headers):
    res = client.get("/api/admin/security", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["users_active"] >= 1
    assert "recent_events" in body


def test_password_reset_audit_no_secret(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        listed = client.get("/api/admin/users", headers=auth_headers).json()
        target = next(u for u in listed if u["username"] != "admin")
        user_id = target["id"]
    finally:
        db.close()

    res = client.post(f"/api/admin/users/{user_id}/reset-password", headers=auth_headers, json={})
    assert res.status_code == 200
    assert "temporary_password" in res.json()
    assert len(res.json()["temporary_password"]) >= 8

    logs = client.get("/api/audit/logs", headers=auth_headers).json()
    reset_logs = [l for l in logs if l["action"] == "admin.user.password_reset"]
    assert reset_logs
    assert "temporary_password" not in (reset_logs[0].get("detail") or "")


def test_user_permissions_from_db(client: TestClient, token):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        perms = user_permissions(user, db)
        assert "admin.user.view" in perms
        assert "employee.view" in perms
    finally:
        db.close()


def test_alembic_head_840_present():
    from pathlib import Path

    versions = list((Path(__file__).resolve().parents[1] / "backend" / "alembic" / "versions").glob("*.py"))
    assert any("a840c4d5e6f7" in v.name for v in versions)
