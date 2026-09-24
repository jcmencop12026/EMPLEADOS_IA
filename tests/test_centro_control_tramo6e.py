"""Tramo 6E — Centro de Control Ejecutivo integrado."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User
from app.security import hash_password
from app.services.control_center_adapters import SEMANTICA_VALOR
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


def test_centro_control_secciones_y_semantica(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo?periodo=mtd", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "secciones" in body
    assert len(body["secciones"]) >= 6
    assert body.get("semantica", {}).get("HECHO")
    assert body.get("valor_consolidado", {}).get("nota_potencial")
    assert "POTENCIAL no se suma" in body["valor_consolidado"]["nota_potencial"]


def test_centro_control_modulos_tramo6e(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    for key in (
        "comercial",
        "aprendizaje",
        "optimizacion",
        "tco",
        "implementacion",
        "multiproveedor",
        "mb07_planificador",
        "mb11_comunicaciones",
        "mb12_soporte",
        "auditor_empleados",
        "mi_trabajo",
        "continuidad",
    ):
        assert key in body
        mod = body[key]
        assert isinstance(mod, dict)
        assert "disponible" in mod


def test_potencial_excluido_de_realizado():
    from app.services.control_center_adapters import _sum_valor_por_naturaleza

    buckets = _sum_valor_por_naturaleza([
        ("VERIFICADO", 100),
        ("ESTIMADO", 50),
        ("POTENCIAL", 999),
    ])
    assert buckets["valor_realizado"] == 150.0
    assert buckets["valor_potencial"] == 999.0
    assert SEMANTICA_VALOR["nota_potencial"]


def test_centro_control_tenant_isolation(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b = Organization(name=f"CC-B-{uuid.uuid4().hex[:6]}")
        db.add(org_b)
        db.flush()
        user_b = User(
            organization_id=org_b.id,
            username=f"ccb-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("CCB2026*"),
            role="admin",
            full_name="Org B CC",
        )
        db.add(user_b)
        db.commit()
        uname = user_b.username
    finally:
        db.close()

    token_b = client.post("/api/auth/login", json={"username": uname, "password": "CCB2026*"}).json()["access_token"]
    res_a = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    res_b = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_header(token_b)).json()
    assert res_a["organization_id"] != res_b["organization_id"]


def test_centro_control_rbac_denied_without_permission(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions
        from app.models import Role, RolePermission, Permission

        org = Organization(name=f"CC-Viewer-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        bootstrap_permissions(db)
        limited = Role(
            organization_id=org.id,
            code=f"cc-limited-{uuid.uuid4().hex[:6]}",
            name="Sin CC",
            is_system=False,
            is_active=True,
        )
        db.add(limited)
        db.flush()
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        db.add(RolePermission(role_id=limited.id, permission_id=view_perm.id))
        viewer = User(
            organization_id=org.id,
            username=f"ccv-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("CCV2026*"),
            role=limited.code,
            full_name="Sin CC",
        )
        db.add(viewer)
        db.commit()
        uname = viewer.username
    finally:
        db.close()

    token = client.post("/api/auth/login", json={"username": uname, "password": "CCV2026*"}).json()["access_token"]
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_header(token))
    assert res.status_code == 403


def test_datetime_naive_aware_vencimiento():
    from app.services.control_center_service import _as_utc, _max_utc

    naive = datetime(2026, 1, 1, 12, 0, 0)
    aware = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    assert _as_utc(naive) == datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _max_utc(naive, aware) == aware
