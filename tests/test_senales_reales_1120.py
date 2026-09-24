"""BLOQUE 1120 — Señales reales y detección proactiva."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AuditLog, Organization, User
from app.opportunity_models import ProactiveSignal
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
    password: str = "Tenant1120*Test1",
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


def _create_source(client: TestClient, headers: dict[str, str], code: str | None = None) -> dict:
    code = code or f"erp-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/senales/fuentes",
        headers=headers,
        json={
            "code": code,
            "name": f"Fuente {code}",
            "tipo_fuente": "api",
            "configuracion": {"endpoint": "https://interno.ejemplo/api"},
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _valid_signal_payload(source_code: str, ref: str | None = None) -> dict:
    ref = ref or f"ref-{uuid.uuid4().hex[:8]}"
    return {
        "source_code": source_code,
        "tipo": "metrica_operativa",
        "dominio": "financiero",
        "evento": "cartera_vencida_alerta",
        "referencia": ref,
        "proceso": "cobranza",
        "metrica": "cartera_vencida",
        "valor": 45_000_000,
        "unidad": "COP",
        "dimension": "regional",
        "evidencia_resumen": "Cartera vencida supera umbral interno",
        "metadata": {"api_key": "secreto-no-debe-aparecer", "region": "andina"},
        "titulo": "Recuperación cartera vencida",
        "tipo_oportunidad": "FINANCIERA",
        "indicadores": {"cartera_vencida": 45_000_000, "dias_mora": 90},
        "impacto_estimado": 12_000_000,
        "valor_potencial": 8_000_000,
        "urgencia": "ALTA",
        "regla_analisis": "umbral_cartera_vencida",
    }


def test_01_create_source_and_valid_ingestion(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    payload = _valid_signal_payload(source["code"])
    res = client.post("/api/senales/ingesta", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["is_new"] is True
    assert body["deduplicated"] is False
    assert body["opportunity_id"] is not None
    signal = body["signal"]
    assert signal["modo_ingesta"] == "REAL"
    assert signal["estado_procesamiento"] == "PROCESADA"
    assert signal["metadata"]["api_key"] == "[REDACTED]"


def test_02_invalid_ingestion_missing_fields(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    res = client.post(
        "/api/senales/ingesta",
        headers=headers,
        json={"source_code": source["code"], "tipo": "x"},
    )
    assert res.status_code == 422


def test_03_duplicate_signal_deduplication(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    ref = f"dup-{uuid.uuid4().hex[:8]}"
    payload = _valid_signal_payload(source["code"], ref=ref)
    first = client.post("/api/senales/ingesta", headers=headers, json=payload)
    assert first.status_code == 201
    opp_first = first.json()["opportunity_id"]

    second = client.post("/api/senales/ingesta", headers=headers, json=payload)
    assert second.status_code == 201
    body = second.json()
    assert body["deduplicated"] is True
    assert body["is_new"] is False
    assert body["opportunity_id"] == opp_first


def test_04_idempotency_key_deduplication(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    idem = f"idem-{uuid.uuid4().hex[:8]}"
    payload = _valid_signal_payload(source["code"], ref=f"ref-a-{uuid.uuid4().hex[:4]}")
    payload["idempotency_key"] = idem
    first = client.post("/api/senales/ingesta", headers=headers, json=payload)
    assert first.status_code == 201

    payload2 = _valid_signal_payload(source["code"], ref=f"ref-b-{uuid.uuid4().hex[:4]}")
    payload2["idempotency_key"] = idem
    second = client.post("/api/senales/ingesta", headers=headers, json=payload2)
    assert second.status_code == 201
    assert second.json()["deduplicated"] is True


def test_05_signal_to_opportunity_traceability(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    payload = _valid_signal_payload(source["code"])
    ingested = client.post("/api/senales/ingesta", headers=headers, json=payload)
    assert ingested.status_code == 201
    signal_id = ingested.json()["signal"]["id"]
    opp_id = ingested.json()["opportunity_id"]
    assert opp_id

    trace = client.get(f"/api/senales/{signal_id}/trazabilidad", headers=headers)
    assert trace.status_code == 200, trace.text
    data = trace.json()
    assert data["fuente"]["code"] == source["code"]
    assert data["opportunity_id"] == opp_id
    assert data["signal"]["referencia"] == payload["referencia"]
    etapas = {t["etapa"] for t in data["trazabilidad"]["trazas"]}
    assert "SENAL_CREADA" in etapas
    assert "OPORTUNIDAD_CREADA" in etapas


def test_06_cross_tenant_isolation(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pass_a = _create_tenant_user(db, org_name="Tenant A Señales")
        org_b, user_b, pass_b = _create_tenant_user(db, org_name="Tenant B Señales")
        source_a = _create_source(client, auth_header(_token(client, user_a.username, pass_a)))
        payload = _valid_signal_payload(source_a["code"])
        ingested = client.post(
            "/api/senales/ingesta",
            headers=auth_header(_token(client, user_a.username, pass_a)),
            json=payload,
        )
        assert ingested.status_code == 201
        signal_id = ingested.json()["signal"]["id"]
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, pass_b))
    listed = client.get("/api/senales", headers=headers_b)
    assert listed.status_code == 200
    ids = {row["id"] for row in listed.json()}
    assert signal_id not in ids

    trace = client.get(f"/api/senales/{signal_id}/trazabilidad", headers=headers_b)
    assert trace.status_code == 404


def test_07_inactive_org_blocks_ingestion(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant_user(db, org_name="Inactive Signal Org")
        user_headers = auth_header(_token(client, user.username, password))
        source = _create_source(client, user_headers)
        org_id = org.id
    finally:
        db.close()

    deactivate = client.post(
        f"/api/platform/organizations/{org_id}/status",
        headers=auth_header(token),
        json={"status": "INACTIVE"},
    )
    assert deactivate.status_code == 200

    res = client.post(
        "/api/senales/ingesta",
        headers=user_headers,
        json=_valid_signal_payload(source["code"]),
    )
    assert res.status_code == 403


def test_08_rbac_viewer_cannot_ingest(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant_user(db, org_name="Viewer Señales", role="viewer")
        username = user.username
    finally:
        db.close()
    headers = auth_header(_token(client, username, password))
    listed = client.get("/api/senales/fuentes", headers=headers)
    assert listed.status_code == 200
    ingest = client.post(
        "/api/senales/ingesta",
        headers=headers,
        json={"source_code": "x", "tipo": "t", "dominio": "d", "evento": "e", "referencia": "r"},
    )
    assert ingest.status_code == 403


def test_09_audit_events_on_ingestion(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    ref = f"audit-{uuid.uuid4().hex[:8]}"
    res = client.post(
        "/api/senales/ingesta",
        headers=headers,
        json=_valid_signal_payload(source["code"], ref=ref),
    )
    assert res.status_code == 201
    signal_id = res.json()["signal"]["id"]

    db = TestingSessionLocal()
    try:
        actions = {
            row.action
            for row in db.query(AuditLog)
            .filter(AuditLog.detail.contains(signal_id))
            .all()
        }
        for secret_action in ("signal.received", "signal.processed", "opportunity.detected"):
            assert secret_action in actions
        detail_rows = [
            row.detail
            for row in db.query(AuditLog)
            .filter(AuditLog.action == "signal.received", AuditLog.detail.contains(signal_id))
            .all()
        ]
        assert detail_rows
        assert "secreto-no-debe-aparecer" not in json.dumps(detail_rows)
    finally:
        db.close()


def test_10_synthetic_mode_differentiated(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.services.proactive_service import run_proactive_pipeline

        org, user, _ = _create_tenant_user(db, org_name="Synth Mode Org")
        result = run_proactive_pipeline(
            db,
            organization_id=org.id,
            tipo="proceso_repetitivo",
            dominio="administrativo",
            evento="automatizacion_sintetica",
            payload={
                "synthetic": True,
                "titulo": "Prueba sintética",
                "tipo_oportunidad": "AUTOMATIZACION",
                "indicadores": {"volumen_mensual": 100},
                "impacto_estimado": 1_000_000,
                "valor_potencial": 800_000,
                "source_reference": f"synth-{uuid.uuid4().hex[:6]}",
            },
            origen="proactive_scheduler_sintetico",
            user_id=user.id,
        )
        db.commit()
        signal = db.query(ProactiveSignal).filter(ProactiveSignal.id == result["signal_id"]).first()
        assert signal is not None
        assert signal.modo_ingesta == "SINTETICO"
        assert signal.origen == "proactive_scheduler_sintetico"
    finally:
        db.close()


def test_11_list_signals_and_sources(client: TestClient, token: str):
    headers = auth_header(token)
    source = _create_source(client, headers)
    client.post(
        "/api/senales/ingesta",
        headers=headers,
        json=_valid_signal_payload(source["code"]),
    )
    sources = client.get("/api/senales/fuentes", headers=headers)
    assert sources.status_code == 200
    assert any(s["code"] == source["code"] for s in sources.json())

    signals = client.get("/api/senales?modo=REAL", headers=headers)
    assert signals.status_code == 200
    assert len(signals.json()) >= 1
    assert all(s["modo_ingesta"] == "REAL" for s in signals.json())
