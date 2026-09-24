"""MB-06 — Ciclo de vida fábrica empleados IA."""

import json
import uuid

import pytest

pytestmark = [pytest.mark.auth, pytest.mark.tenant]

from app.models import AuditLog, Organization, User
from app.orchestration_models import AIEmployee, EmployeeVersion
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _create_ready_employee(client, token, *, risk_level: str = "MEDIUM", name: str | None = None):
    caps = client.get("/api/agent-factory/capabilities", headers=auth_header(token)).json()
    tools = client.get("/api/agent-factory/tools", headers=auth_header(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={
            "name": name or f"Lifecycle {uuid.uuid4().hex[:6]}",
            "specialty": "DOCINT",
            "template_code": "analista-documental",
        },
    )
    assert created.status_code == 200
    emp_id = created.json()["id"]

    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={
            "capability_ids": [docint_cap["id"]],
            "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
            "model_policy": {"preferred_provider": "rule-engine", "preferred_model": "docint-rules-v1"},
            "risk_level": risk_level,
            "instructions": {"role_text": "Analista", "objective_text": "Analizar documentos"},
        },
    )
    return emp_id


def test_auditor_contract(client, token):
    res = client.get("/api/agent-factory/auditor-contract", headers=auth_header(token))
    assert res.status_code == 200
    body = res.json()
    assert body["module"] == "employee_factory"
    ops = {o["op"] for o in body["operations"]}
    assert {"capacitar", "publicar", "rollback", "probar"} <= ops


def test_inventory_and_health(client, token):
    emp_id = _create_ready_employee(client, token)
    inv = client.get(f"/api/agent-factory/employees/{emp_id}/inventory", headers=auth_header(token))
    assert inv.status_code == 200
    body = inv.json()
    assert body["lifecycle_phase"] in ("CONFIGURADO", "BORRADOR")
    assert "model" in body
    assert "finops" in body

    health = client.get(f"/api/agent-factory/employees/{emp_id}/health", headers=auth_header(token))
    assert health.status_code == 200
    assert health.json()["employee_id"] == emp_id


def test_validate_blocks_incomplete(client, token):
    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": f"Incomplete {uuid.uuid4().hex[:6]}", "specialty": "DOCINT"},
    ).json()
    val = client.get(f"/api/agent-factory/employees/{created['id']}/validate", headers=auth_header(token))
    assert val.status_code == 200
    assert val.json()["valid"] is False
    assert val.json()["errors"]


def test_version_on_significant_change(client, token):
    emp_id = _create_ready_employee(client, token)
    before = client.get(f"/api/agent-factory/employees/{emp_id}", headers=auth_header(token)).json()["version"]

    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={"instructions": {"role_text": "Nuevo rol", "objective_text": "Nuevo objetivo"}},
    )
    versions = client.get(f"/api/agent-factory/employees/{emp_id}/versions", headers=auth_header(token)).json()
    assert len(versions) >= 1
    after = client.get(f"/api/agent-factory/employees/{emp_id}", headers=auth_header(token)).json()["version"]
    assert after >= before


def test_publish_blocked_without_certification(client, token):
    emp_id = _create_ready_employee(client, token)
    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub.status_code == 400
    detail = pub.json()["detail"]
    if isinstance(detail, dict):
        msg = str(detail.get("error", "")) + str(detail.get("validation", ""))
        assert "CERTIFIED" in msg or "incompleta" in msg.lower() or "pruebas" in msg.lower()
    else:
        assert "CERTIFIED" in str(detail) or "incompleta" in str(detail).lower()


def test_full_lifecycle_publish(client, token):
    emp_id = _create_ready_employee(client, token)
    client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=auth_header(token))
    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub.status_code == 200
    assert pub.json()["lifecycle_status"] == "PUBLISHED"

    db = TestingSessionLocal()
    try:
        audits = db.query(AuditLog).filter(AuditLog.action == "employee.published").count()
        assert audits >= 1
        versions = db.query(EmployeeVersion).filter(EmployeeVersion.employee_id == emp_id, EmployeeVersion.status == "PUBLISHED").count()
        assert versions >= 1
    finally:
        db.close()


