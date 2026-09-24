"""BLOQUE 1250B — Convergencia inteligencia externa + diagnóstico transversal."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
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
    password: str = "Tenant1250B*Test1",
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


def _create_internal_source(client: TestClient, headers: dict[str, str]) -> dict:
    code = f"erp-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/senales/fuentes",
        headers=headers,
        json={"code": code, "name": f"Fuente {code}", "tipo_fuente": "api"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _ingest_internal(client: TestClient, headers: dict[str, str], source_code: str) -> dict:
    payload = {
        "tipo": "metrica_financiera",
        "dominio": "financiero",
        "evento": "cartera_vencida_alerta",
        "referencia": f"int-{uuid.uuid4().hex[:8]}",
        "proceso": "cobranza",
        "metrica": "cartera_vencida",
        "valor": 50_000_000,
        "unidad": "COP",
        "evidencia_resumen": "Cartera vencida supera umbral",
        "titulo": "Recuperación cartera",
        "tipo_oportunidad": "FINANCIERA",
        "impacto_estimado": 12_000_000,
        "valor_potencial": 8_000_000,
    }
    res = client.post("/api/senales/ingesta", headers=headers, json={"source_code": source_code, **payload})
    assert res.status_code == 201, res.text
    return res.json()


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
            "confiabilidad": 0.75,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _ingest_external(
    client: TestClient,
    headers: dict[str, str],
    source_code: str,
    **extra,
) -> dict:
    payload = {
        "source_code": source_code,
        "hecho_observado": extra.pop("hecho_observado", "Competidor lanzó producto en mercado regional"),
        "evento": extra.pop("evento", "lanzamiento_competidor"),
        "dominio": extra.pop("dominio", "competencia"),
        "classification": extra.pop("classification", "OPORTUNIDAD"),
        "interpretacion": extra.pop("interpretacion", "Posible presión competitiva"),
        "referencia": extra.pop("referencia", f"ref-{uuid.uuid4().hex[:8]}"),
        "relevance": extra.pop("relevance", "RELEVANTE"),
        **extra,
    }
    res = client.post("/api/inteligencia-externa/ingesta", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_external_source_to_signal(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Ext Signal")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    result = _ingest_external(client, headers, src["code"])
    assert result["signal"]["id"]
    assert result["external"]["hecho_observado"]
    assert result["external_source"]["code"] == src["code"]


def test_external_signal_to_finding(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Ext Finding")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    _ingest_external(client, headers, src["code"])
    diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert diag.status_code == 201, diag.text
    hallazgos = diag.json()["hallazgos"]
    externos = [h for h in hallazgos if (h.get("evidencia") or {}).get("ambito") == "EXTERNO"]
    assert len(externos) >= 1
    assert any(h["tipo_contenido"] == "HECHO" for h in externos)


def test_external_finding_in_diagnostic(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Ext Diag")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    _ingest_external(
        client,
        headers,
        src["code"],
        interpretacion="Interpretación externa no promovida a hecho",
        hipotesis="Hipótesis de mercado pendiente de validación",
    )
    diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
    body = diag.json()
    tipos = {h["tipo_contenido"] for h in body["hallazgos"]}
    assert "HECHO" in tipos
    assert "INTERPRETACION" in tipos
    tipos_causa = {c["tipo"] for c in body["causas"]}
    assert "HIPOTESIS" in tipos_causa


def test_mixed_internal_external_diagnostic(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Mixed")
    db.close()
    headers = auth_header(_token(client, username, password))
    int_src = _create_internal_source(client, headers)
    _ingest_internal(client, headers, int_src["code"])
    ext_src = _create_external_source(client, headers)
    _ingest_external(client, headers, ext_src["code"])
    diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert diag.status_code == 201
    body = diag.json()
    ambitos = {(h.get("evidencia") or {}).get("ambito") for h in body["hallazgos"]}
    assert None in ambitos or any(a is None for a in ambitos)
    assert "EXTERNO" in ambitos
    assert len(body["hallazgos"]) >= 2


def test_external_signal_to_opportunity(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Ext Opp")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    ingested = _ingest_external(client, headers, src["code"], classification="OPORTUNIDAD")
    signal_id = ingested["signal"]["id"]
    opp = client.post(f"/api/inteligencia-externa/senales/{signal_id}/oportunidad", headers=headers)
    assert opp.status_code in (200, 201)
    opp_id = opp.json().get("id") or opp.json().get("opportunity_id")
    assert opp_id
    dup = client.post(f"/api/inteligencia-externa/senales/{signal_id}/oportunidad", headers=headers)
    assert dup.status_code in (200, 201)
    dup_id = dup.json().get("id") or dup.json().get("opportunity_id")
    assert dup_id == opp_id


def test_external_risk_not_auto_opportunity(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Risk")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers, code="riesgo-ext")
    ingested = _ingest_external(
        client,
        headers,
        src["code"],
        classification="RIESGO",
        is_risk=True,
        hecho_observado="Regulación restrictiva publicada",
        interpretacion=None,
    )
    signal_id = ingested["signal"]["id"]
    denied = client.post(f"/api/inteligencia-externa/senales/{signal_id}/oportunidad", headers=headers)
    assert denied.status_code == 422
    diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert diag.status_code == 201
    riesgo_hallazgos = [
        h for h in diag.json()["hallazgos"]
        if (h.get("evidencia") or {}).get("is_risk")
    ]
    assert len(riesgo_hallazgos) >= 1
    assert not diag.json()["oportunidades"]


def test_deduplication_external_and_diagnostic(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Dedup")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    idem = f"idem-{uuid.uuid4().hex[:8]}"
    first = _ingest_external(client, headers, src["code"], idempotency_key=idem, referencia="dedup-1250b")
    second = _ingest_external(client, headers, src["code"], idempotency_key=idem, referencia="dedup-1250b")
    assert first["signal"]["id"] == second["signal"]["id"]
    diag1 = client.post("/api/diagnosticos/generar", headers=headers, json={})
    diag2 = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert diag1.status_code == 201 and diag2.status_code == 201


def test_freshness_in_external_trace(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B Fresh")
    db.close()
    headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, headers)
    now = datetime.now(timezone.utc).isoformat()
    _ingest_external(client, headers, src["code"], published_at=now)
    diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
    trace = client.get(f"/api/diagnosticos/{diag.json()['id']}/trazabilidad", headers=headers)
    assert trace.status_code == 200
    data = trace.json()
    assert data.get("cadenas_externas")
    assert data["cadenas_externas"][0].get("freshness_status")


def test_cross_tenant_convergence(client: TestClient):
    db = TestingSessionLocal()
    _, _, pass_a, user_a = _create_tenant_user(db, org_name="1250B Tenant A")
    _, _, pass_b, user_b = _create_tenant_user(db, org_name="1250B Tenant B")
    db.close()
    headers_a = auth_header(_token(client, user_a, pass_a))
    headers_b = auth_header(_token(client, user_b, pass_b))
    src = _create_external_source(client, headers_a)
    ingested = _ingest_external(client, headers_a, src["code"])
    diag = client.post("/api/diagnosticos/generar", headers=headers_a, json={})
    diag_id = diag.json()["id"]
    assert client.get(f"/api/diagnosticos/{diag_id}", headers=headers_b).status_code == 404
    assert client.get(f"/api/inteligencia-externa/senales/{ingested['signal']['id']}", headers=headers_b).status_code == 404


def test_rbac_convergence(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant_user(db, org_name="1250B RBAC", role="viewer")
    db.close()
    headers = auth_header(_token(client, username, password))
    assert client.get("/api/diagnosticos", headers=headers).status_code == 200
    assert client.get("/api/inteligencia-externa/senales", headers=headers).status_code == 200
    assert client.post("/api/diagnosticos/generar", headers=headers, json={}).status_code == 403
    assert client.post("/api/inteligencia-externa/ingesta", headers=headers, json={}).status_code in (403, 422)


def test_inactive_org_blocks_external_ingest(client: TestClient, token: str):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="1250B Inactive")
    org_id = org.id
    db.close()
    user_headers = auth_header(_token(client, username, password))
    src = _create_external_source(client, user_headers)
    client.post(
        f"/api/platform/organizations/{org_id}/status",
        headers=auth_header(token),
        json={"status": "INACTIVE"},
    )
    denied = client.post(
        "/api/inteligencia-externa/ingesta",
        headers=user_headers,
        json={
            "source_code": src["code"],
            "hecho_observado": "No debe procesarse",
            "referencia": f"inactive-{uuid.uuid4().hex[:6]}",
        },
    )
    assert denied.status_code == 403
