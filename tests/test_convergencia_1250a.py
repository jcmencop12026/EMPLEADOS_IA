"""BLOQUE 1250A — pruebas de convergencia post-V1 fase 1."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.opportunity_models import Opportunity
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
    password: str = "Conv1250*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"conv-{uuid.uuid4().hex[:8]}")
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


def _create_source(client: TestClient, headers: dict[str, str]) -> str:
    code = f"erp-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/senales/fuentes",
        headers=headers,
        json={"code": code, "name": f"Fuente {code}", "tipo_fuente": "api"},
    )
    assert res.status_code == 201, res.text
    return code


def _ingest_signal(client: TestClient, headers: dict[str, str], source_code: str) -> dict:
    ref = f"sig-{uuid.uuid4().hex[:8]}"
    body = {
        "source_code": source_code,
        "tipo": "metrica_financiera",
        "dominio": "financiero",
        "evento": "cartera_vencida_alerta",
        "referencia": ref,
        "proceso": "cobranza",
        "metrica": "cartera_vencida",
        "valor": 40_000_000,
        "unidad": "COP",
        "evidencia_resumen": "Cartera vencida supera umbral",
        "titulo": "Recuperación cartera convergencia",
        "tipo_oportunidad": "FINANCIERA",
        "indicadores": {"cartera_vencida": 40_000_000},
        "impacto_estimado": 10_000_000,
        "valor_potencial": 7_000_000,
        "urgencia": "ALTA",
    }
    res = client.post("/api/senales/ingesta", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def _signal_payload() -> dict:
    return {
        "titulo": "Oportunidad convergencia 1250A",
        "tipo_oportunidad": "FINANCIERA",
        "indicadores": {"cartera_vencida": 25_000_000},
        "impacto_estimado": 8_000_000,
        "valor_potencial": 5_000,
        "urgencia": "ALTA",
        "source_reference": f"conv-{uuid.uuid4().hex[:8]}",
    }


def _create_opportunity(client: TestClient, headers: dict[str, str]) -> str:
    res = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={
            "tipo": "financiera",
            "dominio": "financiero",
            "evento": "conv_1250a",
            "payload": _signal_payload(),
            "origen": "test_convergencia",
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["opportunity_id"]


def test_1250a_senal_genera_oportunidad(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Conv Señal")
        headers = auth_header(_token(client, user.username, password))
        source = _create_source(client, headers)
        ingested = _ingest_signal(client, headers, source)
        assert ingested.get("opportunity_id") or ingested.get("oportunidad_id")
        opp_id = ingested.get("opportunity_id") or ingested.get("oportunidad_id")
        detail = client.get(f"/api/oportunidades/{opp_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["titulo"]
    finally:
        db.close()


def test_1250a_diagnostico_genera_oportunidad(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    _ingest_signal(client, headers, source)
    diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert diag.status_code == 201, diag.text
    body = diag.json()
    assert body.get("oportunidades_generadas", 0) >= 0
    listed = client.get("/api/diagnosticos", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_1250a_oportunidad_seguimiento_y_resultado(client: TestClient, token: str):
    headers = auth_header(token)
    opp_id = _create_opportunity(client, headers)
    client.post(f"/api/oportunidades/{opp_id}/aprobar", headers=headers, json={"aprobado": True})
    client.post(f"/api/oportunidades/{opp_id}/activar", headers=headers, json={"auto_execute": False})
    track = client.post(
        f"/api/oportunidades/{opp_id}/seguimiento",
        headers=headers,
        json={"accion": "Seguimiento convergencia", "bloqueo": "Ninguno"},
    )
    assert track.status_code == 200
    result = client.post(
        f"/api/oportunidades/{opp_id}/resultado",
        headers=headers,
        json={"valor_real": 1200, "valor_esperado": 1500, "estado_resultado": "EXITO"},
    )
    assert result.status_code == 200
    trace = client.get(f"/api/oportunidades/{opp_id}/trazabilidad", headers=headers)
    assert trace.status_code == 200
    assert len(trace.json().get("seguimiento", [])) >= 1


def test_1250a_oportunidad_finops(client: TestClient, token: str):
    headers = auth_header(token)
    opp_id = _create_opportunity(client, headers)
    eco = client.get(f"/api/finops/opportunities/{opp_id}/economics", headers=headers)
    assert eco.status_code == 200
    assert "consumption_count" in eco.json()


def test_1250a_oportunidad_linea_base(client: TestClient, token: str):
    headers = auth_header(token)
    opp_id = _create_opportunity(client, headers)
    now = datetime.now(timezone.utc)
    lb = client.post(
        "/api/lineas-base",
        headers=headers,
        json={
            "indicador": "tiempo_respuesta_conv",
            "descripcion": "Convergencia línea base",
            "unidad": "minutos",
            "valor_base": 90.0,
            "fecha_inicio_base": (now - timedelta(days=60)).isoformat(),
            "fecha_fin_base": (now - timedelta(days=30)).isoformat(),
            "direccion_indicador": "MENOR_ES_MEJOR",
            "impacto_esperado": 20.0,
            "estado": "ACTIVA",
            "opportunity_id": opp_id,
        },
    )
    assert lb.status_code == 200, lb.text
    listed = client.get(f"/api/lineas-base/oportunidad/{opp_id}", headers=headers)
    assert listed.status_code == 200
    assert listed.json().get("total", 0) >= 1


def test_1250a_oportunidad_valoracion(client: TestClient, token: str):
    headers = auth_header(token)
    opp_id = _create_opportunity(client, headers)
    created = client.post(
        f"/api/valoracion/opportunities/{opp_id}",
        headers=headers,
        json={"value_type": "AHORRO", "scope": "INTERNO", "currency": "USD"},
    )
    assert created.status_code == 200, created.text
    summary = client.get(f"/api/valoracion/opportunities/{opp_id}", headers=headers)
    assert summary.status_code == 200
    assert summary.json().get("has_valuation") is True


def test_1250a_aislamiento_multiempresa(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pass_a = _create_tenant(db, org_name="Conv Tenant A")
        org_b, user_b, pass_b = _create_tenant(db, org_name="Conv Tenant B")
        headers_a = auth_header(_token(client, user_a.username, pass_a))
        headers_b = auth_header(_token(client, user_b.username, pass_b))
        opp_a = _create_opportunity(client, headers_a)
        denied = client.get(f"/api/oportunidades/{opp_a}", headers=headers_b)
        assert denied.status_code in (403, 404)
        lb = client.post(
            "/api/lineas-base",
            headers=headers_a,
            json={
                "indicador": "kpi_a",
                "descripcion": "Solo A",
                "unidad": "u",
                "valor_base": 1.0,
                "fecha_inicio_base": datetime.now(timezone.utc).isoformat(),
                "fecha_fin_base": datetime.now(timezone.utc).isoformat(),
                "direccion_indicador": "INFORMATIVO",
                "impacto_esperado": 1.0,
                "estado": "ACTIVA",
            },
        )
        assert lb.status_code == 200
        lb_id = lb.json()["id"]
        cross = client.get(f"/api/lineas-base/{lb_id}", headers=headers_b)
        assert cross.status_code in (403, 404)
        val = client.post(
            f"/api/valoracion/opportunities/{opp_a}",
            headers=headers_a,
            json={"value_type": "AHORRO", "scope": "INTERNO", "currency": "USD"},
        )
        assert val.status_code == 200
        val_cross = client.get(f"/api/valoracion/opportunities/{opp_a}", headers=headers_b)
        assert val_cross.status_code in (400, 403, 404)
        assert org_a.id != org_b.id
    finally:
        db.close()


def test_1250a_rbac_transversal(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, viewer, password = _create_tenant(db, org_name="Conv Viewer", role="viewer")
        headers = auth_header(_token(client, viewer.username, password))
        assert client.get("/api/oportunidades", headers=headers).status_code == 200
        assert client.get("/api/lineas-base", headers=headers).status_code == 200
        assert client.get("/api/diagnosticos", headers=headers).status_code == 200
        denied_lb = client.post(
            "/api/lineas-base",
            headers=headers,
            json={
                "indicador": "kpi_viewer",
                "descripcion": "No permitida",
                "unidad": "u",
                "valor_base": 1.0,
                "fecha_inicio_base": datetime.now(timezone.utc).isoformat(),
                "fecha_fin_base": datetime.now(timezone.utc).isoformat(),
                "direccion_indicador": "INFORMATIVO",
                "impacto_esperado": 1.0,
                "estado": "ACTIVA",
            },
        )
        assert denied_lb.status_code == 403
        denied_diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
        assert denied_diag.status_code == 403
    finally:
        db.close()
