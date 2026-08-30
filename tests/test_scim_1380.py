"""Pruebas bloque 1380 — Aprovisionamiento empresarial SCIM 2.0."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.identity_models import OrganizationIdentitySettings
from app.models import Organization, User
from app.scim_enums import ScimProvisionStatus
from app.scim_models import ScimAuditLog, ScimToken, ScimUserResource
from app.security import create_access_token, hash_password
from app.services.scim_auth_service import create_token, set_scim_enabled
from tests.conftest import TestingSessionLocal


def _org(slug: str) -> Organization:
    db = TestingSessionLocal()
    try:
        org = Organization(name=slug, slug=slug)
        db.add(org)
        db.flush()
        settings = OrganizationIdentitySettings(
            organization_id=org.id,
            org_discovery_code=f"org-{uuid.uuid4().hex[:6]}",
        )
        db.add(settings)
        db.commit()
        db.refresh(org)
        return org
    finally:
        db.close()


def _admin(org: Organization) -> tuple[User, dict[str, str]]:
    db = TestingSessionLocal()
    try:
        user = User(
            organization_id=org.id,
            username=f"adm-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Admin123!"),
            email=f"admin-{uuid.uuid4().hex[:6]}@test.com",
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
        return user, headers
    finally:
        db.close()


def _scim_token(org_id: str) -> str:
    db = TestingSessionLocal()
    try:
        set_scim_enabled(db, org_id, True)
        _, plain = create_token(db, org_id, name="test")
        db.commit()
        return plain
    finally:
        db.close()


def _auth(plain: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {plain}"}


class TestScimDiscovery:
    def test_service_provider_config(self, client: TestClient):
        org = _org(f"scim-sp-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        r = client.get("/scim/v2/ServiceProviderConfig", headers=_auth(plain))
        assert r.status_code == 200
        data = r.json()
        assert data["patch"]["supported"] is True
        assert data["filter"]["supported"] is True

    def test_resource_types(self, client: TestClient):
        org = _org(f"scim-rt-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        r = client.get("/scim/v2/ResourceTypes", headers=_auth(plain))
        assert r.status_code == 200
        assert len(r.json()["Resources"]) >= 2

    def test_schemas(self, client: TestClient):
        org = _org(f"scim-sch-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        r = client.get("/scim/v2/Schemas", headers=_auth(plain))
        assert r.status_code == 200
        assert any("User" in s.get("name", "") for s in r.json()["Resources"])


class TestScimUsers:
    def test_create_get_list_user(self, client: TestClient):
        org = _org(f"scim-u-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        payload = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "scim.user@example.com",
            "externalId": "ext-001",
            "displayName": "Usuario SCIM",
            "emails": [{"value": "scim.user@example.com", "primary": True}],
            "active": True,
        }
        r = client.post("/scim/v2/Users", headers=_auth(plain), json=payload)
        assert r.status_code == 201
        created = r.json()
        assert created["userName"] == "scim.user@example.com"
        uid = created["id"]

        r2 = client.get(f"/scim/v2/Users/{uid}", headers=_auth(plain))
        assert r2.status_code == 200

        r3 = client.get("/scim/v2/Users", headers=_auth(plain))
        assert r3.status_code == 200
        assert r3.json()["totalResults"] >= 1

    def test_patch_user_and_deactivate(self, client: TestClient):
        org = _org(f"scim-p-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        r = client.post(
            "/scim/v2/Users",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "patch@example.com",
                "active": True,
            },
        )
        uid = r.json()["id"]

        r2 = client.patch(
            f"/scim/v2/Users/{uid}",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:api:messages:2.0:PatchOp"],
                "Operations": [{"op": "replace", "path": "displayName", "value": "Nuevo Nombre"}],
            },
        )
        assert r2.status_code == 200
        assert r2.json()["displayName"] == "Nuevo Nombre"

        r3 = client.patch(
            f"/scim/v2/Users/{uid}",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:api:messages:2.0:PatchOp"],
                "Operations": [{"op": "replace", "path": "active", "value": False}],
            },
        )
        assert r3.status_code == 200
        assert r3.json()["active"] is False

        r4 = client.patch(
            f"/scim/v2/Users/{uid}",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:api:messages:2.0:PatchOp"],
                "Operations": [{"op": "replace", "path": "active", "value": True}],
            },
        )
        assert r4.status_code == 200
        assert r4.json()["active"] is True

    def test_filter_and_pagination(self, client: TestClient):
        org = _org(f"scim-f-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        client.post(
            "/scim/v2/Users",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "filtro@example.com",
                "externalId": "filt-ext",
                "active": True,
            },
        )
        r = client.get(
            '/scim/v2/Users?filter=userName eq "filtro@example.com"',
            headers=_auth(plain),
        )
        assert r.status_code == 200
        assert r.json()["totalResults"] >= 1

        r2 = client.get(
            '/scim/v2/Users?filter=externalId eq "filt-ext"',
            headers=_auth(plain),
        )
        assert r2.status_code == 200

        r3 = client.get("/scim/v2/Users?startIndex=1&count=1", headers=_auth(plain))
        assert r3.status_code == 200
        assert r3.json()["itemsPerPage"] == 1

    def test_unsupported_filter(self, client: TestClient):
        org = _org(f"scim-uf-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        r = client.get('/scim/v2/Users?filter=foo co "bar"', headers=_auth(plain))
        assert r.status_code == 400
        assert r.json()["schemas"][0] == "urn:ietf:params:scim:api:messages:2.0:Error"

    def test_duplicate_external_id(self, client: TestClient):
        org = _org(f"scim-dup-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        body = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "dup1@example.com",
            "externalId": "same-ext",
            "active": True,
        }
        assert client.post("/scim/v2/Users", headers=_auth(plain), json=body).status_code == 201
        body["userName"] = "dup2@example.com"
        r = client.post("/scim/v2/Users", headers=_auth(plain), json=body)
        assert r.status_code == 409

    def test_idempotency(self, client: TestClient):
        org = _org(f"scim-idem-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        body = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "idem@example.com",
            "externalId": "idem-ext",
            "active": True,
        }
        headers = {**_auth(plain), "X-Idempotency-Key": "key-123"}
        r1 = client.post("/scim/v2/Users", headers=headers, json=body)
        r2 = client.post("/scim/v2/Users", headers=headers, json=body)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] == r2.json()["id"]


class TestScimGroups:
    def test_group_membership_patch(self, client: TestClient):
        org = _org(f"scim-g-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        ur = client.post(
            "/scim/v2/Users",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "member@example.com",
                "active": True,
            },
        ).json()
        gr = client.post(
            "/scim/v2/Groups",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": "Equipo SCIM",
                "externalId": "grp-1",
            },
        )
        assert gr.status_code == 201
        gid = gr.json()["id"]

        r = client.patch(
            f"/scim/v2/Groups/{gid}",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:api:messages:2.0:PatchOp"],
                "Operations": [
                    {"op": "add", "path": "members", "value": [{"value": ur["id"]}]},
                ],
            },
        )
        assert r.status_code == 200
        members = r.json().get("members", [])
        assert any(m["value"] == ur["id"] for m in members)


class TestScimAuth:
    def test_invalid_token(self, client: TestClient):
        org = _org(f"scim-bad-{uuid.uuid4().hex[:6]}")
        _scim_token(org.id)
        r = client.get("/scim/v2/Users", headers={"Authorization": "Bearer invalid-token"})
        assert r.status_code == 401

    def test_revoked_token(self, client: TestClient):
        org = _org(f"scim-rev-{uuid.uuid4().hex[:6]}")
        _, admin_headers = _admin(org)
        plain = _scim_token(org.id)
        estado = client.get("/api/identidad/scim/estado", headers=admin_headers).json()
        token_id = estado["tokens"][0]["id"]
        client.post(f"/api/identidad/scim/tokens/{token_id}/revocar", headers=admin_headers)
        r = client.get("/scim/v2/Users", headers=_auth(plain))
        assert r.status_code == 401

    def test_expired_token(self, client: TestClient):
        org = _org(f"scim-exp-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        db = TestingSessionLocal()
        try:
            token_hash = hashlib.sha256(plain.encode()).hexdigest()
            rec = db.query(ScimToken).filter(ScimToken.token_hash == token_hash).first()
            rec.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            db.commit()
        finally:
            db.close()
        r = client.get("/scim/v2/Users", headers=_auth(plain))
        assert r.status_code == 401


class TestScimMultiTenant:
    def test_isolation(self, client: TestClient):
        org_a = _org(f"scim-a-{uuid.uuid4().hex[:6]}")
        org_b = _org(f"scim-b-{uuid.uuid4().hex[:6]}")
        plain_a = _scim_token(org_a.id)
        plain_b = _scim_token(org_b.id)
        ua = client.post(
            "/scim/v2/Users",
            headers=_auth(plain_a),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "a@example.com",
                "active": True,
            },
        ).json()
        r = client.get(f"/scim/v2/Users/{ua['id']}", headers=_auth(plain_b))
        assert r.status_code == 404


class TestScimRoles:
    def test_role_allowlist(self, client: TestClient):
        org = _org(f"scim-role-{uuid.uuid4().hex[:6]}")
        _, admin_headers = _admin(org)
        plain = _scim_token(org.id)
        client.post(
            "/api/identidad/scim/mapeos-roles",
            headers=admin_headers,
            json={"external_group": "Developers", "role_code": "viewer"},
        )
        gr = client.post(
            "/scim/v2/Groups",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": "Developers",
            },
        ).json()
        ur = client.post(
            "/scim/v2/Users",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "dev@example.com",
                "active": True,
            },
        ).json()
        client.patch(
            f"/scim/v2/Groups/{gr['id']}",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:api:messages:2.0:PatchOp"],
                "Operations": [{"op": "add", "path": "members", "value": [{"value": ur["id"]}]}],
            },
        )
        db = TestingSessionLocal()
        try:
            scim_row = db.query(ScimUserResource).filter(ScimUserResource.id == ur["id"]).first()
            user_db = db.query(User).filter(User.id == scim_row.user_id).first()
            assert user_db.role == "viewer"
        finally:
            db.close()

    def test_privilege_escalation_blocked(self, client: TestClient):
        org = _org(f"scim-priv-{uuid.uuid4().hex[:6]}")
        _, admin_headers = _admin(org)
        r = client.post(
            "/api/identidad/scim/mapeos-roles",
            headers=admin_headers,
            json={"external_group": "Evil", "role_code": "superadmin"},
        )
        assert r.status_code == 422


class TestScimSuperadminProtection:
    def test_cannot_modify_superadmin(self, client: TestClient):
        org = _org(f"scim-sa-{uuid.uuid4().hex[:6]}")
        db = TestingSessionLocal()
        try:
            sa = User(
                organization_id=org.id,
                email="root@platform.com",
                username="root",
                password_hash=hash_password("Root123!"),
                role="superadmin",
                status="ACTIVE",
                is_active=True,
            )
            db.add(sa)
            db.flush()
            resource = ScimUserResource(
                organization_id=org.id,
                user_id=sa.id,
                external_id="root-ext",
                user_name="root@platform.com",
                provision_status=ScimProvisionStatus.ACTIVO,
            )
            db.add(resource)
            db.commit()
            resource_id = resource.id
        finally:
            db.close()
        plain = _scim_token(org.id)
        r = client.patch(
            f"/scim/v2/Users/{resource_id}",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:api:messages:2.0:PatchOp"],
                "Operations": [{"op": "replace", "path": "active", "value": False}],
            },
        )
        assert r.status_code in (403, 409)


class TestScimAdminApi:
    def test_estado_and_tokens(self, client: TestClient):
        org = _org(f"scim-api-{uuid.uuid4().hex[:6]}")
        _, headers = _admin(org)
        r = client.get("/api/identidad/scim/estado", headers=headers)
        assert r.status_code == 200
        assert "scim_base_url" in r.json()
        r2 = client.post("/api/identidad/scim/tokens", headers=headers, json={"name": "prod"})
        assert r2.status_code == 200
        assert "token" in r2.json()

    def test_rotate_token(self, client: TestClient):
        org = _org(f"scim-rot-{uuid.uuid4().hex[:6]}")
        _, headers = _admin(org)
        created = client.post("/api/identidad/scim/tokens", headers=headers, json={"name": "rot"}).json()
        rotated = client.post(f"/api/identidad/scim/tokens/{created['id']}/rotar", headers=headers)
        assert rotated.status_code == 200
        assert "token" in rotated.json()


class TestScimAudit:
    def test_audit_logged(self, client: TestClient):
        org = _org(f"scim-aud-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        client.post(
            "/scim/v2/Users",
            headers=_auth(plain),
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "audit@example.com",
                "active": True,
            },
        )
        db = TestingSessionLocal()
        try:
            count = db.query(ScimAuditLog).filter(ScimAuditLog.organization_id == org.id).count()
            assert count >= 1
        finally:
            db.close()


class TestScimRateLimit:
    def test_rate_limit(self, client: TestClient, monkeypatch):
        from app.services import scim_auth_service as auth_svc

        monkeypatch.setattr(auth_svc, "SCIM_RATE_LIMIT", 3)
        org = _org(f"scim-rl-{uuid.uuid4().hex[:6]}")
        plain = _scim_token(org.id)
        for _ in range(3):
            assert client.get("/scim/v2/ServiceProviderConfig", headers=_auth(plain)).status_code == 200
        r = client.get("/scim/v2/ServiceProviderConfig", headers=_auth(plain))
        assert r.status_code == 429


class TestScimMigration:
    def test_migration_head(self):
        from scripts.migration_control import assert_single_head
        from scripts.schema_repair import HEAD_REVISION

        assert HEAD_REVISION == assert_single_head()
        assert HEAD_REVISION == "1507a1b2c3d4e"
