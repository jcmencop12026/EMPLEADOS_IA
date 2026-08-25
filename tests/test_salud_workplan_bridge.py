"""Puente SALUD IpsActionPlan → WorkPlan → EmployeeTask (ENTREGA-002)."""

from __future__ import annotations

import json
import uuid

import pytest

from app.enums import EmployeeLifecycleStatus, EmployeeMaturity
from app.fixtures.salud_demo import get_demo_datasets
from app.models import Organization, User
from app.orchestration_models import AIEmployee, EmployeeTask, WorkPlan
from app.salud_models import IpsActionPlan
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.salud, pytest.mark.operations]


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


def _run_analysis(client, token: str, ips_name: str = "IPS Bridge") -> tuple[str, list[str]]:
    res = client.post(
        "/api/salud/analisis",
        headers=auth_header(token),
        json={
            "ips_name": ips_name,
            "request_text": "Diagnóstico integral",
            "inline_datasets": get_demo_datasets(),
        },
    )
    assert res.status_code == 200
    analysis_id = res.json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    prop_ids = [p["id"] for p in diag["oportunidades"][:2]]
    return analysis_id, prop_ids


def _create_plan(client, token: str, analysis_id: str, prop_ids: list[str]):
    return client.post(
        f"/api/salud/analisis/{analysis_id}/plan-accion",
        headers=auth_header(token),
        json={"propuesta_ids": prop_ids},
    )


def test_bridge_creates_workplan_and_tasks(client, token):
    analysis_id, prop_ids = _run_analysis(client, token)
    plan_res = _create_plan(client, token, analysis_id, prop_ids)
    assert plan_res.status_code == 200
    body = plan_res.json()
    assert body["work_plan_id"]

    db = TestingSessionLocal()
    try:
        work_plan = db.query(WorkPlan).filter(WorkPlan.id == body["work_plan_id"]).first()
        assert work_plan is not None
        assert work_plan.prioridad in {"BAJA", "MEDIA", "ALTA", "CRITICA"}
        assert work_plan.vencimiento is not None
        assert "SALUD" in (work_plan.summary or "")

        tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == work_plan.id).all()
        assert len(tasks) == len(prop_ids)
        for task in tasks:
            payload = json.loads(task.inputs_json or "{}")
            assert payload["origen"] == "SALUD"
            assert payload["analysis_id"] == analysis_id
            assert payload["propuesta_id"] in prop_ids
            assert payload["hallazgo_id"]
            assert payload["evidencia"]
            assert payload["accion"]
            assert payload["meta"]
            assert payload["confianza"]
    finally:
        db.close()

    ops = client.get("/api/operations/center", headers=auth_header(token)).json()
    ids = {item["id"] for item in ops}
    assert body["work_plan_id"] in ids

    detail = client.get(f"/api/operations/center/{body['work_plan_id']}", headers=auth_header(token)).json()
    assert detail["prioridad_codigo"] in {"BAJA", "MEDIA", "ALTA", "CRITICA"}
    assert detail["vencimiento"] is not None
    assert "SALUD" in (detail.get("resumen") or "")


def test_idempotency_same_propuestas(client, token):
    analysis_id, prop_ids = _run_analysis(client, token, ips_name="IPS Idempotencia")
    first = _create_plan(client, token, analysis_id, prop_ids).json()
    second = _create_plan(client, token, analysis_id, list(reversed(prop_ids))).json()
    assert first["work_plan_id"] == second["work_plan_id"]
    assert first["id"] == second["id"]

    db = TestingSessionLocal()
    try:
        plans = db.query(IpsActionPlan).filter(IpsActionPlan.analysis_id == analysis_id).all()
        work_plan_ids = {p.work_plan_id for p in plans if p.work_plan_id}
        assert len(work_plan_ids) == 1
        task_count = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == first["work_plan_id"]).count()
        assert task_count == len(prop_ids)
    finally:
        db.close()


def test_cross_tenant_propuestas_rejected(client):
    token_a = _create_org_user(client, "Org Salud A", f"sa-{uuid.uuid4().hex[:6]}", "SaludA*")
    token_b = _create_org_user(client, "Org Salud B", f"sb-{uuid.uuid4().hex[:6]}", "SaludB*")
    analysis_a, prop_ids_a = _run_analysis(client, token_a, "IPS Tenant A")
    analysis_b, prop_ids_b = _run_analysis(client, token_b, "IPS Tenant B")

    denied = _create_plan(client, token_a, analysis_a, prop_ids_b)
    assert denied.status_code == 400

    denied2 = _create_plan(client, token_b, analysis_b, prop_ids_a)
    assert denied2.status_code == 400

    ok_a = _create_plan(client, token_a, analysis_a, prop_ids_a)
    ok_b = _create_plan(client, token_b, analysis_b, prop_ids_b)
    assert ok_a.status_code == 200
    assert ok_b.status_code == 200
    assert ok_a.json()["work_plan_id"] != ok_b.json()["work_plan_id"]

    cross_get = client.get(f"/api/operations/center/{ok_b.json()['work_plan_id']}", headers=auth_header(token_a))
    assert cross_get.status_code == 404


def test_responsable_unique_assigns_employee(client, token):
    analysis_id, prop_ids = _run_analysis(client, token, ips_name="IPS Responsable")
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    prop = next(p for p in diag["oportunidades"] if p["id"] == prop_ids[0])
    responsable = prop["responsable_sugerido"] or "Coordinador de radicación"

    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        assert admin is not None
        emp = AIEmployee(
            organization_id=admin.organization_id,
            code=f"resp-{uuid.uuid4().hex[:6]}",
            name=responsable,
            specialty="Prueba",
            role=responsable,
            objective="Asignación puente SALUD",
            lifecycle_status=EmployeeLifecycleStatus.ACTIVE,
            maturity=EmployeeMaturity.AUTONOMOUS_CONTROLLED,
            model_provider="rule-engine",
            model_name="test",
            version=1,
        )
        db.add(emp)
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    plan_res = _create_plan(client, token, analysis_id, [prop_ids[0]]).json()
    db = TestingSessionLocal()
    try:
        tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan_res["work_plan_id"]).all()
        assert len(tasks) == 1
        assert tasks[0].employee_id == emp_id
    finally:
        db.close()


def test_responsable_ambiguous_leaves_unassigned(client, token):
    analysis_id, prop_ids = _run_analysis(client, token, ips_name="IPS Ambiguo")
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    prop = next(p for p in diag["oportunidades"] if p["id"] == prop_ids[0])
    responsable = prop["responsable_sugerido"] or "Analista de glosas"

    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        for i in range(2):
            db.add(
                AIEmployee(
                    organization_id=admin.organization_id,
                    code=f"dup-{i}-{uuid.uuid4().hex[:4]}",
                    name=responsable,
                    specialty="Prueba",
                    role=responsable,
                    objective="Duplicado",
                    lifecycle_status=EmployeeLifecycleStatus.ACTIVE,
                    maturity=EmployeeMaturity.AUTONOMOUS_CONTROLLED,
                    model_provider="rule-engine",
                    model_name="test",
                    version=1,
                )
            )
        db.commit()
    finally:
        db.close()

    plan_res = _create_plan(client, token, analysis_id, [prop_ids[0]]).json()
    db = TestingSessionLocal()
    try:
        tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan_res["work_plan_id"]).all()
        assert len(tasks) == 1
        assert tasks[0].employee_id is None
    finally:
        db.close()
