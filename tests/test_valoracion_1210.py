"""Bloque 1210 — Valoración económica, escenarios y retorno por oportunidad."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.security import hash_password
from app.services import finops_service as finops
from app.services.valuation_service import (
    ValuationValidationError,
    compute_adjusted_expected,
    compute_economic_summary,
    create_valuation,
    register_execution_cost,
    register_real_value,
    update_expected,
    update_scenario,
    validate_valuation,
)
from app.valuation_enums import (
    AttributionLevel,
    RealValueNature,
    ScenarioType,
    ValueScope,
    ValueType,
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


def _create_user_in_org(
    client: TestClient, org_id: str, username: str, password: str, role: str = "viewer"
) -> str:
    db = TestingSessionLocal()
    db.add(
        User(
            organization_id=org_id,
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
    )
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def _seed_opportunity(db: Session, org_id: str, *, scope_note: str = "") -> Opportunity:
    opp = Opportunity(
        organization_id=org_id,
        codigo=f"OPP-{uuid.uuid4().hex[:6]}",
        tipo="EFICIENCIA",
        dominio="operaciones",
        titulo=f"Oportunidad {scope_note}",
        estado="DETECTADA",
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


def test_compute_adjusted_expected_deterministic():
    assert compute_adjusted_expected(Decimal("1000"), Decimal("0.75")) == Decimal("750.0000")
    assert compute_adjusted_expected(None, Decimal("0.5")) is None


def test_create_valuation_ahorro_interno():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Ahorro")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        val = create_valuation(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            value_type=ValueType.AHORRO,
            scope=ValueScope.INTERNO,
        )
        assert val.value_type == ValueType.AHORRO
        assert val.scope == ValueScope.INTERNO
        summary = compute_economic_summary(db, org.id, opp.id)
        assert summary["has_valuation"] is True
        assert len(summary["scenarios"]) == 3
    finally:
        db.close()


@pytest.mark.parametrize(
    "value_type",
    [
        ValueType.PERDIDA_EVITADA,
        ValueType.INGRESO_RECUPERADO,
        ValueType.NUEVO_INGRESO,
        ValueType.OPORTUNIDAD_COMERCIAL,
    ],
)
def test_value_types(value_type: str):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Val {value_type[:8]}")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        val = create_valuation(db, organization_id=org.id, opportunity_id=opp.id, value_type=value_type)
        assert val.value_type == value_type
    finally:
        db.close()


def test_valor_externo():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Externo")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id, scope_note="externa")
        val = create_valuation(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            value_type=ValueType.NUEVO_INGRESO,
            scope=ValueScope.EXTERNO,
        )
        assert val.scope == ValueScope.EXTERNO
    finally:
        db.close()


def test_scenarios_conservador_base_optimista():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Escenarios")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        update_scenario(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            scenario_type=ScenarioType.CONSERVADOR,
            value_amount=Decimal("500"),
            probability=Decimal("0.4"),
            cost=Decimal("100"),
            period_days=180,
            assumptions="Escenario conservador",
        )
        update_scenario(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            scenario_type=ScenarioType.BASE,
            value_amount=Decimal("1000"),
            probability=Decimal("0.6"),
            cost=Decimal("150"),
        )
        update_scenario(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            scenario_type=ScenarioType.OPTIMISTA,
            value_amount=Decimal("2000"),
            probability=Decimal("0.8"),
            cost=Decimal("200"),
        )
        summary = compute_economic_summary(db, org.id, opp.id)
        scenarios = {s["scenario_type"]: s for s in summary["scenarios"]}
        assert scenarios["CONSERVADOR"]["adjusted_value"] == Decimal("200.0000")
        assert scenarios["BASE"]["adjusted_value"] == Decimal("600.0000")
        assert scenarios["OPTIMISTA"]["adjusted_value"] == Decimal("1600.0000")
    finally:
        db.close()


def test_expected_value_with_probability():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Esperado")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        update_expected(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            gross_value=Decimal("10000"),
            probability=Decimal("0.7"),
            execution_cost_expected=Decimal("500"),
            period_days=365,
            assumptions="Ahorro anual estimado",
            source="Análisis financiero",
        )
        summary = compute_economic_summary(db, org.id, opp.id)
        assert summary["adjusted_expected"] == Decimal("7000.0000")
        assert summary["gross_expected"] == Decimal("10000")
    finally:
        db.close()


def test_finops_integration_and_execution_costs():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val FinOps")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        finops.registrar_consumo(
            db,
            organization_id=org.id,
            provider="openai",
            model_name="gpt-4o-mini",
            tokens_in=1000,
            tokens_out=500,
            opportunity_id=opp.id,
            cost=Decimal("2.50"),
            currency="USD",
            skip_budget_enforcement=True,
        )
        register_execution_cost(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            cost_type="HORAS HUMANAS",
            amount=Decimal("500"),
            currency="USD",
        )
        register_real_value(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            materialized_value=Decimal("5000"),
            value_nature=RealValueNature.VERIFICADO,
            attribution_level=AttributionLevel.ATRIBUIBLE,
        )
        summary = compute_economic_summary(db, org.id, opp.id)
        assert summary["finops_ia_cost"] == Decimal("2.5")
        assert summary["total_execution_cost"] == Decimal("502.5")
        assert summary["net_benefit"] == Decimal("4497.5")
        assert summary["return_percent"] is not None
        assert summary["return_percent"] > Decimal("800")
    finally:
        db.close()


def test_net_benefit_and_return():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val ROI")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        update_expected(db, organization_id=org.id, opportunity_id=opp.id, period_days=90)
        register_execution_cost(
            db, organization_id=org.id, opportunity_id=opp.id, cost_type="OTRO", amount=Decimal("1000"), currency="USD"
        )
        register_real_value(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            materialized_value=Decimal("3000"),
            attribution_level=AttributionLevel.ATRIBUIBLE,
        )
        summary = compute_economic_summary(db, org.id, opp.id)
        assert summary["net_benefit"] == Decimal("2000")
        assert summary["return_percent"] == Decimal("200.00")
        assert summary["payback_days"] == 30
    finally:
        db.close()


def test_not_calculable_missing_data():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val NoCalc")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        summary = compute_economic_summary(db, org.id, opp.id)
        assert summary["return_label"] == "NO CALCULABLE"
        assert summary["payback_label"] == "NO CALCULABLE"
        assert len(summary["missing_for_calculation"]) > 0
    finally:
        db.close()


def test_partial_attribution():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Parcial")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        register_execution_cost(
            db, organization_id=org.id, opportunity_id=opp.id, cost_type="SERVICIOS", amount=Decimal("200"), currency="USD"
        )
        real = register_real_value(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            materialized_value=Decimal("1000"),
            value_nature=RealValueNature.ESTIMADO,
            attribution_level=AttributionLevel.PARCIALMENTE_ATRIBUIBLE,
            attribution_pct=Decimal("40"),
            justification="Impacto compartido con otras iniciativas",
        )
        assert real.attributable_value == Decimal("400.0000")
        summary = compute_economic_summary(db, org.id, opp.id)
        assert summary["attributable_value"] == Decimal("400.0000")
    finally:
        db.close()


def test_value_natures_verificado_estimado_potencial():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Naturaleza")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        for nature in (RealValueNature.VERIFICADO, RealValueNature.ESTIMADO, RealValueNature.POTENCIAL):
            real = register_real_value(
                db,
                organization_id=org.id,
                opportunity_id=opp.id,
                materialized_value=Decimal("100"),
                value_nature=nature,
                attribution_level=AttributionLevel.ATRIBUIBLE,
            )
            assert real.value_nature == nature
    finally:
        db.close()


def test_tenant_isolation():
    db = TestingSessionLocal()
    try:
        org_a = Organization(name="Val A")
        org_b = Organization(name="Val B")
        db.add_all([org_a, org_b])
        db.flush()
        opp_a = _seed_opportunity(db, org_a.id)
        create_valuation(db, organization_id=org_a.id, opportunity_id=opp_a.id)
        with pytest.raises(ValuationValidationError, match="no encontrada"):
            compute_economic_summary(db, org_b.id, opp_a.id)
    finally:
        db.close()


def test_history_preserved():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Hist")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        update_expected(
            db,
            organization_id=org.id,
            opportunity_id=opp.id,
            gross_value=Decimal("5000"),
            probability=Decimal("0.5"),
        )
        summary = compute_economic_summary(db, org.id, opp.id)
        assert len(summary["history"]) >= 2
        assert summary["valuation"]["version"] >= 2
    finally:
        db.close()


def test_validate_valuation():
    db = TestingSessionLocal()
    try:
        org = Organization(name="Val Valid")
        db.add(org)
        db.flush()
        opp = _seed_opportunity(db, org.id)
        create_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        update_expected(
            db, organization_id=org.id, opportunity_id=opp.id, gross_value=Decimal("1000"), probability=Decimal("0.5")
        )
        val = validate_valuation(db, organization_id=org.id, opportunity_id=opp.id)
        assert val.status == "VALIDADA"
        with pytest.raises(ValuationValidationError, match="validada"):
            update_expected(db, organization_id=org.id, opportunity_id=opp.id, gross_value=Decimal("2000"))
    finally:
        db.close()


def test_api_valuation_rbac(client: TestClient):
    org_id, admin_token = _create_org_user(client, f"val-api-{uuid.uuid4().hex[:6]}", "ValApi*")
    db = TestingSessionLocal()
    try:
        opp = _seed_opportunity(db, org_id)
        opp_id = opp.id
    finally:
        db.close()

    created = client.post(
        f"/api/valoracion/opportunities/{opp_id}",
        headers=auth_header(admin_token),
        json={"value_type": "AHORRO", "scope": "INTERNO", "currency": "USD"},
    )
    assert created.status_code == 200

    summary = client.get(f"/api/valoracion/opportunities/{opp_id}", headers=auth_header(admin_token))
    assert summary.status_code == 200
    assert summary.json()["has_valuation"] is True

    roi = client.get(f"/api/valoracion/opportunities/{opp_id}/roi", headers=auth_header(admin_token))
    assert roi.status_code == 200

    viewer_token = _create_user_in_org(
        client, org_id, f"val-view-{uuid.uuid4().hex[:6]}", "ValView*", role="viewer"
    )
    denied = client.post(
        f"/api/valoracion/opportunities/{opp_id}",
        headers=auth_header(viewer_token),
        json={"value_type": "AHORRO", "scope": "INTERNO"},
    )
    assert denied.status_code == 403

    viewer_ok = client.get(f"/api/valoracion/opportunities/{opp_id}/roi", headers=auth_header(viewer_token))
    assert viewer_ok.status_code == 200


def test_api_cross_tenant_denied(client: TestClient):
    org_a, token_a = _create_org_user(client, f"val-tenant-a-{uuid.uuid4().hex[:6]}", "ValA*")
    _, token_b = _create_org_user(client, f"val-tenant-b-{uuid.uuid4().hex[:6]}", "ValB*")
    db = TestingSessionLocal()
    try:
        opp = _seed_opportunity(db, org_a)
        opp_id = opp.id
    finally:
        db.close()

    denied = client.get(f"/api/valoracion/opportunities/{opp_id}", headers=auth_header(token_b))
    assert denied.status_code == 400
