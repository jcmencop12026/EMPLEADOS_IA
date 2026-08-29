"""BLOQUE 1280 — Modelo comercial basado en valor."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.commercial_enums import ProposalStatus, ValueCategory, ValueNature
from app.models import AuditLog, Organization, User
from app.opportunity_models import Opportunity
from app.security import hash_password
from app.services.commercial_service import CommercialValidationError, _compute_attributable
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db: Session, org_name: str, role: str = "admin") -> tuple[Organization, User, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"t-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "Tenant1280*Test1"
    user = User(
        organization_id=org.id,
        username=f"u-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password, user.username


def _create_plan(client: TestClient, headers: dict) -> dict:
    code = f"plan-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={
            "code": code,
            "name": f"Plan {code}",
            "fraccion_valor_sugerida": 0.3,
            "margen_minimo_pct": 0.2,
            "consumo_ia_incluido_tokens": 1_000_000,
            "presupuesto_ia_incluido": 500,
            "credential_mode": "IA_ADMINISTRADA",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_proposal(client: TestClient, headers: dict, plan_id: str | None = None) -> dict:
    res = client.post(
        "/api/comercial/propuestas",
        headers=headers,
        json={"titulo": "Propuesta prueba 1280", "plan_id": plan_id, "credential_mode": "IA_ADMINISTRADA"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_value_natures_and_attribution(client: TestClient):
    db = TestingSessionLocal()
    _, user, password, username = _create_tenant(db, "1280 Valor")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    for nat in (ValueNature.VERIFICADO, ValueNature.ESTIMADO, ValueNature.POTENCIAL):
        res = client.post(
            f"/api/comercial/propuestas/{prop['id']}/valores",
            headers=headers,
            json={
                "categoria": ValueCategory.AHORRO,
                "naturaleza": nat,
                "valor_bruto": 100000,
                "atribucion_pct": 40,
                "criterio_atribucion": f"Criterio {nat}",
            },
        )
        assert res.status_code == 201
    detail = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers)
    assert len(detail.json()["valores"]) == 3
    assert _compute_attributable(100000, 40) == 40000


def test_attribution_requires_criteria(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Attr")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    bad = client.post(
        f"/api/comercial/propuestas/{prop['id']}/valores",
        headers=headers,
        json={"categoria": "AHORRO", "valor_bruto": 50000, "atribucion_pct": 0},
    )
    assert bad.status_code == 422


def test_scenarios_conservador_base_alto(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Esc")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    for st in ("CONSERVADOR", "BASE", "ALTO"):
        res = client.post(
            f"/api/comercial/propuestas/{prop['id']}/escenarios",
            headers=headers,
            json={
                "scenario_type": st,
                "valor_esperado": 100000,
                "valor_atribuible": 40000,
                "probabilidad": 0.7,
                "costo": 12000,
                "es_recomendado": st == "BASE",
            },
        )
        assert res.status_code == 201
    detail = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers)
    tipos = {s["scenario_type"] for s in detail.json()["escenarios"]}
    assert tipos == {"CONSERVADOR", "BASE", "ALTO"}


def test_costs_and_margin_floor(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Costos")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _create_plan(client, headers)
    prop = _create_proposal(client, headers, plan["id"])
    client.post(
        f"/api/comercial/propuestas/{prop['id']}/valores",
        headers=headers,
        json={
            "categoria": "AHORRO",
            "naturaleza": "ESTIMADO",
            "valor_bruto": 200000,
            "atribucion_pct": 50,
            "criterio_atribucion": "Automatización",
        },
    )
    client.post(
        f"/api/comercial/propuestas/{prop['id']}/costos",
        headers=headers,
        json={"categoria": "CONSUMO_IA", "clase_costo": "COSTO_PROVEEDOR_IA", "monto": 8000},
    )
    client.post(
        f"/api/comercial/propuestas/{prop['id']}/costos",
        headers=headers,
        json={"categoria": "IMPLEMENTACION", "clase_costo": "COSTO_INTERNO", "monto": 12000},
    )
    price = client.post(f"/api/comercial/propuestas/{prop['id']}/precio-sugerido", headers=headers, json={})
    assert price.status_code == 200
    body = price.json()
    assert body["precio_sugerido"] >= body["piso_costos"]
    assert body["beneficio_neto_cliente"] is not None
    assert body["roi_pct"] is not None


def test_value_based_price_suggestion(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Precio")
    db.close()
    headers = auth_header(_token(client, username, password))
    sim = client.post(
        "/api/comercial/simular",
        headers=headers,
        json={"valor_bruto": 100000, "atribucion_pct": 40, "costo_total": 10000, "fraccion_valor": 0.25},
    )
    assert sim.status_code == 200
    assert sim.json()["valor_atribuible"] == 40000


def test_human_approval_not_automatic(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Aprob")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    client.post(
        f"/api/comercial/propuestas/{prop['id']}/valores",
        headers=headers,
        json={"categoria": "AHORRO", "naturaleza": "ESTIMADO", "valor_bruto": 80000, "atribucion_pct": 30, "criterio_atribucion": "X"},
    )
    client.post(f"/api/comercial/propuestas/{prop['id']}/costos", headers=headers, json={"categoria": "OPERACION", "monto": 5000})
    client.post(f"/api/comercial/propuestas/{prop['id']}/precio-sugerido", headers=headers, json={})
    detail = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers).json()
    assert detail["precio_sugerido"] is not None
    assert detail["precio_final"] is None
    client.post(
        f"/api/comercial/propuestas/{prop['id']}/precio-final",
        headers=headers,
        json={"precio_final": detail["precio_sugerido"], "justificacion": "Aceptar sugerido"},
    )
    approved = client.post(f"/api/comercial/propuestas/{prop['id']}/aprobar", headers=headers)
    assert approved.status_code == 200
    assert approved.json()["estado"] == ProposalStatus.APROBADA


def test_double_count_detection(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "1280 Dedup")
    opp = Opportunity(organization_id=org.id, codigo="OPP-X", tipo="T", dominio="d", titulo="t", estado="DETECTADA")
    db.add(opp)
    db.commit()
    opp_id = opp.id
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    for cat in (ValueCategory.AHORRO, ValueCategory.PERDIDA_EVITADA):
        client.post(
            f"/api/comercial/propuestas/{prop['id']}/valores",
            headers=headers,
            json={"categoria": cat, "naturaleza": "ESTIMADO", "valor_bruto": 50000, "atribucion_pct": 20, "criterio_atribucion": "c", "opportunity_id": opp_id},
        )
    alerts = client.post(f"/api/comercial/propuestas/{prop['id']}/detectar-doble-conteo", headers=headers)
    assert alerts.status_code == 200
    assert len(alerts.json()["alertas"]) >= 1


def test_credential_modes_in_plan(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Cred")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={"code": f"cred-{uuid.uuid4().hex[:4]}", "name": "Plan credenciales propias", "credential_mode": "CREDENCIALES_PROPIAS"},
    )
    assert res.status_code == 201
    assert res.json()["credential_mode"] == "CREDENCIALES_PROPIAS"


def test_tenant_isolation(client: TestClient):
    db = TestingSessionLocal()
    _, _, pass_a, user_a = _create_tenant(db, "1280 Tenant A")
    _, _, pass_b, user_b = _create_tenant(db, "1280 Tenant B")
    db.close()
    headers_a = auth_header(_token(client, user_a, pass_a))
    prop = _create_proposal(client, headers_a)
    headers_b = auth_header(_token(client, user_b, pass_b))
    assert client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers_b).status_code == 404


def test_rbac_viewer_cannot_approve(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 RBAC", role="viewer")
    db.close()
    headers = auth_header(_token(client, username, password))
    assert client.get("/api/comercial/propuestas", headers=headers).status_code == 200
    assert client.post("/api/comercial/propuestas", headers=headers, json={"titulo": "x"}).status_code == 403


def test_audit_on_proposal_create(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "1280 Audit")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    db = TestingSessionLocal()
    try:
        logs = db.query(AuditLog).filter(AuditLog.organization_id == org_id, AuditLog.action.like("comercial%")).all()
        actions = {l.action for l in logs}
        assert "comercial.propuesta.creada" in actions
    finally:
        db.close()


def test_traceability_endpoint(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Trace")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers)
    assert trace.status_code == 200
    assert "oportunidades" in trace.json()
