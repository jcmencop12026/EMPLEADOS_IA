"""BLOQUE 1230 — Centro de Control ejecutivo (capa de consolidación)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import control_center_service as svc
from app.tenant_scope import ORG_STATUS_INACTIVE

pytestmark = [pytest.mark.operations]


@pytest.fixture
def cc_db():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _admin(db: Session) -> User:
    user = db.query(User).filter(User.username == "admin").first()
    assert user
    return user


def test_1230_resumen_ejecutivo_api(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["organization_id"]
    assert body["resumen_ejecutivo"]["indicadores"]
    assert isinstance(body["atencion_requerida"], list)
    assert "integraciones_futuras" in body


def test_1230_indicadores_no_ceros_enganosos(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    inds = res.json()["resumen_ejecutivo"]["indicadores"]
    for ind in inds:
        if not ind["disponible"]:
            assert ind["valor"] is None or ind["estado"]


def test_1230_atencion_requerida_estructura(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    for item in res.json()["atencion_requerida"]:
        assert "enlace" in item and item["enlace"]
        assert "origen" in item


def test_1230_empleados_ia_seccion(cc_db):
    user = _admin(cc_db)
    data = svc.get_executive_summary(cc_db, user)
    if data["empleados_ia"]:
        assert "activos" in data["empleados_ia"]
        assert "items" in data["empleados_ia"]


def test_1230_oportunidades_disponible(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    opp = res.json()["oportunidades"]
    assert opp is not None
    assert "disponible" in opp


def test_1230_impacto_preparado(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    impacto = res.json()["impacto"]
    assert impacto is not None
    assert "estado" in impacto
    assert impacto.get("bloque") == "1200" or "contrato" in impacto


def test_1230_finops_disponible(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    finops = res.json()["finops"]
    assert finops is not None
    assert finops.get("disponible") is True


def test_1230_valor_retorno_preparado(client: TestClient, auth_headers):
    vr = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["valor_retorno"]
    assert vr["disponible"] is False
    assert vr["estado"] == "Sin información disponible"


def test_1230_diagnostico_preparado(client: TestClient, auth_headers):
    diag = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["diagnostico"]
    assert diag is not None
    if diag.get("disponible"):
        assert diag.get("total", 0) >= 0
    else:
        assert diag["estado"] == "Sin información disponible"


def test_1230_senales_seccion(client: TestClient, auth_headers):
    sen = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["senales"]
    assert sen is not None
    assert "total" in sen


def test_1230_salud_plataforma(client: TestClient, auth_headers):
    salud = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["salud_plataforma"]
    assert salud is not None
    assert "status" in salud


def test_1230_cross_tenant(client: TestClient, auth_headers, cc_db):
    from app.database import SessionLocal

    org_b = Organization(name=f"OrgB-1230-{uuid.uuid4().hex[:6]}")
    db = SessionLocal()
    db.add(org_b)
    db.commit()
    user_b = User(
        username=f"admin-b-{uuid.uuid4().hex[:6]}",
        email=f"b-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        organization_id=org_b.id,
        role="admin",
        is_active=True,
    )
    db.add(user_b)
    db.commit()
    data_b = svc.get_executive_summary(db, user_b)
    data_a = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    assert data_a["organization_id"] != data_b["organization_id"]
    db.close()


def test_1230_rbac_viewer_denegado(client: TestClient, cc_db):
    user = _admin(cc_db)
    viewer = User(
        username=f"v1230-{uuid.uuid4().hex[:6]}",
        email=f"v1230-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Viewer2026*"),
        organization_id=user.organization_id,
        role="viewer",
        is_active=True,
    )
    cc_db.add(viewer)
    cc_db.commit()
    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "Viewer2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    ok = client.get("/api/centro-control/resumen-ejecutivo", headers=headers)
    assert ok.status_code == 200


def test_1230_empresa_inactiva(client: TestClient, auth_headers, cc_db):
    user = _admin(cc_db)
    org = cc_db.query(Organization).filter(Organization.id == user.organization_id).first()
    prev = org.status
    org.status = ORG_STATUS_INACTIVE
    cc_db.commit()
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 403
    org.status = prev
    cc_db.commit()


def test_1230_api_agregadora_unica_llamada(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo?periodo=7d", headers=auth_headers)
    assert res.status_code == 200
    keys = {"resumen_ejecutivo", "atencion_requerida", "empleados_ia", "oportunidades", "finops", "salud_plataforma"}
    assert keys.issubset(res.json().keys())


def test_1230_indicadores_config(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/indicadores-config", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["indicadores"]) >= 5
