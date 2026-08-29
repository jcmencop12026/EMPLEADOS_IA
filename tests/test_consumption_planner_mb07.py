"""MB-07 — Planificador de consumo y capacidad IA."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.consumption_planner_models import ConsumptionPlannerOrgConfig
from app.finops_models import FinOpsRate, FinOpsValueRecord
from app.models import Organization, User
from app.orchestration_models import AIEmployee, EmployeeLimits, FinOpsRecord
from app.security import hash_password
from app.services.consumption_planner_service import (
    aggregate_real_consumption,
    classify_finops_record,
    estimate_transversal_monthly,
    get_or_create_org_config,
    realized_value_sum,
    simulate,
    validate_distribution,
    weighted_llm_cost,
)
from app.valuation_enums import RealValueNature
from conftest import auth_header

pytestmark = pytest.mark.operations


def _create_employee(db: Session, org_id: str, user_id: str, code: str) -> AIEmployee:
    emp = AIEmployee(
        organization_id=org_id,
        code=code,
        name=f"Emp {code}",
        specialty="general",
        lifecycle_status="ACTIVE",
        status="DISPONIBLE",
        is_active=True,
    )
    db.add(emp)
    db.flush()
    db.add(EmployeeLimits(employee_id=emp.id, daily_cost_limit=100.0))
    db.flush()
    return emp


def _seed_rate(db: Session, org_id: str, provider: str, model: str, price_in: str, price_out: str) -> FinOpsRate:
    rate = FinOpsRate(
        organization_id=org_id,
        provider=provider,
        model_service=model,
        price_input=Decimal(price_in),
        price_output=Decimal(price_out),
        currency="USD",
        active=True,
    )
    db.add(rate)
    db.flush()
    return rate


def test_classify_consumption_direct_transversal_platform():
    direct = FinOpsRecord(organization_id="o", employee_id="e1", category="Modelo IA")
    trans = FinOpsRecord(organization_id="o", execution_ref="transversal:auditor", category="Modelo IA")
    plat = FinOpsRecord(organization_id="o", execution_ref="platform:benchmark", category="Procesamiento")
    assert classify_finops_record(direct) == "DIRECTO"
    assert classify_finops_record(trans) == "TRANSVERSAL_ATRIBUIBLE"
    assert classify_finops_record(plat) == "PLATAFORMA"


def test_deterministic_llm_cost_zero(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        org_id = admin.organization_id
        db.add(
            FinOpsRecord(
                organization_id=org_id,
                execution_ref="transversal:auditor:deterministic",
                category="Procesamiento",
                cost=Decimal("1.5"),
                tokens_in=0,
                tokens_out=0,
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.get("/api/finops/planner/resumen", headers=auth_headers)
    assert res.status_code == 200
    real = res.json()["real_by_class"]["TRANSVERSAL_ATRIBUIBLE"]
    assert real["cost_ia"] == 0.0
    assert real["cost_other"] >= 1.5


def test_estimate_real_projected_kinds(client: TestClient, auth_headers):
    res = client.get("/api/finops/planner/resumen", headers=auth_headers)
    body = res.json()
    assert body["estimated_direct"]["kind"] == "ESTIMADO"
    assert body["estimated_transversal"]["kind"] == "ESTIMADO"
    sim = client.post(
        "/api/finops/planner/simular",
        headers=auth_headers,
        json={"active_employees": 10, "executions_per_day": 5, "days": 30},
    ).json()
    assert sim["kind"] == "PROYECTADO"


def test_model_distribution_must_sum_100():
    with pytest.raises(ValueError, match="100%"):
        validate_distribution([{"pct": 60}, {"pct": 30}])
    ok = validate_distribution([{"pct": 60}, {"pct": 40}])
    assert len(ok) == 2


def test_simulator_demo_scenario(client: TestClient, auth_headers):
    res = client.post(
        "/api/finops/planner/simular",
        headers=auth_headers,
        json={"active_employees": 25, "executions_per_day": 20, "days": 30},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["directo"]["executions_monthly"] == 15000
    assert body["demo_notice"]
    assert "capacity" in body
    assert "budget" in body


def test_budget_overconsumption(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        cfg = get_or_create_org_config(db, admin.organization_id)
        cfg.included_consumption_usd = 10.0
        db.commit()
    finally:
        db.close()

    pres = client.get("/api/finops/planner/presupuesto", headers=auth_headers).json()
    assert pres["consumo_incluido"] == 10.0
    assert pres["sobreconsumo"] >= 0


def test_capacity_and_concurrency(client: TestClient, auth_headers):
    cap = client.get("/api/finops/planner/capacidad", headers=auth_headers).json()
    assert "max_concurrency" in cap
    assert "executions_per_day" in cap
    assert cap["executions_per_day"] > 0


def test_compare_providers(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        _seed_rate(db, admin.organization_id, "openai", "gpt-4o-mini", "0.00001", "0.00002")
        _seed_rate(db, admin.organization_id, "openai", "gpt-4o", "0.00005", "0.00010")
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/finops/planner/comparar",
        headers=auth_headers,
        json={
            "tokens_in": 1000,
            "tokens_out": 500,
            "scenarios": [
                {"provider": "openai", "model": "gpt-4o-mini"},
                {"provider": "openai", "model": "gpt-4o"},
            ],
        },
    )
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 2
    assert all(r["rate_configured"] for r in rows)
    costs = sorted([r["cost_estimated"] for r in rows])
    assert costs[1] > costs[0]


def test_employee_cost_detail(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        emp = _create_employee(db, admin.organization_id, admin.id, f"pln-{uuid.uuid4().hex[:4]}")
        db.add(
            FinOpsRecord(
                organization_id=admin.organization_id,
                employee_id=emp.id,
                category="Modelo IA",
                cost=Decimal("2.5"),
                tokens_in=1000,
                tokens_out=500,
            )
        )
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    detail = client.get(f"/api/finops/planner/empleado/{emp_id}", headers=auth_headers).json()
    assert detail["real"]["cost_ia"] == 2.5
    assert detail["estimated_monthly_single"]["kind"] == "ESTIMADO"


def test_transversal_auditor_deterministic_zero_llm(client: TestClient, auth_headers):
    rows = client.get("/api/finops/planner/transversal", headers=auth_headers).json()
    auditor = next(r for r in rows if r["capability_code"] == "auditor_empleados")
    assert auditor["is_deterministic"] is True


def test_margin_permission(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        cfg = get_or_create_org_config(db, admin.organization_id)
        cfg.client_price_monthly = 500.0
        db.commit()
    finally:
        db.close()

    ok = client.get("/api/finops/planner/margen", headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json()["available"] is True


def test_potencial_excluded_from_realized_value():
    from app.database import SessionLocal
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    db = SessionLocal()
    try:
        org = Organization(name="Val Org", slug=f"val-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        bootstrap_permissions(db)
        bootstrap_orchestration(db, org.id)
        bootstrap_salud(db, org.id)
        db.add(
            FinOpsValueRecord(
                organization_id=org.id,
                value_type="AHORRO",
                certainty="Real",
                amount=Decimal("100"),
                notes="valor real",
            )
        )
        db.add(
            FinOpsValueRecord(
                organization_id=org.id,
                value_type="AHORRO",
                certainty="Real",
                amount=Decimal("999"),
                notes=f"tipo {RealValueNature.POTENCIAL}",
            )
        )
        db.commit()
        total = float(realized_value_sum(db, org.id))
        assert total == 100.0
    finally:
        db.close()


def test_credential_modes(client: TestClient, auth_headers):
    patch = client.patch(
        "/api/finops/planner/config",
        headers=auth_headers,
        json={"credential_mode": "CREDENCIALES_PROPIAS", "currency": "EUR"},
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["credential_mode"] == "CREDENCIALES_PROPIAS"
    assert body["currency"] == "EUR"


def test_ia_administrada_default(client: TestClient, auth_headers):
    patch = client.patch(
        "/api/finops/planner/config",
        headers=auth_headers,
        json={"credential_mode": "IA_ADMINISTRADA"},
    )
    assert patch.status_code == 200
    cfg = client.get("/api/finops/planner/config", headers=auth_headers).json()
    assert cfg["credential_mode"] == "IA_ADMINISTRADA"


def test_multiempresa(client: TestClient):
    from app.database import SessionLocal
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    db = SessionLocal()
    try:
        org_a = Organization(name="Pln A", slug=f"pln-a-{uuid.uuid4().hex[:6]}")
        org_b = Organization(name="Pln B", slug=f"pln-b-{uuid.uuid4().hex[:6]}")
        db.add_all([org_a, org_b])
        db.flush()
        for org in (org_a, org_b):
            bootstrap_permissions(db)
            bootstrap_orchestration(db, org.id)
            bootstrap_salud(db, org.id)
        pwd = "PlannerTest*1"
        ua = User(
            organization_id=org_a.id,
            username=f"pln_a_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password(pwd),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        ub = User(
            organization_id=org_b.id,
            username=f"pln_b_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password(pwd),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add_all([ua, ub])
        db.commit()
        username_a, username_b = ua.username, ub.username
    finally:
        db.close()

    ta = client.post("/api/auth/login", json={"username": username_a, "password": pwd}).json()["access_token"]
    tb = client.post("/api/auth/login", json={"username": username_b, "password": pwd}).json()["access_token"]
    res_a = client.get("/api/finops/planner/resumen", headers=auth_header(ta)).json()
    res_b = client.get("/api/finops/planner/resumen", headers=auth_header(tb)).json()
    assert res_a["organization_id"] != res_b["organization_id"]


def test_rbac_simulate_requires_permission(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        viewer = User(
            organization_id=admin.organization_id,
            username=f"viewer_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password("Viewer*12345"),
            role="viewer",
            status="ACTIVE",
            is_active=True,
        )
        db.add(viewer)
        db.commit()
        username = viewer.username
    finally:
        db.close()

    token = client.post("/api/auth/login", json={"username": username, "password": "Viewer*12345"}).json()["access_token"]
    denied = client.post(
        "/api/finops/planner/simular",
        headers=auth_header(token),
        json={"active_employees": 5},
    )
    assert denied.status_code == 403


def test_centro_control_contract(client: TestClient, auth_headers):
    res = client.get("/api/finops/planner/contrato-centro-control", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "consumo_real" in body
    assert "presupuesto_limite" in body


def test_weighted_cost_with_rates():
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        org_id = admin.organization_id
        _seed_rate(db, org_id, "openai", "gpt-4o-mini", "0.00001", "0.00002")
        _seed_rate(db, org_id, "openai", "gpt-4o", "0.00005", "0.00010")
        db.commit()
        dist = [
            {"provider": "openai", "model": "gpt-4o-mini", "pct": 60},
            {"provider": "openai", "model": "gpt-4o", "pct": 40},
        ]
        cost = float(weighted_llm_cost(db, org_id, 10000, 5000, dist, "USD"))
        assert cost > 0
    finally:
        db.close()


def test_aggregate_real_by_class():
    from app.database import SessionLocal
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    db = SessionLocal()
    try:
        org = Organization(name="Agg Org", slug=f"agg-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        bootstrap_permissions(db)
        bootstrap_orchestration(db, org.id)
        bootstrap_salud(db, org.id)
        admin = User(
            organization_id=org.id,
            username=f"agg_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password("Agg*12345"),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add(admin)
        db.flush()
        emp = _create_employee(db, org.id, admin.id, f"agg-{uuid.uuid4().hex[:4]}")
        db.add(
            FinOpsRecord(
                organization_id=org.id,
                employee_id=emp.id,
                category="Modelo IA",
                cost=Decimal("3"),
                tokens_in=100,
                tokens_out=50,
            )
        )
        db.add(
            FinOpsRecord(
                organization_id=org.id,
                execution_ref="platform:ops",
                category="Procesamiento",
                cost=Decimal("1"),
            )
        )
        db.commit()
        agg = aggregate_real_consumption(db, org.id)
        assert agg["kind"] == "REAL"
        assert agg["by_class"]["DIRECTO"]["cost_ia"] == 3.0
        assert agg["by_class"]["PLATAFORMA"]["cost_other"] == 1.0
    finally:
        db.close()


def test_transversal_estimate_monthly():
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        cfg = get_or_create_org_config(db, admin.organization_id)
        est = estimate_transversal_monthly(db, admin.organization_id, cfg)
        auditor = next(i for i in est["items"] if i["capability_code"] == "auditor_empleados")
        assert auditor["cost_ia"] == 0.0
        assert auditor["cost_infra"] > 0
    finally:
        db.close()


def test_alerts_contract(client: TestClient, auth_headers):
    res = client.get("/api/finops/planner/alertas", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_config_patch_idempotent(client: TestClient, auth_headers):
    first = client.patch(
        "/api/finops/planner/config",
        headers=auth_headers,
        json={"executions_per_employee_per_day": 7},
    ).json()
    second = client.patch(
        "/api/finops/planner/config",
        headers=auth_headers,
        json={"executions_per_employee_per_day": 7},
    ).json()
    assert first["executions_per_employee_per_day"] == second["executions_per_employee_per_day"]
