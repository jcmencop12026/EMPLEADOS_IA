"""P0-A — Autenticación: bloqueo, revocación de sesión y permisos auditor."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.permissions import user_permissions
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def test_login_valid_and_invalid(client: TestClient):
    ok = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    bad = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})
    assert bad.status_code == 401


def test_unauthenticated_access_denied(client: TestClient):
    res = client.get("/api/admin/users")
    assert res.status_code == 401


def test_logout_revokes_token(client: TestClient):
    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    token = login.json()["access_token"]
    headers = auth_header(token)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_insufficient_role_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        admin = db.query(User).filter(User.username == "admin").first()
        assert admin
        auditor = User(
            organization_id=admin.organization_id,
            username=f"aud-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("AuditorP0*"),
            role="auditor",
            status="ACTIVE",
            is_active=True,
        )
        db.add(auditor)
        db.commit()
        perms = user_permissions(auditor, db)
        assert "admin.user.create" not in perms
        assert "audit.view" in perms
    finally:
        db.close()

    token = client.post(
        "/api/auth/login",
        json={"username": auditor.username, "password": "AuditorP0*"},
    ).json()["access_token"]
    denied = client.post(
        "/api/admin/users",
        headers=auth_header(token),
        json={"username": "x", "password": "Y", "role": "viewer"},
    )
    assert denied.status_code == 403
    allowed = client.get("/api/audit/logs", headers=auth_header(token))
    assert allowed.status_code == 200


def test_account_lockout_after_failed_attempts(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "login_max_failed_attempts", 3)
    monkeypatch.setattr(settings, "login_lockout_minutes", 30)
    db = TestingSessionLocal()
    username = f"lock-{uuid.uuid4().hex[:8]}"
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        assert admin
        victim = User(
            organization_id=admin.organization_id,
            username=username,
            password_hash=hash_password("LockVictim*1"),
            role="viewer",
            status="ACTIVE",
            is_active=True,
        )
        db.add(victim)
        db.commit()
    finally:
        db.close()
    for _ in range(3):
        res = client.post("/api/auth/login", json={"username": username, "password": "bad"})
        assert res.status_code == 401
    locked = client.post("/api/auth/login", json={"username": username, "password": "LockVictim*1"})
    assert locked.status_code == 401
    assert "bloqueado" in locked.json()["detail"].lower()


def test_password_reset_invalidates_sessions(client: TestClient, auth_headers):
    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    old_token = login.json()["access_token"]
    users = client.get("/api/admin/users", headers=auth_headers).json()
    admin_row = next(u for u in users if u["username"] == "admin")
    client.post(
        f"/api/admin/users/{admin_row['id']}/reset-password",
        headers=auth_headers,
        json={"new_password": "ResetP0NewPass*"},
    )
    assert client.get("/api/auth/me", headers=auth_header(old_token)).status_code == 401
    fresh = client.post("/api/auth/login", json={"username": "admin", "password": "ResetP0NewPass*"})
    assert fresh.status_code == 200
    # Restaurar contraseña bootstrap para otros tests en la misma sesión
    client.post(
        f"/api/admin/users/{admin_row['id']}/reset-password",
        headers=auth_header(fresh.json()["access_token"]),
        json={"new_password": "Admin2026*"},
    )


def test_users_survive_service_restart(client: TestClient):
    db = TestingSessionLocal()
    try:
        count_before = db.query(User).count()
    finally:
        db.close()
    assert count_before >= 1
    from app.seed import bootstrap

    db2 = TestingSessionLocal()
    try:
        bootstrap(db2)
        count_after = db2.query(User).count()
    finally:
        db2.close()
    assert count_after >= count_before
