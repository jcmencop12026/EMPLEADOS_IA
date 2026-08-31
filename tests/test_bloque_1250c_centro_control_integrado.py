"""BLOQUE 1250C — Centro de Control integrado con módulos 1100-1220."""

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


def test_1250c_resumen_integraciones(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["oportunidades"]["disponible"] is True
    assert body["finops"]["disponible"] is True
    assert "finops_extendido" in body
    assert "cadena_ejecutiva" in body
    assert body["integraciones_futuras"]["1200"].startswith("Integrado")


def test_1250c_impacto_sin_datos_no_cero(client: TestClient, auth_headers):
    impacto = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["impacto"]
    if not impacto.get("disponible"):
        assert impacto["estado"] == "Sin información disponible"
        assert impacto.get("lineas_base_activas") is None or impacto.get("lineas_base_activas") == 0


def test_1250c_valor_retorno_sin_datos(client: TestClient, auth_headers):
    vr = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["valor_retorno"]
    if not vr.get("disponible"):
        assert vr["estado"] == "Sin información disponible"
        assert vr.get("valor_esperado") is None


def test_1250c_diagnostico_sin_datos(client: TestClient, auth_headers):
    diag = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["diagnostico"]
    if not diag.get("disponible"):
        assert diag["estado"] == "Sin información disponible"


def test_1250c_senales_estructura(client: TestClient, auth_headers):
    sen = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["senales"]
    assert "por_modo_ingesta" in sen
    assert "REAL" in sen["por_modo_ingesta"]


def test_1250c_finops_extendido(client: TestClient, auth_headers):
    fe = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["finops_extendido"]
    assert fe is not None
    assert fe.get("bloque") == "1110"


def test_1250c_oportunidades_estados_operativos(client: TestClient, auth_headers):
    opp = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["oportunidades"]
    assert "estados_operativos" in opp


def test_1250c_cross_tenant(client: TestClient, auth_headers, cc_db):
    from app.database import SessionLocal

    org_b = Organization(name=f"OrgB-1250c-{uuid.uuid4().hex[:6]}")
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
    admin_a = _admin(db)
    summary_a = svc.get_executive_summary(db, admin_a)
    summary_b = svc.get_executive_summary(db, user_b)
    assert summary_a["organization_id"] != summary_b["organization_id"]
    db.close()


def test_1250c_rbac_sin_finops_permiso(cc_db):
    from app.services.control_center_adapters import FinOpsExtendidoAdapter

    admin = _admin(cc_db)
    adapter = FinOpsExtendidoAdapter()
    result = adapter.fetch(cc_db, admin.organization_id, permissions={"control_center.view"})
    assert result.get("restringido") is True
    assert result["disponible"] is False

    summary = svc.get_executive_summary(cc_db, admin)
    assert summary["finops"] is not None


def test_1250c_superadmin_org_context(client: TestClient, auth_headers, cc_db):
    from app.database import SessionLocal

    org_b = Organization(name=f"OrgB-sa-{uuid.uuid4().hex[:6]}")
    db = SessionLocal()
    db.add(org_b)
    db.commit()
    res = client.get(
        f"/api/centro-control/resumen-ejecutivo?organization_id={org_b.id}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["organization_id"] == org_b.id
    db.close()


def test_1250c_periodo_filtro(client: TestClient, auth_headers):
    res7 = client.get("/api/centro-control/resumen-ejecutivo?periodo=7d", headers=auth_headers)
    res30 = client.get("/api/centro-control/resumen-ejecutivo?periodo=30d", headers=auth_headers)
    assert res7.status_code == 200
    assert res30.status_code == 200
    assert res7.json()["filtros"]["periodo"] == "7d"


def test_1250c_navegacion_enlaces(client: TestClient, auth_headers):
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    for ind in body["resumen_ejecutivo"]["indicadores"]:
        if ind["disponible"]:
            assert ind["enlace"].startswith("/")
    for item in body["atencion_requerida"]:
        assert item["enlace"].startswith("/")


def test_1250c_empresa_inactiva(client: TestClient, auth_headers, cc_db):
    from app.models import Organization

    org = cc_db.query(Organization).filter(Organization.id == _admin(cc_db).organization_id).first()
    prev = org.status
    org.status = ORG_STATUS_INACTIVE
    cc_db.commit()
    try:
        res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
        assert res.status_code == 403
    finally:
        org.status = prev
        cc_db.commit()
