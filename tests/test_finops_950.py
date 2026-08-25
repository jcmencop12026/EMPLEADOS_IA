"""Tests FINOPS-950 — costos y valor."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.finops_models import FinOpsRate
from app.models import Organization, User
from app.security import hash_password
from app.services.finops_service import (
    COST_UNAVAILABLE,
    budget_state,
    calculate_cost_from_rate,
    compute_roi,
    find_active_rate,
    registrar_consumo,
    registrar_valor,
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


def test_registrar_consumo_con_tarifa(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        from app.models import User

        user = db.query(User).filter(User.username == "admin").one()
        rate = FinOpsRate(
            organization_id=user.organization_id,
            provider="openai",
            model_service="gpt-4",
            category="Modelo IA",
            price_input=Decimal("0.00001"),
            price_output=Decimal("0.00002"),
            currency="USD",
            active=True,
        )
        db.add(rate)
        db.commit()
        db.refresh(rate)

        record = registrar_consumo(
            db,
            organization_id=user.organization_id,
            provider="openai",
            model_name="gpt-4",
            category="Modelo IA",
            tokens_in=1000,
            tokens_out=500,
        )
        assert record.cost is not None
        assert record.currency == "USD"
        assert record.rate_id == rate.id
    finally:
        db.close()


def test_tarifa_inexistente_costo_no_disponible(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        from app.models import User

        user = db.query(User).filter(User.username == "admin").one()
        record = registrar_consumo(
            db,
            organization_id=user.organization_id,
            provider="desconocido",
            model_name="sin-tarifa",
            category="Otro",
            tokens_in=100,
        )
        assert record.cost is None
    finally:
        db.close()


def test_decimal_cost_calculation():
    rate = FinOpsRate(
        organization_id="x",
        provider="p",
        model_service="m",
        category="Modelo IA",
        price_input=Decimal("0.000001"),
        price_output=Decimal("0.000002"),
        currency="USD",
        active=True,
    )
    cost, source = calculate_cost_from_rate(rate, tokens_in=1_000_000, tokens_out=500_000)
    assert cost == Decimal("2.000000")
    assert source.startswith("tarifa:")


def test_costo_cero_roi():
    roi, label = compute_roi(total_cost=Decimal("0"), total_value=Decimal("100"))
    assert roi is None
    assert "infinito" in label.lower()


def test_valor_real_y_estimado(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        from app.models import User

        user = db.query(User).filter(User.username == "admin").one()
        real = registrar_valor(
            db,
            organization_id=user.organization_id,
            value_type="Ahorro de tiempo",
            certainty="Real",
            amount=Decimal("150.00"),
            currency="USD",
            methodology="Tiempo ahorrado × tarifa hora",
            source="operaciones",
        )
        est = registrar_valor(
            db,
            organization_id=user.organization_id,
            value_type="Productividad",
            certainty="Estimado",
            amount=Decimal("80.00"),
            currency="USD",
        )
        assert real.certainty == "Real"
        assert est.certainty == "Estimado"
    finally:
        db.close()


def test_roi_reproducible():
    roi, _ = compute_roi(total_cost=Decimal("100"), total_value=Decimal("250"))
    assert roi == Decimal("150.00")


def test_presupuesto_estado():
    assert budget_state(Decimal("50"), Decimal("100")) == "Normal"
    assert budget_state(Decimal("80"), Decimal("100")) == "Atención"
    assert budget_state(Decimal("95"), Decimal("100")) == "Cerca del límite"
    assert budget_state(Decimal("100"), Decimal("100")) == "Límite alcanzado"


def test_tenant_isolation(client: TestClient):
    org_a, token_a = _create_org_user(client, f"finops-a-{uuid.uuid4().hex[:6]}", "FinOpsA*")
    _, token_b = _create_org_user(client, f"finops-b-{uuid.uuid4().hex[:6]}", "FinOpsB*")

    db = TestingSessionLocal()
    try:
        registrar_consumo(
            db,
            organization_id=org_a,
            provider="openai",
            model_name="gpt-4",
            cost=Decimal("1.50"),
            currency="USD",
        )
    finally:
        db.close()

    res = client.get("/api/finops/consumptions", headers=auth_header(token_a))
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res_b = client.get("/api/finops/consumptions", headers=auth_header(token_b))
    assert res_b.status_code == 200
    assert res_b.json() == []


def test_permissions_viewer_read_only(client: TestClient):
    _, token = _create_org_user(
        client, f"finops-viewer-{uuid.uuid4().hex[:6]}", "Viewer950*", role="viewer"
    )
    ok = client.get("/api/finops/dashboard", headers=auth_header(token))
    assert ok.status_code == 200
    denied = client.post(
        "/api/finops/consumptions",
        headers=auth_header(token),
        json={"category": "Otro"},
    )
    assert denied.status_code == 403


def test_patch_tarifa_parcial(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        from app.models import User

        user = db.query(User).filter(User.username == "admin").one()
        rate = FinOpsRate(
            organization_id=user.organization_id,
            provider="azure",
            model_service="gpt-4o",
            category="Modelo IA",
            unit_price=Decimal("0.01"),
            currency="USD",
            active=True,
        )
        db.add(rate)
        db.commit()
        rate_id = rate.id
    finally:
        db.close()

    res = client.patch(
        f"/api/finops/rates/{rate_id}",
        headers=auth_header(token),
        json={"unit_price": "0.02", "active": False},
    )
    assert res.status_code == 200
    body = res.json()
    assert Decimal(str(body["unit_price"])) == Decimal("0.02")
    assert body["active"] is False


def test_trazabilidad_tarifa(client: TestClient, token: str):
    res = client.post(
        "/api/finops/rates",
        headers=auth_header(token),
        json={
            "provider": "anthropic",
            "model_service": "claude-3",
            "category": "Modelo IA",
            "price_input": "0.000003",
            "price_output": "0.000015",
            "currency": "USD",
        },
    )
    assert res.status_code == 200
    logs = client.get("/api/audit/logs", headers=auth_header(token))
    assert logs.status_code == 200
    actions = [row["action"] for row in logs.json()]
    assert "finops.rate.created" in actions


def test_dashboard_sin_datos_ficticios(client: TestClient, token: str):
    res = client.get("/api/finops/dashboard", headers=auth_header(token))
    assert res.status_code == 200
    body = res.json()
    assert body["total_cost_label"] == COST_UNAVAILABLE or body["total_cost"] is not None


def test_presupuesto_api(client: TestClient, token: str):
    now = datetime.now(timezone.utc)
    res = client.post(
        "/api/finops/budgets",
        headers=auth_header(token),
        json={
            "scope_type": "empresa",
            "period_start": now.isoformat(),
            "period_end": (now + timedelta(days=30)).isoformat(),
            "amount_limit": "1000.00",
            "currency": "USD",
            "policy": "Solo informar",
            "name": "Presupuesto mensual",
        },
    )
    assert res.status_code == 200
    assert res.json()["state"] == "Normal"


def test_tarifa_vigente():
    db = TestingSessionLocal()
    try:
        from app.models import User

        user = db.query(User).filter(User.username == "admin").one()
        past = datetime.now(timezone.utc) - timedelta(days=10)
        future = datetime.now(timezone.utc) + timedelta(days=10)
        active = FinOpsRate(
            organization_id=user.organization_id,
            provider="openai",
            model_service="gpt-test",
            category="Modelo IA",
            unit_price=Decimal("1"),
            currency="USD",
            valid_from=past,
            valid_until=future,
            active=True,
        )
        expired = FinOpsRate(
            organization_id=user.organization_id,
            provider="openai",
            model_service="gpt-test",
            category="Modelo IA",
            unit_price=Decimal("2"),
            currency="USD",
            valid_until=past,
            active=True,
        )
        db.add_all([active, expired])
        db.commit()
        found = find_active_rate(
            db,
            organization_id=user.organization_id,
            provider="openai",
            model_service="gpt-test",
            category="Modelo IA",
        )
        assert found is not None
        assert found.unit_price == Decimal("1")
    finally:
        db.close()
