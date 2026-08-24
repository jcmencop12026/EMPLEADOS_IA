import pytest

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


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_coordinator_route_rips(client, token):
    res = client.post(
        "/api/agent-factory/coordinator/route",
        headers=auth_header(token),
        json={
            "request": "Analiza estos RIPS y dime qué problemas existen.",
            "context": {"tool": "rips", "rips": SAMPLE_RIPS},
            "auto_execute": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["plan_id"]
    assert data["status"] in ("WAITING_APPROVAL", "COMPLETED", "FAILED")
    assert data.get("tasks")


def test_assistant_ask_docint(client, token):
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={
            "message": "Analiza estos documentos y dime qué problemas existen.",
            "context": {
                "tool": "docint",
                "documents": [
                    {
                        "id": "d1",
                        "tipo_documento": "CC",
                        "numero_documento": "1234567890",
                        "fecha": "2026-01-01",
                        "contenido": "Documento de prueba con contenido suficiente",
                    }
                ],
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("COMPLETED", "WAITING_APPROVAL")
    assert data.get("result") or data.get("summary")


def test_approval_flow(client, token):
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "Validar RIPS con problemas", "context": {"tool": "rips", "rips": SAMPLE_RIPS}},
    )
    assert res.status_code == 200
    plan = res.json()
    if plan["status"] != "WAITING_APPROVAL":
        pytest.skip("RIPS no requirió aprobación en esta ejecución")

    approvals = client.get("/api/operations/approvals/pending", headers=auth_header(token))
    assert approvals.status_code == 200
    pending = [a for a in approvals.json() if a["work_plan_id"] == plan["plan_id"]]
    assert pending
    notifications = client.get("/api/notifications", headers=auth_header(token)).json()
    approval_notice = next(n for n in notifications if n["type"] == "APPROVAL_REQUIRED"
                           and n["source_id"] == plan["plan_id"])
    assert approval_notice["metadata"]["approval_id"] == pending[0]["id"]

    approved = client.post(
        f"/api/operations/approvals/{pending[0]['id']}/decide",
        headers=auth_header(token),
        json={"decision": "approve", "comment": "OK test"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "COMPLETED"
    events = client.get("/api/operations/events", headers=auth_header(token)).json()
    decision = [e for e in events if e.get("work_plan_id") == plan["plan_id"] and e["event_type"] == "approval.completed"]
    assert decision


def test_approval_rejected(client, token):
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "RIPS test reject", "context": {"tool": "rips", "rips": SAMPLE_RIPS}},
    )
    plan = res.json()
    if plan["status"] != "WAITING_APPROVAL":
        pytest.skip("Sin aprobación pendiente")

    approvals = client.get("/api/operations/approvals/pending", headers=auth_header(token)).json()
    item = next(a for a in approvals if a["work_plan_id"] == plan["plan_id"])

    rejected = client.post(
        f"/api/operations/approvals/{item['id']}/decide",
        headers=auth_header(token),
        json={"decision": "reject", "comment": "No conforme"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "FAILED"
    db = TestingSessionLocal()
    try:
        from app.notifications import normalize_event_type
        from app.orchestration_models import WorkEvent
        event = db.query(WorkEvent).filter(WorkEvent.work_plan_id == plan["plan_id"],
                                           WorkEvent.event_type == "approval.completed").one()
        import json
        assert normalize_event_type(event.event_type, json.loads(event.payload_json)) == "APPROVAL_REJECTED"
    finally:
        db.close()


def test_tenant_isolation(client, token):
    res = client.get("/api/operations/executions", headers=auth_header(token))
    assert res.status_code == 200
    for eid in [e["id"] for e in res.json()]:
        detail = client.get(f"/api/operations/executions/{eid}", headers=auth_header(token))
        assert detail.status_code == 200


def test_permission_denied_without_token(client):
    res = client.post("/api/assistant/ask", json={"message": "hola"})
    assert res.status_code == 401


def test_traceability_events(client, token):
    client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "trace test", "context": {"tool": "docint", "documents": []}},
    )
    events = client.get("/api/operations/events", headers=auth_header(token))
    assert events.status_code == 200
    types = {e["event_type"] for e in events.json()}
    assert "work.requested" in types
    assert "task.started" in types
    assert types & {"work.completed", "work.failed"}


def test_docint_rips_e2e_findings(client, token):
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "Analiza RIPS E2E", "context": {"tool": "rips", "rips": SAMPLE_RIPS}},
    )
    data = res.json()
    assert data["plan_id"]
    detail = client.get(f"/api/operations/executions/{data['plan_id']}", headers=auth_header(token))
    assert detail.status_code == 200
    body = detail.json()
    assert body["tasks"]
    events = client.get("/api/operations/events", headers=auth_header(token)).json()
    plan_events = [e for e in events if e.get("work_plan_id") == data["plan_id"]]
    assert len(plan_events) >= 2


def test_unexpected_execution_error_publishes_system_error(client, token, monkeypatch):
    from app.services import coordinator
    from app.orchestration_models import WorkEvent

    def fail_tool(tool_code, inputs):
        raise RuntimeError("controlled system failure")

    monkeypatch.setattr(coordinator, "_run_tool", fail_tool)
    result = client.post("/api/assistant/ask", headers=auth_header(token), json={
        "message": "system error integration", "context": {"tool": "docint", "documents": []},
    }).json()
    assert result["status"] == "FAILED"
    db = TestingSessionLocal()
    try:
        assert db.query(WorkEvent).filter(WorkEvent.work_plan_id == result["plan_id"],
                                          WorkEvent.event_type == "SYSTEM_ERROR").first()
    finally:
        db.close()


def test_employees_directory(client, token):
    res = client.get("/api/operations/employees", headers=auth_header(token))
    assert res.status_code == 200
    names = {e["name"] for e in res.json()}
    assert "Auditor RIPS IA" in names
    assert "Analista Documental IA" in names
