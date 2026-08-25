import uuid

import pytest

pytestmark = [pytest.mark.auth, pytest.mark.tenant]

from app.models import Organization, User
from app.orchestration_models import EmployeeTask, WorkEvent
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

SAMPLE_RIPS = {
    "usuarios": [
        {
            "tipoDocumentoIdentificacion": "CC",
            "numDocumentoIdentificacion": "1234567890",
            "codSexo": "M",
            "fechaNacimiento": "1980-01-15",
        }
    ],
    "consultas": [{"codConsulta": "890201", "numDocumentoIdentificacion": "9999999999"}],
    "procedimientos": [],
    "medicamentos": [],
    "otrosServicios": [],
}


def _pause_docint_active(client, token):
    paused = []
    for e in client.get("/api/agent-factory/employees", headers=auth_header(token)).json():
        if e.get("lifecycle_status") == "ACTIVE" and "DOCINT" in e.get("specialty", ""):
            client.post(f"/api/agent-factory/employees/{e['id']}/pause", headers=auth_header(token))
            paused.append(e["id"])
    return paused


def _restore_paused(client, token, ids: list[str]):
    for eid in ids:
        emp = client.get(f"/api/agent-factory/employees/{eid}", headers=auth_header(token)).json()
        if emp.get("lifecycle_status") == "PAUSED":
            client.post(f"/api/agent-factory/employees/{eid}/activate", headers=auth_header(token))


def test_list_templates(client, token):
    res = client.get("/api/agent-factory/templates", headers=auth_header(token))
    assert res.status_code == 200
    codes = {t["code"] for t in res.json()}
    assert "analista-documental" in codes
    assert "auditor-rips" in codes


def test_create_configure_test_certify_publish_activate(client, token):
    caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": "Test DOCINT 802", "specialty": "DOCINT", "template_code": "analista-documental"},
    )
    assert created.status_code == 200
    emp_id = created.json()["id"]

    updated = client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={
            "capability_ids": [docint_cap["id"]],
            "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
            "model_policy": {"preferred_provider": "rule-engine", "preferred_model": "docint-rules-v1"},
            "risk_level": "MEDIUM",
        },
    )
    assert updated.status_code == 200

    test_res = client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=auth_header(token))
    assert test_res.status_code == 200
    assert test_res.json()["total"] >= 1

    cert = client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=auth_header(token))
    assert cert.status_code == 200
    assert cert.json()["result"] in ("PASS", "PASS_WITH_WARNINGS")

    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub.status_code == 200
    assert pub.json()["lifecycle_status"] == "PUBLISHED"

    act = client.post(f"/api/agent-factory/employees/{emp_id}/activate", headers=auth_header(token))
    assert act.status_code == 200
    assert act.json()["lifecycle_status"] == "ACTIVE"
    db = TestingSessionLocal()
    try:
        event_types = {row.event_type for row in db.query(WorkEvent).all()
                       if emp_id in (row.payload_json or "")}
        assert {"employee.created", "employee.certified", "employee.activated"} <= event_types
    finally:
        db.close()


def test_orchestrator_selects_published_employee(client, token):
    caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": "Orch Select 802", "specialty": "DOCINT", "template_code": "analista-documental"},
    )
    emp_id = created.json()["id"]
    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={
            "capability_ids": [docint_cap["id"]],
            "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
        },
    )
    client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/activate", headers=auth_header(token))

    orch = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={
            "message": "Analiza documentos",
            "context": {
                "tool": "docint",
                "documents": [
                    {
                        "id": "d1",
                        "tipo_documento": "CC",
                        "numero_documento": "1234567890",
                        "fecha": "2026-01-01",
                        "contenido": "Documento de prueba suficientemente largo",
                    }
                ],
            },
        },
    )
    assert orch.status_code == 200
    assert orch.json()["plan_id"]


def test_permission_denied_viewer(client):
    username = f"viewer-{uuid.uuid4().hex[:8]}"
    db = TestingSessionLocal()
    org = db.query(Organization).first()
    db.add(User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password("Viewer802*"),
        role="viewer",
    ))
    db.commit()
    db.close()

    login = client.post("/api/auth/login", json={"username": username, "password": "Viewer802*"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    res = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": "X", "specialty": "Y"},
    )
    assert res.status_code == 403


def test_tenant_isolation_employees(client, token):
    res = client.get("/api/agent-factory/employees", headers=auth_header(token))
    assert res.status_code == 200
    for emp in res.json():
        detail = client.get(f"/api/agent-factory/employees/{emp['id']}", headers=auth_header(token))
        assert detail.status_code == 200


def test_existing_health_employees_active(client, token):
    res = client.get("/api/agent-factory/employees", headers=auth_header(token))
    names = {e["name"] for e in res.json()}
    assert "Analista Documental IA" in names
    docint = next(e for e in res.json() if e["name"] == "Analista Documental IA")
    assert docint["lifecycle_status"] == "ACTIVE"


def test_regression_orchestrator_rips(client, token):
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "RIPS regression", "context": {"tool": "rips", "rips": SAMPLE_RIPS}},
    )
    assert res.status_code == 200
    assert res.json()["plan_id"]


