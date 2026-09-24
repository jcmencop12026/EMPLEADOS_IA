"""V1 Paquete C — Multi-tenant / alta de empresas / aislamiento."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.automation_models import Automation
from app.models import Organization, User
from app.orchestration_models import AIEmployee
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant_user(
    db: Session,
    *,
    org_name: str,
    username: str | None = None,
    role: str = "admin",
    password: str = "TenantC*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"tenant-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    uname = username or f"user-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=uname,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password


def test_superadmin_can_list_and_create_company(client: TestClient, token):
    headers = auth_header(token)
    listed = client.get("/api/platform/organizations", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    slug = f"acme-{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/platform/organizations",
        headers=headers,
        json={
            "name": f"ACME {slug}",
            "slug": slug,
            "timezone": "America/Bogota",
            "admin_username": f"admin-{slug}",
            "admin_password": "AcmeAdmin2026*",
            "admin_full_name": "Admin ACME",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["organization"]["slug"] == slug
    assert body["admin_username"] == f"admin-{slug}"


def test_duplicate_slug_rejected(client: TestClient, token):
    headers = auth_header(token)
    slug = f"dup-{uuid.uuid4().hex[:6]}"
    payload = {
        "name": f"Empresa {slug}",
        "slug": slug,
        "admin_username": f"u-{slug}",
        "admin_password": "DupTest2026*",
    }
    first = client.post("/api/platform/organizations", headers=headers, json=payload)
    assert first.status_code == 201
    second = client.post(
        "/api/platform/organizations",
        headers=headers,
        json={**payload, "name": f"Otra {slug}", "admin_username": f"u2-{slug}"},
    )
    assert second.status_code == 409


def test_tenant_admin_cannot_create_company(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant_user(db, org_name="Tenant Sin Plataforma", role="admin")
        username = user.username
    finally:
        db.close()
    headers = auth_header(_token(client, username, password))
    res = client.post(
        "/api/platform/organizations",
        headers=headers,
        json={
            "name": "Nueva Empresa",
            "slug": f"nueva-{uuid.uuid4().hex[:6]}",
            "admin_username": f"adm-{uuid.uuid4().hex[:6]}",
            "admin_password": "Nueva2026*",
        },
    )
    assert res.status_code == 403


def test_inactive_company_blocks_login(client: TestClient, token):
    headers = auth_header(token)
    slug = f"inact-{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/platform/organizations",
        headers=headers,
        json={
            "name": f"Inactiva {slug}",
            "slug": slug,
            "admin_username": f"adm-{slug}",
            "admin_password": "Inact2026*",
        },
    )
    assert created.status_code == 201
    org_id = created.json()["organization"]["id"]
    admin_username = created.json()["admin_username"]

    deactivated = client.post(
        f"/api/platform/organizations/{org_id}/status",
        headers=headers,
        json={"status": "INACTIVE"},
    )
    assert deactivated.status_code == 200

    login = client.post("/api/auth/login", json={"username": admin_username, "password": "Inact2026*"})
    assert login.status_code == 401
    assert "inactiva" in login.json()["detail"].lower()


def test_cross_tenant_employee_list_denied(client: TestClient, token):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="Tenant A CF", role="admin")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B CF", role="admin")
        emp_a = AIEmployee(
            organization_id=org_a.id,
            code=f"emp-a-{uuid.uuid4().hex[:6]}",
            name="Empleado A",
            specialty="general",
            lifecycle_status="ACTIVE",
        )
        db.add(emp_a)
        db.commit()
        emp_a_id = emp_a.id
        username_b = user_b.username
        org_a_id = org_a.id
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    listed = client.get("/api/agent-factory/employees", headers=headers_b)
    assert listed.status_code == 200
    ids = {row["id"] for row in listed.json()}
    assert emp_a_id not in ids

    headers_super = auth_header(token)
    super_list = client.get("/api/agent-factory/employees", headers=headers_super)
    assert super_list.status_code == 200
    super_emp_ids = {row["id"] for row in super_list.json()}
    assert emp_a_id not in super_emp_ids


def test_cross_tenant_knowledge_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, password_a = _create_tenant_user(db, org_name="Tenant A Know")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B Know")
        from app.orchestration_models import KnowledgeSource

        source = KnowledgeSource(
            organization_id=org_a.id,
            code=f"src-{uuid.uuid4().hex[:6]}",
            name="Fuente A",
            source_type="manual",
        )
        db.add(source)
        db.commit()
        source_id = source.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    res = client.get(f"/api/knowledge/sources/{source_id}/detail", headers=headers_b)
    assert res.status_code in {403, 404}


def test_cross_tenant_automation_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="Tenant A Auto")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B Auto")

        auto = Automation(
            organization_id=org_a.id,
            name="Auto A",
            status="ACTIVE",
            trigger_type="MANUAL",
            objective="Probar aislamiento",
            created_by_id=user_a.id,
        )
        db.add(auto)
        db.commit()
        auto_id = auto.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    res = client.get(f"/api/automations/{auto_id}", headers=headers_b)
    assert res.status_code == 404


def test_cross_tenant_operations_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="Tenant A Ops")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B Ops")
        from app.orchestration_models import WorkPlan

        plan = WorkPlan(
            organization_id=org_a.id,
            user_id=user_a.id,
            correlation_id=str(uuid.uuid4()),
            request="Solicitud A",
            objective="Objetivo A",
            status="READY",
        )
        db.add(plan)
        db.commit()
        plan_id = plan.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    res = client.get(f"/api/operations/center/{plan_id}", headers=headers_b)
    assert res.status_code == 404


def test_cross_tenant_finops_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="Tenant A Fin")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B Fin")
        from app.orchestration_models import FinOpsRecord, WorkPlan

        plan = WorkPlan(
            organization_id=org_a.id,
            user_id=user_a.id,
            correlation_id=str(uuid.uuid4()),
            request="req",
            objective="obj",
            status="READY",
        )
        db.add(plan)
        db.flush()
        record = FinOpsRecord(
            organization_id=org_a.id,
            work_plan_id=plan.id,
            provider="test",
            category="Otro",
            quantity=1,
            cost=10,
        )
        db.add(record)
        db.commit()
        record_id = plan.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    res = client.get(
        "/api/finops/drill-down",
        headers=headers_b,
        params={"work_plan_id": record_id},
    )
    assert res.status_code == 404


def test_viewer_cannot_manage_companies(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant_user(db, org_name="Viewer Platform", role="viewer")
        username = user.username
    finally:
        db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/platform/organizations", headers=headers)
    assert res.status_code == 403


def test_cross_tenant_opportunities_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="Tenant A Opp")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B Opp")
        from app.opportunity_models import Opportunity

        opp = Opportunity(
            organization_id=org_a.id,
            codigo=f"OPP-{uuid.uuid4().hex[:6]}",
            tipo="EFICIENCIA",
            dominio="operaciones",
            titulo="Oportunidad A",
            estado="DETECTADA",
        )
        db.add(opp)
        db.commit()
        opp_id = opp.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    res = client.get(f"/api/oportunidades/{opp_id}", headers=headers_b)
    assert res.status_code == 404

    listed = client.get("/api/oportunidades", headers=headers_b)
    assert listed.status_code == 200
    ids = {row["id"] for row in listed.json()["items"]}
    assert opp_id not in ids


def test_cross_tenant_audit_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="Tenant A Audit")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B Audit")
        from app.models import AuditLog

        log = AuditLog(
            organization_id=org_a.id,
            user_id=user_a.id,
            action="tenant.test.audit",
            detail="evento tenant A",
        )
        db.add(log)
        db.commit()
        log_id = log.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    res = client.get("/api/audit/logs", headers=headers_b)
    assert res.status_code == 200
    ids = {row["id"] for row in res.json()}
    assert log_id not in ids


def test_cross_tenant_employee_detail_edit_execute_denied(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, _ = _create_tenant_user(db, org_name="Tenant A Emp")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="Tenant B Emp")
        emp_a = AIEmployee(
            organization_id=org_a.id,
            code=f"emp-edit-{uuid.uuid4().hex[:6]}",
            name="Empleado Editar A",
            specialty="general",
            lifecycle_status="ACTIVE",
        )
        db.add(emp_a)
        db.commit()
        emp_a_id = emp_a.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    detail = client.get(f"/api/agent-factory/employees/{emp_a_id}", headers=headers_b)
    assert detail.status_code == 404

    patched = client.patch(
        f"/api/agent-factory/employees/{emp_a_id}",
        headers=headers_b,
        json={"name": "Hackeado"},
    )
    assert patched.status_code == 404

    executed = client.post(f"/api/agent-factory/employees/{emp_a_id}/test", headers=headers_b)
    assert executed.status_code in {400, 404}


def test_bootstrap_org_has_slug(client: TestClient):
    db = TestingSessionLocal()
    try:
        org = db.query(Organization).first()
        assert org is not None
        assert org.slug
    finally:
        db.close()

    me = client.get("/api/auth/me", headers=auth_header(client.post(
        "/api/auth/login", json={"username": "admin", "password": "Admin2026*"}
    ).json()["access_token"]))
    assert me.status_code == 200
    assert "platform.organization.view" in me.json()["permissions"]
