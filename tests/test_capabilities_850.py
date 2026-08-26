"""CURSOR-850: Capabilities, Tools, Knowledge, Test Lab."""

import uuid

import pytest

from app.models import Organization, User
from app.orchestration_models import AIEmployee, Capability, EmployeeCapability, EmployeeToolGrant, Tool
from app.security import hash_password
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


def _create_org_b(client) -> tuple[str, str]:
  """Crea ORG B con admin y devuelve (token, org_id)."""
  db = TestingSessionLocal()
  org_b = Organization(name=f"ORG-B-{uuid.uuid4().hex[:6]}")
  db.add(org_b)
  db.flush()
  user_b = User(
      organization_id=org_b.id,
      username=f"admin-b-{uuid.uuid4().hex[:6]}",
      password_hash=hash_password("Admin2026*"),
      role="admin",
  )
  db.add(user_b)
  db.commit()
  org_id = org_b.id
  token = client.post("/api/auth/login", json={"username": user_b.username, "password": "Admin2026*"}).json()["access_token"]
  db.close()
  return token, org_id


def _create_employee(client, token, name="Empleado Test 850"):
    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": name, "specialty": "DOCINT"},
    )
    assert created.status_code == 200
    return created.json()["id"]


def test_capabilities_crud(client, token):
    created = client.post(
        "/api/capabilities",
        headers=auth_header(token),
        json={"name": "Validar datos", "category": "validacion", "risk_level": "LOW"},
    )
    assert created.status_code == 200
    cap = created.json()
    assert cap["status"] == "ACTIVA"

    listed = client.get("/api/capabilities", headers=auth_header(token))
    assert listed.status_code == 200
    assert any(c["id"] == cap["id"] for c in listed.json())

    updated = client.patch(
        f"/api/capabilities/{cap['id']}",
        headers=auth_header(token),
        json={"description": "Capacidad de validación"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Capacidad de validación"

    deactivated = client.post(f"/api/capabilities/{cap['id']}/deactivate", headers=auth_header(token))
    assert deactivated.status_code == 200
    assert deactivated.json()["status"] == "INACTIVA"


def test_tools_crud(client, token):
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")

    created = client.post(
        "/api/tools",
        headers=auth_header(token),
        json={"name": "Herramienta Test", "capability_id": docint_cap["id"], "tool_type": "PYTHON"},
    )
    assert created.status_code == 200
    tool = created.json()
    assert tool["status"] == "ACTIVA"

    listed = client.get("/api/tools", headers=auth_header(token))
    assert any(t["id"] == tool["id"] for t in listed.json())

    updated = client.patch(
        f"/api/tools/{tool['id']}",
        headers=auth_header(token),
        json={"description": "Herramienta de prueba"},
    )
    assert updated.status_code == 200


def test_knowledge_crud_and_ingest(client, token):
    created = client.post(
        "/api/knowledge/sources",
        headers=auth_header(token),
        json={"name": "Manual interno", "source_type": "TEXT", "description": "Notas"},
    )
    assert created.status_code == 200
    source = created.json()

    ingest = client.post(
        f"/api/knowledge/sources/{source['id']}/ingest",
        headers=auth_header(token),
        json={"content": "Texto de conocimiento de prueba para ingesta V1"},
    )
    assert ingest.status_code == 200
    assert ingest.json()["status"] == "COMPLETADO"


def test_employee_capability_assignment(client, token):
    emp_id = _create_employee(client, token)
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")

    assigned = client.post(
        f"/api/capabilities/employees/{emp_id}/assign/{docint_cap['id']}",
        headers=auth_header(token),
    )
    assert assigned.status_code == 200
    assert any(c["id"] == docint_cap["id"] for c in assigned.json()["assigned"])


def test_employee_tool_assignment(client, token):
    emp_id = _create_employee(client, token)
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    client.post(f"/api/capabilities/employees/{emp_id}/assign/{docint_cap['id']}", headers=auth_header(token))
    assigned = client.post(
        f"/api/tools/employees/{emp_id}/assign",
        headers=auth_header(token),
        json={"tool_id": docint_tool["id"], "permission": "ALLOW"},
    )
    assert assigned.status_code == 200
    assert any(t["id"] == docint_tool["id"] for t in assigned.json()["assigned"])


def test_employee_knowledge_assignment(client, token):
    emp_id = _create_employee(client, token)
    source = client.post(
        "/api/knowledge/sources",
        headers=auth_header(token),
        json={"name": "Base DOCINT", "source_type": "TEXT"},
    ).json()

    assigned = client.post(
        f"/api/knowledge/employees/{emp_id}/assign/{source['id']}",
        headers=auth_header(token),
    )
    assert assigned.status_code == 200
    assert any(k["id"] == source["id"] for k in assigned.json()["assigned"])


def test_tenant_isolation_capability(client, token):
    token_b, _ = _create_org_b(client)
    caps_a = client.get("/api/capabilities", headers=auth_header(token)).json()
    cap_a = caps_a[0]

    res = client.post(
        f"/api/capabilities/employees/{_create_employee(client, token_b)}/assign/{cap_a['id']}",
        headers=auth_header(token_b),
    )
    assert res.status_code == 400


def test_tenant_isolation_cross_org_tool(client, token):
    token_b, org_b = _create_org_b(client)
    db = TestingSessionLocal()
    tool_b = db.query(Tool).filter(Tool.organization_id == org_b).first()
    if not tool_b:
        cap_b = Capability(organization_id=org_b, code="x-cap", name="X", risk_level="low")
        db.add(cap_b)
        db.flush()
        tool_b = Tool(organization_id=org_b, capability_id=cap_b.id, code="x-tool", name="X Tool", executor_type="PYTHON", risk_level="low")
        db.add(tool_b)
        db.commit()
    tool_id = tool_b.id
    db.close()

    emp_a = _create_employee(client, token)
    res = client.post(
        f"/api/tools/employees/{emp_a}/assign",
        headers=auth_header(token),
        json={"tool_id": tool_id},
    )
    assert res.status_code == 400


def test_test_lab_allowed_execution(client, token):
    emp_id = _create_employee(client, token, "Test Lab OK")
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    client.post(f"/api/capabilities/employees/{emp_id}/assign/{docint_cap['id']}", headers=auth_header(token))
    client.post(
        f"/api/tools/employees/{emp_id}/assign",
        headers=auth_header(token),
        json={"tool_id": docint_tool["id"], "permission": "ALLOW"},
    )

    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={
            "employee_id": emp_id,
            "capability_id": docint_cap["id"],
            "tool_id": docint_tool["id"],
            "task_description": "Analizar documentos de prueba",
            "context": SAMPLE_DOC,
        },
    )
    assert run.status_code == 200
    data = run.json()
    assert data["status"] in ("COMPLETADO", "ESPERANDO_APROBACION")
    assert data["work_plan_id"]


def test_test_lab_blocked_without_capability(client, token):
    emp_id = _create_employee(client, token, "Sin Cap")
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={
            "employee_id": emp_id,
            "capability_id": docint_cap["id"],
            "tool_id": docint_tool["id"],
            "task_description": "Debe bloquearse",
            "context": SAMPLE_DOC,
        },
    )
    assert run.status_code == 200
    assert run.json()["status"] == "BLOQUEADO"


