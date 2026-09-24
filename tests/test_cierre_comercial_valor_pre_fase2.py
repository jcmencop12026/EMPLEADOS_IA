"""Cierre funcional comercial/valor pre-Fase 2 — escenarios obligatorios."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.commercial_enums import ValueCategory, ValueNature
from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.security import hash_password
from app.services import finops_service
from app.services.valuation_service import create_valuation, register_real_value
from app.valuation_enums import AttributionLevel, RealValueNature
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db: Session, org_name: str, role: str = "admin") -> tuple[Organization, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"t-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "CierreValor*Test1"
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
    return org, password, user.username


def _headers(client: TestClient, db: Session, role: str = "admin") -> tuple[dict, Organization]:
    org, password, username = _create_tenant(db, f"Org {uuid.uuid4().hex[:6]}", role=role)
    return auth_header(_token(client, username, password)), org


def _proposal(client: TestClient, headers: dict, **kwargs) -> dict:
    res = client.post("/api/comercial/propuestas", headers=headers, json={"titulo": "Cierre valor", **kwargs})
    assert res.status_code == 201, res.text
    return res.json()


def _add_value(client, headers, prop_id, **kwargs):
    payload = {
        "categoria": ValueCategory.AHORRO,
        "naturaleza": ValueNature.ESTIMADO,
        "valor_bruto": 100000,
        "atribucion_pct": 50,
        "criterio_atribucion": "Criterio prueba",
        **kwargs,
    }
    res = client.post(f"/api/comercial/propuestas/{prop_id}/valores", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_01_valor_verificado(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    _add_value(client, headers, prop["id"], naturaleza=ValueNature.VERIFICADO, valor_bruto=80000, atribucion_pct=40)
    detail = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers).json()
    assert detail["valores"][0]["naturaleza"] == ValueNature.VERIFICADO


def test_02_valor_estimado(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    _add_value(client, headers, prop["id"], naturaleza=ValueNature.ESTIMADO)
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers).json()
    assert trace["desglose_naturaleza"]["valor_estimado_atribuible"] == 50000.0


def test_03_valor_potencial(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    _add_value(
        client, headers, prop["id"],
        categoria=ValueCategory.NUEVO_INGRESO,
        naturaleza=ValueNature.POTENCIAL,
        valor_bruto=200000,
        external_intelligence_ref="ext-001",
    )
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers).json()
    assert trace["desglose_naturaleza"]["valor_potencial_atribuible"] == 100000.0


def test_04_potencial_no_como_realizado(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    _add_value(client, headers, prop["id"], naturaleza=ValueNature.VERIFICADO, valor_bruto=100000, atribucion_pct=50)
    _add_value(
        client, headers, prop["id"],
        categoria=ValueCategory.NUEVO_INGRESO,
        naturaleza=ValueNature.POTENCIAL,
        valor_bruto=300000,
        atribucion_pct=50,
    )
    price = client.post(f"/api/comercial/propuestas/{prop['id']}/precio-sugerido", headers=headers, json={}).json()
    assert price["valor_atribuible"] == 50000.0
    assert price["desglose_naturaleza"]["valor_potencial_atribuible"] == 150000.0
    assert any("POTENCIAL" in a for a in price.get("advertencias", []))


def test_05_costo_ia_administrada(client: TestClient):
    db = TestingSessionLocal()
    headers, org = _headers(client, db)
    record = finops_service.registrar_consumo(
        db,
        organization_id=org.id,
        provider="openai",
        model_name="gpt-4",
        tokens_in=1000,
        tokens_out=500,
        cost=Decimal("18.75"),
        currency="USD",
    )
    db.commit()
    record_id = record.id
    db.close()
    prop = _proposal(client, headers, credential_mode="IA_ADMINISTRADA")
    client.post(
        f"/api/comercial/propuestas/{prop['id']}/costos",
        headers=headers,
        json={
            "categoria": "CONSUMO_IA",
            "clase_costo": "COSTO_PROVEEDOR_IA",
            "monto": 18.75,
            "finops_record_id": record_id,
            "descripcion": "Consumo API OpenAI",
        },
    )
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers).json()
    assert record_id in trace["finops_refs"]
    assert prop["credential_mode"] == "IA_ADMINISTRADA"


def test_06_credenciales_propias(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    plan = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={"code": f"byok-{uuid.uuid4().hex[:4]}", "name": "Plan BYOK", "credential_mode": "CREDENCIALES_PROPIAS"},
    ).json()
    prop = _proposal(client, headers, plan_id=plan["id"])
    assert prop["credential_mode"] == "CREDENCIALES_PROPIAS"


def test_07_consumo_incluido(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    plan = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={
            "code": f"inc-{uuid.uuid4().hex[:4]}",
            "name": "Plan incluido",
            "consumo_ia_incluido_tokens": 2_000_000,
            "presupuesto_ia_incluido": 800,
        },
    ).json()
    sim = client.post(
        "/api/comercial/simular",
        headers=headers,
        json={"valor_bruto": 100000, "atribucion_pct": 40, "costo_total": 5000, "plan_id": plan["id"], "tokens_usados": 1_000_000},
    ).json()
    assert sim["consumo_ia"]["consumo_ia_incluido_tokens"] == 2_000_000
    assert sim["consumo_ia"]["excedente_tokens"] == 0


def test_08_sobreconsumo_y_bloqueo(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    plan = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={
            "code": f"blk-{uuid.uuid4().hex[:4]}",
            "name": "Plan bloqueo",
            "consumo_ia_incluido_tokens": 1_000_000,
            "excedente_ia_por_millon": 10,
            "bloqueo_excedente": True,
        },
    ).json()
    sim = client.post(
        "/api/comercial/simular",
        headers=headers,
        json={"valor_bruto": 50000, "atribucion_pct": 30, "costo_total": 1000, "plan_id": plan["id"], "tokens_usados": 1_200_000},
    ).json()
    assert sim["consumo_ia"]["excedente_tokens"] == 200_000
    assert sim["consumo_ia"]["bloqueado"] is True


def test_09_roi_y_payback(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    sim = client.post(
        "/api/comercial/simular",
        headers=headers,
        json={"valor_bruto": 120000, "atribucion_pct": 50, "costo_total": 10000, "fraccion_valor": 0.25},
    ).json()
    assert sim["roi_pct"] == 300.0
    assert sim["payback_meses"] == 3.0


def test_10_planes_configurables_sin_ia_ilimitada(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    plan = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={
            "code": f"cfg-{uuid.uuid4().hex[:4]}",
            "name": "Plan configurable",
            "consumo_ia_incluido_tokens": 500_000,
            "presupuesto_ia_incluido": 250,
            "limits": {"empleados_ia": 5, "usuarios": 20, "automatizaciones": 10},
        },
    ).json()
    detail = client.get(f"/api/comercial/planes/{plan['id']}", headers=headers).json()
    assert detail["consumo_ia_incluido_tokens"] == 500_000
    assert detail["limits"]["empleados_ia"] == 5
    assert detail.get("consumo_ia_ilimitado") is None


def test_11_importacion_valoracion_1210(client: TestClient):
    db = TestingSessionLocal()
    headers, org = _headers(client, db)
    opp = Opportunity(organization_id=org.id, codigo="OPP-1210", tipo="T", dominio="d", titulo="t", estado="DETECTADA")
    db.add(opp)
    db.commit()
    opp_id = opp.id
    create_valuation(db, organization_id=org.id, opportunity_id=opp_id)
    register_real_value(
        db,
        organization_id=org.id,
        opportunity_id=opp_id,
        materialized_value=Decimal("75000"),
        attribution_level=AttributionLevel.PARCIALMENTE_ATRIBUIBLE,
        attribution_pct=Decimal("60"),
        value_nature=RealValueNature.VERIFICADO,
        justification="Medición línea base 1200",
    )
    db.commit()
    db.close()
    prop = _proposal(client, headers)
    res = client.post(
        f"/api/comercial/propuestas/{prop['id']}/importar-valoracion",
        headers=headers,
        json={"opportunity_id": opp_id},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["valor_atribuible"] == 45000.0
    detail = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers).json()
    imported = [v for v in detail["valores"] if v.get("valuation_id")][0]
    assert imported["naturaleza"] == RealValueNature.VERIFICADO


def test_12_valor_interno_y_externo(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    _add_value(client, headers, prop["id"], categoria=ValueCategory.AHORRO, naturaleza=ValueNature.VERIFICADO)
    _add_value(
        client, headers, prop["id"],
        categoria=ValueCategory.OPORTUNIDAD_CAPTURADA,
        naturaleza=ValueNature.ESTIMADO,
        valor_bruto=120000,
        external_intelligence_ref="mercado-001",
    )
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers).json()
    assert trace["valor_interno_atribuible"] > 0
    assert trace["valor_externo_atribuible"] > 0
    assert "mercado-001" in trace["inteligencia_externa_1240"]


def test_13_atribucion_explicita(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    bad = client.post(
        f"/api/comercial/propuestas/{prop['id']}/valores",
        headers=headers,
        json={"categoria": "AHORRO", "valor_bruto": 50000, "atribucion_pct": 0},
    )
    assert bad.status_code == 422


def test_14_contrato_centro_control_preparado(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    _add_value(client, headers, prop["id"], naturaleza=ValueNature.VERIFICADO, valor_bruto=100000, atribucion_pct=40)
    client.post(f"/api/comercial/propuestas/{prop['id']}/precio-sugerido", headers=headers, json={})
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers).json()
    cc = trace["contrato_centro_control"]
    assert cc["valor_verificado"] == 40000.0
    assert cc["valor_potencial"] == 0.0
    assert cc["semantica_contrato_transversal"]["VERIFICADO"] == "HECHO"
    assert cc["semantica_contrato_transversal"]["POTENCIAL"] == "INFERENCIA"


def test_15_multiempresa_aislamiento(client: TestClient):
    db = TestingSessionLocal()
    _, pass_a, user_a = _create_tenant(db, "Org A")
    _, pass_b, user_b = _create_tenant(db, "Org B")
    db.close()
    headers_a = auth_header(_token(client, user_a, pass_a))
    headers_b = auth_header(_token(client, user_b, pass_b))
    prop = _proposal(client, headers_a)
    _add_value(client, headers_a, prop["id"], naturaleza=ValueNature.VERIFICADO)
    assert client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers_b).status_code == 404
    assert client.post(f"/api/comercial/propuestas/{prop['id']}/precio-sugerido", headers=headers_b, json={}).status_code == 404


def test_16_rbac_viewer_sin_aprobar(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db, role="viewer")
    db.close()
    assert client.post("/api/comercial/propuestas", headers=headers, json={"titulo": "x"}).status_code == 403


def test_17_superadmin_acceso_global(client: TestClient, token: str):
    headers = auth_header(token)
    assert client.get("/api/comercial/propuestas", headers=headers).status_code == 200


def test_18_ciclo_implementacion_trazable(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    _add_value(client, headers, prop["id"], naturaleza=ValueNature.VERIFICADO, valor_bruto=90000, atribucion_pct=50)
    client.post(f"/api/comercial/propuestas/{prop['id']}/precio-sugerido", headers=headers, json={})
    detail = client.get(f"/api/comercial/propuestas/{prop['id']}", headers=headers).json()
    proj = client.post(
        "/api/implementacion/proyectos",
        headers=headers,
        json={"titulo": "Impl cierre", "proposal_id": prop["id"]},
    )
    assert proj.status_code == 201, proj.text
    assert proj.json()["valor_compromiso"]["valor_atribuible_total"] == detail["valor_atribuible_total"]


def test_19_tco_finops_reutilizado(client: TestClient):
    db = TestingSessionLocal()
    headers, org = _headers(client, db)
    finops_service.registrar_consumo(
        db, organization_id=org.id, provider="openai", model_name="gpt-4",
        tokens_in=500, tokens_out=200, cost=Decimal("12.00"), currency="USD",
    )
    db.commit()
    db.close()
    tco = client.post("/api/tco/calcular", headers=headers, json={"incluir_finops": True})
    assert tco.status_code == 200
    assert tco.json()["finops_ia"] == 12.0


def test_20_semantica_contrato_transversal_documentada(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _proposal(client, headers)
    trace = client.get(f"/api/comercial/propuestas/{prop['id']}/trazabilidad", headers=headers).json()
    sem = trace["contrato_centro_control"]["semantica_contrato_transversal"]
    assert sem["ESTIMADO"] == "INFERENCIA"
    assert sem["PROPUESTA_PLAN_ACCION"] == "RECOMENDACION"
    assert "POTENCIAL" in sem["nota"]
