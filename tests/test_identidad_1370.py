"""Tests Bloque 1370 — Identidad empresarial, SSO, OIDC y SAML."""

from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.identity_enums import AuthMode, IdPStatus, IdPType
from app.identity_models import OrganizationIdentitySettings, UserExternalIdentity
from app.models import Organization, User
from app.security import hash_password
from app.services.saml_xml import XmlSecurityError, safe_parse_xml
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _bootstrap(db: Session):
    from app.seed_permissions import bootstrap_permissions
    bootstrap_permissions(db)


def _create_org_admin(client: TestClient, *, role: str = "admin") -> tuple[str, str, str, str]:
    db = TestingSessionLocal()
    try:
        _bootstrap(db)
        org = Organization(name=f"Org1370-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        username = f"u-{uuid.uuid4().hex[:6]}"
        password = "Test1370*Pass"
        user = User(
            organization_id=org.id,
            username=username,
            password_hash=hash_password(password),
            role=role,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        settings = OrganizationIdentitySettings(
            organization_id=org.id,
            org_discovery_code=f"org-{uuid.uuid4().hex[:4]}",
        )
        db.add(settings)
        db.commit()
        org_id = org.id
        discovery = settings.org_discovery_code
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    return org_id, username, password, login.json()["access_token"], discovery


def _oidc_config(*, issuer: str = "https://idp.mock.test", client_id: str = "client-1370") -> dict:
    secret = "test-oidc-hmac-secret-1370"
    return {
        "issuer": issuer,
        "client_id": client_id,
        "redirect_uri": "http://testserver/api/identidad/oidc/callback",
        "mock_discovery": {
            "issuer": issuer,
            "authorization_endpoint": "https://idp.mock.test/authorize",
            "token_endpoint": "https://idp.mock.test/token",
            "jwks_uri": "https://idp.mock.test/jwks",
        },
        "mock_hmac_secret": secret,
        "mock_tokens": {
            "good-code": {"id_token": None},
        },
    }


def _make_id_token(config: dict, *, sub: str = "ext-sub-1", nonce: str | None = None, expired: bool = False) -> str:
    secret = config["mock_hmac_secret"]
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    claims = {
        "sub": sub,
        "iss": config["issuer"],
        "aud": config["client_id"],
        "exp": int(exp.timestamp()),
        "email": "user@corp.test",
        "given_name": "Ana",
        "family_name": "Prueba",
        "groups": ["equipo-ops"],
    }
    if nonce:
        claims["nonce"] = nonce
    return jwt.encode(claims, secret, algorithm="HS256")


def _create_oidc_provider(client: TestClient, headers: dict, config: dict | None = None) -> dict:
    cfg = config or _oidc_config()
    res = client.post(
        "/api/identidad/proveedores",
        headers=headers,
        json={
            "code": f"oidc-{uuid.uuid4().hex[:4]}",
            "name": "IdP Mock OIDC",
            "provider_type": IdPType.OIDC,
            "config": cfg,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_oidc_discovery_and_test(client: TestClient):
    _, _, _, token, _discovery = _create_org_admin(client)
    headers = auth_header(token)
    provider = _create_oidc_provider(client, headers)
    test = client.post(f"/api/identidad/proveedores/{provider['id']}/probar", headers=headers)
    assert test.status_code == 200
    assert test.json()["resultado"] == "EXITOSA"


def test_oidc_authorization_code_flow(client: TestClient):
    org_id, username, password, token, discovery = _create_org_admin(client)
    headers = auth_header(token)
    config = _oidc_config()
    provider = _create_oidc_provider(client, headers, config)
    client.put("/api/identidad/politica", headers=headers, json={
        "auth_mode": AuthMode.LOCAL_Y_SSO,
        "auto_provision_enabled": True,
        "org_discovery_code": discovery,
    })
    client.post(f"/api/identidad/proveedores/{provider['id']}/probar", headers=headers)
    client.post(f"/api/identidad/proveedores/{provider['id']}/activar", headers=headers)
    begin = client.post(f"/api/identidad/public/oidc/{provider['id']}/iniciar", json={"org_code": discovery})
    assert begin.status_code == 200
    state = begin.json()["state"]
    db = TestingSessionLocal()
    from app.identity_models import SsoAuthState
    auth_state = db.query(SsoAuthState).filter(SsoAuthState.state == state).one()
    nonce = auth_state.nonce
    db.close()
    id_token = _make_id_token(config, nonce=nonce)
    config["mock_tokens"]["good-code"]["id_token"] = id_token
    db = TestingSessionLocal()
    from app.identity_models import IdentityProvider
    row = db.query(IdentityProvider).filter(IdentityProvider.id == provider["id"]).one()
    row.config_json = json.dumps(config)
    db.commit()
    db.close()
    callback = client.post("/api/identidad/oidc/callback", json={"state": state, "code": "good-code"})
    assert callback.status_code == 200, callback.text
    assert "access_token" in callback.json()


def test_oidc_invalid_signature(client: TestClient):
    _, _, _, token, discovery = _create_org_admin(client)
    headers = auth_header(token)
    config = _oidc_config()
    provider = _create_oidc_provider(client, headers, config)
    client.post(f"/api/identidad/proveedores/{provider['id']}/activar", headers=headers)
    begin = client.post(f"/api/identidad/public/oidc/{provider['id']}/iniciar", json={"org_code": discovery})
    state = begin.json()["state"]
    bad_token = jwt.encode({"sub": "x", "iss": config["issuer"], "aud": config["client_id"]}, "wrong-secret", algorithm="HS256")
    config["mock_tokens"] = {"bad-code": {"id_token": bad_token}}
    db = TestingSessionLocal()
    from app.identity_models import IdentityProvider
    row = db.query(IdentityProvider).filter(IdentityProvider.id == provider["id"]).one()
    row.config_json = json.dumps(config)
    db.commit()
    db.close()
    res = client.post("/api/identidad/oidc/callback", json={"state": state, "code": "bad-code"})
    assert res.status_code == 401


def test_oidc_expired_token(client: TestClient):
    _, _, _, token, discovery = _create_org_admin(client)
    headers = auth_header(token)
    config = _oidc_config()
    provider = _create_oidc_provider(client, headers, config)
    client.post(f"/api/identidad/proveedores/{provider['id']}/activar", headers=headers)
    begin = client.post(f"/api/identidad/public/oidc/{provider['id']}/iniciar", json={"org_code": discovery})
    state = begin.json()["state"]
    db = TestingSessionLocal()
    from app.identity_models import SsoAuthState
    nonce = db.query(SsoAuthState).filter(SsoAuthState.state == state).one().nonce
    db.close()
    id_token = _make_id_token(config, nonce=nonce, expired=True)
    config["mock_tokens"] = {"exp-code": {"id_token": id_token}}
    db = TestingSessionLocal()
    from app.identity_models import IdentityProvider
    row = db.query(IdentityProvider).filter(IdentityProvider.id == provider["id"]).one()
    row.config_json = json.dumps(config)
    db.commit()
    db.close()
    res = client.post("/api/identidad/oidc/callback", json={"state": state, "code": "exp-code"})
    assert res.status_code == 401


def test_saml_valid_and_invalid_signature(client: TestClient):
    _, _, _, token, discovery = _create_org_admin(client)
    headers = auth_header(token)
    client.put("/api/identidad/politica", headers=headers, json={"auto_provision_enabled": True, "org_discovery_code": discovery})
    saml_xml = """<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
      xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
      <saml:Assertion><saml:Subject><saml:NameID>nameid-1370</saml:NameID></saml:Subject>
      <saml:AttributeStatement><saml:Attribute Name="email"><saml:AttributeValue>u@test.com</saml:AttributeValue></saml:Attribute></saml:AttributeStatement>
      </saml:Assertion></samlp:Response>"""
    fp = __import__("hashlib").sha256(saml_xml.encode()).hexdigest()[:32]
    res = client.post("/api/identidad/proveedores", headers=headers, json={
        "code": f"saml-{uuid.uuid4().hex[:4]}",
        "name": "IdP SAML Mock",
        "provider_type": IdPType.SAML,
        "config": {"sso_url": "https://idp.mock/saml", "mock_signature_valid": True, "idp_cert_fingerprint": fp, "mock_saml_redirect": True},
        "saml_cert_fingerprint": fp,
    })
    provider = res.json()
    client.post(f"/api/identidad/proveedores/{provider['id']}/activar", headers=headers)
    begin = client.post(f"/api/identidad/saml/{provider['id']}/iniciar", headers=headers)
    relay = begin.json()["relay_state"]
    encoded = base64.b64encode(saml_xml.encode()).decode()
    ok = client.post("/api/identidad/saml/acs", json={"relay_state": relay, "saml_response": encoded})
    assert ok.status_code == 200
    begin2 = client.post(f"/api/identidad/saml/{provider['id']}/iniciar", headers=headers)
    relay2 = begin2.json()["relay_state"]
    db = TestingSessionLocal()
    from app.identity_models import IdentityProvider
    row = db.query(IdentityProvider).filter(IdentityProvider.id == provider["id"]).one()
    cfg = json.loads(row.config_json)
    cfg["mock_signature_valid"] = False
    row.config_json = json.dumps(cfg)
    db.commit()
    db.close()
    bad = client.post("/api/identidad/saml/acs", json={"relay_state": relay2, "saml_response": encoded})
    assert bad.status_code == 401


def test_xxe_blocked():
    evil = b'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>'
    with pytest.raises(XmlSecurityError):
        safe_parse_xml(evil)


def test_auto_provision_disabled(client: TestClient):
    _, _, _, token, discovery = _create_org_admin(client)
    headers = auth_header(token)
    config = _oidc_config()
    provider = _create_oidc_provider(client, headers, config)
    client.put("/api/identidad/politica", headers=headers, json={"auto_provision_enabled": False, "org_discovery_code": discovery})
    client.post(f"/api/identidad/proveedores/{provider['id']}/activar", headers=headers)
    begin = client.post(f"/api/identidad/public/oidc/{provider['id']}/iniciar", json={"org_code": discovery})
    state = begin.json()["state"]
    db = TestingSessionLocal()
    from app.identity_models import SsoAuthState, IdentityProvider
    nonce = db.query(SsoAuthState).filter(SsoAuthState.state == state).one().nonce
    config["mock_tokens"] = {"c1": {"id_token": _make_id_token(config, sub="new-user-1", nonce=nonce)}}
    row = db.query(IdentityProvider).filter(IdentityProvider.id == provider["id"]).one()
    row.config_json = json.dumps(config)
    db.commit()
    db.close()
    res = client.post("/api/identidad/oidc/callback", json={"state": state, "code": "c1"})
    assert res.status_code == 401


def test_group_role_mapping(client: TestClient):
    _, _, _, token, discovery = _create_org_admin(client)
    headers = auth_header(token)
    config = _oidc_config()
    provider = _create_oidc_provider(client, headers, config)
    client.put("/api/identidad/politica", headers=headers, json={"auto_provision_enabled": True, "org_discovery_code": discovery})
    client.post(f"/api/identidad/proveedores/{provider['id']}/mapeos-roles", headers=headers, json={
        "external_group": "equipo-ops", "role_code": "viewer",
    })
    forbidden = client.post(f"/api/identidad/proveedores/{provider['id']}/mapeos-roles", headers=headers, json={
        "external_group": "admins", "role_code": "admin",
    })
    assert forbidden.status_code == 422


def test_solo_sso_blocks_local(client: TestClient):
    org_id, username, password, token, _ = _create_org_admin(client)
    headers = auth_header(token)
    client.put("/api/identidad/politica", headers=headers, json={"auth_mode": AuthMode.SOLO_SSO})
    db = TestingSessionLocal()
    db.query(OrganizationIdentitySettings).filter(OrganizationIdentitySettings.organization_id == org_id).update(
        {"auth_mode": AuthMode.SOLO_SSO}
    )
    db.commit()
    db.close()
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 403


def test_local_y_sso_allows_local(client: TestClient):
    org_id, username, password, token, _ = _create_org_admin(client)
    headers = auth_header(token)
    client.put("/api/identidad/politica", headers=headers, json={"auth_mode": AuthMode.LOCAL_Y_SSO})
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200


def test_break_glass(client: TestClient):
    os.environ["BREAK_GLASS_1370"] = "emergency-token-1370"
    db = TestingSessionLocal()
    _bootstrap(db)
    org = Organization(name="BG Org")
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"super-{uuid.uuid4().hex[:4]}",
        password_hash=hash_password("Super1370*"),
        role="superadmin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    settings = OrganizationIdentitySettings(
        organization_id=org.id,
        auth_mode=AuthMode.SOLO_SSO,
        break_glass_enabled=True,
        break_glass_secret_ref="env:BREAK_GLASS_1370",
    )
    db.add(settings)
    db.commit()
    username = user.username
    db.close()
    res = client.post("/api/identidad/break-glass", json={
        "username": username,
        "password": "Super1370*",
        "break_glass_token": "emergency-token-1370",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_tenant_isolation(client: TestClient):
    org_a, _, _, token_a, _ = _create_org_admin(client)
    org_b, _, _, token_b, _ = _create_org_admin(client)
    headers_a = auth_header(token_a)
    headers_b = auth_header(token_b)
    provider = _create_oidc_provider(client, headers_a)
    assert client.get(f"/api/identidad/proveedores/{provider['id']}", headers=headers_b).status_code == 404


def test_secrets_not_exposed(client: TestClient):
    os.environ["IDP_SECRET_1370"] = "super-secret-client"
    _, _, _, token, _ = _create_org_admin(client)
    headers = auth_header(token)
    res = client.post("/api/identidad/proveedores", headers=headers, json={
        "code": "sec-test",
        "name": "Sec",
        "provider_type": IdPType.OIDC,
        "secret_env_var": "IDP_SECRET_1370",
        "config": _oidc_config(),
    })
    detail = res.json()
    assert detail["secret_configured"] is True
    assert "super-secret" not in json.dumps(detail)


def test_rbac_viewer_cannot_manage(client: TestClient):
    db = TestingSessionLocal()
    _bootstrap(db)
    org = Organization(name="RBAC Org")
    db.add(org)
    db.flush()
    username = f"viewer-{uuid.uuid4().hex[:4]}"
    password = "Viewer1370*"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        role="viewer",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    headers = auth_header(login.json()["access_token"])
    assert client.get("/api/identidad/politica", headers=headers).status_code == 403


def test_disabled_user_sso_blocked(client: TestClient):
    org_id, username, password, token, discovery = _create_org_admin(client)
    headers = auth_header(token)
    config = _oidc_config()
    provider = _create_oidc_provider(client, headers, config)
    client.put("/api/identidad/politica", headers=headers, json={"auto_provision_enabled": True, "org_discovery_code": discovery})
    client.post(f"/api/identidad/proveedores/{provider['id']}/activar", headers=headers)
    begin = client.post(f"/api/identidad/public/oidc/{provider['id']}/iniciar", json={"org_code": discovery})
    state = begin.json()["state"]
    db = TestingSessionLocal()
    from app.identity_models import SsoAuthState, IdentityProvider
    nonce = db.query(SsoAuthState).filter(SsoAuthState.state == state).one().nonce
    sub = "disabled-sub"
    config["mock_tokens"] = {"d1": {"id_token": _make_id_token(config, sub=sub, nonce=nonce)}}
    row = db.query(IdentityProvider).filter(IdentityProvider.id == provider["id"]).one()
    row.config_json = json.dumps(config)
    db.commit()
    client.post("/api/identidad/oidc/callback", json={"state": state, "code": "d1"})
    link = db.query(UserExternalIdentity).filter(UserExternalIdentity.external_subject == sub).first()
    if link:
        u = db.query(User).filter(User.id == link.user_id).one()
        u.status = "DISABLED"
        u.is_active = False
        db.commit()
    begin2 = client.post(f"/api/identidad/public/oidc/{provider['id']}/iniciar", json={"org_code": discovery})
    state2 = begin2.json()["state"]
    nonce2 = db.query(SsoAuthState).filter(SsoAuthState.state == state2).one().nonce
    config["mock_tokens"]["d2"] = {"id_token": _make_id_token(config, sub=sub, nonce=nonce2)}
    row.config_json = json.dumps(config)
    db.commit()
    db.close()
    res = client.post("/api/identidad/oidc/callback", json={"state": state2, "code": "d2"})
    assert res.status_code == 401
