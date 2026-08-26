"""CURSOR-850B — Correcciones post-auditoría Codex."""
from __future__ import annotations

import subprocess
import uuid

import pytest

from app.enums import ToolPermission
from app.models import Organization, User
from app.orchestration_models import Capability, EmployeeCapability, EmployeeToolGrant, Tool
from app.security import hash_password
from app.services.authorization import AuthorizationError, ExecutionDecision, evaluate_tool_execution
from app.services.coordinator import get_tool_execution_counter, reset_tool_execution_counter
from conftest import TestingSessionLocal, auth_header

SAMPLE_DOC = {
    "tool": "docint",
    "documents": [{
        "id": "d1",
        "tipo_documento": "CC",
        "numero_documento": "1234567890",
        "fecha": "2026-01-01",
        "contenido": "Documento de prueba con contenido suficiente para análisis",
    }],
}

SAMPLE_RIPS = {
    "tool": "rips",
    "rips": {
        "usuarios": [{"tipoDocumentoIdentificacion": "CC", "numDocumentoIdentificacion": "1", "codSexo": "M", "fechaNacimiento": "1980-01-01"}],
        "consultas": [],
        "procedimientos": [],
        "medicamentos": [],
        "otrosServicios": [],
    },
}


def _assign_employee(client, token, emp_id, cap_code="docint", tool_code="docint", permission="ALLOW"):
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    cap = next(c for c in caps if c["code"] == cap_code)
    tool = next(t for t in tools if t["code"] == tool_code)
    client.post(f"/api/capabilities/employees/{emp_id}/assign/{cap['id']}", headers=auth_header(token))
    client.post(
        f"/api/tools/employees/{emp_id}/assign",
        headers=auth_header(token),
        json={"tool_id": tool["id"], "permission": permission},
    )
    return cap, tool


def _create_employee(client, token, name=None):
    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": name or f"Emp850B-{uuid.uuid4().hex[:6]}", "specialty": "DOCINT"},
    )
    assert created.status_code == 200
    return created.json()["id"]


def test_tool_not_executed_before_approval(client, token):
    reset_tool_execution_counter()
    emp_id = _create_employee(client, token, "Before Approval")
    cap, tool = _assign_employee(client, token, emp_id, "rips", "rips", "ALLOW")

    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={
            "employee_id": emp_id,
            "capability_id": cap["id"],
            "tool_id": tool["id"],
            "task_description": "RIPS approval gate",
            "context": SAMPLE_RIPS,
        },
    )
    assert run.status_code == 200
    assert run.json()["status"] == "ESPERANDO_APROBACION"
    assert get_tool_execution_counter() == 0


def test_reject_means_zero_tool_executions(client, token):
    reset_tool_execution_counter()
    emp_id = _create_employee(client, token, "Reject Zero")
    cap, tool = _assign_employee(client, token, emp_id, "rips", "rips", "ALLOW")
    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={"employee_id": emp_id, "capability_id": cap["id"], "tool_id": tool["id"], "task_description": "reject", "context": SAMPLE_RIPS},
    )
    approval_id = run.json()["approval_id"]
    client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(token),
        json={"decision": "reject", "comment": "no"},
    )
    assert get_tool_execution_counter() == 0


def test_approve_executes_tool_after_decision(client, token):
    reset_tool_execution_counter()
    emp_id = _create_employee(client, token, "Approve After")
    cap, tool = _assign_employee(client, token, emp_id, "rips", "rips", "ALLOW")
    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={"employee_id": emp_id, "capability_id": cap["id"], "tool_id": tool["id"], "task_description": "approve", "context": SAMPLE_RIPS},
    )
    approval_id = run.json()["approval_id"]
    assert get_tool_execution_counter() == 0
    approved = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(token),
        json={"decision": "approve", "comment": "ok"},
    )
    assert approved.status_code == 200
    assert get_tool_execution_counter() == 1


def test_capability_requires_approval(client, token):
    emp_id = _create_employee(client, token, "Cap Req Approval")
    _assign_employee(client, token, emp_id, "docint", "docint", "ALLOW")
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    org_id = admin.organization_id
    cap = db.query(Capability).filter(Capability.code == "docint").first()
    tool = db.query(Tool).filter(Tool.code == "docint").first()
    cap.requires_approval = True
    tool.requires_approval = False
    db.commit()
    decision, _, _ = evaluate_tool_execution(
        db, org_id=org_id, employee_id=emp_id, tool_id=tool.id, capability_id=cap.id, user_id=admin.id,
    )
    cap.requires_approval = False
    db.commit()
    db.close()
    assert decision == ExecutionDecision.REQUIRES_APPROVAL


