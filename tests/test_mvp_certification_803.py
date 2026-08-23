"""CURSOR-803 — certificación integrada MVP."""
import uuid

import pytest

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

SAMPLE_RIPS = {
    "usuarios": [{"tipoDocumentoIdentificacion": "CC", "numDocumentoIdentificacion": "1", "codSexo": "M", "fechaNacimiento": "1980-01-01"}],
    "consultas": [{"codConsulta": "890201", "numDocumentoIdentificacion": "999"}],
    "procedimientos": [], "medicamentos": [], "otrosServicios": [],
}


def _create_org_user(client, org_name: str, username: str, password: str) -> str:
    db = TestingSessionLocal()
    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    db.add(User(organization_id=org.id, username=username, password_hash=hash_password(password), role="admin"))
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_auth_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})
    assert res.status_code == 401


def test_auth_me_requires_token(client, token):
    ok = client.get("/api/auth/me", headers=auth_header(token))
    assert ok.status_code == 200
    assert ok.json()["username"] == "admin"
    denied = client.get("/api/auth/me")
    assert denied.status_code == 401


def test_tenant_cross_org_employee_access(client):
    token_a = _create_org_user(client, "Org A Cert803", f"admin-a-{uuid.uuid4().hex[:6]}", "AdminA803*")
    token_b = _create_org_user(client, "Org B Cert803", f"admin-b-{uuid.uuid4().hex[:6]}", "AdminB803*")

    emp_a = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token_a),
        json={"name": "Empleado Org A", "specialty": "DOCINT"},
    ).json()

    cross = client.get(f"/api/agent-factory/employees/{emp_a['id']}", headers=auth_header(token_b))
    assert cross.status_code == 404

    exec_a = client.post(
        "/api/assistant/ask",
        headers=auth_header(token_a),
        json={"message": "org a docint", "context": {"tool": "docint", "documents": []}},
    ).json()
    assert exec_a["plan_id"]
    cross_exec = client.get(f"/api/operations/executions/{exec_a['plan_id']}", headers=auth_header(token_b))
    assert cross_exec.status_code == 404


def test_knowledge_tenant_isolation(client, token):
    caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    emp = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": f"Knowledge Test {uuid.uuid4().hex[:6]}", "specialty": "DOCINT"},
    ).json()
    client.patch(
        f"/api/agent-factory/employees/{emp['id']}",
        headers=auth_header(token),
        json={
            "capability_ids": [docint_cap["id"]],
            "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
            "knowledge": [{"source_type": "DOCUMENTS", "name": "Docs Org Demo", "config": {"path": "/demo"}}],
        },
    )
    detail = client.get(f"/api/agent-factory/employees/{emp['id']}", headers=auth_header(token)).json()
    assert detail["knowledge"]
    assert detail["knowledge"][0]["name"] == "Docs Org Demo"

    token_b = _create_org_user(client, "Org B Know", f"know-b-{uuid.uuid4().hex[:6]}", "KnowB803*")
    cross = client.get(f"/api/agent-factory/employees/{emp['id']}", headers=auth_header(token_b))
    assert cross.status_code == 404


def test_mvp_full_orchestrator_traceability(client, token):
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={
            "message": "Certificación MVP RIPS",
            "context": {"tool": "rips", "rips": SAMPLE_RIPS},
        },
    )
    assert res.status_code == 200
    plan_id = res.json()["plan_id"]
    detail = client.get(f"/api/operations/executions/{plan_id}", headers=auth_header(token)).json()
    assert detail["tasks"]
    events = client.get("/api/operations/events", headers=auth_header(token)).json()
    plan_events = [e for e in events if e.get("work_plan_id") == plan_id]
    assert any(e["event_type"] == "work.requested" for e in plan_events)
    assert any(e["event_type"] in ("work.completed", "approval.required") for e in plan_events)


def test_alembic_chain_present():
    from pathlib import Path
    versions = list(Path("/workspace/backend/alembic/versions").glob("*.py"))
    assert any("4355c73adcb8" in v.name for v in versions)
    assert any("5b2eb2437398" in v.name for v in versions)