def test_high_risk_publish_requires_approval(client, token):
    emp_id = _create_ready_employee(client, token, risk_level="CRITICAL")
    client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=auth_header(token))
    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub.status_code == 403
    assert pub.json()["detail"]["requires_approval"] is True


def test_test_case_crud(client, token):
    emp_id = _create_ready_employee(client, token)
    created = client.post(
        f"/api/agent-factory/employees/{emp_id}/test-cases",
        headers=auth_header(token),
        json={
            "name": "Prueba funcional doc",
            "test_type": "FUNCTIONAL",
            "test_category": "FUNCTIONAL",
            "input": {"documents": []},
            "expected": {"has_findings": True},
            "criterion": "Debe detectar hallazgos",
        },
    )
    assert created.status_code == 200
    assert created.json()["test_category"] == "FUNCTIONAL"
    cases = client.get(f"/api/agent-factory/employees/{emp_id}/test-cases", headers=auth_header(token)).json()
    assert any(c["name"] == "Prueba funcional doc" for c in cases)


def test_rollback_to_version(client, token):
    emp_id = _create_ready_employee(client, token)
    client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=auth_header(token))
    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub.status_code == 200
    version = pub.json()["version"]

    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_header(token),
        json={"objective": "Objetivo modificado temporal"},
    )
    rb = client.post(
        f"/api/agent-factory/employees/{emp_id}/rollback",
        headers=auth_header(token),
        json={"target_version": version, "reason": "Revertir cambio de prueba"},
    )
    assert rb.status_code == 200
    assert rb.json()["lifecycle_status"] == "CONFIGURING"


def test_training_creates_record(client, token):
    emp_id = _create_ready_employee(client, token)
    res = client.post(
        f"/api/agent-factory/employees/{emp_id}/train",
        headers=auth_header(token),
        json={
            "training_type": "INSTRUCTIONS",
            "reason": "Actualizar procedimiento interno",
            "source": "manual-operaciones",
            "config_delta": {"instructions": {"operating_rules": "Nueva regla operativa"}},
        },
    )
    assert res.status_code == 200
    assert res.json()["training_id"]
    health = client.get(f"/api/agent-factory/employees/{emp_id}/health", headers=auth_header(token)).json()
    assert health["last_training_at"] is not None


def test_retire_employee(client, token):
    emp_id = _create_ready_employee(client, token)
    res = client.post(
        f"/api/agent-factory/employees/{emp_id}/retire",
        headers=auth_header(token),
        json={"reason": "Fin de ciclo de prueba"},
    )
    assert res.status_code == 200
    assert res.json()["lifecycle_status"] == "RETIRED"


def test_rbac_viewer_cannot_publish(client, token):
    username = f"viewer-mb06-{uuid.uuid4().hex[:8]}"
    db = TestingSessionLocal()
    org = db.query(Organization).first()
    db.add(User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password("ViewerMb06*"),
        role="viewer",
    ))
    db.commit()
    db.close()

    login = client.post("/api/auth/login", json={"username": username, "password": "ViewerMb06*"})
    viewer_token = login.json()["access_token"]
    emp_id = _create_ready_employee(client, token)
    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(viewer_token))
    assert pub.status_code == 403


def test_tenant_isolation_lifecycle(client, token):
    emp_id = _create_ready_employee(client, token)
    username = f"other-org-{uuid.uuid4().hex[:8]}"
    db = TestingSessionLocal()
    other_org = Organization(name=f"Org B {uuid.uuid4().hex[:6]}", slug=f"org-b-{uuid.uuid4().hex[:8]}")
    db.add(other_org)
    db.flush()
    db.add(User(
        organization_id=other_org.id,
        username=username,
        password_hash=hash_password("OtherOrg*"),
        role="admin",
    ))
    db.commit()
    db.close()

    other_login = client.post("/api/auth/login", json={"username": username, "password": "OtherOrg*"})
    other_token = other_login.json()["access_token"]
    res = client.get(f"/api/agent-factory/employees/{emp_id}/inventory", headers=auth_header(other_token))
    assert res.status_code == 404