def test_capability_deny_overrides_tool_allow(client, token):
    emp_id = _create_employee(client, token, "Grant Deny")
    _assign_employee(client, token, emp_id, "docint", "docint", "DENY")
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    org_id = admin.organization_id
    tool = db.query(Tool).filter(Tool.code == "docint").first()
    cap = db.query(Capability).filter(Capability.code == "docint").first()
    decision, _, _ = evaluate_tool_execution(
        db, org_id=org_id, employee_id=emp_id, tool_id=tool.id, capability_id=cap.id, user_id=admin.id,
    )
    db.close()
    assert decision == ExecutionDecision.DENY


def test_tool_requires_approval_overrides_capability_allow(client, token):
    emp_id = _create_employee(client, token, "Tool Req")
    _assign_employee(client, token, emp_id, "docint", "docint", "ALLOW")
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    org_id = admin.organization_id
    tool = db.query(Tool).filter(Tool.code == "docint").first()
    cap = db.query(Capability).filter(Capability.code == "docint").first()
    cap.requires_approval = False
    tool.requires_approval = True
    db.commit()
    decision, _, _ = evaluate_tool_execution(
        db, org_id=org_id, employee_id=emp_id, tool_id=tool.id, capability_id=cap.id, user_id=admin.id,
    )
    tool.requires_approval = False
    db.commit()
    db.close()
    assert decision == ExecutionDecision.REQUIRES_APPROVAL


def test_arbitrary_permission_does_not_authorize_tool(client, token):
    """Admin API permissions no sustituyen asignación employee/tool."""
    emp_id = _create_employee(client, token, "No Assignment")
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    org_id = admin.organization_id
    tool = db.query(Tool).filter(Tool.code == "docint").first()
    cap = db.query(Capability).filter(Capability.code == "docint").first()
    decision, _, _ = evaluate_tool_execution(
        db, org_id=org_id, employee_id=emp_id, tool_id=tool.id, capability_id=cap.id, user_id=admin.id,
    )
    db.close()
    assert decision == ExecutionDecision.DENY


def test_no_capability_assignment_deny(client, token):
    emp_id = _create_employee(client, token, "No Cap")
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    org_id = admin.organization_id
    tool = db.query(Tool).filter(Tool.code == "docint").first()
    cap = db.query(Capability).filter(Capability.code == "docint").first()
    decision, _, _ = evaluate_tool_execution(
        db, org_id=org_id, employee_id=emp_id, tool_id=tool.id, capability_id=cap.id, user_id=admin.id,
    )
    db.close()
    assert decision == ExecutionDecision.DENY


def test_cross_tenant_deny(client, token):
    db = TestingSessionLocal()
    org_b = Organization(name=f"ORG-B-850B-{uuid.uuid4().hex[:6]}")
    db.add(org_b)
    db.flush()
    user_b = User(
        organization_id=org_b.id,
        username=f"b-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Admin2026*"),
        role="admin",
    )
    db.add(user_b)
    db.flush()
    cap_b = Capability(organization_id=org_b.id, code="xcap", name="X", risk_level="low")
    db.add(cap_b)
    db.flush()
    tool_b = Tool(organization_id=org_b.id, capability_id=cap_b.id, code="xtool", name="X Tool", executor_type="PYTHON", risk_level="low")
    db.add(tool_b)
    db.commit()
    org_a = db.query(Organization).filter(Organization.id != org_b.id).first()
    emp_a = _create_employee(client, token)
    with pytest.raises(AuthorizationError):
        evaluate_tool_execution(
            db, org_id=org_a.id, employee_id=emp_a, tool_id=tool_b.id, capability_id=cap_b.id, user_id=user_b.id,
        )
    db.close()


def test_test_lab_uses_same_policy_as_production(client, token):
    reset_tool_execution_counter()
    emp_id = _create_employee(client, token, "Lab Policy")
    cap, tool = _assign_employee(client, token, emp_id, "rips", "rips", "ALLOW")
    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={"employee_id": emp_id, "capability_id": cap["id"], "tool_id": tool["id"], "task_description": "lab", "context": SAMPLE_RIPS},
    )
    assert run.json()["status"] == "ESPERANDO_APROBACION"
    assert get_tool_execution_counter() == 0


def test_git_diff_check_clean():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "diff", "--check"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
