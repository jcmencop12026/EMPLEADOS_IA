"""Reauditoría adversarial FINOPS-950 — dinero, tenant, ROI, presupuestos, tarifas."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.finops_models import FinOpsRate
from app.models import Organization, User
from app.orchestration_models import AIEmployee
from app.security import hash_password
from app.services.finops_service import (
    COST_UNAVAILABLE,
    ROI_UNAVAILABLE,
    budget_state,
    compute_roi,
    find_active_rate,
    registrar_consumo,
)
from conftest import TestingSessionLocal, auth_header


def _create_org_user(client: TestClient, username: str, password: str, role: str = "admin") -> tuple[str, str]:
    db = TestingSessionLocal()
    org = Organization(name=f"Org {username}")
    db.add(org)
    db.flush()
    db.add(
        User(
            organization_id=org.id,
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
    )
    db.commit()
    org_id = org.id
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return org_id, login.json()["access_token"]


def test_roi_mathematical_cases():
    roi, _ = compute_roi(total_cost=Decimal("100"), total_value=Decimal("150"))
    assert roi == Decimal("50.00")
    roi, _ = compute_roi(total_cost=Decimal("100"), total_value=Decimal("50"))
    assert roi == Decimal("-50.00")
    roi, _ = compute_roi(total_cost=Decimal("100"), total_value=Decimal("100"))
    assert roi == Decimal("0.00")
    roi, label = compute_roi(total_cost=None, total_value=Decimal("100"))
    assert roi is None
    assert label == ROI_UNAVAILABLE
    roi, label = compute_roi(total_cost=Decimal("100"), total_value=None)
    assert roi is None
    assert label == ROI_UNAVAILABLE
    roi, label = compute_roi(total_cost=Decimal("100"), total_value=Decimal("50"), same_currency=False)
    assert roi is None
    assert label == ROI_UNAVAILABLE


def test_budget_state_boundaries():
    assert budget_state(Decimal("74.99"), Decimal("100")) == "Normal"
    assert budget_state(Decimal("75"), Decimal("100")) == "Atención"
    assert budget_state(Decimal("89.99"), Decimal("100")) == "Atención"
    assert budget_state(Decimal("90"), Decimal("100")) == "Cerca del límite"
    assert budget_state(Decimal("99.99"), Decimal("100")) == "Cerca del límite"
    assert budget_state(Decimal("100"), Decimal("100")) == "Límite alcanzado"
    assert budget_state(Decimal("150"), Decimal("100")) == "Límite alcanzado"


def test_cross_tenant_employee_id_rejected(client: TestClient):
    org_a, token_a = _create_org_user(client, f"fa-{uuid.uuid4().hex}", "FinA*")
    _, token_b = _create_org_user(client, f"fb-{uuid.uuid4().hex}", "FinB*")

    db = TestingSessionLocal()
    emp = AIEmployee(organization_id=org_a, code="E1", name="Emp A", specialty="DOCINT")
    db.add(emp)
    db.commit()
    emp_id = emp.id
    db.close()

    res = client.post(
        "/api/finops/consumptions",
        headers=auth_header(token_b),
        json={"employee_id": emp_id, "category": "Otro", "cost": "1.00", "currency": "USD"},
    )
    assert res.status_code == 400


def test_cross_tenant_rate_id_rejected(client: TestClient, token: str):
    org_b, token_b = _create_org_user(client, f"fr-{uuid.uuid4().hex}", "FinR*")
    db = TestingSessionLocal()
    rate = FinOpsRate(
        organization_id=org_b,
        provider="openai",
        model_service="gpt-4",
        category="Modelo IA",
        unit_price=Decimal("1"),
        currency="USD",
        active=True,
    )
    db.add(rate)
    db.commit()
    rate_id = rate.id
    db.close()

    res = client.post(
        "/api/finops/consumptions",
        headers=auth_header(token),
        json={"rate_id": rate_id, "category": "Modelo IA", "tokens_in": 10},
    )
    assert res.status_code == 400


def test_dashboard_no_cross_tenant_leakage(client: TestClient):
    org_a, token_a = _create_org_user(client, f"fd-a-{uuid.uuid4().hex}", "FinDA*")
    _, token_b = _create_org_user(client, f"fd-b-{uuid.uuid4().hex}", "FinDB*")

    db = TestingSessionLocal()
    registrar_consumo(
        db,
        organization_id=org_a,
        cost=Decimal("1000000"),
        currency="USD",
        category="Otro",
    )
    db.close()

    dash_b = client.get("/api/finops/dashboard", headers=auth_header(token_b)).json()
    assert dash_b["total_cost"] is None or Decimal(str(dash_b["total_cost"])) < Decimal("1000000")


def test_mixed_currency_roi_unavailable(client: TestClient, token: str):
    db = TestingSessionLocal()
    from app.models import User

    user = db.query(User).filter(User.username == "admin").one()
    registrar_consumo(db, organization_id=user.organization_id, cost=Decimal("10"), currency="USD", category="Otro")
    from app.services.finops_service import registrar_valor

    registrar_valor(
        db,
        organization_id=user.organization_id,
        value_type="Ahorro de tiempo",
        certainty="Real",
        amount=Decimal("20"),
        currency="COP",
    )
    db.close()

    dash = client.get("/api/finops/dashboard", headers=auth_header(token)).json()
    assert dash["roi_label"] == ROI_UNAVAILABLE


def test_tarifa_superpuesta_elige_mas_reciente():
    db = TestingSessionLocal()
    try:
        from app.models import User

        user = db.query(User).filter(User.username == "admin").one()
        now = datetime.now(timezone.utc)
        older = FinOpsRate(
            organization_id=user.organization_id,
            provider="openai",
            model_service="gpt-4",
            category="Modelo IA",
            unit_price=Decimal("1"),
            currency="USD",
            valid_from=now - timedelta(days=30),
            active=True,
        )
        newer = FinOpsRate(
            organization_id=user.organization_id,
            provider="openai",
            model_service="gpt-4",
            category="Modelo IA",
            unit_price=Decimal("2"),
            currency="USD",
            valid_from=now - timedelta(days=1),
            active=True,
        )
        db.add_all([older, newer])
        db.commit()
        found = find_active_rate(
            db,
            organization_id=user.organization_id,
            provider="openai",
            model_service="gpt-4",
            category="Modelo IA",
        )
        assert found is not None
        assert found.unit_price == Decimal("2")
    finally:
        db.close()


def test_budget_employee_scope(client: TestClient, token: str):
    db = TestingSessionLocal()
    from app.models import User

    user = db.query(User).filter(User.username == "admin").one()
    emp_a = AIEmployee(organization_id=user.organization_id, code="BA", name="A", specialty="DOCINT")
    emp_b = AIEmployee(organization_id=user.organization_id, code="BB", name="B", specialty="DOCINT")
    db.add_all([emp_a, emp_b])
    db.commit()
    emp_a_id = emp_a.id
    emp_b_id = emp_b.id
    registrar_consumo(
        db,
        organization_id=user.organization_id,
        employee_id=emp_a_id,
        cost=Decimal("80"),
        currency="USD",
        category="Otro",
    )
    registrar_consumo(
        db,
        organization_id=user.organization_id,
        employee_id=emp_b_id,
        cost=Decimal("500"),
        currency="USD",
        category="Otro",
    )
    db.close()

    now = datetime.now(timezone.utc)
    res = client.post(
        "/api/finops/budgets",
        headers=auth_header(token),
        json={
            "scope_type": "empleado",
            "scope_id": emp_a_id,
            "period_start": (now - timedelta(days=1)).isoformat(),
            "period_end": (now + timedelta(days=30)).isoformat(),
            "amount_limit": "100.00",
            "currency": "USD",
            "policy": "Solo informar",
            "name": "Presupuesto empleado A",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert Decimal(str(body["spent"])) == Decimal("80")
    assert body["state"] == "Atención"


def test_operator_denied_finops_rates(client: TestClient):
    _, token = _create_org_user(client, f"fo-{uuid.uuid4().hex}", "FinOp*", role="operator")
    denied = client.get("/api/finops/rates", headers=auth_header(token))
    assert denied.status_code == 403


def test_drill_down_cross_tenant_work_plan_404(client: TestClient):
    org_a, token_a = _create_org_user(client, f"dd-a-{uuid.uuid4().hex}", "DDA*")
    _, token_b = _create_org_user(client, f"dd-b-{uuid.uuid4().hex}", "DDB*")

    db = TestingSessionLocal()
    from app.models import User
    from app.orchestration_models import WorkPlan

    user_a = db.query(User).filter(User.organization_id == org_a).first()
    plan = WorkPlan(
        organization_id=org_a,
        user_id=user_a.id,
        request="req",
        objective="obj",
        correlation_id=str(uuid.uuid4()),
        status="READY",
    )
    db.add(plan)
    db.commit()
    plan_id = plan.id
    db.close()

    res = client.get(
        "/api/finops/drill-down",
        headers=auth_header(token_b),
        params={"work_plan_id": plan_id},
    )
    assert res.status_code == 404


def test_consumo_sin_tarifa_costo_no_disponible(client: TestClient, token: str):
    res = client.post(
        "/api/finops/consumptions",
        headers=auth_header(token),
        json={"provider": "x", "model_name": "y", "category": "Otro", "tokens_in": 100},
    )
    assert res.status_code == 200
    assert res.json()["cost_label"] == COST_UNAVAILABLE


def test_decimal_micro_pricing():
    rate = FinOpsRate(
        organization_id="x",
        provider="p",
        model_service="m",
        category="Modelo IA",
        price_input=Decimal("0.000001"),
        currency="USD",
        active=True,
    )
    from app.services.finops_service import calculate_cost_from_rate

    cost, _ = calculate_cost_from_rate(rate, tokens_in=1_000_000)
    assert cost == Decimal("1.000000")
