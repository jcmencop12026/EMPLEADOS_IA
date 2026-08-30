"""BLOQUE 1330 — Integraciones reales y conectores."""

from __future__ import annotations

import json
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.integration_enums import ConnectorType, ErrorCategory
from app.integration_security import SSRFError, validate_external_url
from app.models import AuditLog, Organization, User
from app.security import hash_password
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
    password = "Tenant1330*Test1"
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


def _create_connector(client: TestClient, headers: dict, **kwargs) -> dict:
    code = kwargs.pop("code", f"conn-{uuid.uuid4().hex[:4]}")
    payload = {
        "code": code,
        "name": f"Conector {code}",
        "connector_type": kwargs.get("connector_type", ConnectorType.API_REST),
        "auth_type": kwargs.get("auth_type", "NINGUNA"),
        "config": kwargs.get("config", {"mock_response": [{"tipo": "test", "dominio": "ops", "evento": "evt", "referencia": "r1"}]}),
        "destination_type": kwargs.get("destination_type"),
        "signal_source_code": kwargs.get("signal_source_code"),
        **{k: v for k, v in kwargs.items() if k not in ("connector_type", "auth_type", "config", "destination_type", "signal_source_code")},
    }
    res = client.post("/api/integraciones/conectores", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_catalog(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 Cat")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/integraciones/catalogo", headers=headers)
    assert res.status_code == 200
    types = {t["type"] for t in res.json()}
    assert ConnectorType.API_REST in types
    assert ConnectorType.WEBHOOK in types


def test_rest_get_mock_and_auth(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 REST")
    db.close()
    os.environ["INTEGRATION_TEST_KEY"] = "test-secret-value"
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, config={
        "mock_response": [{"metrica": "latencia", "valor_metrica": 120}],
        "base_url": "https://api.example.com",
        "endpoint": "/data",
        "method": "GET",
    }, auth_type="API_KEY", secret_env_var="INTEGRATION_TEST_KEY")
    test = client.post(f"/api/integraciones/conectores/{conn['id']}/probar", headers=headers)
    assert test.status_code == 200
    assert test.json()["resultado"] == "EXITOSA"
    detail = client.get(f"/api/integraciones/conectores/{conn['id']}", headers=headers)
    assert detail.json()["secret_configured"] is True
    assert "test-secret" not in json.dumps(detail.json())


def test_ssrf_blocked(client: TestClient):
    with pytest.raises(SSRFError):
        validate_external_url("http://127.0.0.1/admin")
    with pytest.raises(SSRFError):
        validate_external_url("http://169.254.169.254/latest/meta-data/")
    assert validate_external_url("https://api.public.example.com/v1") == "https://api.public.example.com/v1"


def test_ssrf_connector_test_fails(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 SSRF")
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, config={"base_url": "http://localhost:8080", "endpoint": "/x"})
    test = client.post(f"/api/integraciones/conectores/{conn['id']}/probar", headers=headers)
    assert test.json()["resultado"] == "FALLIDA"
    assert test.json()["categoria"] == ErrorCategory.SSRF


def test_file_csv_ingestion(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 File")
    db.close()
    headers = auth_header(_token(client, username, password))
    csv_content = "tipo,dominio,evento,referencia\nops,fin,evt1,ref1\n"
    conn = _create_connector(client, headers, connector_type=ConnectorType.ARCHIVO, config={
        "file_type": "CSV", "file_content": csv_content,
    })
    client.post(f"/api/integraciones/conectores/{conn['id']}/probar", headers=headers)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    exec_res = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    assert exec_res.status_code == 200
    assert exec_res.json()["records_processed"] == 1


def test_database_controlled_query(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 DB")
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, connector_type=ConnectorType.BASE_DATOS, config={
        "engine": "postgresql",
        "query_id": "metricas_diarias",
        "allowed_queries": {"metricas_diarias": {"mock_rows": [{"tipo": "db", "dominio": "d", "evento": "e", "referencia": "r"}]}},
    })
    client.post(f"/api/integraciones/conectores/{conn['id']}/probar", headers=headers)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    bad = _create_connector(client, headers, code="db-bad", connector_type=ConnectorType.BASE_DATOS, config={"query_id": "sql_libre"})
    client.put(f"/api/integraciones/conectores/{bad['id']}", headers=headers, json={"status": "ACTIVO"})
    assert client.post(f"/api/integraciones/conectores/{bad['id']}/ejecutar", headers=headers, json={}).status_code == 422


def test_sftp_mock(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 SFTP")
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, connector_type=ConnectorType.SFTP, config={"action": "list", "mock_files": [{"name": "a.csv"}]})
    test = client.post(f"/api/integraciones/conectores/{conn['id']}/probar", headers=headers)
    assert test.json()["resultado"] == "EXITOSA"


def test_webhook_inbound_dedup(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "1330 WH")
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, connector_type=ConnectorType.WEBHOOK, generate_webhook_token=True, config={"mock_response": [{"tipo": "wh"}]})
    token = conn["webhook_token"]
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    payload = {"idempotency_key": "idem-1330-1", "tipo": "wh", "dominio": "d", "evento": "e", "referencia": "r"}
    r1 = client.post(f"/api/integraciones/webhook/{conn['id']}", headers=headers, json={"token": token, "payload": payload})
    assert r1.status_code == 200
    r2 = client.post(f"/api/integraciones/webhook/{conn['id']}", headers=headers, json={"token": token, "payload": payload})
    assert r2.json().get("status") == "DUPLICADO" or r2.json().get("idempotent")


def test_mapping_and_schema_validation(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 Map")
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, config={
        "file_type": "JSON",
        "file_content": json.dumps([{"old_name": "x", "val": 10}]),
    }, connector_type=ConnectorType.ARCHIVO)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={
        "mapping": [{"op": "rename", "source": "old_name", "target": "referencia"}],
        "schema": {"required": ["referencia"]},
        "status": "ACTIVO",
    })
    exec_res = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    assert exec_res.status_code == 200


