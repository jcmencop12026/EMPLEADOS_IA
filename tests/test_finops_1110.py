"""Bloque 1110 — FinOps trazabilidad costo↔oportunidad y operativo."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.finops_enums import FinOpsBudgetPolicy
from app.finops_models import FinOpsBudget
from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.orchestration_models import WorkPlan
from app.security import hash_password
from app.services.finops_service import (
    FinOpsBudgetBlockedError,
    FinOpsValidationError,
    assert_budget_allows_consumption,
    process_budget_alerts,
    registrar_consumo,
    registrar_valor,
    summarize_opportunity_economics,
)
from conftest import TestingSessionLocal, auth_header


def _create_org_user(
    client: TestClient, username: str, password: str, role: str = "admin"
) -> tuple[str, str]:
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


def _seed_opportunity(db: Session, org_id: str) -> Opportunity:
    opp = Opportunity(
        organization_id=org_id,
        codigo=f"OPP-{uuid.uuid4().hex[:6]}",
        tipo="EFICIENCIA",
        dominio="operaciones",
        titulo="Oportunidad FinOps",
        estado="DETECTADA",
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


def _seed_work_plan(db: Session, org_id: str, user_id: str) -> WorkPlan:
    wp = WorkPlan(
        organization_id=org_id,
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        request="Analizar oportunidad",
        objective="Evaluar impacto",
        status="CREATED",
    )
    db.add(wp)
    db.commit()
    db.refresh(wp)
    return wp


def test_registrar_consumo_vincula_opportunity_id():
    db = TestingSessionLocal()
    try:
        org = Organization(name="FinOps Opp")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        record = registrar_consumo(
            db,
            organization_id=org.id,
            provider="openai",
            model_name="gpt-4o-mini",
            tokens_in=100,
            tokens_out=50,
            opportunity_id=opp.id,
            category="Modelo IA",
            cost=Decimal("0.50"),
            currency="USD",
        )
        assert record.opportunity_id == opp.id
        assert record.cost == 0.5
    finally:
        db.close()


def test_registrar_consumo_resuelve_opportunity_desde_work_plan():
    db = TestingSessionLocal()
    try:
        org = Organization(name="FinOps WP")
        db.add(org)
        db.flush()
        user = User(
            organization_id=org.id,
            username=f"wp-user-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("secret"),
            role="admin",
        )
        db.add(user)
        db.flush()
        wp = _seed_work_plan(db, org.id, user.id)
        opp = Opportunity(
            organization_id=org.id,
            codigo=f"OPP-{uuid.uuid4().hex[:6]}",
            tipo="EFICIENCIA",
            dominio="operaciones",
            titulo="Oportunidad WP",
            estado="DETECTADA",
            work_plan_id=wp.id,
        )
        db.add(opp)
        db.commit()
        record = registrar_consumo(
            db,
            organization_id=org.id,
            provider="openai",
            model_name="gpt-4o-mini",
            tokens_in=10,
            tokens_out=5,
            work_plan_id=wp.id,
            cost=Decimal("0.10"),
            currency="USD",
        )
        assert record.opportunity_id == opp.id
    finally:
        db.close()


def test_summarize_opportunity_economics():
    db = TestingSessionLocal()
    try:
        org = Organization(name="FinOps Eco")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        registrar_consumo(
            db,
            organization_id=org.id,
            provider="openai",
            model_name="gpt-4o-mini",
            tokens_in=1000,
            tokens_out=500,
            opportunity_id=opp.id,
            category="Modelo IA",
            cost=Decimal("2.50"),
            currency="USD",
        )
        registrar_valor(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            value_type="Reducción de costo",
            amount=Decimal("250.00"),
            currency="USD",
            notes="Ahorro estimado",
        )
        summary = summarize_opportunity_economics(db, organization_id=org.id, opportunity_id=opp.id)
        assert summary["total_cost"] == Decimal("2.50")
        assert summary["finops_value_sum"] == Decimal("250.00")
        assert summary["consumption_count"] == 1
        assert summary["consumptions"][0]["opportunity_id"] == opp.id
    finally:
        db.close()


def test_budget_alert_dedup():
    db = TestingSessionLocal()
    try:
        org = Organization(name="FinOps Alert")
        db.add(org)
        db.flush()
        now = datetime.now(timezone.utc)
        registrar_consumo(
            db,
            organization_id=org.id,
            provider="openai",
            model_name="gpt-4o-mini",
            category="Modelo IA",
            cost=Decimal("95"),
            currency="USD",
            skip_budget_enforcement=True,
        )
        budget = FinOpsBudget(
            organization_id=org.id,
            scope_type="empresa",
            period_start=now - timedelta(days=1),
            period_end=now + timedelta(days=30),
            amount_limit=Decimal("100"),
            currency="USD",
            policy=FinOpsBudgetPolicy.SOLO_INFORMAR,
            alert_threshold_pct=90,
            name="IA mensual",
            active=True,
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)
        first = process_budget_alerts(db, organization_id=org.id)
        second = process_budget_alerts(db, organization_id=org.id)
        assert len(first) == 1
        assert second == []
    finally:
        db.close()


def test_budget_block_only_when_policy_blocks():
    db = TestingSessionLocal()
    try:
        now = datetime.now(timezone.utc)
        org_inform = Organization(name="FinOps Inform")
        org_block = Organization(name="FinOps Block")
        db.add_all([org_inform, org_block])
        db.flush()
        inform_budget = FinOpsBudget(
            organization_id=org_inform.id,
            scope_type="empresa",
            period_start=now - timedelta(days=1),
            period_end=now + timedelta(days=30),
            amount_limit=Decimal("10"),
            currency="USD",
            policy=FinOpsBudgetPolicy.SOLO_INFORMAR,
            name="Solo informar",
            active=True,
        )
        block_budget = FinOpsBudget(
            organization_id=org_block.id,
            scope_type="empresa",
            period_start=now - timedelta(days=1),
            period_end=now + timedelta(days=30),
            amount_limit=Decimal("10"),
            currency="USD",
            policy=FinOpsBudgetPolicy.BLOQUEAR,
            name="Bloqueo",
            active=True,
        )
        db.add_all([inform_budget, block_budget])
        db.commit()
        registrar_consumo(
            db,
            organization_id=org_inform.id,
            provider="openai",
            model_name="gpt-4o-mini",
            category="Modelo IA",
            cost=Decimal("10"),
            currency="USD",
            skip_budget_enforcement=True,
        )
        registrar_consumo(
            db,
            organization_id=org_block.id,
            provider="openai",
            model_name="gpt-4o-mini",
            category="Modelo IA",
            cost=Decimal("10"),
            currency="USD",
            skip_budget_enforcement=True,
        )
        assert_budget_allows_consumption(db, organization_id=org_inform.id) is None
        with pytest.raises(FinOpsBudgetBlockedError):
            assert_budget_allows_consumption(db, organization_id=org_block.id)
    finally:
        db.close()


def test_tenant_isolation_opportunity_economics():
    db = TestingSessionLocal()
    try:
        org_a = Organization(name="FinOps A")
        org_b = Organization(name="FinOps B")
        db.add_all([org_a, org_b])
        db.flush()
        opp_a = _seed_opportunity(db, org_a.id)
        with pytest.raises(FinOpsValidationError, match="no encontrada"):
            summarize_opportunity_economics(db, organization_id=org_b.id, opportunity_id=opp_a.id)
    finally:
        db.close()


def test_api_opportunity_economics_rbac(client: TestClient):
    org_id, admin_token = _create_org_user(
        client, f"finops-api-{uuid.uuid4().hex[:6]}", "FinOpsApi*"
    )
    db = TestingSessionLocal()
    try:
        opp = _seed_opportunity(db, org_id)
        opp_id = opp.id
        registrar_consumo(
            db,
            organization_id=org_id,
            provider="openai",
            model_name="gpt-4o-mini",
            tokens_in=100,
            tokens_out=50,
            opportunity_id=opp_id,
            cost=Decimal("1.00"),
            currency="USD",
        )
    finally:
        db.close()

    ok = client.get(
        f"/api/finops/opportunities/{opp_id}/economics",
        headers=auth_header(admin_token),
    )
    assert ok.status_code == 200
    assert ok.json()["opportunity_id"] == opp_id

    _, viewer_token = _create_org_user(
        client, f"finops-view-{uuid.uuid4().hex[:6]}", "FinView*", role="viewer"
    )
    denied = client.post(
        "/api/finops/budgets",
        headers=auth_header(viewer_token),
        json={
            "scope_type": "empresa",
            "period_start": datetime.now(timezone.utc).isoformat(),
            "period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "amount_limit": "100",
            "currency": "USD",
            "policy": "Solo informar",
        },
    )
    assert denied.status_code == 403


def test_api_budget_create_and_list(client: TestClient):
    _, token = _create_org_user(
        client, f"finops-budget-{uuid.uuid4().hex[:6]}", "FinBudget*"
    )
    now = datetime.now(timezone.utc)
    created = client.post(
        "/api/finops/budgets",
        headers=auth_header(token),
        json={
            "scope_type": "empresa",
            "period_start": now.isoformat(),
            "period_end": (now + timedelta(days=30)).isoformat(),
            "amount_limit": "500",
            "currency": "USD",
            "policy": "Solo informar",
            "alert_threshold_pct": 85,
            "name": "Presupuesto IA",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["alert_threshold_pct"] == 85
    assert Decimal(str(body["balance"])) == Decimal("500")

    listed = client.get("/api/finops/budgets", headers=auth_header(token))
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
