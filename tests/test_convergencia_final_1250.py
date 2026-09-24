"""BLOQUE 1250 — Convergencia final post-V1 (1250A + 1250B + 1250C)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(
    db: Session,
    *,
    org_name: str,
    role: str = "admin",
    password: str = "Conv1250Final*1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"final-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    username = f"user-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password


def _internal_signal(client: TestClient, headers: dict[str, str]) -> dict:
    code = f"erp-{uuid.uuid4().hex[:6]}"
    src = client.post(
        "/api/senales/fuentes",
        headers=headers,
        json={"code": code, "name": f"Fuente {code}", "tipo_fuente": "api"},
    )
    assert src.status_code == 201, src.text
    body = {
        "source_code": code,
        "tipo": "metrica_financiera",
        "dominio": "financiero",
        "evento": "cartera_vencida_alerta",
        "referencia": f"sig-{uuid.uuid4().hex[:8]}",
        "proceso": "cobranza",
        "metrica": "cartera_vencida",
        "valor": 30_000_000,
        "unidad": "COP",
        "evidencia_resumen": "Alerta convergencia final",
        "titulo": "Oportunidad cadena final",
        "tipo_oportunidad": "FINANCIERA",
        "impacto_estimado": 9_000_000,
        "valor_potencial": 6_000_000,
    }
    res = client.post("/api/senales/ingesta", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def _external_signal(client: TestClient, headers: dict[str, str]) -> dict:
    code = f"mercado-{uuid.uuid4().hex[:6]}"
    src = client.post(
        "/api/inteligencia-externa/fuentes",
        headers=headers,
        json={
            "code": code,
            "name": f"Fuente {code}",
            "source_type": "MERCADO",
            "ingestion_channel": "CARGA MANUAL",
            "sector": "servicios",
            "pais_region": "Colombia",
            "confiabilidad": 0.8,
        },
    )
    assert src.status_code == 201, src.text
    res = client.post(
        "/api/inteligencia-externa/ingesta",
        headers=headers,
        json={
            "source_code": code,
            "hecho_observado": "Demanda regional en alza",
            "evento": "demanda_cliente",
            "dominio": "cliente",
            "classification": "OPORTUNIDAD",
            "interpretacion": "Oportunidad comercial detectada",
            "referencia": f"ext-{uuid.uuid4().hex[:8]}",
            "relevance": "RELEVANTE",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_opportunity(client: TestClient, headers: dict[str, str]) -> str:
    res = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={
            "tipo": "financiera",
            "dominio": "financiero",
            "evento": "conv_final",
            "payload": {
                "titulo": "Oportunidad convergencia final",
                "tipo_oportunidad": "FINANCIERA",
                "indicadores": {"kpi": 1},
                "impacto_estimado": 5000,
                "valor_potencial": 3000,
                "urgencia": "ALTA",
                "source_reference": f"ref-{uuid.uuid4().hex[:8]}",
            },
            "origen": "test_convergencia_final",
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["opportunity_id"]


def test_final_internal_signal_to_diagnostic_to_opportunity(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Final Interna")
        headers = auth_header(_token(client, user.username, password))
        ingested = _internal_signal(client, headers)
        opp_id = ingested.get("opportunity_id") or ingested.get("oportunidad_id")
        assert opp_id
        diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
        assert diag.status_code == 201, diag.text
        assert client.get(f"/api/oportunidades/{opp_id}", headers=headers).status_code == 200
    finally:
        db.close()


def test_final_external_signal_to_diagnostic_to_opportunity(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Final Externa")
        headers = auth_header(_token(client, user.username, password))
        ingested = _external_signal(client, headers)
        signal_id = ingested["signal"]["id"]
        opp = client.post(f"/api/inteligencia-externa/senales/{signal_id}/oportunidad", headers=headers)
        assert opp.status_code in (200, 201)
        diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
        assert diag.status_code == 201
        externos = [
            h for h in diag.json()["hallazgos"]
            if (h.get("evidencia") or {}).get("ambito") == "EXTERNO"
        ]
        assert len(externos) >= 1
    finally:
        db.close()


def test_final_opportunity_execution_result_impact_valuation(client: TestClient, token: str):
    headers = auth_header(token)
    opp_id = _create_opportunity(client, headers)
    client.post(f"/api/oportunidades/{opp_id}/aprobar", headers=headers, json={"aprobado": True})
    client.post(f"/api/oportunidades/{opp_id}/activar", headers=headers, json={"auto_execute": False})
    client.post(
        f"/api/oportunidades/{opp_id}/resultado",
        headers=headers,
        json={"valor_real": 2500, "valor_esperado": 3000, "estado_resultado": "EXITO"},
    )
    now = datetime.now(timezone.utc)
    lb = client.post(
        "/api/lineas-base",
        headers=headers,
        json={
            "indicador": "kpi_final",
            "descripcion": "Impacto convergencia",
            "unidad": "u",
            "valor_base": 100.0,
            "fecha_inicio_base": (now - timedelta(days=30)).isoformat(),
            "fecha_fin_base": now.isoformat(),
            "direccion_indicador": "MAYOR_ES_MEJOR",
            "impacto_esperado": 15.0,
            "estado": "ACTIVA",
            "opportunity_id": opp_id,
        },
    )
    assert lb.status_code == 200, lb.text
    val = client.post(
        f"/api/valoracion/opportunities/{opp_id}",
        headers=headers,
        json={"value_type": "AHORRO", "scope": "INTERNO", "currency": "USD"},
    )
    assert val.status_code == 200, val.text
    summary = client.get(f"/api/valoracion/opportunities/{opp_id}", headers=headers)
    assert summary.status_code == 200
    assert summary.json().get("has_valuation") is True


def test_final_valuation_finops_diagnostic_in_control_center(client: TestClient, token: str):
    headers = auth_header(token)
    opp_id = _create_opportunity(client, headers)
    client.post(
        f"/api/valoracion/opportunities/{opp_id}",
        headers=headers,
        json={"value_type": "AHORRO", "scope": "INTERNO", "currency": "USD"},
    )
    _internal_signal(client, headers)
    client.post("/api/diagnosticos/generar", headers=headers, json={})
    cc = client.get("/api/centro-control/resumen-ejecutivo", headers=headers)
    assert cc.status_code == 200, cc.text
    body = cc.json()
    assert body["oportunidades"]["disponible"] is True
    assert body["finops"]["disponible"] is True
    assert body["finops_extendido"] is not None
    assert "cadena_ejecutiva" in body
    diag = body["diagnostico"]
    assert diag is not None
    if not diag.get("disponible"):
        assert diag["estado"] == "Sin información disponible"
    vr = body["valor_retorno"]
    if not vr.get("disponible"):
        assert vr["estado"] == "Sin información disponible"
        assert vr.get("valor_esperado") is None


def test_final_cross_tenant_control_center(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user_a, pass_a = _create_tenant(db, org_name="Final Tenant A")
        _, user_b, pass_b = _create_tenant(db, org_name="Final Tenant B")
        headers_a = auth_header(_token(client, user_a.username, pass_a))
        headers_b = auth_header(_token(client, user_b.username, pass_b))
        opp_a = _create_opportunity(client, headers_a)
        cc_b = client.get("/api/centro-control/resumen-ejecutivo", headers=headers_b)
        assert cc_b.status_code == 200
        assert client.get(f"/api/oportunidades/{opp_a}", headers=headers_b).status_code in (403, 404)
        assert cc_b.json()["organization_id"] != client.get(
            "/api/centro-control/resumen-ejecutivo", headers=headers_a
        ).json()["organization_id"]
    finally:
        db.close()


def test_final_rbac_control_center_viewer(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, viewer, password = _create_tenant(db, org_name="Final Viewer", role="viewer")
        headers = auth_header(_token(client, viewer.username, password))
        assert client.get("/api/centro-control/resumen-ejecutivo", headers=headers).status_code == 200
        denied = client.post("/api/diagnosticos/generar", headers=headers, json={})
        assert denied.status_code == 403
    finally:
        db.close()
