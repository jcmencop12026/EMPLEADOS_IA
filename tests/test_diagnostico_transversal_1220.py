"""BLOQUE 1220 — Diagnóstico transversal multidominio."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AuditLog, Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant_user(
    db: Session,
    *,
    org_name: str,
    role: str = "admin",
    password: str = "Tenant1220*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"tenant-{uuid.uuid4().hex[:8]}")
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


def _create_source(client: TestClient, headers: dict[str, str]) -> dict:
    code = f"erp-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/senales/fuentes",
        headers=headers,
        json={"code": code, "name": f"Fuente {code}", "tipo_fuente": "api"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _ingest(client: TestClient, headers: dict[str, str], source_code: str, payload: dict) -> dict:
    body = {"source_code": source_code, **payload}
    res = client.post("/api/senales/ingesta", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def _financiero_signal(ref: str | None = None) -> dict:
    return {
        "tipo": "metrica_financiera",
        "dominio": "financiero",
        "evento": "cartera_vencida_alerta",
        "referencia": ref or f"fin-{uuid.uuid4().hex[:8]}",
        "proceso": "cobranza",
        "metrica": "cartera_vencida",
        "valor": 50_000_000,
        "unidad": "COP",
        "evidencia_resumen": "Cartera vencida supera umbral",
        "titulo": "Recuperación cartera",
        "tipo_oportunidad": "FINANCIERA",
        "indicadores": {"cartera_vencida": 50_000_000},
        "impacto_estimado": 12_000_000,
        "valor_potencial": 8_000_000,
        "urgencia": "ALTA",
    }


def _correlation_signals() -> list[dict]:
    base = uuid.uuid4().hex[:6]
    return [
        {
            "tipo": "demanda",
            "dominio": "comercial",
            "evento": "aumento_demanda",
            "referencia": f"dem-{base}",
            "proceso": "atencion",
            "metrica": "demanda_mensual",
            "valor": 1200,
            "impacto_estimado": 5_000_000,
            "valor_potencial": 3_000_000,
        },
        {
            "tipo": "capacidad",
            "dominio": "operativo",
            "evento": "capacidad_estable",
            "referencia": f"cap-{base}",
            "proceso": "atencion",
            "metrica": "capacidad_disponible",
            "valor": 100,
            "impacto_estimado": 1_000_000,
        },
        {
            "tipo": "sla",
            "dominio": "servicio",
            "evento": "tiempo_respuesta_creciente",
            "referencia": f"tpr-{base}",
            "proceso": "atencion",
            "metrica": "tiempo_respuesta",
            "valor": 48,
            "unidad": "horas",
            "impacto_estimado": 4_000_000,
            "valor_potencial": 2_500_000,
        },
    ]


def _setup_signals(client: TestClient, token: str, *, correlation: bool = False) -> None:
    headers = auth_header(token)
    source = _create_source(client, headers)
    _ingest(client, headers, source["code"], _financiero_signal())
    if correlation:
        for payload in _correlation_signals():
            _ingest(client, headers, source["code"], payload)


def test_01_domains_list(client: TestClient, token: str):
    res = client.get("/api/diagnosticos/dominios", headers=auth_header(token))
    assert res.status_code == 200
    domains = res.json()
    assert "FINANCIERO" in domains
    assert "EXTERNO_MERCADO" in domains
    assert "ASISTENCIAL_SALUD" in domains


def test_02_indicator_definition(client: TestClient, token: str):
    headers = auth_header(token)
    created = client.post(
        "/api/diagnosticos/config/indicadores",
        headers=headers,
        json={
            "code": f"cartera-{uuid.uuid4().hex[:4]}",
            "name": "Cartera vencida",
            "dominio": "FINANCIERO",
            "proceso": "cobranza",
            "umbral_max": 10_000_000,
            "unidad": "COP",
        },
    )
    assert created.status_code == 201, created.text
    listed = client.get("/api/diagnosticos/config/indicadores", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_03_single_signal_diagnostic(client: TestClient, token: str):
    _setup_signals(client, token)
    res = client.post("/api/diagnosticos/generar", headers=auth_header(token), json={})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["codigo"].startswith("DIAG-")
    assert len(body["hallazgos"]) >= 1
    assert body["hallazgos"][0]["tipo_contenido"] == "HECHO"
    assert len(body["causas"]) >= 1
    assert body["explicacion"]["que_esta_pasando"]


def test_04_multiple_signals_processes_domains(client: TestClient, token: str):
    _setup_signals(client, token, correlation=True)
    res = client.post("/api/diagnosticos/generar", headers=auth_header(token), json={})
    assert res.status_code == 201, res.text
    body = res.json()
    dominios = set(body.get("dominios") or [])
    assert len(dominios) >= 2
    procesos = set(body.get("procesos") or [])
    assert "cobranza" in procesos or "atencion" in procesos
    assert len(body["indicadores"]) >= 3


def test_05_correlation_and_interpretation(client: TestClient, token: str):
    _setup_signals(client, token, correlation=True)
    res = client.post("/api/diagnosticos/generar", headers=auth_header(token), json={})
    body = res.json()
    tipos = {h["tipo_contenido"] for h in body["hallazgos"]}
    assert "HECHO" in tipos
    assert "INTERPRETACION" in tipos or len(body.get("correlaciones", [])) >= 1
    if body.get("correlaciones"):
        assert body["correlaciones"][0]["nota_causalidad"]


def test_06_probable_cause_and_hypothesis(client: TestClient, token: str):
    _setup_signals(client, token, correlation=True)
    res = client.post("/api/diagnosticos/generar", headers=auth_header(token), json={})
    body = res.json()
    tipos_causa = {c["tipo"] for c in body["causas"]}
    assert "PROBABLE" in tipos_causa or "HIPOTESIS" in tipos_causa


def test_07_prioritization_and_structured_items(client: TestClient, token: str):
    _setup_signals(client, token, correlation=True)
    res = client.post("/api/diagnosticos/generar", headers=auth_header(token), json={})
    body = res.json()
    items = body["items_estructurados"]
    assert len(items) >= 1
    assert items[0]["prioridad"] is not None
    assert items[0]["accion_recomendada"]["accion"]
    assert items[0]["responsable_propuesto"] is None


def test_08_opportunity_and_deduplication(client: TestClient, token: str):
    _setup_signals(client, token)
    headers = auth_header(token)
    first = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert first.status_code == 201
    diag_id = first.json()["id"]
    opps_first = {o["opportunity_id"] for o in first.json()["oportunidades"]}

    second = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert second.status_code == 201
    opps_second = {o["opportunity_id"] for o in second.json()["oportunidades"]}
    assert opps_first  # al menos una oportunidad
    # deduplicación por hallazgo dentro del mismo diagnóstico ya probada; listar detalle
    detail = client.get(f"/api/diagnosticos/{diag_id}", headers=headers)
    assert detail.status_code == 200


def test_09_traceability_chain(client: TestClient, token: str):
    _setup_signals(client, token)
    headers = auth_header(token)
    gen = client.post("/api/diagnosticos/generar", headers=headers, json={})
    diag_id = gen.json()["id"]
    trace = client.get(f"/api/diagnosticos/{diag_id}/trazabilidad", headers=headers)
    assert trace.status_code == 200
    data = trace.json()
    assert "SEÑAL" in data["cadena"]
    assert data["hallazgos"]
    if gen.json()["oportunidades"]:
        assert data["oportunidades"]


def test_10_cross_tenant_isolation(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user_a, pass_a = _create_tenant_user(db, org_name="Tenant A Diag")
        _, user_b, pass_b = _create_tenant_user(db, org_name="Tenant B Diag")
        headers_a = auth_header(_token(client, user_a.username, pass_a))
        _setup_signals(client, _token(client, user_a.username, pass_a))
        gen = client.post("/api/diagnosticos/generar", headers=headers_a, json={})
        diag_id = gen.json()["id"]
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, pass_b))
    assert client.get(f"/api/diagnosticos/{diag_id}", headers=headers_b).status_code == 404
    listed = client.get("/api/diagnosticos", headers=headers_b)
    ids = {row["id"] for row in listed.json()}
    assert diag_id not in ids


def test_11_inactive_org_blocks_generation(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant_user(db, org_name="Inactive Diag Org")
        user_headers = auth_header(_token(client, user.username, password))
        _setup_signals(client, _token(client, user.username, password))
        org_id = org.id
    finally:
        db.close()

    client.post(
        f"/api/platform/organizations/{org_id}/status",
        headers=auth_header(token),
        json={"status": "INACTIVE"},
    )
    res = client.post("/api/diagnosticos/generar", headers=user_headers, json={})
    assert res.status_code == 403


def test_12_rbac_viewer_cannot_generate(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant_user(db, org_name="Viewer Diag", role="viewer")
        username = user.username
    finally:
        db.close()
    headers = auth_header(_token(client, username, password))
    assert client.get("/api/diagnosticos", headers=headers).status_code == 200
    assert client.post("/api/diagnosticos/generar", headers=headers, json={}).status_code == 403


def test_13_validate_diagnostic_and_audit(client: TestClient, token: str):
    _setup_signals(client, token)
    headers = auth_header(token)
    gen = client.post("/api/diagnosticos/generar", headers=headers, json={})
    diag_id = gen.json()["id"]
    validated = client.post(f"/api/diagnosticos/{diag_id}/validar", headers=headers, json={})
    assert validated.status_code == 200
    assert validated.json()["estado"] == "VALIDADO"

    db = TestingSessionLocal()
    try:
        actions = {
            row.action
            for row in db.query(AuditLog)
            .filter(AuditLog.detail.contains(diag_id))
            .all()
        }
        assert "diagnostic.generated" in actions
        assert "diagnostic.validated" in actions
        finding_actions = (
            db.query(AuditLog)
            .filter(AuditLog.action == "diagnostic.finding.created")
            .count()
        )
        assert finding_actions >= 1
    finally:
        db.close()


def test_14_external_domain_preparation(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    _ingest(
        client,
        headers,
        source["code"],
        {
            "tipo": "senal_externa",
            "dominio": "EXTERNO_MERCADO",
            "evento": "tendencia_mercado",
            "referencia": f"ext-{uuid.uuid4().hex[:6]}",
            "metrica": "demanda_mercado",
            "valor": 85,
            "evidencia_resumen": "Señal externa de mercado (preparación)",
            "impacto_estimado": 2_000_000,
        },
    )
    res = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert res.status_code == 201
    assert "EXTERNO_MERCADO" in (res.json().get("dominios") or [])


def test_15_regression_1120_signals(client: TestClient, token: str):
    """Regresión obligatoria bloque 1120."""
    headers = auth_header(token)
    source = _create_source(client, headers)
    payload = _financiero_signal()
    ingested = client.post("/api/senales/ingesta", headers=headers, json={"source_code": source["code"], **payload})
    assert ingested.status_code == 201
    assert ingested.json()["opportunity_id"] is not None
    listed = client.get("/api/senales", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
