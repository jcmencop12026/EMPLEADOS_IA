"""Motor Económico EIAAX — Bloque 1600."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.economic_motor_enums import CostSource, EconomicValueType
from app.economic_motor_models import EconomicCostEntry
from app.models import Organization, User
from app.orchestration_models import FinOpsRecord
from app.security import hash_password
from app.services import economic_motor_service as motor
from app.valuation_enums import RealValueNature
from conftest import TestingSessionLocal, auth_header

pytestmark = pytest.mark.operations


def _db_session():
    return TestingSessionLocal()


def _org_user(db: Session, suffix: str) -> tuple[Organization, User, str]:
    from app.seed_permissions import bootstrap_permissions

    bootstrap_permissions(db)
    org = Organization(name=f"Motor Eco {suffix}", slug=f"motor-eco-{suffix}")
    db.add(org)
    db.flush()
    pwd = f"MotorEco*{suffix}1"
    user = User(
        organization_id=org.id,
        username=f"motor-{suffix}",
        password_hash=hash_password(pwd),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, pwd


def test_register_cost_real_creates_finops_and_motor_entry():
    db = _db_session()
    try:
        org, user, _ = _org_user(db, "cost")
        row = motor.register_cost(
            db,
            user,
            organization_id=org.id,
            amount_kind="REAL",
            cost_source=CostSource.CONSUMO_IA,
            amount=Decimal("1.25"),
            cost_class="DIRECTO",
            provider="openai",
            model_name="gpt-4o-mini",
            tokens_in=1000,
            tokens_out=200,
            register_finops=True,
        )
        db.commit()
        assert row.finops_record_id
        assert row.amount_kind == "REAL"
    finally:
        db.close()


def test_register_estimated_cost_no_finops():
    db = _db_session()
    try:
        org, user, _ = _org_user(db, "est")
        row = motor.register_cost(
            db,
            user,
            organization_id=org.id,
            amount_kind="ESTIMADO",
            cost_source=CostSource.IMPLEMENTACION,
            amount=Decimal("500"),
            register_finops=False,
        )
        db.commit()
        assert row.finops_record_id is None
    finally:
        db.close()


def test_potencial_not_in_realizado():
    db = _db_session()
    try:
        org, user, _ = _org_user(db, "pot")
        motor.register_value(
            db,
            user,
            organization_id=org.id,
            value_type=EconomicValueType.AHORRO,
            value_nature=RealValueNature.POTENCIAL,
            amount=Decimal("10000"),
            register_finops=False,
        )
        motor.register_value(
            db,
            user,
            organization_id=org.id,
            value_type=EconomicValueType.AHORRO,
            value_nature=RealValueNature.VERIFICADO,
            amount=Decimal("100"),
            register_finops=False,
        )
        db.commit()
        sums = motor.sum_values_by_nature(db, org.id)
        assert sums["valor_potencial"] == 10000.0
        assert sums["valor_realizado"] == 100.0
    finally:
        db.close()


def test_entity_view_excludes_private_economy(client: TestClient):
    db = _db_session()
    try:
        org, user, pwd = _org_user(db, "ent")
        motor.save_private_economy(
            db,
            user,
            org.id,
            {"margin": 0.45, "suggested_price": 9999, "client_value": 12000},
        )
        db.commit()
        login = client.post("/api/auth/login", json={"username": user.username, "password": pwd})
        token = login.json()["access_token"]
        res = client.get("/api/motor-economico/vista-entidad", headers=auth_header(token))
        assert res.status_code == 200
        body = res.json()
        assert body["economia_privada_incluida"] is False
        assert "9999" not in str(body)
    finally:
        db.close()


def test_private_economy_requires_permission(client: TestClient):
    db = _db_session()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        org = Organization(name="Motor Eco viewer", slug="motor-eco-viewer")
        db.add(org)
        db.flush()
        pwd = "Viewer*123"
        user = User(
            organization_id=org.id,
            username="motor-viewer-only",
            password_hash=hash_password(pwd),
            role="viewer",
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()
        login = client.post("/api/auth/login", json={"username": user.username, "password": pwd})
        token = login.json()["access_token"]
        res = client.get("/api/motor-economico/economia-privada", headers=auth_header(token))
        assert res.status_code == 403
    finally:
        db.close()


def test_private_economy_superadmin(client: TestClient, auth_headers):
    db = _db_session()
    try:
        org, _, _ = _org_user(db, "sa")
        res = client.put(
            f"/api/motor-economico/economia-privada?organization_id={org.id}",
            headers=auth_headers,
            json={"margin": 0.3, "roi": 1.2, "suggested_price": 5000},
        )
        assert res.status_code == 200
        assert res.json()["margin"] == 0.3
    finally:
        db.close()


def test_price_recommendation_is_draft(client: TestClient, auth_headers):
    res = client.post(
        "/api/motor-economico/precio-recomendado",
        headers=auth_headers,
        json={"attributable_value": "1000", "complexity": 0.6, "risk": 0.4},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "BORRADOR"
    assert body["auto_published"] is False


def test_indicators_phases(client: TestClient, auth_headers):
    res = client.get("/api/motor-economico/indicadores", headers=auth_headers)
    assert res.status_code == 200
    fases = res.json()["fases"]
    assert "ANTES" in fases and "PROYECTADO" in fases and "REAL" in fases


def test_backfill_finops_idempotent():
    db = _db_session()
    try:
        org, _, _ = _org_user(db, "bf")
        record = FinOpsRecord(
            organization_id=org.id,
            category="Modelo IA",
            cost=2.5,
            currency="USD",
            execution_ref="transversal:auditor",
            provider="openai",
            model_name="gpt-4o-mini",
            tokens_in=500,
            tokens_out=100,
        )
        db.add(record)
        db.commit()
        n1 = motor.backfill_costs_from_finops(db, org.id)
        n2 = motor.backfill_costs_from_finops(db, org.id)
        db.commit()
        assert n1 == 1
        assert n2 == 0
        entry = db.query(EconomicCostEntry).filter(EconomicCostEntry.finops_record_id == record.id).first()
        assert entry.cost_class == "TRANSVERSAL_ATRIBUIBLE"
    finally:
        db.close()