def test_test_lab_blocked_without_tool(client, token):
    emp_id = _create_employee(client, token, "Sin Tool")
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    client.post(f"/api/capabilities/employees/{emp_id}/assign/{docint_cap['id']}", headers=auth_header(token))

    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={
            "employee_id": emp_id,
            "capability_id": docint_cap["id"],
            "tool_id": docint_tool["id"],
            "task_description": "Sin herramienta asignada",
            "context": SAMPLE_DOC,
        },
    )
    assert run.status_code == 200
    assert run.json()["status"] == "BLOQUEADO"


def test_test_lab_blocked_disabled_tool(client, token):
    emp_id = _create_employee(client, token, "Tool Disabled")
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    client.post(f"/api/capabilities/employees/{emp_id}/assign/{docint_cap['id']}", headers=auth_header(token))
    client.post(
        f"/api/tools/employees/{emp_id}/assign",
        headers=auth_header(token),
        json={"tool_id": docint_tool["id"], "permission": "ALLOW"},
    )
    client.post(f"/api/tools/{docint_tool['id']}/deactivate", headers=auth_header(token))

    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={
            "employee_id": emp_id,
            "capability_id": docint_cap["id"],
            "tool_id": docint_tool["id"],
            "task_description": "Tool desactivada",
            "context": SAMPLE_DOC,
        },
    )
    assert run.status_code == 200
    assert run.json()["status"] == "BLOQUEADO"

    client.post(f"/api/tools/{docint_tool['id']}/activate", headers=auth_header(token))


