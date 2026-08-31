"""Cableado real 1330 ↔ 1350 ↔ 1360 sobre Fase 1."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.continuidad_models import ContinuidadAlerta, ContinuidadServicioCritico
from app.governance_models import GovAccessLog, GovCatalogEntry, GovLineageEvent
from app.integration_enums import ConnectorType
from app.models import Organization, User
from app.security import hash_password
from app.services import integration_wiring as wiring
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _tenant(client: TestClient, name: str, role: str = "admin") -> tuple[str, str, str]:
    db = TestingSessionLocal()
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=name, slug=f"w-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "Wiring1330*Test1"
    username = f"u-{uuid.uuid4().hex[:6]}"
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
    org_id = org.id
    db.close()
    return org_id, username, password


def _gov_catalog(client: TestClient, headers: dict, name: str = "Cat wiring", classification_code: str | None = None) -> str:
    payload: dict = {"name": name, "functional_owner": "Ops", "data_environment": "PRODUCCION"}
    if classification_code:
        cls = client.get("/api/gobierno-datos/clasificaciones", headers=headers).json()
        level = next(c for c in cls if c["code"] == classification_code)
        payload["classification_level_id"] = level["id"]
    res = client.post(
        "/api/gobierno-datos/catalogo",
        headers=headers,
        json=payload,
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _deny_provider_policy(client: TestClient, headers: dict, classification_code: str = "RESTRINGIDO") -> None:
    cls = client.get("/api/gobierno-datos/clasificaciones", headers=headers).json()
    level = next(c for c in cls if c["code"] == classification_code)
    res = client.post(
        "/api/gobierno-datos/politicas-proveedor",
        headers=headers,
        json={"classification_level_id": level["id"], "decision": "PROHIBIDO"},
    )
    assert res.status_code == 201, res.text


def _connector(client: TestClient, headers: dict, **extra) -> dict:
    code = extra.pop("code", f"c-{uuid.uuid4().hex[:4]}")
    payload = {
        "code": code,
        "name": f"Conector {code}",
        "connector_type": ConnectorType.API_REST,
        "config": {"mock_response": [{"tipo": "test", "dominio": "ops", "evento": "evt", "referencia": "r1", "email": "user@example.com"}]},
        **extra,
    }
    res = client.post("/api/integraciones/conectores", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_wiring01_catalog_same_org(client: TestClient):
    org_id, username, password = _tenant(client, "Wiring01 OK")
    headers = auth_header(_token(client, username, password))
    cat_id = _gov_catalog(client, headers)
    conn = _connector(client, headers, gov_catalog_entry_id=cat_id)
    assert conn["gov_catalog_entry_id"] == cat_id


def test_p1_01_catalog_cross_org_blocked(client: TestClient):
    _, ua, pa = _tenant(client, "Wiring01 A")
    _, ub, pb = _tenant(client, "Wiring01 B")
    ha = auth_header(_token(client, ua, pa))
    hb = auth_header(_token(client, ub, pb))
    cat_b = _gov_catalog(client, hb, "Cat B only")
    res = client.post(
        "/api/integraciones/conectores",
        headers=ha,
        json={
            "code": f"x-{uuid.uuid4().hex[:4]}",
            "name": "Cross",
            "connector_type": ConnectorType.API_REST,
            "gov_catalog_entry_id": cat_b,
        },
    )
    assert res.status_code == 422


def test_wiring02_policy_denied_no_execution(client: TestClient):
    org_id, username, password = _tenant(client, "Wiring02 Deny")
    headers = auth_header(_token(client, username, password))
    _deny_provider_policy(client, headers, "RESTRINGIDO")
    cat_id = _gov_catalog(client, headers, classification_code="RESTRINGIDO")
    conn = _connector(client, headers, gov_catalog_entry_id=cat_id)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    exec_res = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    assert exec_res.status_code == 422
    db = TestingSessionLocal()
    logs = db.query(GovAccessLog).filter(GovAccessLog.organization_id == org_id).all()
    db.close()
    assert any(l.result == "DENEGADO" for l in logs)


def test_wiring04_masking_on_transform(client: TestClient):
    org_id, username, password = _tenant(client, "Wiring04 Mask")
    headers = auth_header(_token(client, username, password))
    cls = client.get("/api/gobierno-datos/clasificaciones", headers=headers).json()
    conf = next(c for c in cls if c["code"] == "CONFIDENCIAL")
    client.post(
        "/api/gobierno-datos/politicas-proveedor",
        headers=headers,
        json={
            "classification_level_id": conf["id"],
            "decision": "PERMITIDO_CON_RESTRICCIONES",
            "minimization_action": "email",
        },
    )
    cat_id = _gov_catalog(client, headers, classification_code="CONFIDENCIAL")
    conn = _connector(client, headers, gov_catalog_entry_id=cat_id)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    exec_res = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    assert exec_res.status_code == 200, exec_res.text
    assert "correlation_id" in exec_res.json()


def test_wiring05_lineage_and_access(client: TestClient):
    org_id, username, password = _tenant(client, "Wiring05 Lineage")
    headers = auth_header(_token(client, username, password))
    cat_id = _gov_catalog(client, headers)
    conn = _connector(client, headers, gov_catalog_entry_id=cat_id)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    db = TestingSessionLocal()
    access = db.query(GovAccessLog).filter(
        GovAccessLog.organization_id == org_id,
        GovAccessLog.catalog_entry_id == cat_id,
    ).count()
    lineage = db.query(GovLineageEvent).filter(
        GovLineageEvent.organization_id == org_id,
        GovLineageEvent.catalog_entry_id == cat_id,
    ).count()
    db.close()
    assert access >= 1
    assert lineage >= 1


def test_wiring09_continuidad_proveedor_ref(client: TestClient):
    org_id, username, password = _tenant(client, "Wiring09 Cont")
    headers = auth_header(_token(client, username, password))
    conn = _connector(client, headers)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    db = TestingSessionLocal()
    ref = wiring.proveedor_ref_for_connector(conn["id"])
    svc = db.query(ContinuidadServicioCritico).filter(
        ContinuidadServicioCritico.organization_id == org_id,
        ContinuidadServicioCritico.proveedor_ref == ref,
    ).first()
    db.close()
    assert svc is not None


def test_wiring10_recovery_event(client: TestClient):
    org_id, username, password = _tenant(client, "Wiring10 Rec")
    headers = auth_header(_token(client, username, password))
    conn = _connector(client, headers, config={"mock_response": [{"tipo": "t"}], "simulate_failure": True, "failure_category": "CONEXION"})
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    for _ in range(6):
        client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    conn2 = _connector(client, headers, code=f"ok-{uuid.uuid4().hex[:4]}", config={"mock_response": [{"tipo": "t", "dominio": "ops", "evento": "e", "referencia": "r"}]})
    client.put(f"/api/integraciones/conectores/{conn2['id']}", headers=headers, json={"status": "ACTIVO"})
    client.post(f"/api/integraciones/conectores/{conn2['id']}/ejecutar", headers=headers, json={})


def test_wiring12_restore_blocked_privacy(client: TestClient):
    org_id, username, password = _tenant(client, "Wiring12 Restore")
    headers = auth_header(_token(client, username, password))
    cat_id = _gov_catalog(client, headers)
    client.post(
        "/api/gobierno-datos/legal-hold",
        headers=headers,
        json={"reason": "Litigio", "catalog_entry_id": cat_id},
    )
    pol = client.post(
        "/api/continuidad/backups/politicas",
        headers=headers,
        json={"recurso": "db-test", "frecuencia": "DIARIA"},
    )
    assert pol.status_code == 201
    pol_id = pol.json()["id"]
    ej = client.post(
        "/api/continuidad/backups/ejecuciones",
        headers=headers,
        json={
            "politica_id": pol_id,
            "inicio": "2026-01-01T00:00:00Z",
            "resultado": "EXITOSO",
            "catalog_entry_id": cat_id,
        },
    )
    assert ej.status_code == 201
    ej_id = ej.json()["id"]
    restore = client.post(
        "/api/continuidad/backups/restores",
        headers=headers,
        json={
            "ejecucion_id": ej_id,
            "tipo": "SIMULADA",
            "entorno_destino": "LAB",
            "fecha": "2026-01-02T00:00:00Z",
            "catalog_entry_id": cat_id,
        },
    )
    assert restore.status_code == 400
    db = TestingSessionLocal()
    alerts = db.query(ContinuidadAlerta).filter(
        ContinuidadAlerta.organization_id == org_id,
        ContinuidadAlerta.tipo == wiring.EVENT_RESTORE_BLOQUEADO_PRIVACIDAD,
    ).count()
    db.close()
    assert alerts >= 1


def test_e2e_success_with_correlation(client: TestClient):
    org_id, username, password = _tenant(client, "E2E OK")
    headers = auth_header(_token(client, username, password))
    cat_id = _gov_catalog(client, headers)
    conn = _connector(client, headers, gov_catalog_entry_id=cat_id)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    res = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    assert res.status_code == 200
    body = res.json()
    assert body.get("correlation_id")
    assert body.get("execution_id")


def test_cross_org_connector_404(client: TestClient):
    _, ua, pa = _tenant(client, "Cross Conn A")
    _, ub, pb = _tenant(client, "Cross Conn B")
    ha = auth_header(_token(client, ua, pa))
    hb = auth_header(_token(client, ub, pb))
    conn = _connector(client, ha)
    assert client.get(f"/api/integraciones/conectores/{conn['id']}", headers=hb).status_code == 404


def test_idempotency_no_duplicate_lineage(client: TestClient):
    org_id, username, password = _tenant(client, "Idem Lineage")
    headers = auth_header(_token(client, username, password))
    cat_id = _gov_catalog(client, headers)
    conn = _connector(client, headers, gov_catalog_entry_id=cat_id)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    key = "idem-wiring-key"
    r1 = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={"idempotency_key": key})
    r2 = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={"idempotency_key": key})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json().get("idempotent") is True
    db = TestingSessionLocal()
    count = db.query(GovLineageEvent).filter(
        GovLineageEvent.organization_id == org_id,
        GovLineageEvent.catalog_entry_id == cat_id,
    ).count()
    db.close()
    assert count == 1
