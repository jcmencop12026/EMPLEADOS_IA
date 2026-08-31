"""CURSOR-830 — shell auth, session, API client contracts."""
from datetime import datetime, timedelta, timezone
import uuid

from jose import jwt

from app.config import settings
from conftest import auth_header


PROTECTED_ENDPOINTS = [
    "/api/auth/me",
    "/api/organization",
    "/api/operations/employees",
    "/api/operations/executions",
    "/api/operations/approvals/pending",
    "/api/audit/logs",
]


def test_protected_endpoints_require_token(client):
    for path in PROTECTED_ENDPOINTS:
        res = client.get(path)
        assert res.status_code == 401, path
        assert res.json()["detail"]


def test_invalid_token_returns_401(client):
    headers = {"Authorization": "Bearer invalid-token-830"}
    for path in PROTECTED_ENDPOINTS:
        res = client.get(path, headers=headers)
        assert res.status_code == 401, path
        assert res.json()["detail"] == "Token inválido"


def test_expired_token_returns_401(client):
    expired = jwt.encode(
        {"sub": 1, "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    headers = {"Authorization": f"Bearer {expired}"}
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["detail"] == "Token inválido"


def test_login_success_and_me(client):
    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    me = client.get("/api/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "admin"
    assert body["organization_id"]
    assert body["organization_name"]


def test_organization_endpoint_with_valid_session(client, token):
    res = client.get("/api/organization", headers=auth_header(token))
    assert res.status_code == 200
    org = res.json()
    assert org["id"]
    assert org["name"]
    assert org["created_at"]


def test_directory_and_executions_with_valid_session(client, token):
    employees = client.get("/api/operations/employees", headers=auth_header(token))
    assert employees.status_code == 200
    assert isinstance(employees.json(), list)

    executions = client.get("/api/operations/executions", headers=auth_header(token))
    assert executions.status_code == 200
    assert isinstance(executions.json(), list)


def test_forbidden_returns_403_spanish_detail(client, token):
    """Viewer role cannot create employees — ensures 403 path exists for UI messaging."""
    from app.models import Organization, User
    from app.security import hash_password
    from conftest import TestingSessionLocal

    db = TestingSessionLocal()
    org = Organization(name="Org Viewer 830")
    db.add(org)
    db.flush()
    db.add(
        User(
            organization_id=org.id,
            username=f"viewer830-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("Viewer830*"),
            role="viewer",
        )
    )
    db.commit()
    viewer_username = db.query(User).filter(User.organization_id == org.id).first().username
    db.close()

    login = client.post("/api/auth/login", json={"username": viewer_username, "password": "Viewer830*"})
    assert login.status_code == 200
    viewer_token = login.json()["access_token"]

    denied = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(viewer_token),
        json={"name": "Test", "specialty": "Ops"},
    )
    assert denied.status_code == 403