def test_draft_employee_not_selected_by_orchestrator(client, token):
    paused = _pause_docint_active(client, token)
    try:
        caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
        tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
        docint_cap = next(c for c in caps if c["code"] == "docint")
        docint_tool = next(t for t in tools if t["code"] == "docint")

        draft = client.post(
            "/api/agent-factory/employees",
            headers=auth_header(token),
            json={"name": f"Solo Draft {uuid.uuid4().hex[:6]}", "specialty": "DOCINT"},
        ).json()
        client.patch(
            f"/api/agent-factory/employees/{draft['id']}",
            headers=auth_header(token),
            json={
                "capability_ids": [docint_cap["id"]],
                "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
            },
        )
        assert draft["lifecycle_status"] == "DRAFT"

        orch = client.post(
            "/api/assistant/ask",
            headers=auth_header(token),
            json={"message": "audit draft only", "context": {"tool": "docint", "documents": []}},
        ).json()
        assert orch.get("plan_id")
        db = TestingSessionLocal()
        task = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == orch["plan_id"]).first()
        db.close()
        assert task is not None
        assert task.employee_id is None or task.employee_id != draft["id"]
    finally:
        _restore_paused(client, token, paused)


def test_deny_blocks_orchestrator_execution(client, token):
    paused = _pause_docint_active(client, token)
    try:
        caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
        tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
        docint_cap = next(c for c in caps if c["code"] == "docint")
        docint_tool = next(t for t in tools if t["code"] == "docint")

        created = client.post(
            "/api/agent-factory/employees",
            headers=auth_header(token),
            json={"name": f"Deny Orch {uuid.uuid4().hex[:6]}", "specialty": "DOCINT"},
        ).json()
        emp_id = created["id"]
        client.patch(
            f"/api/agent-factory/employees/{emp_id}",
            headers=auth_header(token),
            json={
                "capability_ids": [docint_cap["id"]],
                "tools": [{"tool_id": docint_tool["id"], "permission": "DENY"}],
            },
        )
        for step in ("test", "certify", "publish", "activate"):
            client.post(f"/api/agent-factory/employees/{emp_id}/{step}", headers=auth_header(token))

        orch = client.post(
            "/api/assistant/ask",
            headers=auth_header(token),
            json={"message": "deny orch audit", "context": {"tool": "docint", "documents": []}},
        ).json()
        assert orch["status"] == "FAILED"
        assert "denegada" in (orch.get("error") or "").lower()
        db = TestingSessionLocal()
        try:
            assert db.query(WorkEvent).filter(WorkEvent.work_plan_id == orch["plan_id"],
                                              WorkEvent.event_type == "TOOL_DENIED").first()
        finally:
            db.close()
    finally:
        _restore_paused(client, token, paused)


def test_finops_limit_reached_is_published_from_real_execution(client, token):
    paused = _pause_docint_active(client, token)
    try:
        caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
        tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
        cap = next(c for c in caps if c["code"] == "docint")
        tool = next(t for t in tools if t["code"] == "docint")
        emp = client.post("/api/agent-factory/employees", headers=auth_header(token),
                          json={"name": f"FinOps {uuid.uuid4().hex[:6]}", "specialty": "DOCINT"}).json()
        client.patch(f"/api/agent-factory/employees/{emp['id']}", headers=auth_header(token), json={
            "capability_ids": [cap["id"]], "tools": [{"tool_id": tool["id"], "permission": "ALLOW"}],
            "limits": {"daily_cost_limit": 0},
        })
        for step in ("test", "certify", "publish", "activate"):
            client.post(f"/api/agent-factory/employees/{emp['id']}/{step}", headers=auth_header(token))
        result = client.post("/api/assistant/ask", headers=auth_header(token), json={
            "message": "FinOps limit", "context": {"tool": "docint", "documents": []},
        }).json()
        assert result["status"] == "FAILED"
        db = TestingSessionLocal()
        try:
            assert db.query(WorkEvent).filter(WorkEvent.work_plan_id == result["plan_id"],
                                              WorkEvent.event_type == "FINOPS_LIMIT_REACHED").first()
        finally:
            db.close()
    finally:
        _restore_paused(client, token, paused)
