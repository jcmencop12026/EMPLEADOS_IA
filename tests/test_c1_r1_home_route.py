"""Pruebas C1-R1 — fallback determinístico de ruta inicial /."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, Permission, Role, RolePermission, User
from app.permissions import user_permissions
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"
PERMISSIONS_TS = FRONTEND / "auth" / "permissions.ts"
HOME_ROUTE_TS = FRONTEND / "navigation" / "homeRoute.ts"
MENU_TS = FRONTEND / "navigation" / "menu.ts"
HOME_PAGE_TSX = FRONTEND / "pages" / "HomePage.tsx"
APP_TSX = FRONTEND / "src" / "App.tsx" if False else ROOT / "frontend" / "src" / "App.tsx"


def _parse_route_permissions() -> dict[str, list[str]]:
    src = PERMISSIONS_TS.read_text(encoding="utf-8")
    block = re.search(r"export const ROUTE_PERMISSIONS.*?= \{(.*?)\n\};", src, re.S)
    assert block, "ROUTE_PERMISSIONS no encontrado"
    routes: dict[str, list[str]] = {}
    for match in re.finditer(r'"(/[^"]*)": \[(.*?)\]', block.group(1), re.S):
        path = match.group(1)
        perms = re.findall(r'"([^"]+)"', match.group(2))
        routes[path] = perms
    return routes


def _parse_nav_order() -> list[str]:
    src = MENU_TS.read_text(encoding="utf-8")
    return re.findall(r'to: "(/[^"]*)"', src)


def _parse_home_exclude() -> set[str]:
    src = HOME_ROUTE_TS.read_text(encoding="utf-8")
    match = re.search(r"HOME_ROUTE_EXCLUDE = new Set<string>\(\[(.*?)\]\)", src, re.S)
    if not match:
        return set()
    return set(re.findall(r'"(/[^"]+)"', match.group(1)))


def can_access_route(path: str, permissions: set[str], route_permissions: dict[str, list[str]]) -> bool:
    required = route_permissions.get(path)
    if not required:
        return True
    return any(code in permissions for code in required)


def resolve_home_route(permissions: set[str]) -> str | None:
    route_permissions = _parse_route_permissions()
    exclude = _parse_home_exclude()
    for path in _parse_nav_order():
        if path in exclude:
            continue
        if can_access_route(path, permissions, route_permissions):
            return path
    return None


def test_home_route_source_uses_menu_and_permissions():
    src = HOME_ROUTE_TS.read_text(encoding="utf-8")
    assert 'from "./menu"' in src
    assert "canAccessRoute" in src
    assert "getNavRoutesInOrder" in src
    assert "resolveHomeRoute" in src


def test_app_uses_home_page_for_index():
    src = APP_TSX.read_text(encoding="utf-8")
    assert '<Route index element={<HomePage />} />' in src
    assert '<Route path="centro-control" element={<HomePage />} />' in src


def test_home_page_redirect_logic():
    src = HOME_PAGE_TSX.read_text(encoding="utf-8")
    assert "resolveHomeRoute" in src
    assert 'has("control_center.view")' in src
    assert "NoModulesPage" in src
    assert "<Navigate" in src


def test_resolve_home_superadmin():
    perms = {"control_center.view", "operations.view", "notification.view"}
    assert resolve_home_route(perms) == "/"


def test_resolve_home_without_cc_mi_trabajo():
    perms = {"notification.view"}
    assert resolve_home_route(perms) == "/trabajo"


def test_resolve_home_without_cc_other_module():
    perms = {"comercial.view"}
    assert resolve_home_route(perms) == "/comercial"


def test_resolve_home_no_operational_modules():
    perms: set[str] = set()
    assert resolve_home_route(perms) is None


def test_resolve_home_no_redirect_loop_to_self():
    perms = {"notification.view"}
    home = resolve_home_route(perms)
    assert home != "/"
    assert home == "/trabajo"


def _create_user_with_permissions(client: TestClient, username: str, permission_codes: set[str]) -> str:
    db = TestingSessionLocal()
    from app.seed_permissions import bootstrap_permissions

    bootstrap_permissions(db)
    org = Organization(name=f"Org {username}", slug=f"org-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    role_code = f"role_{username}"
    role = Role(
        organization_id=org.id,
        code=role_code,
        name=f"Role {username}",
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()
    for code in permission_codes:
        perm = db.query(Permission).filter(Permission.code == code).first()
        assert perm is not None, code
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    password = "TestPass*123"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        role=role_code,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    effective = set(user_permissions(user, db))
    db.close()
    if permission_codes:
        assert permission_codes.issubset(effective)
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def test_backend_rbac_superadmin_has_control_center(client: TestClient, token: str):
    me = client.get("/api/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    perms = set(me.json()["permissions"])
    assert "control_center.view" in perms
    assert resolve_home_route(perms) == "/"


def test_backend_restricted_cc_without_centro_control(client: TestClient):
    token = _create_user_with_permissions(client, "restricted_cc", {"notification.view"})
    me = client.get("/api/auth/me", headers=auth_header(token))
    perms = set(me.json()["permissions"])
    assert "control_center.view" not in perms
    assert resolve_home_route(perms) == "/trabajo"
    denied = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_header(token))
    assert denied.status_code == 403


def test_backend_no_modules_user_still_authenticated(client: TestClient):
    token = _create_user_with_permissions(client, "no_modules_user", set())
    me = client.get("/api/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    perms = set(me.json()["permissions"])
    assert resolve_home_route(perms) is None


def test_login_hotfix_still_present():
    api = (FRONTEND / "api.ts").read_text(encoding="utf-8")
    text_idx = api.index("const text = await res.text()")
    not_ok_idx = api.index("if (!res.ok)")
    assert text_idx < not_ok_idx
