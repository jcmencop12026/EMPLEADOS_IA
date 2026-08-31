"""NX03 — Matriz RBAC V2: ≥6 permisos, 403 sin permiso y 200 con permiso."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, Permission, Role, RolePermission, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant]

RBAC_MATRIX: list[tuple[str, str, str]] = [
    ("control_center.view", "GET", "/api/centro-control/resumen-ejecutivo"),
    ("auditor_empleados.view", "GET", "/api/empleados-auditor/politica"),
    ("communications.view", "GET", "/api/comunicaciones/canales"),
    ("support.view", "GET", "/api/soporte/casos"),
    ("finops.view", "GET", "/api/finops/dashboard"),
    ("optimizacion.view", "GET", "/api/optimizacion/configuracion"),
]


def _limited_token(client: TestClient, permission_code: str) -> str:
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        org = Organization(name=f"NX03 {uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        role_code = f"nx03-{uuid.uuid4().hex[:6]}"
        role = Role(
            organization_id=org.id,
            code=role_code,
            name="NX03 limited",
            is_system=False,
            is_active=True,
        )
        db.add(role)
        db.flush()
        perm = db.query(Permission).filter(Permission.code == permission_code).one()
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        username = f"nx03-{uuid.uuid4().hex[:6]}"
        password = "Nx03*Test"
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
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def _limited_token_other_permission(client: TestClient, exclude: str) -> str:
    """Usuario autenticado con employee.view pero sin el permiso bajo prueba."""
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        org = Organization(name=f"NX03-deny {uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        role_code = f"nx03-deny-{uuid.uuid4().hex[:6]}"
        role = Role(
            organization_id=org.id,
            code=role_code,
            name="NX03 deny",
            is_system=False,
            is_active=True,
        )
        db.add(role)
        db.flush()
        perm = db.query(Permission).filter(Permission.code == "employee.view").one()
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        username = f"nx03-deny-{uuid.uuid4().hex[:6]}"
        password = "Nx03Deny*Test"
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
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


@pytest.mark.parametrize("permission,method,path", RBAC_MATRIX)
def test_nx03_rbac_matrix_denied_without_permission(
    client: TestClient, permission: str, method: str, path: str
):
    deny_token = _limited_token_other_permission(client, exclude=permission)
    denied = client.request(method, path, headers=auth_header(deny_token))
    assert denied.status_code == 403, f"{permission} sin permiso → {denied.status_code}"

    token = _limited_token(client, permission)
    allowed = client.request(method, path, headers=auth_header(token))
    assert allowed.status_code == 200, f"{permission} → {allowed.status_code}: {allowed.text[:200]}"


def test_nx03_rbac_matrix_covers_six_permissions():
    assert len(RBAC_MATRIX) >= 6
