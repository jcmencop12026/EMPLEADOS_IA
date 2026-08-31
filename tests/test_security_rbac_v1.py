"""Tests adversariales — hardening RBAC V1 (Paquete D)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jose import jwt

from app.config import settings
from app.models import Organization, Permission, Role, RolePermission, User
from app.permissions import user_permissions
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _create_limited_user(client, *, permission_codes: set[str]) -> tuple[str, str]:
    """Usuario con rol custom limitado; retorna (username, token)."""
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        org = Organization(name=f"Sec Org {uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        role_code = f"limited-{uuid.uuid4().hex[:6]}"
        role = Role(
            organization_id=org.id,
            code=role_code,
            name="Limited RBAC",
            is_system=False,
            is_active=True,
        )
        db.add(role)
        db.flush()
        for code in permission_codes:
            perm = db.query(Permission).filter(Permission.code == code).first()
            assert perm is not None, code
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        username = f"limited-{uuid.uuid4().hex[:6]}"
        password = "LimitedSec*"
        db.add(
            User(
                organization_id=org.id,
                username=username,
                password_hash=hash_password(password),
                role=role_code,
                status="ACTIVE",
                is_active=True,
            )
        )
        db.commit()
        user = db.query(User).filter(User.username == username).one()
        assert user_permissions(user, db) == permission_codes
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return username, login.json()["access_token"]


def _viewer_token(client) -> str:
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Viewer Org {uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        username = f"viewer-{uuid.uuid4().hex[:6]}"
        db.add(
            User(
                organization_id=org.id,
                username=username,
                password_hash=hash_password("ViewerSec*"),
                role="viewer",
                status="ACTIVE",
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": "ViewerSec*"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_limited_user_denied_audit_logs(client):
    _, token = _create_limited_user(client, permission_codes={"employee.view"})
    res = client.get("/api/audit/logs", headers=auth_header(token))
    assert res.status_code == 403
    assert "permiso" in res.json()["detail"].lower()


def test_limited_user_denied_assistant_execute(client):
    _, token = _create_limited_user(client, permission_codes={"employee.view"})
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "test rbac", "context": {}, "auto_execute": False},
    )
    assert res.status_code == 403


def test_limited_user_denied_coordinator_route(client):
    _, token = _create_limited_user(client, permission_codes={"employee.view"})
    res = client.post(
        "/api/agent-factory/coordinator/route",
        headers=auth_header(token),
        json={"request": "test rbac", "context": {}, "auto_execute": False},
    )
    assert res.status_code == 403


def test_viewer_denied_assistant_auto_execute(client):
    token = _viewer_token(client)
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "viewer test", "context": {"tool": "docint", "documents": []}, "auto_execute": True},
    )
    assert res.status_code == 403


def test_viewer_allowed_assistant_plan_only_when_execute_present(client):
    """Viewer tiene operations.view pero no operations.execute — plan sin ejecutar sigue bloqueado."""
    token = _viewer_token(client)
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "viewer plan", "context": {}, "auto_execute": False},
    )
    assert res.status_code == 403


def test_inactive_user_login_rejected(client):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Inactive Org {uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        username = f"inactive-{uuid.uuid4().hex[:6]}"
        db.add(
            User(
                organization_id=org.id,
                username=username,
                password_hash=hash_password("Inactive*"),
                role="viewer",
                status="INACTIVE",
                is_active=False,
            )
        )
        db.commit()
    finally:
        db.close()
    res = client.post("/api/auth/login", json={"username": username, "password": "Inactive*"})
    assert res.status_code == 401
    assert "inactivo" in res.json()["detail"].lower()


def test_expired_token_rejected(client, token):
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401


def test_operator_cannot_assign_admin_role(client, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        assert admin
        username_op = f"operator-{uuid.uuid4().hex[:6]}"
        operator = User(
            organization_id=admin.organization_id,
            username=username_op,
            password_hash=hash_password("Operator*"),
            role="operator",
            status="ACTIVE",
            is_active=True,
        )
        db.add(operator)
        db.commit()
    finally:
        db.close()
    login = client.post(
        "/api/auth/login",
        json={"username": username_op, "password": "Operator*"},
    )
    assert login.status_code == 200
    op_headers = auth_header(login.json()["access_token"])
    res = client.post(
        "/api/admin/users",
        headers=op_headers,
        json={
            "username": f"new-{uuid.uuid4().hex[:6]}",
            "password": "NewUser*",
            "role": "admin",
        },
    )
    assert res.status_code == 403


def test_create_user_rejects_or_ignores_organization_id_injection(client, auth_headers):
    foreign_org = str(uuid.uuid4())
    username = f"inj-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/admin/users",
        headers=auth_headers,
        json={
            "username": username,
            "password": "Inject01*",
            "role": "viewer",
            "organization_id": foreign_org,
        },
    )
    assert res.status_code in {201, 422}
    if res.status_code == 201:
        db = TestingSessionLocal()
        try:
            admin = db.query(User).filter(User.username == "admin").one()
            created = db.query(User).filter(User.username == username).one()
            assert created.organization_id == admin.organization_id
            assert created.organization_id != foreign_org
        finally:
            db.close()


def test_security_config_rejects_default_jwt_on_postgresql(monkeypatch):
    from app.security_config import validate_security_settings

    monkeypatch.delenv("ALLOW_INSECURE_DEV_DEFAULTS", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_security_settings(
            database_url="postgresql+psycopg2://u:p@localhost/db",
            jwt_secret="change-me-in-env-local-dev-only",
            bootstrap_admin_password="x",
        )


def test_security_config_allows_sqlite_default_jwt():
    from app.security_config import validate_security_settings

    validate_security_settings(
        database_url="sqlite:///tmp/test.db",
        jwt_secret="change-me-in-env-local-dev-only",
        bootstrap_admin_password="Admin2026*",
    )


def test_security_config_rejects_default_bootstrap_on_postgresql(monkeypatch):
    from app.security_config import DEFAULT_BOOTSTRAP_ADMIN_PASSWORD, validate_security_settings

    monkeypatch.delenv("ALLOW_INSECURE_DEV_DEFAULTS", raising=False)
    with pytest.raises(RuntimeError, match="BOOTSTRAP_ADMIN_PASSWORD"):
        validate_security_settings(
            database_url="postgresql+psycopg2://u:p@localhost/db",
            jwt_secret="a-secure-jwt-secret-with-enough-length-for-prod",
            bootstrap_admin_password=DEFAULT_BOOTSTRAP_ADMIN_PASSWORD,
        )


def test_security_config_rejects_short_jwt_on_postgresql(monkeypatch):
    from app.security_config import validate_security_settings

    monkeypatch.delenv("ALLOW_INSECURE_DEV_DEFAULTS", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET demasiado corto"):
        validate_security_settings(
            database_url="postgresql+psycopg2://u:p@localhost/db",
            jwt_secret="short-secret",
            bootstrap_admin_password="secure-bootstrap-password-2026",
        )


def test_security_config_rejects_wildcard_cors_in_production(monkeypatch):
    from app.security_config import validate_security_settings

    monkeypatch.delenv("ALLOW_INSECURE_DEV_DEFAULTS", raising=False)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_security_settings(
            database_url="postgresql+psycopg2://u:p@localhost/db",
            jwt_secret="a-secure-jwt-secret-with-enough-length-for-prod",
            bootstrap_admin_password="secure-bootstrap-password-2026",
            app_env="prod",
            cors_origins="*",
        )


def test_docker_compose_requires_bootstrap_password():
    compose_path = Path(__file__).resolve().parents[1] / "docker-compose.yml"
    content = compose_path.read_text(encoding="utf-8")
    assert "BOOTSTRAP_ADMIN_PASSWORD: ${BOOTSTRAP_ADMIN_PASSWORD:?" in content
    assert "Admin2026*" not in content