def test_test_lab_waiting_approval(client, token):
    emp_id = _create_employee(client, token, "Approval Required")
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    rips_cap = next(c for c in caps if c["code"] == "rips")
    rips_tool = next(t for t in tools if t["code"] == "rips")

    client.post(f"/api/capabilities/employees/{emp_id}/assign/{rips_cap['id']}", headers=auth_header(token))
    client.post(
        f"/api/tools/employees/{emp_id}/assign",
        headers=auth_header(token),
        json={"tool_id": rips_tool["id"], "permission": "ALLOW"},
    )

    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={
            "employee_id": emp_id,
            "capability_id": rips_cap["id"],
            "tool_id": rips_tool["id"],
            "task_description": "Validar RIPS con aprobación",
            "context": {"tool": "rips", "rips": {"usuarios": [], "consultas": [], "procedimientos": [], "medicamentos": [], "otrosServicios": []}},
        },
    )
    assert run.status_code == 200
    assert run.json()["status"] == "ESPERANDO_APROBACION"
    assert run.json().get("approval_id")


def test_test_lab_knowledge_not_assigned(client, token):
    emp_id = _create_employee(client, token, "No Knowledge")
    caps = client.get("/api/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")
    source = client.post("/api/knowledge/sources", headers=auth_header(token), json={"name": "KB", "source_type": "TEXT"}).json()

    client.post(f"/api/capabilities/employees/{emp_id}/assign/{docint_cap['id']}", headers=auth_header(token))
    client.post(
        f"/api/tools/employees/{emp_id}/assign",
        headers=auth_header(token),
        json={"tool_id": docint_tool["id"], "permission": "ALLOW"},
    )

    run = client.post(
        "/api/test-lab/run",
        headers=auth_header(token),
        json={
            "employee_id": emp_id,
            "capability_id": docint_cap["id"],
            "tool_id": docint_tool["id"],
            "knowledge_source_ids": [source["id"]],
            "task_description": "Fuente no asignada",
            "context": SAMPLE_DOC,
        },
    )
    assert run.status_code == 200
    assert run.json()["status"] == "BLOQUEADO"


def test_permissions_viewer_cannot_manage(client, token, unique_username):
    db = TestingSessionLocal()
    org = db.query(Organization).first()
    viewer = User(
        organization_id=org.id,
        username=unique_username,
        password_hash=hash_password("Viewer2026*"),
        role="viewer",
    )
    db.add(viewer)
    db.commit()
    db.close()

    viewer_token = client.post("/api/auth/login", json={"username": unique_username, "password": "Viewer2026*"}).json()["access_token"]
    res = client.post(
        "/api/capabilities",
        headers=auth_header(viewer_token),
        json={"name": "No permitido", "risk_level": "LOW"},
    )
    assert res.status_code == 403


def test_audit_capability_created(client, token):
    client.post(
        "/api/capabilities",
        headers=auth_header(token),
        json={"name": "Audit Cap", "risk_level": "LOW"},
    )
    logs = client.get("/api/audit/logs", headers=auth_header(token))
    assert logs.status_code == 200
    actions = [l["action"] for l in logs.json()]
    assert "capability.created" in actions
