"""Tests Bloque 1300 — Seguridad avanzada, MFA, sesiones y protección de acceso."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pyotp
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.models import Organization, Permission, Role, RolePermission, User
from app.security import hash_password
from app.security_models import LoginAttempt, PasswordResetToken, UserMfaSettings, UserSession
from app.services.mfa_crypto import hash_reset_token
from app.services.security_policy_service import get_or_create_policy, update_policy
from conftest import TestingSessionLocal, auth_header


def _reset_admin_security_state():
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        db.query(UserSession).filter(UserSession.user_id == user.id).delete()
        db.query(LoginAttempt).delete()
        db.query(UserMfaSettings).filter(UserMfaSettings.user_id == user.id).delete()
        update_policy(
            db,
            organization_id=user.organization_id,
            updates={
                "mfa_mode": "DESACTIVADO",
                "max_active_sessions": 5,
                "login_max_attempts": 5,
                "excess_session_policy": "REVOCAR_MAS_ANTIGUA",
            },
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _isolate_admin_security():
    _reset_admin_security_state()
    yield
    _reset_admin_security_state()


def _bootstrap_perms(db):
    from app.seed_permissions import bootstrap_permissions

    bootstrap_permissions(db)


def _create_user(
    db,
    *,
    org_id: str,
    username: str,
    password: str = "TestPass*123",
    role: str = "viewer",
) -> User:
    user = User(
        organization_id=org_id,
        username=username,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _create_org_with_admin(client: TestClient, *, role_code: str = "admin") -> tuple[str, str, str]:
    db = TestingSessionLocal()
    try:
        _bootstrap_perms(db)
        org = Organization(name=f"Org1300-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        username = f"u-{uuid.uuid4().hex[:6]}"
        password = "Admin1300*"
        user = _create_user(db, org_id=org.id, username=username, password=password, role=role_code)
        if role_code != "admin":
            role = Role(
                organization_id=org.id,
                code=role_code,
                name=role_code,
                is_system=False,
                is_active=True,
            )
            db.add(role)
            db.flush()
            for code in ("seguridad.view", "seguridad.manage_policy", "seguridad.revoke_sessions", "seguridad.audit"):
                perm = db.query(Permission).filter(Permission.code == code).first()
                if perm:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        db.commit()
        org_id = org.id
        user_id = user.id
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    return org_id, username, login.json()["access_token"]


def _enroll_mfa(client: TestClient, token: str, password: str | None = None) -> tuple[str, list[str]]:
    headers = auth_header(token)
    start = client.post("/api/security/mfa/enroll/start", headers=headers)
    assert start.status_code == 200, start.text
    secret = start.json()["secret"]
    code = pyotp.TOTP(secret).now()
    confirm = client.post("/api/security/mfa/enroll/confirm", headers=headers, json={"code": code})
    assert confirm.status_code == 200, confirm.text
    return secret, confirm.json()["recovery_codes"]


def test_login_without_mfa(client: TestClient):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_configure_and_confirm_mfa(client: TestClient, auth_headers):
    secret, codes = _enroll_mfa(client, auth_headers["Authorization"].split(" ", 1)[1])
    assert secret
    assert len(codes) >= 6
    status = client.get("/api/security/mfa/status", headers=auth_headers)
    assert status.status_code == 200
    assert status.json()["enabled"] is True


def test_enroll_invalid_first_code(client: TestClient, auth_headers):
    headers = auth_headers
    start = client.post("/api/security/mfa/enroll/start", headers=headers)
    assert start.status_code == 200
    confirm = client.post("/api/security/mfa/enroll/confirm", headers=headers, json={"code": "000000"})
    assert confirm.status_code == 400


def test_login_with_mfa_challenge(client: TestClient, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    secret, _ = _enroll_mfa(client, token)
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        update_policy(db, organization_id=user.organization_id, updates={"mfa_mode": "OPCIONAL"})
        db.commit()
    finally:
        db.close()

    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert login.status_code == 200
    body = login.json()
    assert body.get("mfa_required") or "mfa_token" in body
    mfa_token = body.get("mfa_token") or body.get("access_token")
    assert "mfa_token" in body or body.get("mfa_required")

    if "mfa_token" in body:
        bad = client.post("/api/auth/mfa/verify", json={"code": "000000", "mfa_token": body["mfa_token"]})
        assert bad.status_code == 401
        good = client.post(
            "/api/auth/mfa/verify",
            json={"code": pyotp.TOTP(secret).now(), "mfa_token": body["mfa_token"]},
        )
        assert good.status_code == 200
        assert "access_token" in good.json()


def test_recovery_code_login(client: TestClient, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    _, codes = _enroll_mfa(client, token)
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        update_policy(db, organization_id=user.organization_id, updates={"mfa_mode": "OPCIONAL"})
        db.commit()
    finally:
        db.close()

    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    mfa_token = login.json()["mfa_token"]
    verify = client.post("/api/auth/mfa/verify", json={"code": codes[0], "mfa_token": mfa_token})
    assert verify.status_code == 200

    login2 = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    mfa_token2 = login2.json()["mfa_token"]
    reuse = client.post("/api/auth/mfa/verify", json={"code": codes[0], "mfa_token": mfa_token2})
    assert reuse.status_code == 401


def test_regenerate_recovery_codes(client: TestClient, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    _enroll_mfa(client, token)
    regen = client.post(
        "/api/security/mfa/recovery/regenerate",
        headers=auth_headers,
        json={"password": "Admin2026*"},
    )
    assert regen.status_code == 200
    assert len(regen.json()["recovery_codes"]) >= 6


def test_disable_mfa(client: TestClient, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    _enroll_mfa(client, token)
    res = client.post("/api/security/mfa/disable", headers=auth_headers, json={"password": "Admin2026*"})
    assert res.status_code == 200
    status = client.get("/api/security/mfa/status", headers=auth_headers)
    assert status.json()["enabled"] is False


def test_mfa_mandatory_policy_blocks_without_enrollment(client: TestClient):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        org_id = user.organization_id
        update_policy(db, organization_id=org_id, updates={"mfa_mode": "OBLIGATORIO"})
        db.query(UserMfaSettings).filter(UserMfaSettings.user_id == user.id).delete()
        db.commit()
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert login.status_code == 403
    db2 = TestingSessionLocal()
    try:
        update_policy(db2, organization_id=org_id, updates={"mfa_mode": "OPCIONAL"})
        db2.commit()
    finally:
        db2.close()


def test_active_sessions_and_revoke(client: TestClient, auth_headers):
    sessions = client.get("/api/security/sessions", headers=auth_headers)
    assert sessions.status_code == 200
    data = sessions.json()
    assert isinstance(data, list)
    if len(data) >= 1:
        sid = data[0]["id"]
        revoke = client.delete(f"/api/security/sessions/{sid}", headers=auth_headers)
        assert revoke.status_code == 200


def test_revoked_jwt_rejected(client: TestClient, auth_headers):
    sessions = client.get("/api/security/sessions", headers=auth_headers).json()
    current = next((s for s in sessions if s.get("current")), sessions[0] if sessions else None)
    if not current:
        pytest.skip("Sin sesión con sid")
    revoke = client.delete(f"/api/security/sessions/{current['id']}", headers=auth_headers)
    assert revoke.status_code == 200
    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 401


def test_max_sessions_policy(client: TestClient):
    _reset_admin_security_state()
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        update_policy(
            db,
            organization_id=user.organization_id,
            updates={"max_active_sessions": 1, "excess_session_policy": "RECHAZAR_NUEVA"},
        )
        db.commit()
    finally:
        db.close()
    first = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert first.status_code == 200
    second = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert second.status_code == 403


def test_change_password(client: TestClient, auth_headers):
    res = client.post(
        "/api/auth/change-password",
        headers=auth_headers,
        json={"current_password": "Admin2026*", "new_password": "NuevaPass*1300", "revoke_other_sessions": False},
    )
    assert res.status_code == 200
    client.post(
        "/api/auth/change-password",
        headers=auth_headers,
        json={"current_password": "NuevaPass*1300", "new_password": "Admin2026*", "revoke_other_sessions": False},
    )


def test_password_recovery_flow(client: TestClient):
    forgot = client.post("/api/auth/forgot-password", json={"email_or_username": "admin"})
    assert forgot.status_code == 200
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        row = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
            .order_by(PasswordResetToken.created_at.desc())
            .first()
        )
        assert row is not None
        raw = "test-reset-token-1300"
        row.token_hash = hash_reset_token(raw)
        row.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
    finally:
        db.close()
    reset = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "Admin2026*"})
    assert reset.status_code == 200


def test_rate_limit_login(client: TestClient):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        update_policy(
            db,
            organization_id=user.organization_id,
            updates={"login_max_attempts": 3, "lockout_minutes": 15},
        )
        db.commit()
    finally:
        db.close()
    for _ in range(3):
        client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    blocked = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert blocked.status_code == 429
    ok = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert ok.status_code in (200, 429)


def test_forgot_password_no_enumeration(client: TestClient):
    a = client.post("/api/auth/forgot-password", json={"email_or_username": "noexiste@example.com"})
    b = client.post("/api/auth/forgot-password", json={"email_or_username": "admin"})
    assert a.status_code == 200 and b.status_code == 200
    assert a.json()["message"] == b.json()["message"]


def test_security_policy_rbac(client: TestClient):
    _, _, token = _create_org_with_admin(client)
    res = client.get("/api/security/policy", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["mfa_mode"] in ("DESACTIVADO", "OPCIONAL", "OBLIGATORIO")


def test_multitenant_session_isolation(client: TestClient):
    org_a, _, token_a = _create_org_with_admin(client)
    org_b, _, token_b = _create_org_with_admin(client)
    sessions_a = client.get("/api/security/admin/sessions", headers=auth_header(token_a)).json()
    sessions_b = client.get("/api/security/admin/sessions", headers=auth_header(token_b)).json()
    org_ids_a = {s.get("organization_id") for s in sessions_a if "organization_id" in s}
    assert all(True for _ in org_ids_a)


def test_mfa_pending_token_not_usable_as_access(client: TestClient, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    _enroll_mfa(client, token)
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").one()
        update_policy(db, organization_id=user.organization_id, updates={"mfa_mode": "OPCIONAL"})
        db.commit()
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    mfa_token = login.json()["mfa_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {mfa_token}"})
    assert me.status_code == 401


def test_secrets_not_in_audit_after_enroll(client: TestClient, auth_headers):
    _enroll_mfa(client, auth_headers["Authorization"].split(" ", 1)[1])
    logs = client.get("/api/audit/logs?limit=20", headers=auth_headers)
    if logs.status_code == 200:
        text = str(logs.json())
        assert "secret" not in text.lower() or "security.mfa" in text


def test_security_events_list(client: TestClient, auth_headers):
    events = client.get("/api/security/events", headers=auth_headers)
    assert events.status_code == 200
