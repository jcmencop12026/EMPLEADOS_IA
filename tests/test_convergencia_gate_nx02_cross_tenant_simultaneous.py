"""NX02 — Cross-tenant simultáneo org A/B: CC + Mi Trabajo + MB-11 + MB-12 (+ superadmin ctx)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.communications_models import CommChannel
from app.config import settings
from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.operations]


def _bootstrap_org_user(db, prefix: str) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=f"{prefix}-{uuid.uuid4().hex[:6]}", slug=f"{prefix}-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = f"{prefix}*Test1"
    user = User(
        organization_id=org.id,
        username=f"{prefix}-{uuid.uuid4().hex[:8]}",
        password_hash=hash_password(password),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return auth_header(res.json()["access_token"])


def test_nx02_cross_tenant_simultaneous_cc_trabajo_comms_support(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pwd_a = _bootstrap_org_user(db, "nx02a")
        org_b, user_b, pwd_b = _bootstrap_org_user(db, "nx02b")
        db.add(CommChannel(organization_id=org_a.id, tipo="INTERNO_PLATAFORMA", nombre="Canal A", activo=True))
        db.add(CommChannel(organization_id=org_b.id, tipo="INTERNO_PLATAFORMA", nombre="Canal B", activo=True))
        db.commit()
        org_a_id, org_b_id = org_a.id, org_b.id
        user_a_name, user_b_name = user_a.username, user_b.username
    finally:
        db.close()

    headers_a = _login(client, user_a_name, pwd_a)
    headers_b = _login(client, user_b_name, pwd_b)
    super_headers = auth_header(token)

    cc_a = client.get("/api/centro-control/resumen-ejecutivo", headers=headers_a).json()
    cc_b = client.get("/api/centro-control/resumen-ejecutivo", headers=headers_b).json()
    assert cc_a["organization_id"] == org_a_id
    assert cc_b["organization_id"] == org_b_id
    assert cc_a["organization_id"] != cc_b["organization_id"]

    case_a = client.post(
        "/api/soporte/casos",
        headers=headers_a,
        json={"tipo": "SOLICITUD", "asunto": "NX02 Org A", "descripcion": "Solo A"},
    ).json()
    case_b = client.post(
        "/api/soporte/casos",
        headers=headers_b,
        json={"tipo": "SOLICITUD", "asunto": "NX02 Org B", "descripcion": "Solo B"},
    ).json()
    assert client.get(f"/api/soporte/casos/{case_a['id']}", headers=headers_b).status_code in (403, 404)
    assert client.get(f"/api/soporte/casos/{case_b['id']}", headers=headers_a).status_code in (403, 404)

    msgs_a = {m["id"] for m in client.get("/api/comunicaciones/mensajes", headers=headers_a).json()}
    msgs_b = {m["id"] for m in client.get("/api/comunicaciones/mensajes", headers=headers_b).json()}
    assert msgs_a.isdisjoint(msgs_b)

    items_a = client.get("/api/trabajo/items", headers=headers_a).json()["items"]
    items_b = client.get("/api/trabajo/items", headers=headers_b).json()["items"]
    ids_a = {i.get("source_id") for i in items_a if i.get("source_id")}
    ids_b = {i.get("source_id") for i in items_b if i.get("source_id")}
    assert case_b["id"] not in ids_a
    assert case_a["id"] not in ids_b

    resumen_b = client.get(f"/api/trabajo/resumen?organization_id={org_b_id}", headers=super_headers)
    assert resumen_b.status_code == 200
    cc_super_b = client.get(
        f"/api/centro-control/resumen-ejecutivo?organization_id={org_b_id}",
        headers=super_headers,
    )
    assert cc_super_b.status_code == 200
    assert cc_super_b.json()["organization_id"] == org_b_id

    finops_a = client.get("/api/finops/dashboard", headers=headers_a)
    finops_b = client.get("/api/finops/dashboard", headers=headers_b)
    assert finops_a.status_code == 200
    assert finops_b.status_code == 200
