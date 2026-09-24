"""Centro de Control — cableado ejecutivo Fase 2 (Agente D)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import control_center_service as svc

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


def test_fase2_estructura_secciones(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "secciones" in body
    ids = {s["id"] for s in body["secciones"]}
    assert {"resumen", "valor", "operacion", "ia_costos", "implementacion", "salud"} <= ids
    assert "semantica" in body
    assert "valor_consolidado" in body
    assert "integraciones_futuras" in body
    assert body["integraciones_futuras"]["1260"].startswith("Integrado")
    assert body["integraciones_futuras"]["MB-07"].startswith("Integrado")


def test_fase2_modulos_cableados(client: TestClient, auth_headers):
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    for key in (
        "aprendizaje",
        "optimizacion",
        "tco",
        "implementacion",
        "multiproveedor",
        "comercial",
        "linea_base",
        "mb07_planificador",
        "mb11_comunicaciones",
        "mb12_soporte",
        "auditor_empleados",
        "mi_trabajo",
        "continuidad",
    ):
        assert key in body


def test_fase2_valor_potencial_separado(client: TestClient, auth_headers):
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    vc = body["valor_consolidado"]
    assert "potencial" in vc
    assert "realizado" in vc
    assert "nota_potencial" in vc
    if vc.get("potencial") and vc.get("realizado"):
        assert vc["realizado"] != vc["potencial"] or vc["potencial"] == 0


def test_fase2_valor_retorno_naturaleza(client: TestClient, auth_headers):
    vr = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["valor_retorno"]
    if vr.get("disponible"):
        assert "valor_verificado" in vr
        assert "valor_estimado" in vr
        assert "valor_potencial" in vr
        assert vr.get("semantica", {}).get("VERIFICADO") == "HECHO"


def test_fase2_rbac_sin_tco(client: TestClient, cc_db):
    from app.services.control_center_adapters import TcoAdapter

    admin = _admin(cc_db)
    adapter = TcoAdapter()
    result = adapter.fetch(cc_db, admin.organization_id, permissions={"control_center.view"})
    assert result.get("restringido") is True
    assert result["disponible"] is False


def test_fase2_margen_restringido_comercial(client: TestClient, cc_db):
    from app.services.control_center_adapters import ComercialResumenAdapter

    admin = _admin(cc_db)
    adapter = ComercialResumenAdapter()
    result = adapter.fetch(
        cc_db,
        admin.organization_id,
        permissions={"comercial.view", "control_center.view"},
    )
    if result.get("disponible"):
        assert result.get("margen_restringido") is True
        assert result.get("margen_promedio_pct") is None


def test_fase2_multiempresa(client: TestClient, cc_db):
    org_b = Organization(name=f"OrgB-cc-f2-{uuid.uuid4().hex[:6]}")
    cc_db.add(org_b)
    cc_db.commit()
    user_b = User(
        username=f"user-b-{uuid.uuid4().hex[:6]}",
        email=f"b-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        organization_id=org_b.id,
        role="admin",
        is_active=True,
    )
    cc_db.add(user_b)
    cc_db.commit()
    admin_a = _admin(cc_db)
    summary_a = svc.get_executive_summary(cc_db, admin_a)
    summary_b = svc.get_executive_summary(cc_db, user_b)
    assert summary_a["organization_id"] != summary_b["organization_id"]


def test_fase2_drill_down_enlaces(client: TestClient, auth_headers):
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    for mod_key in ("oportunidades", "impacto", "aprendizaje", "optimizacion", "tco", "implementacion"):
        mod = body.get(mod_key) or {}
        if mod.get("enlace"):
            assert mod["enlace"].startswith("/")


def test_fase2_cc_dt_contaminacion_3x(client: TestClient, auth_headers, cc_db):
    """Repetir escenario CC-DT: timestamps heterogéneos — 0 TypeError."""
    from app.orchestration_models import WorkPlan

    admin = _admin(cc_db)
    org_id = admin.organization_id
    user_id = admin.id
    now = datetime.now(timezone.utc)
    naive = now.replace(tzinfo=None)
    for i in range(3):
        plan = WorkPlan(
            organization_id=org_id,
            user_id=user_id,
            correlation_id=str(uuid.uuid4()),
            request=f"CC-DT contam {i}",
            objective=f"CC-DT contam {i}",
            status="RUNNING",
            vencimiento=naive if i % 2 == 0 else now,
            created_at=naive,
        )
        cc_db.add(plan)
    cc_db.commit()
    for _ in range(3):
        summary = svc.get_executive_summary(cc_db, admin)
        assert "atencion_requerida" in summary
        assert isinstance(summary["atencion_requerida"], list)