def test_approval_idempotency(client, token):
    emp_id = _create_ready_employee(client, token, risk_level="CRITICAL")
    body = {"kind": "PUBLISH", "reason": "Publicar en producción", "target_version": 1}
    r1 = client.post(f"/api/agent-factory/employees/{emp_id}/request-approval", headers=auth_header(token), json=body)
    assert r1.status_code == 200
    r2 = client.post(f"/api/agent-factory/employees/{emp_id}/request-approval", headers=auth_header(token), json=body)
    assert r2.status_code == 400


def test_model_policy_no_secrets_in_inventory(client, token):
    emp_id = _create_ready_employee(client, token)
    inv = client.get(f"/api/agent-factory/employees/{emp_id}/inventory", headers=auth_header(token)).json()
    dumped = json.dumps(inv)
    assert "api_key" not in dumped.lower()
    assert "secret" not in dumped.lower() or inv["model"].get("provider") == "rule-engine"


def _create_approver_user(client, org_id: str) -> str:
    username = f"approver-mb06-{uuid.uuid4().hex[:8]}"
    db = TestingSessionLocal()
    db.add(User(
        organization_id=org_id,
        username=username,
        password_hash=hash_password("ApproverMb06*"),
        role="admin",
    ))
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": "ApproverMb06*"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_approval_list_and_segregation(client, token):
    emp_id = _create_ready_employee(client, token, risk_level="CRITICAL")
    client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=auth_header(token))

    req = client.post(
        f"/api/agent-factory/employees/{emp_id}/request-approval",
        headers=auth_header(token),
        json={"kind": "PUBLISH", "reason": "Publicación producción", "target_version": 1},
    )
    assert req.status_code == 200
    approval_request_id = req.json()["approval_request_id"]

    listing = client.get(f"/api/agent-factory/employees/{emp_id}/approvals", headers=auth_header(token)).json()
    assert len(listing) >= 1
    row = next(r for r in listing if r["approval_request_id"] == approval_request_id)
    assert row["status"] == "PENDING"
    assert row["approval_kind"] == "PUBLISH"
    assert row["requested_by_name"]
    assert row["can_decide"] is False

    pub_blocked = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub_blocked.status_code == 403

    self_decide = client.post(
        f"/api/agent-factory/employees/{emp_id}/approvals/{approval_request_id}/decide",
        headers=auth_header(token),
        json={"decision": "approve"},
    )
    assert self_decide.status_code == 403

    db = TestingSessionLocal()
    org_id = db.query(Organization).first().id
    db.close()
    approver_token = _create_approver_user(client, org_id)

    decide = client.post(
        f"/api/agent-factory/employees/{emp_id}/approvals/{approval_request_id}/decide",
        headers=auth_header(approver_token),
        json={"decision": "approve", "comment": "Aprobado por segundo revisor"},
    )
    assert decide.status_code == 200
    assert decide.json()["status"] == "APPROVED"

    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub.status_code == 200


def test_rejected_approval_blocks_publish(client, token):
    emp_id = _create_ready_employee(client, token, risk_level="CRITICAL")
    client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=auth_header(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=auth_header(token))
    req = client.post(
        f"/api/agent-factory/employees/{emp_id}/request-approval",
        headers=auth_header(token),
        json={"kind": "PUBLISH", "reason": "Intento publicación", "target_version": 1},
    ).json()
    approval_request_id = req["approval_request_id"]

    db = TestingSessionLocal()
    org_id = db.query(Organization).first().id
    db.close()
    approver_token = _create_approver_user(client, org_id)

    reject = client.post(
        f"/api/agent-factory/employees/{emp_id}/approvals/{approval_request_id}/decide",
        headers=auth_header(approver_token),
        json={"decision": "reject", "comment": "No cumple política"},
    )
    assert reject.status_code == 200
    assert reject.json()["status"] == "REJECTED"

    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_header(token))
    assert pub.status_code == 403


def test_create_employee_does_not_auto_approve(client, token):
    emp_id = _create_ready_employee(client, token, risk_level="CRITICAL")
    listing = client.get(f"/api/agent-factory/employees/{emp_id}/approvals", headers=auth_header(token)).json()
    assert listing == []
