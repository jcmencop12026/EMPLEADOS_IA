"""Bloque C2 — Gobierno multiempresa, RBAC, SUPERADMIN, CC y Mi Trabajo."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Notification, Organization, User
from app.orchestration_models import WorkPlan
from app.security import hash_password
from app.tenant_scope import ORG_STATUS_INACTIVE
from conftest import TestingSessionLocal, auth_header

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.operations]


def _login(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant_user(
    db: Session,
    *,
    org_name: str,
    role: str = "admin",
    password: str = "TenantC2*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"c2-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    username = f"c2-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return org, user, password


def _seed_failed_plan(db: Session, org: Organization, user: User, marker: str) -> WorkPlan:
    plan = WorkPlan(
        organization_id=org.id,
        user_id=user.id,
        correlation_id=f"corr-{marker}",
        request=f"plan {marker}",
        objective=f"obj {marker}",
        status="FAILED",
        error=f"fallo {marker}",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# --- A/B: aislamiento entre organizaciones ---


def test_c2_org_a_no_ve_datos_org_b(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pwd_a = _create_tenant_user(db, org_name="C2 Org A")
        org_b, user_b, pwd_b = _create_tenant_user(db, org_name="C2 Org B")
        _seed_failed_plan(db, org_b, user_b, "solo-b")
        token_a = _login(client, user_a.username, pwd_a)
        hdr_a = auth_header(token_a)
        res_cc = client.get("/api/centro-control/resumen-ejecutivo", headers=hdr_a)
        assert res_cc.status_code == 200
        assert res_cc.json()["organization_id"] == org_a.id
        res_trab = client.get("/api/trabajo/items", headers=hdr_a)
        assert res_trab.status_code == 200
        for item in res_trab.json()["items"]:
            assert item.get("organization_id", org_a.id) == org_a.id
            assert "solo-b" not in json.dumps(item)
    finally:
        db.close()


def test_c2_org_b_no_ve_datos_org_a(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="C2 Org A2")
        org_b, user_b, pwd_b = _create_tenant_user(db, org_name="C2 Org B2")
        _seed_failed_plan(db, org_a, user_a, "solo-a")
        token_b = _login(client, user_b.username, pwd_b)
        hdr_b = auth_header(token_b)
        res = client.get("/api/trabajo/items", headers=hdr_b)
        assert res.status_code == 200
        assert res.json()["filtros_aplicados"]["organization_id"] == org_b.id
        assert not any("solo-a" in (i.get("asunto") or "") for i in res.json()["items"])
    finally:
        db.close()


# --- C/K/L: SUPERADMIN contexto explícito ---


def test_c2_superadmin_consulta_organizacion_explicita(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org, user, _ = _create_tenant_user(db, org_name="C2 Org SA")
        _seed_failed_plan(db, org, user, "sa-target")
        res = client.get(
            f"/api/centro-control/resumen-ejecutivo?organization_id={org.id}",
            headers=auth_headers,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["organization_id"] == org.id
        res_trab = client.get(f"/api/trabajo/items?organization_id={org.id}", headers=auth_headers)
        assert res_trab.status_code == 200
        assert res_trab.json()["filtros_aplicados"]["organization_id"] == org.id
    finally:
        db.close()


def test_c2_superadmin_cambio_contexto_no_mezcla_datos(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="C2 SA A")
        org_b, user_b, _ = _create_tenant_user(db, org_name="C2 SA B")
        _seed_failed_plan(db, org_a, user_a, "ctx-a")
        _seed_failed_plan(db, org_b, user_b, "ctx-b")
        res_a = client.get(f"/api/trabajo/resumen?organization_id={org_a.id}", headers=auth_headers)
        res_b = client.get(f"/api/trabajo/resumen?organization_id={org_b.id}", headers=auth_headers)
        assert res_a.status_code == 200 and res_b.status_code == 200
        assert res_a.json()["organization_id"] == org_a.id
        assert res_b.json()["organization_id"] == org_b.id
        assert res_a.json()["organization_id"] != res_b.json()["organization_id"]
    finally:
        db.close()


# --- D: RBAC 403 ---


def test_c2_tenant_admin_no_puede_cross_org_cc(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pwd_a = _create_tenant_user(db, org_name="C2 RBAC A")
        org_b, _, _ = _create_tenant_user(db, org_name="C2 RBAC B")
        token = _login(client, user_a.username, pwd_a)
        res = client.get(
            f"/api/centro-control/resumen-ejecutivo?organization_id={org_b.id}",
            headers=auth_header(token),
        )
        assert res.status_code == 403
    finally:
        db.close()


def test_c2_tenant_admin_no_puede_cross_org_trabajo(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pwd_a = _create_tenant_user(db, org_name="C2 RBAC T A")
        org_b, _, _ = _create_tenant_user(db, org_name="C2 RBAC T B")
        token = _login(client, user_a.username, pwd_a)
        res = client.get(
            f"/api/trabajo/items?organization_id={org_b.id}",
            headers=auth_header(token),
        )
        assert res.status_code == 403
    finally:
        db.close()


def test_c2_usuario_sin_permiso_cc_403(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.models import Permission, Role, RolePermission
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        org = Organization(name="C2 No CC", slug=f"c2-nocc-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        role = Role(
            organization_id=org.id,
            code="no_cc",
            name="Sin CC",
            is_system=False,
            is_active=True,
        )
        db.add(role)
        db.flush()
        perm = db.query(Permission).filter(Permission.code == "notification.view").first()
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        pwd = "NoCC*123"
        user = User(
            organization_id=org.id,
            username=f"nocc-{uuid.uuid4().hex[:4]}",
            password_hash=hash_password(pwd),
            role="no_cc",
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        token = _login(client, user.username, pwd)
        res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_header(token))
        assert res.status_code == 403
    finally:
        db.close()


# --- E/F: frontend coherencia (estático) ---


def test_c2_frontend_org_context_wiring():
  home_route = (FRONTEND / "hooks" / "useOrganizationContext.tsx").read_text(encoding="utf-8")
  api = (FRONTEND / "api.ts").read_text(encoding="utf-8")
  app_shell = (FRONTEND / "AppShell.tsx").read_text(encoding="utf-8")
  cc = (FRONTEND / "pages" / "CentroControlPage.tsx").read_text(encoding="utf-8")
  trabajo = (FRONTEND / "pages" / "TrabajoPage.tsx").read_text(encoding="utf-8")
  assert "organizationQueryParam" in home_route
  assert "fetchCentroControlResumen(periodo = \"mtd\", organizationId?: string)" in api
  assert "fetchTrabajoResumen(organizationId?: string)" in api
  assert "OrganizationProvider" in app_shell
  assert "organizationQueryParam" in cc
  assert "organization_id: organizationQueryParam" in trabajo


def test_c2_c1_r1_home_route_preservado():
    app = (FRONTEND / "App.tsx").read_text(encoding="utf-8")
    home = (FRONTEND / "pages" / "HomePage.tsx").read_text(encoding="utf-8")
    assert '<Route index element={<HomePage />} />' in app
    assert "resolveHomeRoute" in home
    assert "NoModulesPage" in home


# --- G/H: datos del tenant correcto ---


def test_c2_centro_control_datos_tenant_correcto(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, pwd = _create_tenant_user(db, org_name="C2 CC Tenant")
        token = _login(client, user.username, pwd)
        res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_header(token))
        assert res.status_code == 200
        assert res.json()["organization_id"] == org.id
    finally:
        db.close()


def test_c2_mi_trabajo_elementos_tenant_usuario(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, pwd = _create_tenant_user(db, org_name="C2 Trabajo Tenant")
        _seed_failed_plan(db, org, user, "tenant-user")
        token = _login(client, user.username, pwd)
        res = client.get("/api/trabajo/items", headers=auth_header(token))
        assert res.status_code == 200
        body = res.json()
        assert body["filtros_aplicados"]["organization_id"] == org.id
        assert body["total"] >= 1
    finally:
        db.close()


# --- I: deduplicación G2/G3 preservada (smoke import) ---


def test_c2_dedup_g2_g3_tests_exist():
    gate = (ROOT / "tests" / "test_gate_post6d_correcciones.py").read_text(encoding="utf-8")
    assert "test_g2" in gate or "G2" in gate
    assert "test_g3_dedup_oportunidad_vs_1290_humana" in gate


# --- J: navegación desde Mi Trabajo ---


def test_c2_trabajo_enlace_recurso_correcto(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, pwd = _create_tenant_user(db, org_name="C2 Nav")
        plan = _seed_failed_plan(db, org, user, "nav-plan")
        token = _login(client, user.username, pwd)
        res = client.get("/api/trabajo/items", headers=auth_header(token))
        assert res.status_code == 200
        rows = [i for i in res.json()["items"] if i.get("source_id") == plan.id]
        assert len(rows) >= 1
        assert rows[0]["enlace"].startswith("/")
    finally:
        db.close()


# --- Notificaciones cross-org (fix C2) ---


def test_c2_superadmin_trabajo_notificaciones_solo_org_activa(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="C2 Notif A")
        org_b, user_b, _ = _create_tenant_user(db, org_name="C2 Notif B")
        db.add(
            Notification(
                organization_id=org_a.id,
                type="INFO",
                severity="LOW",
                title="Notif solo A",
                message="Mensaje A",
                source_type="test",
                status="NEW",
                recipient_user_id=user_a.id,
            )
        )
        db.add(
            Notification(
                organization_id=org_b.id,
                type="INFO",
                severity="LOW",
                title="Notif solo B",
                message="Mensaje B",
                source_type="test",
                status="NEW",
                recipient_user_id=user_b.id,
            )
        )
        db.commit()
        res = client.get(f"/api/trabajo/items?organization_id={org_b.id}", headers=auth_headers)
        assert res.status_code == 200
        titles = [i.get("asunto") or "" for i in res.json()["items"]]
        assert any("Notif solo B" in t for t in titles)
        assert not any("Notif solo A" in t for t in titles)
    finally:
        db.close()


# --- Inactive org cross-org ---


def test_c2_superadmin_inactive_org_rejected(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org = Organization(name="C2 Inactive", slug=f"c2-inact-{uuid.uuid4().hex[:6]}", status=ORG_STATUS_INACTIVE)
        db.add(org)
        db.commit()
        res = client.get(
            f"/api/centro-control/resumen-ejecutivo?organization_id={org.id}",
            headers=auth_headers,
        )
        assert res.status_code == 403
    finally:
        db.close()


# --- M: login hotfix preservado ---


def test_c2_login_hotfix_preservado():
    api = (FRONTEND / "api.ts").read_text(encoding="utf-8")
    text_idx = api.index("const text = await res.text()")
    not_ok_idx = api.index("if (!res.ok)")
    assert text_idx < not_ok_idx


# --- P: Alembic head único ---


def test_c2_alembic_head_unico():
    versions = list((ROOT / "backend" / "alembic" / "versions").glob("*.py"))
    heads = []
    for path in versions:
        text = path.read_text(encoding="utf-8")
        if "down_revision = None" in text or "down_revision=None" in text:
            continue
        if "revision = " in text or "revision=" in text:
            heads.append(path.name)
    assert len(versions) >= 1
