"""Tests BLOQUE 1350 — Gobierno de datos, privacidad y retención."""
from __future__ import annotations

import uuid

import pytest

from app.governance_models import GovCatalogEntry
from app.models import Organization, User
from app.security import hash_password
from app.services.governance_adapters import GovernanceConnectorAdapter, GovernanceProviderAdapter
from app.services.governance_masking import apply_mask, sanitize_secret_fields
from app.services import governance_service as svc
from conftest import TestingSessionLocal, auth_header


def _create_org_user(client, org_name: str, username: str, password: str, role: str = "admin") -> tuple[str, str]:
    db = TestingSessionLocal()
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=org_name, slug=f"gov-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
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
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"], org_id


def _headers(token: str) -> dict[str, str]:
    return auth_header(token)


@pytest.fixture()
def tenant_a(client):
    token, org_id = _create_org_user(client, "Org Gov A", f"gov-a-{uuid.uuid4().hex[:6]}", "Gov1350*A1")
    return {"token": token, "org_id": org_id}


@pytest.fixture()
def tenant_b(client):
    token, org_id = _create_org_user(client, "Org Gov B", f"gov-b-{uuid.uuid4().hex[:6]}", "Gov1350*B1")
    return {"token": token, "org_id": org_id}


def test_catalog_create_and_list(client, tenant_a):
    h = _headers(tenant_a["token"])
    res = client.post(
        "/api/gobierno-datos/catalogo",
        headers=h,
        json={"name": "Base clientes", "functional_owner": "Operaciones", "data_environment": "PRODUCCION"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Base clientes"
    listed = client.get("/api/gobierno-datos/catalogo", headers=h)
    assert listed.status_code == 200
    assert any(row["id"] == body["id"] for row in listed.json())


def test_classification_defaults(client, tenant_a):
    h = _headers(tenant_a["token"])
    res = client.get("/api/gobierno-datos/clasificaciones", headers=h)
    assert res.status_code == 200
    codes = {row["code"] for row in res.json()}
    assert "PUBLICO" in codes
    assert "RESTRINGIDO" in codes


def test_category_defaults(client, tenant_a):
    h = _headers(tenant_a["token"])
    res = client.get("/api/gobierno-datos/categorias", headers=h)
    assert res.status_code == 200
    codes = {row["code"] for row in res.json()}
    assert "DATOS_PERSONALES" in codes


def test_retention_and_disposition(client, tenant_a):
    h = _headers(tenant_a["token"])
    res = client.post(
        "/api/gobierno-datos/retencion",
        headers=h,
        json={
            "name": "Retención operativa",
            "scope_type": "ORGANIZACION",
            "duration_unit": "MESES",
            "duration_value": 24,
            "disposition": "ANONIMIZAR",
        },
    )
    assert res.status_code == 201
    assert res.json()["disposition"] == "ANONIMIZAR"


def test_legal_hold(client, tenant_a):
    h = _headers(tenant_a["token"])
    cat = client.post("/api/gobierno-datos/catalogo", headers=h, json={"name": "Hold test"}).json()
    hold = client.post(
        "/api/gobierno-datos/legal-hold",
        headers=h,
        json={"catalog_entry_id": cat["id"], "reason": "Investigación interna"},
    )
    assert hold.status_code == 201
    assert hold.json()["status"] == "ACTIVO"
    release = client.post(f"/api/gobierno-datos/legal-hold/{hold.json()['id']}/liberar", headers=h)
    assert release.status_code == 200
    assert release.json()["status"] == "LIBERADO"


def test_lineage(client, tenant_a):
    h = _headers(tenant_a["token"])
    cat = client.post("/api/gobierno-datos/catalogo", headers=h, json={"name": "Linaje"}).json()
    ev = client.post(
        "/api/gobierno-datos/linaje",
        headers=h,
        json={
            "catalog_entry_id": cat["id"],
            "step_type": "FUENTE",
            "label": "ERP origen",
        },
    )
    assert ev.status_code == 201
    listed = client.get(f"/api/gobierno-datos/catalogo/{cat['id']}/linaje", headers=h)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_ai_usage(client, tenant_a):
    h = _headers(tenant_a["token"])
    grant = client.post(
        "/api/gobierno-datos/usos-ia",
        headers=h,
        json={
            "target_type": "EMPLEADO",
            "target_id": uuid.uuid4().hex,
            "source_type": "CATEGORIA",
            "source_ref": "DATOS_OPERATIVOS",
            "permission": "LECTURA",
        },
    )
    assert grant.status_code == 201
    listed = client.get("/api/gobierno-datos/usos-ia", headers=h)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_provider_policy_allowed(client, tenant_a):
    h = _headers(tenant_a["token"])
    cls = client.get("/api/gobierno-datos/clasificaciones", headers=h).json()
    publico = next(c for c in cls if c["code"] == "PUBLICO")
    client.post(
        "/api/gobierno-datos/politicas-proveedor",
        headers=h,
        json={"classification_level_id": publico["id"], "decision": "PERMITIDO"},
    )
    eval_res = client.post(
        "/api/gobierno-datos/evaluar-proveedor",
        headers=h,
        json={"classification_level_id": publico["id"], "provider": "openai"},
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["result"] == "PERMITIDO"


def test_provider_policy_denied(client, tenant_a):
    h = _headers(tenant_a["token"])
    cls = client.get("/api/gobierno-datos/clasificaciones", headers=h).json()
    restr = next(c for c in cls if c["code"] == "RESTRINGIDO")
    client.post(
        "/api/gobierno-datos/politicas-proveedor",
        headers=h,
        json={"classification_level_id": restr["id"], "decision": "PROHIBIDO"},
    )
    eval_res = client.post(
        "/api/gobierno-datos/evaluar-proveedor",
        headers=h,
        json={"classification_level_id": restr["id"]},
    )
    assert eval_res.json()["result"] == "DENEGADO"


def test_provider_transform_required(client, tenant_a):
    h = _headers(tenant_a["token"])
    cls = client.get("/api/gobierno-datos/clasificaciones", headers=h).json()
    conf = next(c for c in cls if c["code"] == "CONFIDENCIAL")
    client.post(
        "/api/gobierno-datos/politicas-proveedor",
        headers=h,
        json={
            "classification_level_id": conf["id"],
            "decision": "PERMITIDO_CON_RESTRICCIONES",
            "minimization_action": "ENMASCARAR",
        },
    )
    eval_res = client.post(
        "/api/gobierno-datos/evaluar-proveedor",
        headers=h,
        json={"classification_level_id": conf["id"]},
    )
    assert eval_res.json()["result"] == "PERMITIDO_CON_TRANSFORMACIÓN"
    assert eval_res.json()["minimization_action"] == "ENMASCARAR"


def test_purpose_and_authorization(client, tenant_a):
    h = _headers(tenant_a["token"])
    purposes = client.get("/api/gobierno-datos/propositos", headers=h).json()
    assert any(p["code"] == "OPERACION" for p in purposes)
    auth = client.post(
        "/api/gobierno-datos/autorizaciones",
        headers=h,
        json={"auth_type": "CONSENTIMIENTO", "purpose": "Análisis interno", "source_ref": "cliente-1"},
    )
    assert auth.status_code == 201
    assert auth.json()["status"] == "VIGENTE"


def test_subject_request(client, tenant_a):
    h = _headers(tenant_a["token"])
    req = client.post(
        "/api/gobierno-datos/solicitudes",
        headers=h,
        json={"request_type": "CONSULTAR", "subject_ref": "persona-42"},
    )
    assert req.status_code == 201
    assert req.json()["status"] == "RECIBIDA"
    patched = client.patch(
        f"/api/gobierno-datos/solicitudes/{req.json()['id']}",
        headers=h,
        json={"status": "EN_REVISIÓN"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "EN_REVISIÓN"


def test_export_and_multitenant(client, tenant_a, tenant_b):
    h_a = _headers(tenant_a["token"])
    h_b = _headers(tenant_b["token"])
    cat = client.post("/api/gobierno-datos/catalogo", headers=h_a, json={"name": "Export A"}).json()
    cls = client.get("/api/gobierno-datos/clasificaciones", headers=h_a).json()
    publico = next(c for c in cls if c["code"] == "PUBLICO")
    client.patch(
        f"/api/gobierno-datos/catalogo/{cat['id']}",
        headers=h_a,
        json={"classification_level_id": publico["id"]},
    )
    client.post(
        "/api/gobierno-datos/politicas-proveedor",
        headers=h_a,
        json={"classification_level_id": publico["id"], "decision": "PERMITIDO"},
    )
    export = client.post(
        "/api/gobierno-datos/exportaciones",
        headers=h_a,
        json={"catalog_entry_id": cat["id"], "reason": "Reporte", "format": "CSV"},
    )
    assert export.status_code == 201
    denied = client.post(
        "/api/gobierno-datos/exportaciones",
        headers=h_b,
        json={"catalog_entry_id": cat["id"], "reason": "Intento cruzado"},
    )
    assert denied.status_code in (404, 400)
    list_b = client.get("/api/gobierno-datos/catalogo", headers=h_b).json()
    assert all(row["id"] != cat["id"] for row in list_b)


def test_masking():
    assert "@" in apply_mask("email", "usuario@empresa.com")
    assert apply_mask("email", "usuario@empresa.com") != "usuario@empresa.com"
    masked = sanitize_secret_fields({"password": "secret123", "name": "dato"})
    assert masked["password"] == "CONFIGURADO"
    assert masked["name"] == "dato"


def test_test_data_environment(client, tenant_a):
    h = _headers(tenant_a["token"])
    res = client.post(
        "/api/gobierno-datos/catalogo",
        headers=h,
        json={"name": "Datos sintéticos", "data_environment": "SINTETICO"},
    )
    assert res.status_code == 201
    assert res.json()["data_environment"] == "SINTETICO"


def test_risk(client, tenant_a):
    h = _headers(tenant_a["token"])
    cat = client.post("/api/gobierno-datos/catalogo", headers=h, json={"name": "Riesgo"}).json()
    risk = client.get(f"/api/gobierno-datos/catalogo/{cat['id']}/riesgo", headers=h)
    assert risk.status_code == 200
    assert risk.json()["risk_level"] in ("BAJO", "MEDIO", "ALTO", "CRÍTICO")


def test_findings_scan(client, tenant_a):
    h = _headers(tenant_a["token"])
    client.post("/api/gobierno-datos/catalogo", headers=h, json={"name": "Sin clasificar"})
    scan = client.post("/api/gobierno-datos/hallazgos/escanear", headers=h)
    assert scan.status_code == 200
    types = {f["finding_type"] for f in scan.json()}
    assert "SIN_CLASIFICACION" in types or "RETENCION_AUSENTE" in types


def test_corrective_action(client, tenant_a):
    h = _headers(tenant_a["token"])
    client.post("/api/gobierno-datos/catalogo", headers=h, json={"name": "Hallazgo fuente"})
    findings = client.post("/api/gobierno-datos/hallazgos/escanear", headers=h).json()
    finding_id = findings[0]["id"]
    action = client.post(
        "/api/gobierno-datos/acciones",
        headers=h,
        json={"finding_id": finding_id, "status": "PENDIENTE"},
    )
    assert action.status_code == 201
    assert action.json()["status"] == "PENDIENTE"


def test_rbac_viewer_denied_manage(client, tenant_a):
    db = TestingSessionLocal()
    viewer_name = f"viewer-{uuid.uuid4().hex[:6]}"
    viewer = User(
        organization_id=tenant_a["org_id"],
        username=viewer_name,
        password_hash=hash_password("Viewer1350*"),
        role="viewer",
        status="ACTIVE",
        is_active=True,
    )
    db.add(viewer)
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": viewer_name, "password": "Viewer1350*"})
    assert login.status_code == 200
    h = _headers(login.json()["access_token"])
    denied = client.post("/api/gobierno-datos/retencion", headers=h, json={"name": "No permitido"})
    assert denied.status_code == 403


def test_audit_access_log(client, tenant_a):
    h = _headers(tenant_a["token"])
    cat = client.post("/api/gobierno-datos/catalogo", headers=h, json={"name": "Auditoría"}).json()
    client.get(f"/api/gobierno-datos/catalogo/{cat['id']}", headers=h)
    logs = client.get("/api/gobierno-datos/accesos", headers=h)
    assert logs.status_code == 200
    assert any(log["action"] == "CONSULTA" for log in logs.json())


def test_secrets_not_exposed_in_catalog(client, tenant_a):
    h = _headers(tenant_a["token"])
    res = client.post(
        "/api/gobierno-datos/catalogo",
        headers=h,
        json={
            "name": "Credenciales API",
            "secret_status": "CONFIGURADO",
            "metadata": {"api_key": "sk-live-abc", "password": "pwd"},
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body.get("secret_status") == "CONFIGURADO"
    meta = body.get("metadata") or {}
    assert meta.get("api_key") == "CONFIGURADO"
    assert meta.get("password") == "CONFIGURADO"
    assert "sk-live" not in str(body)


def test_adapter_1270(client, tenant_a):
    h = _headers(tenant_a["token"])
    cls = client.get("/api/gobierno-datos/clasificaciones", headers=h).json()
    publico = next(c for c in cls if c["code"] == "PUBLICO")
    res = client.post(
        "/api/gobierno-datos/adaptador-1270/evaluar",
        headers=h,
        json={"classification_level_id": publico["id"], "provider": "openai"},
    )
    assert res.status_code == 200
    assert "result" in res.json()


def test_adapter_1330(client, tenant_a):
    h = _headers(tenant_a["token"])
    cat = client.post("/api/gobierno-datos/catalogo", headers=h, json={"name": "Conector"}).json()
    res = client.get(f"/api/gobierno-datos/adaptador-1330/catalogo/{cat['id']}", headers=h)
    assert res.status_code == 200
    assert "restrictions" in res.json()


def test_multitenant_policies_isolated(client, tenant_a, tenant_b):
    h_a = _headers(tenant_a["token"])
    h_b = _headers(tenant_b["token"])
    cat_a = client.post("/api/gobierno-datos/catalogo", headers=h_a, json={"name": "Solo A"}).json()
    view_b = client.get(f"/api/gobierno-datos/adaptador-1330/catalogo/{cat_a['id']}", headers=h_b)
    assert view_b.status_code == 404


def test_dashboard(client, tenant_a):
    h = _headers(tenant_a["token"])
    res = client.get("/api/gobierno-datos/dashboard", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert "fuentes_catalogadas" in body


def test_service_purpose_mismatch():
    db = TestingSessionLocal()
    org = Organization(name="Purpose Org", slug=f"p-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    svc.ensure_org_defaults(db, org.id)
    purposes = svc.list_purposes(db, org.id)
    p_op = next(p for p in purposes if p["code"] == "OPERACION")
    p_audit = next(p for p in purposes if p["code"] == "AUDITORIA")
    entry = svc.create_catalog_entry(
        db,
        org.id,
        "u1",
        {"name": "Propósito", "purpose_id": p_op["id"]},
    )
    mismatch = svc.detect_purpose_mismatch(db, org.id, entry["id"], p_op["id"], p_audit["id"])
    assert mismatch is True
    db.close()


def test_adapters_direct():
    db = TestingSessionLocal()
    org = Organization(name="Adapter Org", slug=f"ad-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    svc.ensure_org_defaults(db, org.id)
    cls = svc.list_classification_levels(db, org.id)
    publico = next(c for c in cls if c["code"] == "PUBLICO")
    svc.create_provider_policy(
        db,
        org.id,
        None,
        {"classification_level_id": publico["id"], "decision": "PERMITIDO"},
    )
    entry = svc.create_catalog_entry(db, org.id, "u1", {"name": "Adapter", "classification_level_id": publico["id"]})
    provider = GovernanceProviderAdapter(db)
    decision = provider.can_send_to_provider(org.id, catalog_entry_id=entry["id"], provider="openai")
    assert decision.result == "PERMITIDO"
    connector = GovernanceConnectorAdapter(db)
    view = connector.get_resource_policy(org.id, entry["id"])
    assert view is not None
    assert view.classification_code == "PUBLICO"
    db.close()


def test_catalog_secret_status_only():
    db = TestingSessionLocal()
    org = Organization(name="Secret Org", slug=f"s-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    row = GovCatalogEntry(
        organization_id=org.id,
        name="Secretos",
        secret_status="CONFIGURADO",
        metadata_json='{"api_key":"real-key-never"}',
    )
    db.add(row)
    db.commit()
    payload = svc.catalog_to_dict(row, db)
    assert payload["secret_status"] == "CONFIGURADO"
    assert "real-key" not in str(payload)
    db.close()
