"""BLOQUE 1240 — Inteligencia externa y oportunidades estratégicas."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.external_intelligence_enums import FreshnessStatus, SignalClassification
from app.models import AuditLog, Organization, User
from app.services.external_intelligence_service import compute_freshness, evaluate_relevance
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
    password: str = "Tenant1240*Test1",
) -> tuple[Organization, User, str, str]:
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
        password_hash=__import__("app.security", fromlist=["hash_password"]).hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password, username


def _create_external_source(client: TestClient, headers: dict[str, str], code: str | None = None) -> dict:
    code = code or f"mercado-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/inteligencia-externa/fuentes",
        headers=headers,
        json={
            "code": code,
            "name": f"Fuente {code}",
            "source_type": "MERCADO",
            "ingestion_channel": "CARGA MANUAL",
            "sector": "servicios",
            "pais_region": "Colombia",
            "confiabilidad": 0.7,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _ingest_external(client: TestClient, headers: dict[str, str], source_code: str, **extra) -> dict:
    payload = {
        "source_code": source_code,
        "hecho_observado": "Competidor X lanzó nuevo servicio en el mercado regional",
        "evento": "lanzamiento_competidor",
        "dominio": "competencia",
        "classification": "OPORTUNIDAD",
        "interpretacion": "Posible presión competitiva en nuestro segmento",
        "referencia": f"ref-{uuid.uuid4().hex[:8]}",
        **extra,
    }
    res = client.post("/api/inteligencia-externa/ingesta", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_and_edit_external_source(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Source Org")
    db.close()
    token = _token(client, username, password)
    headers = auth_header(token)
    src = _create_external_source(client, headers)
    patch = client.patch(
        f"/api/inteligencia-externa/fuentes/{src['id']}",
        headers=headers,
        json={"confiabilidad": 0.85, "descripcion": "Fuente de inteligencia de mercado"},
    )
    assert patch.status_code == 200
    assert patch.json()["confiabilidad"] == 0.85


def test_external_ingest_with_evidence_and_freshness(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Ingest")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    now = datetime.now(timezone.utc).isoformat()
    result = _ingest_external(
        client,
        headers,
        src["code"],
        published_at=now,
        hipotesis="Podríamos perder cuota si no respondemos",
    )
    assert result["is_new"] is True
    assert result["external"]["classification"] == "OPORTUNIDAD"
    assert result["external"]["hecho_observado"]
    assert result["external"]["freshness_status"] in (FreshnessStatus.ACTUAL, FreshnessStatus.RECIENTE)


def test_compute_freshness_thresholds():
    now = datetime.now(timezone.utc)
    assert compute_freshness(now - timedelta(days=5), now, recent_days=30, stale_days=180) == FreshnessStatus.ACTUAL
    assert compute_freshness(now - timedelta(days=60), now, recent_days=30, stale_days=180) == FreshnessStatus.RECIENTE
    assert compute_freshness(now - timedelta(days=200), now, recent_days=30, stale_days=180) == FreshnessStatus.DESACTUALIZADA
    assert compute_freshness(None, None) == FreshnessStatus.SIN_FECHA


def test_deduplication_external_ingest(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Dedup")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    idem = f"idem-{uuid.uuid4().hex[:8]}"
    first = _ingest_external(client, headers, src["code"], idempotency_key=idem, referencia="dedup-ref-1")
    second = _ingest_external(client, headers, src["code"], idempotency_key=idem, referencia="dedup-ref-1")
    assert first["signal"]["id"] == second["signal"]["id"]
    assert second.get("deduplicated") is True


def test_classification_and_relevance_patch(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Class")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers, code="competencia-test")
    ingested = _ingest_external(client, headers, src["code"], classification="INFORMACIÓN")
    signal_id = ingested["signal"]["id"]
    cls = client.patch(
        f"/api/inteligencia-externa/senales/{signal_id}/clasificacion",
        headers=headers,
        json={"classification": "RIESGO"},
    )
    assert cls.status_code == 200
    assert cls.json()["classification"] == "RIESGO"
    rel = client.patch(
        f"/api/inteligencia-externa/senales/{signal_id}/relevancia",
        headers=headers,
        json={"relevance": "RELEVANTE"},
    )
    assert rel.status_code == 200


def test_fact_vs_interpretation_separated(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Layers")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    result = _ingest_external(
        client,
        headers,
        src["code"],
        hecho_observado="Norma publicada en gaceta oficial",
        interpretacion="Podría abrir mercado de nuevos servicios",
        hipotesis="Demanda crecerá 10% en 12 meses",
    )
    ext = result["external"]
    assert ext["hecho_observado"] != ext["interpretacion"]
    assert ext["hipotesis"]


def test_register_risk(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Risk")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers, code="regulacion-src")
    ingested = _ingest_external(
        client,
        headers,
        src["code"],
        classification="RIESGO",
        hecho_observado="Nueva regulación restrictiva publicada",
        regulation={"entidad": "Superintendencia", "norma": "Res. 123", "vigencia": "2026-01-01"},
        is_risk=True,
        risk_type="RIESGO REGULATORIO",
    )
    signal_id = ingested["signal"]["id"]
    risk = client.post(
        f"/api/inteligencia-externa/senales/{signal_id}/riesgo",
        headers=headers,
        json={"risk_type": "RIESGO REGULATORIO"},
    )
    assert risk.status_code == 200
    assert risk.json()["is_risk"] is True


def test_competitor_technology_demand_payloads(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Domains")
    db.close()
    headers = auth_header(_token(client, username, password))
    for stype, extra in [
        ("COMPETENCIA", {"competitor": {"nombre": "RivalCo", "movimiento": "nuevo producto"}}),
        ("TECNOLOGÍA", {"technology": {"nombre": "IA generativa", "impacto": "automatización"}}),
        ("CLIENTES", {"demand": {"tendencia": "aumento demanda", "segmento": "pymes"}}),
    ]:
        src = _create_external_source(client, headers, code=f"{stype.lower()}-{uuid.uuid4().hex[:4]}")
        result = _ingest_external(
            client,
            headers,
            src["code"],
            hecho_observado=f"Hallazgo de tipo {stype}",
            **extra,
        )
        assert result["external"]["classification"]


def test_tenant_isolation(client: TestClient):
    db = TestingSessionLocal()
    org_a, user_a, pass_a, user_a_name = _create_tenant_user(db, org_name="Ext Tenant A")
    org_b, user_b, pass_b, user_b_name = _create_tenant_user(db, org_name="Ext Tenant B")
    db.close()
    headers_a = auth_header(_token(client, user_a_name, pass_a))
    headers_b = auth_header(_token(client, user_b_name, pass_b))
    src = _create_external_source(client, headers_a)
    ingested = _ingest_external(client, headers_a, src["code"])
    signal_id = ingested["signal"]["id"]
    denied = client.get(f"/api/inteligencia-externa/senales/{signal_id}", headers=headers_b)
    assert denied.status_code == 404


def test_rbac_viewer_cannot_ingest(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext RBAC", role="viewer")
    db.close()
    headers = auth_header(_token(client, username, password))
    denied = client.post(
        "/api/inteligencia-externa/fuentes",
        headers=headers,
        json={
            "code": "no-auth",
            "name": "No",
            "source_type": "MERCADO",
            "ingestion_channel": "CARGA MANUAL",
        },
    )
    assert denied.status_code == 403


def test_audit_on_source_and_ingest(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Audit")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    _ingest_external(client, headers, src["code"])
    db = TestingSessionLocal()
    try:
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.organization_id == org_id, AuditLog.action.like("inteligencia_externa%"))
            .all()
        )
        actions = {log.action for log in logs}
        assert "inteligencia_externa.fuente.creada" in actions
        assert "inteligencia_externa.senal.incorporada" in actions
    finally:
        db.close()


def test_validate_analysis(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Valid")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    ingested = _ingest_external(client, headers, src["code"])
    signal_id = ingested["signal"]["id"]
    val = client.post(f"/api/inteligencia-externa/senales/{signal_id}/validar", headers=headers)
    assert val.status_code == 200
    assert val.json()["validated_at"]


def test_list_empty_shows_message(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Empty")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/inteligencia-externa/senales", headers=headers)
    assert res.status_code == 200
    assert res.json().get("message") == "Sin información externa disponible"


def test_regression_1120_signals_still_work(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Ext Reg1120")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = client.post(
        "/api/senales/fuentes",
        headers=headers,
        json={"code": f"int-{uuid.uuid4().hex[:6]}", "name": "Interna", "tipo_fuente": "api"},
    )
    assert src.status_code == 201
    list_res = client.get("/api/senales", headers=headers)
    assert list_res.status_code == 200
