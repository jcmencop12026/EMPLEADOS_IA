"""P1-ID-01 — Centro de Control: QUÉ → POR QUÉ → evidencia → certeza (1220)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.diagnostic_models import DiagnosticProbableCause
from app.models import Organization, User
from app.security import hash_password
from app.services import control_center_service as svc
from app.services.control_center_adapters import DiagnosticoExplicacionAdapter
from conftest import auth_header
from tests.test_diagnostico_transversal_1220 import _setup_signals

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


def _generate_diag(client: TestClient, headers: dict, *, correlation: bool = False) -> dict:
    token = headers["Authorization"].replace("Bearer ", "")
    _setup_signals(client, token, correlation=correlation)
    res = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert res.status_code == 201, res.text
    return res.json()


def test_p1_explicacion_seccion_presente(client: TestClient, auth_headers):
    _generate_diag(client, auth_headers, correlation=True)
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    assert "explicacion" in body
    exp = body["explicacion"]
    assert exp is not None
    assert exp.get("bloque") == "1220"
    assert "nota_causalidad" in exp


def test_p1_que_porque_evidencia_certeza(client: TestClient, auth_headers):
    _generate_diag(client, auth_headers, correlation=True)
    elementos = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["explicacion"]["elementos"]
    assert elementos
    causa_items = [e for e in elementos if e.get("tipo_entrada") == "CAUSA"]
    assert causa_items
    item = causa_items[0]
    assert item.get("situacion")
    assert item.get("causa")
    assert item.get("certeza")
    assert item.get("evidencia") is not None
    assert item.get("enlace", "").startswith("/diagnosticos/")


def test_p1_causa_probable(client: TestClient, auth_headers):
    _generate_diag(client, auth_headers)
    elementos = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["explicacion"]["elementos"]
    probables = [e for e in elementos if e.get("certeza_codigo") == "PROBABLE"]
    assert probables
    assert probables[0]["certeza"] == "CAUSA PROBABLE"


def test_p1_hipotesis(cc_db):
    from app.diagnostic_models import Diagnostic, DiagnosticFinding, DiagnosticProbableCause, DiagnosticItem
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-HIP-{uuid.uuid4().hex[:6]}")
    cc_db.add(org)
    cc_db.flush()
    bootstrap_permissions(cc_db)
    bootstrap_orchestration(cc_db, org.id)
    user = User(
        organization_id=org.id,
        username=f"u-hip-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    cc_db.add(user)
    cc_db.flush()

    diag = Diagnostic(
        organization_id=org.id,
        codigo=f"DIAG-HIP-{uuid.uuid4().hex[:6]}",
        version=1,
        estado="GENERADO",
        resumen="Hipótesis de prueba",
        prioridad_score=98.0,
        correlation_id=str(uuid.uuid4()),
    )
    cc_db.add(diag)
    cc_db.flush()
    finding = DiagnosticFinding(
        organization_id=org.id,
        codigo="HAL-HIP",
        tipo_contenido="INTERPRETACION",
        que_ocurre="Posible cuello de botella operativo",
        dominio="OPERATIVO",
        proceso="logistica",
        evidencia_json='{"resumen":"correlación observada","nota":"no causalidad"}',
    )
    cc_db.add(finding)
    cc_db.flush()
    cause = DiagnosticProbableCause(
        organization_id=org.id,
        finding_id=finding.id,
        diagnostic_id=diag.id,
        tipo="HIPOTESIS",
        descripcion="Hipótesis: demanda supera capacidad instalada",
        justificacion="Basada en correlación — requiere validación",
        confianza=0.45,
    )
    cc_db.add(cause)
    cc_db.flush()
    cc_db.add(
        DiagnosticItem(
            organization_id=org.id,
            diagnostic_id=diag.id,
            item_type="HALLAZGO",
            hallazgo_id=finding.id,
            causa_id=cause.id,
            orden=1,
        )
    )
    cc_db.commit()

    from app.services import diagnostic_service as dsvc

    exp = dsvc.build_executive_explanations(cc_db, org.id)
    hipotesis = [e for e in exp["elementos"] if e.get("certeza_codigo") == "HIPOTESIS"]
    assert hipotesis
    assert hipotesis[0]["certeza"] == "HIPÓTESIS"
    assert hipotesis[0]["tipo_contenido"] == "INFERENCIA"


def test_p1_correlacion_no_es_causalidad(client: TestClient, auth_headers):
    _generate_diag(client, auth_headers, correlation=True)
    exp = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["explicacion"]
    correlaciones = [e for e in exp.get("elementos", []) if e.get("tipo_entrada") == "CORRELACION"]
    if correlaciones:
        corr = correlaciones[0]
        assert corr["certeza_codigo"] == "CORRELACION"
        assert "correlación" in corr["certeza"].lower()
    else:
        assert "no implica causalidad" in (exp.get("nota_causalidad") or "").lower()


def test_p1_hecho_inferencia_distintos(client: TestClient, auth_headers):
    _generate_diag(client, auth_headers, correlation=True)
    elementos = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["explicacion"]["elementos"]
    tipos = {e.get("tipo_contenido") for e in elementos if e.get("tipo_contenido")}
    assert "HECHO" in tipos or "INFERENCIA" in tipos


def test_p1_correlation_id_preservado(client: TestClient, auth_headers):
    diag = _generate_diag(client, auth_headers, correlation=True)
    elementos = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["explicacion"]["elementos"]
    with_corr = [e for e in elementos if e.get("correlation_id")]
    assert with_corr
    assert any(e["correlation_id"] == diag.get("correlation_id") for e in with_corr if diag.get("correlation_id"))


def test_p1_cross_tenant(client: TestClient, auth_headers, cc_db):
    from app.database import SessionLocal

    _generate_diag(client, auth_headers)
    org_b = Organization(name=f"OrgB-p1-{uuid.uuid4().hex[:6]}")
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
    ids_a = {e["id"] for e in (summary_a.get("explicacion") or {}).get("elementos") or []}
    ids_b = {e["id"] for e in (summary_b.get("explicacion") or {}).get("elementos") or []}
    assert not ids_a.intersection(ids_b) or (not ids_a and not ids_b)
    db.close()


def test_p1_rbac_sin_diagnosticos_view(cc_db):
    admin = _admin(cc_db)
    adapter = DiagnosticoExplicacionAdapter()
    result = adapter.fetch(cc_db, admin.organization_id, permissions={"control_center.view"})
    assert result.get("restringido") is True
    assert result["disponible"] is False


def test_p1_degradacion_1220(cc_db):
    admin = _admin(cc_db)
    adapter = DiagnosticoExplicacionAdapter()

    def _boom(*_a, **_k):
        raise RuntimeError("fallo simulado")

    with patch.object(adapter, "fetch", side_effect=_boom):
        modulos = svc._fetch_module_adapters(
            cc_db,
            admin.organization_id,
            user=admin,
            permissions={"diagnosticos.view", "control_center.view"},
            period_start=None,
            adapter_instances=[adapter],
        )
    assert modulos["explicacion"]["disponible"] is False
    assert modulos["explicacion"]["estado"] == "NO DISPONIBLE"


def test_p1_cc_responde_sin_diagnostico(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "resumen_ejecutivo" in body
    assert body.get("explicacion") is not None


def test_p1_1240_preservado(client: TestClient, auth_headers):
    _generate_diag(client, auth_headers)
    body = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()
    assert body["inteligencia_externa"] is not None
    assert body["inteligencia_externa"].get("bloque") == "1240"


def test_p1_filtro_proceso(client: TestClient, auth_headers):
    _generate_diag(client, auth_headers, correlation=True)
    all_elems = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).json()["explicacion"]["elementos"]
    filtered = client.get(
        "/api/centro-control/resumen-ejecutivo?proceso=atencion",
        headers=auth_headers,
    ).json()["explicacion"]["elementos"]
    if all_elems and filtered:
        assert len(filtered) <= len(all_elems)
        for el in filtered:
            if el.get("proceso"):
                assert el["proceso"].lower() == "atencion"


def test_p1_filtro_estado(client: TestClient, auth_headers):
    diag = _generate_diag(client, auth_headers)
    estado = diag.get("estado", "GENERADO")
    body = client.get(
        f"/api/centro-control/resumen-ejecutivo?estado={estado}",
        headers=auth_headers,
    ).json()
    assert body["filtros"]["estado"] == estado


def test_p1_superadmin_org_context(client: TestClient, auth_headers, cc_db):
    from app.database import SessionLocal

    _generate_diag(client, auth_headers)
    org_b = Organization(name=f"OrgB-sa-p1-{uuid.uuid4().hex[:6]}")
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


def test_p1_causa_demostrada_manual(cc_db):
    from app.diagnostic_models import Diagnostic, DiagnosticFinding, DiagnosticItem, DiagnosticProbableCause
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-CONF-{uuid.uuid4().hex[:6]}")
    cc_db.add(org)
    cc_db.flush()
    bootstrap_permissions(cc_db)
    bootstrap_orchestration(cc_db, org.id)
    user = User(
        organization_id=org.id,
        username=f"u-conf-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    cc_db.add(user)
    cc_db.flush()

    diag = Diagnostic(
        organization_id=org.id,
        codigo=f"DIAG-P1-{uuid.uuid4().hex[:6]}",
        version=1,
        estado="GENERADO",
        resumen="Prueba causa demostrada",
        prioridad_score=99.0,
        correlation_id=str(uuid.uuid4()),
    )
    cc_db.add(diag)
    cc_db.flush()
    finding = DiagnosticFinding(
        organization_id=org.id,
        codigo="HAL-TEST",
        tipo_contenido="HECHO",
        que_ocurre="Aumento de costos operativos del 15%",
        dominio="FINANCIERO",
        proceso="cobranza",
        evidencia_json='{"resumen":"costo subió","referencia":"fin-001"}',
    )
    cc_db.add(finding)
    cc_db.flush()
    cause = DiagnosticProbableCause(
        organization_id=org.id,
        finding_id=finding.id,
        diagnostic_id=diag.id,
        tipo="CONFIRMADA",
        descripcion="El aumento está asociado principalmente a mayor consumo de tokens IA",
        justificacion="Evidencia validada en FinOps",
        confianza=0.92,
        evidencia_json='{"fuente":"finops","valor":15000,"comparacion":12000}',
    )
    cc_db.add(cause)
    cc_db.flush()
    cc_db.add(
        DiagnosticItem(
            organization_id=org.id,
            diagnostic_id=diag.id,
            item_type="HALLAZGO",
            hallazgo_id=finding.id,
            causa_id=cause.id,
            orden=1,
        )
    )
    cc_db.commit()

    from app.services import diagnostic_service as dsvc

    exp = dsvc.build_executive_explanations(cc_db, org.id)
    demostradas = [e for e in exp["elementos"] if e.get("certeza_codigo") == "CONFIRMADA"]
    assert demostradas
    assert demostradas[0]["certeza"] == "CAUSA DEMOSTRADA"
    assert demostradas[0]["tipo_contenido"] == "HECHO"
