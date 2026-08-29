"""BLOQUE 1280 — Modelo comercial basado en valor."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.commercial_enums import ProposalStatus, ValueCategory, ValueNature, ValueScope
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


def test_value_scope_interno_externo(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Scope")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    res_int = client.post(
        f"/api/comercial/propuestas/{prop['id']}/valores",
        headers=headers,
        json={"categoria": ValueCategory.AHORRO, "naturaleza": "VERIFICADO", "valor_bruto": 50000, "atribucion_pct": 30, "criterio_atribucion": "Interno"},
    )
    assert res_int.status_code == 201
    res_ext = client.post(
        f"/api/comercial/propuestas/{prop['id']}/valores",
        headers=headers,
        json={
            "categoria": ValueCategory.NUEVO_INGRESO,
            "naturaleza": "POTENCIAL",
            "valor_bruto": 80000,
            "atribucion_pct": 25,
            "criterio_atribucion": "Mercado",
            "external_intelligence_ref": "ext-signal-001",
        },
    )
    assert res_ext.status_code == 201
    detail = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers).json()
    alcances = {v["alcance"] for v in detail["valores"]}
    assert ValueScope.INTERNO in alcances
    assert ValueScope.EXTERNO in alcances
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers).json()
    assert trace["valor_interno_atribuible"] == 15000.0
    assert trace["valor_externo_atribuible"] == 20000.0
    assert "ext-signal-001" in trace["inteligencia_externa_1240"]


def test_simulation_does_not_modify_proposal(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 SimProp")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    client.post(
        f"/api/comercial/propuestas/{prop['id']}/valores",
        headers=headers,
        json={"categoria": "AHORRO", "naturaleza": "ESTIMADO", "valor_bruto": 100000, "atribucion_pct": 40, "criterio_atribucion": "X"},
    )
    before = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers).json()
    sim = client.post(
        f"/api/comercial/propuestas/{prop['id']}/simular",
        headers=headers,
        json={"valor_bruto": 200000, "atribucion_pct": 50, "fraccion_valor": 0.5},
    )
    assert sim.status_code == 200
    assert sim.json()["simulacion"] is True
    assert sim.json()["valor_atribuible"] == 100000.0
    after = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers).json()
    assert after["valor_atribuible_total"] == before["valor_atribuible_total"]
    assert after["precio_sugerido"] == before["precio_sugerido"]


def test_excedentes_ia(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Exced")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={
            "code": f"exc-{uuid.uuid4().hex[:4]}",
            "name": "Plan excedentes",
            "consumo_ia_incluido_tokens": 1_000_000,
            "excedente_ia_por_millon": 12.5,
            "alerta_consumo_pct": 80,
        },
    ).json()
    sim = client.post(
        "/api/comercial/simular",
        headers=headers,
        json={"valor_bruto": 100000, "atribucion_pct": 40, "costo_total": 10000, "plan_id": plan["id"], "tokens_usados": 1_500_000},
    )
    assert sim.status_code == 200
    consumo = sim.json()["consumo_ia"]
    assert consumo["excedente_tokens"] == 500_000
    assert consumo["costo_excedente"] == 6.25
    assert consumo["alerta"] is True


def test_roi_payback_numeric_deterministic(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 ROI")
    db.close()
    headers = auth_header(_token(client, username, password))
    sim = client.post(
        "/api/comercial/simular",
        headers=headers,
        json={"valor_bruto": 120000, "atribucion_pct": 50, "costo_total": 10000, "fraccion_valor": 0.25, "margen_minimo_pct": 0.2},
    ).json()
    assert sim["valor_atribuible"] == 60000.0
    assert sim["precio_sugerido"] == 15000.0
    assert sim["beneficio_neto_cliente"] == 45000.0
    assert sim["roi_pct"] == 300.0
    assert sim["payback_meses"] == 3.0
    assert sim["pct_valor_capturado_empleados_ia"] == 25.0
    assert sim["pct_valor_conservado_cliente"] == 75.0


def test_plan_detail_endpoint(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 PlanDet")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _create_plan(client, headers)
    detail = client.get(f"/api/comercial/planes/{plan['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["code"] == plan["code"]


def test_traceability_endpoint(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "1280 Trace")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _create_proposal(client, headers)
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers)
    assert trace.status_code == 200
    assert "oportunidades" in trace.json()
