"""CURSOR-840B — Correcciones post-auditoría Codex."""
from __future__ import annotations

import os
import sqlite3
import tempfile
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, Permission, Role, RolePermission, User
from app.permissions import user_permissions
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header
from tests.test_admin_840 import _create_org_admin, _token


def _alembic_cfg(db_url: str) -> Config:
    backend = Path(__file__).resolve().parents[1] / "backend"
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_migration_a840_sqlite_upgrade_downgrade_upgrade(monkeypatch):
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "5b2eb2437398")
        command.upgrade(cfg, "a840c4d5e6f7")
        command.downgrade(cfg, "5b2eb2437398")
        command.upgrade(cfg, "a840c4d5e6f7")

        conn = sqlite3.connect(db_path)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        user_cols = {c[1] for c in conn.execute("PRAGMA table_info(users)")}
        conn.close()
        assert "permissions" in tables
        assert "roles" in tables
        assert "role_permissions" in tables
        assert "email" in user_cols
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_authorization_single_source_db_not_fallback(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, actor, _ = _create_org_admin(db, "Auth Source Org")
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        custom = Role(
            organization_id=org.id,
            code=f"limited-{uuid.uuid4().hex[:6]}",
            name="Limited",
            is_system=False,
            is_active=True,
        )
        db.add(custom)
        db.flush()
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        assert view_perm
        db.add(RolePermission(role_id=custom.id, permission_id=view_perm.id))
        limited_user = User(
            organization_id=org.id,
            username=f"limited-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Limited840*"),
            role=custom.code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(limited_user)
        db.commit()
        perms = user_permissions(limited_user, db)
        assert perms == {"employee.view"}
        assert "admin.user.view" not in perms
        token = _token(client, limited_user.username, "Limited840*")
    finally:
        db.close()

    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_privilege_escalation_superadmin_denied(client: TestClient, auth_headers):
    res = client.post(
        "/api/admin/users",
        headers=auth_headers,
        json={
            "username": f"hack-{uuid.uuid4().hex[:6]}",
            "password": "Hack840*Test",
            "role": "superadmin",
        },
    )
    assert res.status_code == 403


def test_privilege_escalation_platform_role_denied(client: TestClient, auth_headers):
    res = client.post(
        "/api/admin/users",
        headers=auth_headers,
        json={
            "username": f"hack2-{uuid.uuid4().hex[:6]}",
            "password": "Hack840*Test",
            "role": "SUPERADMIN",
        },
    )
    assert res.status_code == 403


def test_privilege_escalation_extra_permissions_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Escalation Org")
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        assigner_role = Role(
            organization_id=org.id,
            code=f"assigner-{uuid.uuid4().hex[:6]}",
            name="Assigner",
            is_system=False,
            is_active=True,
        )
        target_role = Role(
            organization_id=org.id,
            code=f"target-{uuid.uuid4().hex[:6]}",
            name="Target",
            is_system=False,
            is_active=True,
        )
        db.add_all([assigner_role, target_role])
        db.flush()
        assign_perm = db.query(Permission).filter(Permission.code == "admin.role.assign_permissions").first()
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        db.add_all(
            [
                RolePermission(role_id=assigner_role.id, permission_id=assign_perm.id),
                RolePermission(role_id=assigner_role.id, permission_id=view_perm.id),
            ]
        )
        assigner = User(
            organization_id=org.id,
            username=f"assigner-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Assigner840*"),
            role=assigner_role.code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(assigner)
        db.commit()
        token = _token(client, assigner.username, "Assigner840*")
        target_role_id = target_role.id
    finally:
        db.close()

    res = client.put(
        f"/api/admin/roles/{target_role_id}/permissions",
        headers=auth_header(token),
        json={"permission_codes": ["employee.view", "admin.user.create"]},
    )
    assert res.status_code == 403


def test_protected_system_role_permissions_denied(client: TestClient, auth_headers):
    roles = client.get("/api/admin/roles", headers=auth_headers).json()
    admin_role = next(r for r in roles if r["code"] == "admin" and r["is_system"])
    res = client.put(
        f"/api/admin/roles/{admin_role['id']}/permissions",
        headers=auth_headers,
        json={"permission_codes": ["employee.view"]},
    )
    assert res.status_code == 403


def test_cross_tenant_role_permissions_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pass_a = _create_org_admin(db, "Org A role 840", username=f"a-{uuid.uuid4().hex[:6]}")
        org_b, _, _ = _create_org_admin(db, "Org B role 840", username=f"b-{uuid.uuid4().hex[:6]}")
        custom_b = Role(
            organization_id=org_b.id,
            code=f"custom-b-{uuid.uuid4().hex[:6]}",
            name="Custom B",
            is_system=False,
            is_active=True,
        )
        db.add(custom_b)
        db.commit()
        token_a = _token(client, user_a.username, pass_a)
        role_b_id = custom_b.id
        assert org_a.id != org_b.id
    finally:
        db.close()

    res = client.put(
        f"/api/admin/roles/{role_b_id}/permissions",
        headers=auth_header(token_a),
        json={"permission_codes": ["employee.view"]},
    )
    assert res.status_code == 404


def test_cross_tenant_role_assignment_denied(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b, _, _ = _create_org_admin(db, "Org B assign 840")
        custom_b = Role(
            organization_id=org_b.id,
            code=f"only-b-{uuid.uuid4().hex[:6]}",
            name="Only B",
            is_system=False,
            is_active=True,
        )
        db.add(custom_b)
        db.commit()
        role_code = custom_b.code
    finally:
        db.close()

    res = client.post(
        "/api/admin/users",
        headers=auth_headers,
        json={
            "username": f"user-{uuid.uuid4().hex[:6]}",
            "password": "User840*Test",
            "role": role_code,
        },
    )
    assert res.status_code in (403, 422)


def test_matrix_edit_add_permission(client: TestClient, auth_headers):
    code = f"matrix_{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/admin/roles",
        headers=auth_headers,
        json={"code": code, "name": "Matrix Test", "description": "840B"},
    )
    assert created.status_code == 201
    role_id = created.json()["id"]

    updated = client.put(
        f"/api/admin/roles/{role_id}/permissions",
        headers=auth_headers,
        json={"permission_codes": ["employee.view", "operations.view"]},
    )
    assert updated.status_code == 200

    matrix = client.get("/api/admin/roles/permission-matrix", headers=auth_headers).json()
    assert matrix["matrix"][role_id]["employee.view"] is True
    assert matrix["matrix"][role_id]["operations.view"] is True
    assert matrix["matrix"][role_id]["admin.user.create"] is False


def test_matrix_edit_remove_permission(client: TestClient, auth_headers):
    code = f"matrix_rm_{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/admin/roles",
        headers=auth_headers,
        json={"code": code, "name": "Matrix Remove", "description": "840B"},
    )
    role_id = created.json()["id"]
    client.put(
        f"/api/admin/roles/{role_id}/permissions",
        headers=auth_headers,
        json={"permission_codes": ["employee.view", "operations.view"]},
    )
    removed = client.put(
        f"/api/admin/roles/{role_id}/permissions",
        headers=auth_headers,
        json={"permission_codes": ["employee.view"]},
    )
    assert removed.status_code == 200
    matrix = client.get("/api/admin/roles/permission-matrix", headers=auth_headers).json()
    assert matrix["matrix"][role_id]["employee.view"] is True
    assert matrix["matrix"][role_id]["operations.view"] is False


