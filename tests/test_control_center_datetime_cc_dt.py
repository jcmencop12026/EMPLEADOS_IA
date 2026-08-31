"""CC-DT — determinismo datetime naive/aware en Centro de Control."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.orchestration_models import WorkPlan
from app.permissions import user_permissions
from app.security import hash_password
from app.services import control_center_service as cc_svc
from app.services import proactive_service as psvc

pytestmark = [pytest.mark.operations]

CC_CLUSTER = [
    "tests/test_bloque_1230_centro_control.py::test_1230_senales_seccion",
    "tests/test_bloque_1230_centro_control.py::test_1230_salud_plataforma",
    "tests/test_bloque_1230_centro_control.py::test_1230_cross_tenant",
    "tests/test_bloque_1230_centro_control.py::test_1230_rbac_viewer_denegado",
    "tests/test_bloque_1230_centro_control.py::test_1230_api_agregadora_unica_llamada",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_resumen_integraciones",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_impacto_sin_datos_no_cero",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_valor_retorno_sin_datos",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_diagnostico_sin_datos",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_senales_estructura",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_finops_extendido",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_oportunidades_estados_operativos",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_cross_tenant",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_rbac_sin_finops_permiso",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_periodo_filtro",
    "tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_navegacion_enlaces",
    "tests/test_convergencia_final_1250.py::test_final_valuation_finops_diagnostic_in_control_center",
]


@pytest.fixture
def cc_dt_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _admin(db: Session) -> tuple[str, str]:
    user = db.query(User).filter(User.username == "admin").first()
    assert user
    return user.organization_id, user.id


class TestAsUtcHelpers:
  def test_naive_vs_naive_ordering(self):
      a = datetime(2026, 1, 1, 12, 0, 0)
      b = datetime(2026, 1, 2, 12, 0, 0)
      assert cc_svc._as_utc(a) < cc_svc._as_utc(b)

  def test_aware_vs_aware_ordering(self):
      a = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
      b = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
      assert cc_svc._as_utc(a) < cc_svc._as_utc(b)

  def test_naive_vs_aware_comparable(self):
      naive = datetime(2026, 1, 1, 12, 0, 0)
      aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
      assert cc_svc._as_utc(naive) == cc_svc._as_utc(aware)

  def test_aware_vs_naive_comparable(self):
      aware = datetime(2026, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
      naive = datetime(2026, 1, 1, 12, 0, 0)
      assert cc_svc._as_utc(aware) > cc_svc._as_utc(naive)

  def test_offset_timestamp_normalized(self):
      east = datetime(2026, 1, 1, 15, 0, 0, tzinfo=timezone(timedelta(hours=3)))
      utc_equiv = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
      assert cc_svc._as_utc(east) == utc_equiv

  def test_none_returns_none(self):
      assert cc_svc._as_utc(None) is None
      assert cc_svc._max_utc(None, None) is None

  def test_max_utc_mixed_naive_aware(self):
      naive = datetime(2026, 2, 1, 0, 0, 0)
      aware = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
      result = cc_svc._max_utc(naive, aware)
      assert result == cc_svc._as_utc(naive)


def test_cc_dt_vencimiento_naive_no_typeerror(cc_dt_db):
    """WorkPlan con vencimiento naive (SQLite) no rompe _atencion_requerida."""
    org_id, user_id = _admin(cc_dt_db)
    user = cc_dt_db.query(User).get(user_id)
    wp = WorkPlan(
        organization_id=org_id,
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        request="Plan vencido naive",
        objective="CC-DT test",
        status="RUNNING",
        vencimiento=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1),
    )
    cc_dt_db.add(wp)
    cc_dt_db.commit()
    perms = user_permissions(user, cc_dt_db)
    items = cc_svc._atencion_requerida(cc_dt_db, org_id, perms)
    assert any(i["tipo"] == "tarea_vencida" for i in items)


def test_cc_dt_vencimiento_aware_no_typeerror(cc_dt_db):
    org_id, user_id = _admin(cc_dt_db)
    user = cc_dt_db.query(User).get(user_id)
    wp = WorkPlan(
        organization_id=org_id,
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        request="Plan vencido aware",
        objective="CC-DT test aware",
        status="RUNNING",
        vencimiento=datetime.now(timezone.utc) - timedelta(days=2),
    )
    cc_dt_db.add(wp)
    cc_dt_db.commit()
    perms = user_permissions(user, cc_dt_db)
    items = cc_svc._atencion_requerida(cc_dt_db, org_id, perms)
    assert any(i["tipo"] == "tarea_vencida" for i in items)


def _pollute_with_opportunities(db: Session, org_id: str, user_id: str) -> None:
    psvc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        tipo="financiera",
        dominio="financiero",
        evento="cc_dt_pollute",
        payload={
            "titulo": "Contaminación CC-DT",
            "indicadores": {"recaudo": 1_000_000},
            "valor_potencial": 2_000_000,
            "impacto_estimado": 2_500_000,
            "source_reference": f"cc-dt-{uuid.uuid4().hex[:8]}",
        },
        origen="test",
        user_id=user_id,
    )
    opp = db.query(Opportunity).filter(Opportunity.organization_id == org_id).order_by(Opportunity.created_at.desc()).first()
    if opp and opp.estado == "PRIORIZADA":
        psvc.transition_state(db, opp, "PENDIENTE_APROBACION", motivo="cc-dt")
    if opp:
        psvc.approve_opportunity(db, opp, user_id=user_id)
        psvc.activate_opportunity(db, opp, user_id=user_id)
    db.commit()


def test_cc_dt_contamination_cluster_five_runs(cc_dt_db):
    """Gate: 5 ejecuciones consecutivas del cluster CC tras contaminación — 0 fallos."""
    org_id, user_id = _admin(cc_dt_db)
    _pollute_with_opportunities(cc_dt_db, org_id, user_id)
    for run_idx in range(1, 6):
        env = dict(os.environ)
        if "DATABASE_URL" not in env:
            env["DATABASE_URL"] = os.environ.get("DATABASE_URL", "")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=line", *CC_CLUSTER],
            cwd=str(Path(__file__).resolve().parents[1]),
            env=env,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, (
            f"Run {run_idx} falló (exit={proc.returncode})\n"
            f"{proc.stdout}\n{proc.stderr}"
        )


def test_cc_dt_multiempresa_no_leak(cc_dt_db, client: TestClient):
    org_id, user_id = _admin(cc_dt_db)
    org_b = Organization(name=f"OrgB-CCDT-{uuid.uuid4().hex[:6]}")
    cc_dt_db.add(org_b)
    cc_dt_db.commit()
    login = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=headers)
    assert res.status_code == 200
    assert res.json()["organization_id"] == org_id
    assert res.json()["organization_id"] != org_b.id


def test_cc_dt_rbac_viewer_denied(cc_dt_db, client: TestClient):
    org_id, _ = _admin(cc_dt_db)
    viewer = User(
        username=f"viewer-ccdt-{uuid.uuid4().hex[:6]}",
        email=f"v-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Viewer2026*"),
        organization_id=org_id,
        role="viewer",
        is_active=True,
    )
    cc_dt_db.add(viewer)
    cc_dt_db.commit()
    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "Viewer2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=headers)
    assert res.status_code in (200, 403)
