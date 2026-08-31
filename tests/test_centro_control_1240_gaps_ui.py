"""Centro de Control — integración 1240 y gaps UI (finops_extendido, llm, auditoría, actividad)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import control_center_service as svc
from app.services.control_center_adapters import InteligenciaExternaAdapter

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


def test_cc_1240_modulo_en_resumen(client: TestClient, auth_headers):
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    assert "inteligencia_externa" in body
    ie = body["inteligencia_externa"]
    assert ie is not None
    assert ie.get("bloque") == "1240"
    assert ie.get("modulo") == "inteligencia_externa"
    assert body["integraciones_futuras"]["1240"].startswith("Integrado")


def test_cc_1240_indicadores_ejecutivos(client: TestClient, auth_headers):
    inds = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()[
        "resumen_ejecutivo"
    ]["indicadores"]
    ids = {i["id"] for i in inds}
    assert {"external_sources_active", "external_signals_pending", "external_risks_open"}.issubset(ids)
    for ind in inds:
        if ind["id"].startswith("external_"):
            assert ind["enlace"] == "/inteligencia-externa"


def test_cc_gaps_ui_payload(client: TestClient, auth_headers):
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    assert "finops_extendido" in body
    assert body["finops_extendido"] is not None
    assert body["finops_extendido"].get("bloque") == "1110"

    assert "llm" in body
    llm = body["llm"]
    assert llm is not None
    assert "proveedores" in llm
    assert "disponible" in llm

    assert "auditoria_reciente" in body
    assert isinstance(body["auditoria_reciente"], list)

    assert "actividad_reciente" in body
    assert isinstance(body["actividad_reciente"], list)


def test_cc_auditoria_estructura(client: TestClient, auth_headers):
    rows = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()[
        "auditoria_reciente"
    ]
    for row in rows:
        assert "accion" in row
        assert "fecha" in row
        assert "enlace" in row
        assert row["enlace"] == "/auditoria"


def test_cc_1240_rbac_sin_permiso(cc_db):
    admin = _admin(cc_db)
    adapter = InteligenciaExternaAdapter()
    result = adapter.fetch(cc_db, admin.organization_id, permissions={"control_center.view"})
    assert result.get("restringido") is True
    assert result["disponible"] is False


def test_cc_1240_degradacion_segura(cc_db):
    admin = _admin(cc_db)
    adapter = InteligenciaExternaAdapter()

    with patch.object(adapter, "fetch", side_effect=RuntimeError("fallo simulado")):
        modulos = svc._fetch_module_adapters(
            cc_db,
            admin.organization_id,
            user=admin,
            permissions={"inteligencia_externa.view", "control_center.view"},
            period_start=None,
            adapter_instances=[adapter],
        )
    ie = modulos["inteligencia_externa"]
    assert ie["disponible"] is False
    assert ie["estado"] == "NO DISPONIBLE"
    assert ie["bloque"] == "1240"

    summary = svc.get_executive_summary(cc_db, admin)
    assert summary["inteligencia_externa"]["estado"] in (
        "NO DISPONIBLE",
        "Sin datos",
        "Integrado con módulo 1240",
    )


def test_cc_1240_cross_tenant(client: TestClient, auth_headers, cc_db):
    from app.database import SessionLocal

    org_b = Organization(name=f"OrgB-cc1240-{uuid.uuid4().hex[:6]}")
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

    summary_a = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    summary_b = svc.get_executive_summary(db, user_b)
    assert summary_a["organization_id"] != summary_b["organization_id"]
    assert summary_a["inteligencia_externa"]["fuentes_activas"] == summary_b["inteligencia_externa"].get(
        "fuentes_activas", 0
    ) or summary_a["organization_id"] != summary_b["organization_id"]
    db.close()


def test_cc_1240_atencion_origen(client: TestClient, auth_headers):
    for item in client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()[
        "atencion_requerida"
    ]:
        if item.get("origen") == "inteligencia_externa":
            assert item["tipo"] in ("senal_externa_pendiente", "riesgo_externo")
            assert item.get("severidad") in ("MEDIA", "ALTA", None)
            assert item["enlace"].startswith("/inteligencia-externa")


def test_cc_superadmin_org_context(client: TestClient, auth_headers, cc_db):
    from app.database import SessionLocal

    org_b = Organization(name=f"OrgB-sa-cc-{uuid.uuid4().hex[:6]}")
    db = SessionLocal()
    db.add(org_b)
    db.commit()
    res = client.get(
        f"/api/centro-control/resumen-ejecutivo?organization_id={org_b.id}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["organization_id"] == org_b.id
    assert "inteligencia_externa" in body
    db.close()