def test_self_role_elevation_denied(client: TestClient, auth_headers):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    res = client.put(
        f"/api/admin/users/{me['id']}",
        headers=auth_headers,
        json={"role": "viewer"},
    )
    assert res.status_code == 403


def test_inactive_db_role_denies_not_fallback(client: TestClient):
    """Rol inactivo en BD no debe activar fallback hardcoded con permisos elevados."""
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Inactive Role Org")
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        inactive = Role(
            organization_id=org.id,
            code="admin",
            name="Admin Inactivo",
            is_system=False,
            is_active=False,
        )
        db.add(inactive)
        db.flush()
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        db.add(RolePermission(role_id=inactive.id, permission_id=view_perm.id))
        user = User(
            organization_id=org.id,
            username=f"inactive-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Inactive840*"),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        perms = user_permissions(user, db)
        token = _token(client, user.username, "Inactive840*")
    finally:
        db.close()

    assert perms == set()
    assert "admin.user.view" not in perms
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_db_role_limits_permissions_no_escalation(client: TestClient):
    """Permisos de BD restringen; nunca se elevan vía fallback hardcoded."""
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Limited Admin Org")
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        admin_role = (
            db.query(Role)
            .filter(Role.code == "admin", Role.organization_id.is_(None))
            .first()
        )
        assert admin_role
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        db.query(RolePermission).filter(RolePermission.role_id == admin_role.id).delete()
        db.add(RolePermission(role_id=admin_role.id, permission_id=view_perm.id))
        user = User(
            organization_id=org.id,
            username=f"limited-admin-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("LimitedA840*"),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        perms = user_permissions(user, db)
        token = _token(client, user.username, "LimitedA840*")
    finally:
        db.close()

    assert perms == {"employee.view"}
    assert "admin.user.view" not in perms
    assert "operations.execute" not in perms
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_active_db_role_without_permissions_denies(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Empty Perms Org")
        empty_role = Role(
            organization_id=org.id,
            code=f"empty-{uuid.uuid4().hex[:6]}",
            name="Sin permisos",
            is_system=False,
            is_active=True,
        )
        db.add(empty_role)
        user = User(
            organization_id=org.id,
            username=f"empty-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Empty840*"),
            role=empty_role.code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        perms = user_permissions(user, db)
        token = _token(client, user.username, "Empty840*")
    finally:
        db.close()

    assert perms == set()
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_revoked_inactive_role_denies(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Revoked Role Org")
        revoked = Role(
            organization_id=org.id,
            code=f"revoked-{uuid.uuid4().hex[:6]}",
            name="Revocado",
            is_system=False,
            is_active=False,
        )
        db.add(revoked)
        db.flush()
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        db.add(RolePermission(role_id=revoked.id, permission_id=view_perm.id))
        user = User(
            organization_id=org.id,
            username=f"revoked-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Revoked840*"),
            role=revoked.code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        perms = user_permissions(user, db)
        token = _token(client, user.username, "Revoked840*")
    finally:
        db.close()

    assert perms == set()
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_db_error_on_role_lookup_denies(monkeypatch):
    db = TestingSessionLocal()
    try:
        org, user, _ = _create_org_admin(db, "DB Error Org")

        def boom(*_args, **_kwargs):
            raise RuntimeError("db unavailable")

        monkeypatch.setattr("app.permissions.resolve_authoritative_role", boom)
        perms = user_permissions(user, db)
    finally:
        db.close()

    assert perms == set()


def test_nonexistent_role_denies_no_fallback(client: TestClient):
    """Rol inexistente → DENY, sin fallback hardcoded."""
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Ghost Role")
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        user = User(
            organization_id=org.id,
            username=f"ghost-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Ghost840*"),
            role=f"nonexistent-{uuid.uuid4().hex[:8]}",
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        perms = user_permissions(user, db)
        token = _token(client, user.username, "Ghost840*")
    finally:
        db.close()

    assert perms == set()
    assert "employee.view" not in perms
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_duplicate_global_role_denies(client: TestClient):
    """Roles globales duplicados → DENY (ambigüedad)."""
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Dup Global")
        dup_code = f"dup-global-{uuid.uuid4().hex[:6]}"
        role_a = Role(
            organization_id=None,
            code=dup_code,
            name="Global A",
            is_system=False,
            is_active=True,
        )
        role_b = Role(
            organization_id=None,
            code=dup_code,
            name="Global B",
            is_system=False,
            is_active=True,
        )
        db.add_all([role_a, role_b])
        user = User(
            organization_id=org.id,
            username=f"dup-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Dup840*"),
            role=dup_code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        perms = user_permissions(user, db)
        token = _token(client, user.username, "Dup840*")
    finally:
        db.close()

    assert perms == set()
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


@pytest.mark.parametrize("bad_active", [False, 0, None, "yes", 1])
def test_corrupt_is_active_denies(bad_active):
    """is_active corrupto/no booleano True → DENY."""
    from app.permissions import is_role_strictly_active

    role = Role(code="x", name="x", is_active=True)
    object.__setattr__(role, "is_active", bad_active)
    assert is_role_strictly_active(role) is False


def test_corrupt_is_active_in_db_denies(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Inactive Bool")
        role = Role(
            organization_id=org.id,
            code=f"inactive-bool-{uuid.uuid4().hex[:6]}",
            name="Inactivo",
            is_system=False,
            is_active=False,
        )
        db.add(role)
        user = User(
            organization_id=org.id,
            username=f"inactive-bool-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("InactiveB840*"),
            role=role.code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        perms = user_permissions(user, db)
        token = _token(client, user.username, "InactiveB840*")
    finally:
        db.close()

    assert perms == set()
    res = client.get("/api/admin/users", headers=auth_header(token))
    assert res.status_code == 403


def test_empty_role_code_denies():
    db = TestingSessionLocal()
    try:
        org, user, _ = _create_org_admin(db, "Empty Role Code")
        user.role = "   "
        db.commit()
        perms = user_permissions(user, db)
    finally:
        db.close()
    assert perms == set()
