"""CURSOR-830B — Correcciones post-auditoría Codex."""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.models import Organization, User
from app.orchestration_models import ApprovalRequest, EmployeeTask, WorkPlan
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _viewer_token(client: TestClient) -> str:
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Org Viewer 830B {uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        db.add(
            User(
                organization_id=org.id,
                username=f"viewer830b-{uuid.uuid4().hex[:6]}",
                password_hash=hash_password("Viewer830*"),
                role="viewer",
            )
        )
        db.commit()
        username = db.query(User).filter(User.organization_id == org.id).first().username
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": "Viewer830*"})
    assert login.status_code == 200
    return login.json()["access_token"]


def _pending_approval(org_id: str, user_id: str) -> str:
    db = TestingSessionLocal()
    try:
        plan = WorkPlan(
            organization_id=org_id,
            user_id=user_id,
            correlation_id=str(uuid.uuid4()),
            request="test approval 830b",
            objective="validar permisos",
            status="WAITING_APPROVAL",
            approval_status="PENDING",
        )
        db.add(plan)
        db.flush()
        task = EmployeeTask(
            organization_id=org_id,
            work_plan_id=plan.id,
            title="Tarea de prueba",
            executor_type="TOOL",
            status="WAITING_APPROVAL",
            approval_status="PENDING",
            sequence=1,
        )
        db.add(task)
        db.flush()
        approval = ApprovalRequest(
            organization_id=org_id,
            work_plan_id=plan.id,
            task_id=task.id,
            action="Publicar resultado",
            reason="Prueba 830B",
            status="PENDING",
            requested_by=user_id,
        )
        db.add(approval)
        db.commit()
        return approval.id
    finally:
        db.close()


def test_viewer_approval_denied(client: TestClient, token):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        approval_id = _pending_approval(admin.organization_id, admin.id)
    finally:
        db.close()

    viewer = _viewer_token(client)
    res = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(viewer),
        json={"decision": "approve", "comment": "viewer hack"},
    )
    assert res.status_code == 403


def test_viewer_rejection_denied(client: TestClient, token):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        approval_id = _pending_approval(admin.organization_id, admin.id)
    finally:
        db.close()

    viewer = _viewer_token(client)
    res = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(viewer),
        json={"decision": "reject", "comment": "viewer hack"},
    )
    assert res.status_code == 403


def test_admin_approval_allowed(client: TestClient, token):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        approval_id = _pending_approval(admin.organization_id, admin.id)
    finally:
        db.close()

    res = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(token),
        json={"decision": "approve", "comment": "ok"},
    )
    assert res.status_code == 200


def test_cross_tenant_approval_denied(client: TestClient, token):
    db = TestingSessionLocal()
    try:
        org_b = Organization(name="Org B approval 830B")
        db.add(org_b)
        db.flush()
        user_b = User(
            organization_id=org_b.id,
            username=f"adminb-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Admin830*"),
            role="admin",
        )
        db.add(user_b)
        db.commit()
        approval_id = _pending_approval(org_b.id, user_b.id)
    finally:
        db.close()

    res = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(token),
        json={"decision": "approve", "comment": "cross tenant"},
    )
    assert res.status_code == 404


def test_approval_decide_requires_auth(client: TestClient, token):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        approval_id = _pending_approval(admin.organization_id, admin.id)
    finally:
        db.close()

    res = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        json={"decision": "approve"},
    )
    assert res.status_code == 401


def _configured_employee(client: TestClient, token: str) -> tuple[str, str, str, str]:
    caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": f"Wizard830B {uuid.uuid4().hex[:6]}", "specialty": "DOCINT"},
    )
    emp_id = created.json()["id"]
    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={
            "capability_ids": [docint_cap["id"]],
            "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
            "model_policy": {"preferred_provider": "rule-engine", "preferred_model": "docint-rules-v1"},
        },
    )
    return emp_id, docint_cap["id"], docint_tool["id"], "docint-rules-v1"


def test_wizard_edit_preserves_capabilities(client: TestClient, token):
    emp_id, cap_id, _, _ = _configured_employee(client, token)
    updated = client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={"name": "Nombre actualizado 830B"},
    )
    assert updated.status_code == 200
    detail = client.get(f"/api/agent-factory/employees/{emp_id}", headers=auth_header(token)).json()
    cap_ids = [c["id"] for c in detail["capabilities"]]
    assert cap_id in cap_ids


def test_wizard_edit_preserves_tools(client: TestClient, token):
    emp_id, _, tool_id, _ = _configured_employee(client, token)
    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={"description": "Solo descripción"},
    )
    detail = client.get(f"/api/agent-factory/employees/{emp_id}", headers=auth_header(token)).json()
    tool_ids = [t["id"] for t in detail["tools"]]
    assert tool_id in tool_ids


def test_wizard_edit_preserves_model(client: TestClient, token):
    emp_id, _, _, model_name = _configured_employee(client, token)
    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={"name": "Otro nombre"},
    )
    detail = client.get(f"/api/agent-factory/employees/{emp_id}", headers=auth_header(token)).json()
    assert detail["model_policy"]["model"] == model_name


def test_partial_update_does_not_clear_untouched_fields(client: TestClient, token):
    emp_id, cap_id, tool_id, model_name = _configured_employee(client, token)
    before = client.get(f"/api/agent-factory/employees/{emp_id}", headers=auth_header(token)).json()
    assert before["specialty"] == "DOCINT"

    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={"name": "Parcial 830B"},
    )
    after = client.get(f"/api/agent-factory/employees/{emp_id}", headers=auth_header(token)).json()
    assert after["name"] == "Parcial 830B"
    assert after["specialty"] == "DOCINT"
    assert cap_id in [c["id"] for c in after["capabilities"]]
    assert tool_id in [t["id"] for t in after["tools"]]
    assert after["model_policy"]["model"] == model_name