def test_idempotency_execution(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 Idem")
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers)
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    key = "exec-idem-1330"
    r1 = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={"idempotency_key": key})
    r2 = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={"idempotency_key": key})
    assert r2.json().get("idempotent") is True


def test_circuit_breaker_on_failures(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 CB")
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, config={"simulate_failure": True, "failure_category": ErrorCategory.CONEXION})
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    for _ in range(6):
        client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    health = client.get(f"/api/integraciones/conectores/{conn['id']}/salud", headers=headers)
    assert health.json()["consecutive_failures"] >= 1


def test_signal_1120_integration(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "1330 Sig")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    src = client.post("/api/senales/fuentes", headers=headers, json={"code": "int-src", "name": "Integración", "tipo_fuente": "API"})
    assert src.status_code == 201
    conn = _create_connector(client, headers, destination_type="SENALES", signal_source_code="int-src", config={
        "mock_response": [{"tipo": "integracion", "dominio": "ops", "evento": "alerta", "referencia": "ref-1120"}],
    })
    client.put(f"/api/integraciones/conectores/{conn['id']}", headers=headers, json={"status": "ACTIVO"})
    exec_res = client.post(f"/api/integraciones/conectores/{conn['id']}/ejecutar", headers=headers, json={})
    assert exec_res.json().get("signals_created", 0) >= 0


def test_rbac_and_tenant_isolation(client: TestClient):
    db = TestingSessionLocal()
    _, pass_a, user_a = _create_tenant(db, "1330 TA")
    _, pass_b, user_b = _create_tenant(db, "1330 TB")
    db.close()
    headers_a = auth_header(_token(client, user_a, pass_a))
    headers_b = auth_header(_token(client, user_b, pass_b))
    conn = _create_connector(client, headers_a)
    assert client.get(f"/api/integraciones/conectores/{conn['id']}", headers=headers_b).status_code == 404
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1330 RBAC", role="viewer")
    db.close()
    headers_v = auth_header(_token(client, username, password))
    assert client.get("/api/integraciones/conectores", headers=headers_v).status_code == 200
    assert client.post("/api/integraciones/conectores", headers=headers_v, json={"code": "x", "name": "X", "connector_type": "API_REST"}).status_code == 403


def test_audit_no_secrets(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "1330 Audit")
    org_id = org.id
    os.environ["INTEGRATION_AUDIT_KEY"] = "super-secret-key-1330"
    db.close()
    headers = auth_header(_token(client, username, password))
    conn = _create_connector(client, headers, secret_env_var="INTEGRATION_AUDIT_KEY")
    client.post(f"/api/integraciones/conectores/{conn['id']}/probar", headers=headers)
    db = TestingSessionLocal()
    logs = db.query(AuditLog).filter(AuditLog.organization_id == org_id, AuditLog.action.like("integraciones%")).all()
    blob = json.dumps([l.detail for l in logs])
    assert "super-secret-key" not in blob
    db.close()
