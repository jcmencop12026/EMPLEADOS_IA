"""Tests OPERACIONES-940 — Centro de Operaciones."""
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

pytestmark = pytest.mark.operations


def _create_org_user(client, org_name: str, username: str, password: str, role: str = "admin") -> str:
    db = TestingSessionLocal()
    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    db.add(User(organization_id=org.id, username=username, password_hash=hash_password(password), role=role))
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def _create_plan(client, token: str) -> str:
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "analizar rips", "context": {"tool": "rips", "rips": SAMPLE_RIPS}, "auto_execute": True},
    )
    assert res.status_code == 200
    return res.json()["plan_id"]


def test_operations_summary_and_list(client, token):
    plan_id = _create_plan(client, token)
    summary = client.get("/api/operations/summary", headers=auth_header(token))
    assert summary.status_code == 200
    assert summary.json()["pending"] >= 0
    listed = client.get("/api/operations/center", headers=auth_header(token))
    assert listed.status_code == 200
    assert any(row["id"] == plan_id for row in listed.json())


def test_operations_detail_tasks_activity_results(client, token):
    plan_id = _create_plan(client, token)
    detail = client.get(f"/api/operations/center/{plan_id}", headers=auth_header(token))
    assert detail.status_code == 200
    body = detail.json()
    assert body["estado"]
    assert body["objective"]
    tasks = client.get(f"/api/operations/center/{plan_id}/tasks", headers=auth_header(token))
    assert tasks.status_code == 200
    activity = client.get(f"/api/operations/center/{plan_id}/activity", headers=auth_header(token))
    assert activity.status_code == 200
    results = client.get(f"/api/operations/center/{plan_id}/results", headers=auth_header(token))
    assert results.status_code == 200


def test_operations_filter_search(client, token):
    _create_plan(client, token)
    filtered = client.get("/api/operations/center", headers=auth_header(token), params={"search": "rips"})
    assert filtered.status_code == 200
    assert len(filtered.json()) >= 1


def test_operations_tenant_isolation(client):
    token_a = _create_org_user(client, "Org Ops A", f"a-{uuid.uuid4().hex[:6]}", "AdminOpsA*")
    token_b = _create_org_user(client, "Org Ops B", f"b-{uuid.uuid4().hex[:6]}", "AdminOpsB*")
    plan_id = _create_plan(client, token_a)
    cross = client.get(f"/api/operations/center/{plan_id}", headers=auth_header(token_b))
    assert cross.status_code == 404


def test_viewer_can_list_but_not_cancel(client, token):
    plan_id = _create_plan(client, token)
    viewer = _create_org_user(client, "Org Viewer Ops", f"v-{uuid.uuid4().hex[:6]}", "ViewerOps*", role="viewer")
    ok = client.get("/api/operations/center", headers=auth_header(viewer))
    assert ok.status_code == 200
    denied = client.post(f"/api/operations/center/{plan_id}/cancel", headers=auth_header(viewer))
    assert denied.status_code == 403


def test_cancel_operation(client, token):
    plan_id = _create_plan(client, token)
    cancelled = client.post(f"/api/operations/center/{plan_id}/cancel", headers=auth_header(token))
    assert cancelled.status_code == 200
    assert cancelled.json()["estado_codigo"] == "CANCELLED"


def test_cancel_invalid_transition_completed(client, token):
    plan_id = _create_plan(client, token)
    client.post(f"/api/operations/center/{plan_id}/cancel", headers=auth_header(token))
    again = client.post(f"/api/operations/center/{plan_id}/cancel", headers=auth_header(token))
    assert again.status_code == 400


def test_operations_not_found(client, token):
    missing = client.get("/api/operations/center/does-not-exist", headers=auth_header(token))
    assert missing.status_code == 404


def test_partial_update_reassign(client, token):
    plan_id = _create_plan(client, token)
    emp = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": "Ops Employee", "specialty": "DOCINT"},
    ).json()
    patched = client.patch(
        f"/api/operations/center/{plan_id}",
        headers=auth_header(token),
        json={"employee_id": emp["id"]},
    )
    assert patched.status_code == 200
    assert patched.json()["employee_id"] == emp["id"]


def test_approval_requires_permission(client, token):
    plan_id = _create_plan(client, token)
    approvals = client.get(f"/api/operations/center/{plan_id}/approvals", headers=auth_header(token))
    assert approvals.status_code == 200
    viewer = _create_org_user(client, "Org Viewer Appr", f"va-{uuid.uuid4().hex[:6]}", "ViewerAppr*", role="viewer")
    pending = client.get("/api/operations/approvals/pending", headers=auth_header(viewer))
    assert pending.status_code == 200
