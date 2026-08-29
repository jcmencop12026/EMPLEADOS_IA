"""Bandeja unificada de trabajo humano."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User
from app.notifications import emit_event
from app.orchestration_models import ApprovalRequest, WorkPlan
from app.security import hash_password

pytestmark = pytest.mark.operations


def test_trabajo_items_api(client: TestClient, auth_headers):
    res = client.get("/api/trabajo/items", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


def test_trabajo_resumen_api(client: TestClient, auth_headers):
    res = client.get("/api/trabajo/resumen", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["pendientes"] >= 0
    assert body["vencidas"] >= 0
    assert body["requieren_aprobacion"] >= 0


def test_trabajo_item_estructura(client: TestClient, auth_headers):
    res = client.get("/api/trabajo/items", headers=auth_headers)
    for item in res.json()["items"]:
        assert item["id"]
        assert item["asunto"]
        assert item["modulo"]
        assert item["enlace"]
        assert "requires_action" in item
        assert "estado_dominio" in item
        assert "estado_presentacion" in item


def test_trabajo_deduplicacion_aprobacion_notificacion(client: TestClient, auth_headers, token):
    from app.config import settings
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        assert admin
        org_id = admin.organization_id
        plan = WorkPlan(
            organization_id=org_id,
            user_id=admin.id,
            correlation_id="corr-dedupe-test",
            request="test dedupe",
            objective="Plan dedupe",
            status="WAITING_APPROVAL",
        )
        db.add(plan)
        db.flush()
        approval = ApprovalRequest(
            organization_id=org_id,
            work_plan_id=plan.id,
            action="Acción sensible",
            reason="Motivo dedupe",
            requested_by=admin.id,
            status="PENDING",
        )
        db.add(approval)
        db.flush()
        emit_event(
            "APPROVAL_REQUIRED",
            org_id,
            "work_plan",
            plan.id,
            {"approval_id": approval.id, "reason": approval.reason},
            db,
            commit=True,
        )
        db.commit()
        approval_id = approval.id
    finally:
        db.close()

    res = client.get("/api/trabajo/items", headers=auth_headers)
    items = res.json()["items"]
    approval_rows = [i for i in items if i["tipo"] == "aprobacion" and i["source_id"] == approval_id]
    notif_rows = [
        i
        for i in items
        if i["tipo"] == "notificacion"
        and i.get("metadata", {}).get("approval_id") == approval_id
    ]
    assert len(approval_rows) == 1
    assert len(notif_rows) == 0


def test_trabajo_multiempresa_aislamiento(client: TestClient):
    import uuid

    from app.database import SessionLocal
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud
    from conftest import auth_header

    db = SessionLocal()
    try:
        org_a = Organization(name="Org Trabajo A", slug=f"trab-a-{uuid.uuid4().hex[:6]}")
        org_b = Organization(name="Org Trabajo B", slug=f"trab-b-{uuid.uuid4().hex[:6]}")
        db.add_all([org_a, org_b])
        db.flush()
        for org in (org_a, org_b):
            bootstrap_permissions(db)
            bootstrap_orchestration(db, org.id)
            bootstrap_salud(db, org.id)
        pwd = "TrabajoTest*1"
        user_a = User(
            organization_id=org_a.id,
            username=f"trabajo_a_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password(pwd),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        user_b = User(
            organization_id=org_b.id,
            username=f"trabajo_b_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password(pwd),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add_all([user_a, user_b])
        db.flush()
        plan_b = WorkPlan(
            organization_id=org_b.id,
            user_id=user_b.id,
            correlation_id="corr-org-b-only",
            request="solo org b",
            objective="Plan org B",
            status="FAILED",
            error="fallo aislado",
        )
        db.add(plan_b)
        db.commit()
        username_a = user_a.username
        username_b = user_b.username
        plan_b_id = plan_b.id
    finally:
        db.close()

    token_a = client.post("/api/auth/login", json={"username": username_a, "password": pwd}).json()["access_token"]
    token_b = client.post("/api/auth/login", json={"username": username_b, "password": pwd}).json()["access_token"]
    headers_a = auth_header(token_a)
    headers_b = auth_header(token_b)

    items_b = client.get("/api/trabajo/items", headers=headers_b).json()["items"]
    items_a = client.get("/api/trabajo/items", headers=headers_a).json()["items"]
    assert any(i["source_id"] == plan_b_id for i in items_b)
    assert not any(i["source_id"] == plan_b_id for i in items_a)


def test_trabajo_filtro_requires_action(client: TestClient, auth_headers):
    res = client.get("/api/trabajo/items?requires_action=true", headers=auth_headers)
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["requires_action"] is True
