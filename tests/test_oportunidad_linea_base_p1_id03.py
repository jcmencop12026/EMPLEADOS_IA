"""P1-ID-03 — Cierre oportunidad con enlace trazable a línea base 1200."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.baseline_models import LineaBase, LineaBaseMedicion
from app.models import AuditLog, Organization, User
from app.opportunity_models import Opportunity
from app.security import hash_password
from app.services import baseline_service as bsvc
from app.services import proactive_service as psvc
from app.valuation_enums import RealValueNature

pytestmark = [pytest.mark.operations]


@pytest.fixture
def p1_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _admin(db: Session) -> tuple[str, str]:
    user = db.query(User).filter(User.username == "admin").first()
    assert user
    return user.organization_id, user.id


def _pipeline(db: Session, org_id: str, user_id: str, ref: str | None = None) -> Opportunity:
    ref = ref or f"p1id03-{uuid.uuid4().hex[:8]}"
    result = psvc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        tipo="financiera",
        dominio="financiero",
        evento="p1_id03",
        payload={
            "titulo": "Oportunidad P1-ID-03",
            "tipo_oportunidad": "FINANCIERA",
            "indicadores": {"recaudo_mensual": 1_000_000},
            "impacto_estimado": 5_000_000,
            "valor_potencial": 4_000_000,
            "urgencia": "ALTA",
            "source_reference": ref,
        },
        origen="test",
        user_id=user_id,
    )
    opp = db.query(Opportunity).get(result["opportunity_id"])
    assert opp
    return opp


def _approve_activate(db: Session, opp: Opportunity, user_id: str) -> None:
    if opp.estado == "PRIORIZADA":
        psvc.transition_state(db, opp, "PENDIENTE_APROBACION", motivo="test")
    psvc.approve_opportunity(db, opp, user_id=user_id, aprobado=True)
    psvc.activate_opportunity(db, opp, user_id=user_id)


def test_p1id03_linea_base_existente_reutilizada(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    now = datetime.now(timezone.utc)
    existing = bsvc.create_linea_base(
        p1_db,
        organization_id=org_id,
        user_id=user_id,
        indicador="recaudo_mensual",
        valor_base=1_000_000,
        fecha_inicio_base=now - timedelta(days=30),
        fecha_fin_base=now,
        proceso="financiero",
        fuente="OPORTUNIDAD",
        opportunity_id=opp.id,
        estado="ACTIVA",
    )
    p1_db.commit()
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(
        p1_db, opp, user_id=user_id, valor_real=4_500_000, evidencia={"informe": "ok"}
    )
    p1_db.commit()
    assert res["linea_base"]["id"] == existing.id
    assert res["linea_base"]["reutilizada"] is True
    count = p1_db.query(LineaBase).filter(LineaBase.opportunity_id == opp.id).count()
    assert count == 1


def test_p1id03_creacion_controlada_sin_linea_base(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    before = p1_db.query(LineaBase).filter(LineaBase.opportunity_id == opp.id).count()
    assert before >= 1
    res = psvc.register_result(
        p1_db, opp, user_id=user_id, valor_real=3_800_000, evidencia={"doc": "1"}
    )
    p1_db.commit()
    assert res["linea_base"]["id"]
    assert res["medicion_id"]
    assert res["comparacion"]["evaluacion"] in ("MEJORA", "DETERIORO", "SIN_CAMBIO", "INFORMATIVO")


def test_p1id03_no_duplicacion_linea_base(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    psvc.register_result(p1_db, opp, user_id=user_id, valor_real=2_000_000, evidencia={"a": 1})
    p1_db.commit()
    lb_id = json.loads(opp.resultado_json)["linea_base"]["id"]
    med_count = p1_db.query(LineaBaseMedicion).filter(LineaBaseMedicion.linea_base_id == lb_id).count()
    psvc.register_result(p1_db, opp, user_id=user_id, valor_real=2_500_000, evidencia={"a": 2})
    p1_db.commit()
    med_count_after = p1_db.query(LineaBaseMedicion).filter(LineaBaseMedicion.linea_base_id == lb_id).count()
    assert med_count_after == med_count


def test_p1id03_cierre_verificado(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(
        p1_db, opp, user_id=user_id, valor_real=5_000_000, evidencia={"verificado": True}
    )
    p1_db.commit()
    assert res["valor_clasificacion"] == RealValueNature.VERIFICADO
    assert res["resultado_tipo"] == "HECHO"


def test_p1id03_cierre_estimado(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(p1_db, opp, user_id=user_id, valor_real=1_200_000)
    p1_db.commit()
    assert res["valor_clasificacion"] == RealValueNature.ESTIMADO
    assert res["verificacion_pendiente"] is False


def test_p1id03_potencial_no_convertido(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(p1_db, opp, user_id=user_id, valor_real=None)
    p1_db.commit()
    assert res["valor_clasificacion"] == RealValueNature.POTENCIAL
    assert opp.valor_materializado is None


def test_p1id03_cierre_sin_evidencia_no_verificado(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(
        p1_db,
        opp,
        user_id=user_id,
        valor_real=9_000_000,
        evidencia=None,
        valor_esperado=8_000_000,
    )
    p1_db.commit()
    assert res["valor_clasificacion"] == RealValueNature.ESTIMADO


def test_p1id03_oportunidad_descartada_sin_beneficio(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    if opp.estado == "PRIORIZADA":
        psvc.transition_state(p1_db, opp, "PENDIENTE_APROBACION", motivo="test")
    psvc.approve_opportunity(p1_db, opp, user_id=user_id, aprobado=False, motivo="No viable")
    p1_db.commit()
    assert opp.estado == "DESCARTADA"
    assert opp.valor_materializado is None
    meds = p1_db.query(LineaBaseMedicion).join(LineaBase).filter(LineaBase.opportunity_id == opp.id).count()
    assert meds == 0


def test_p1id03_idempotencia(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    r1 = psvc.register_result(p1_db, opp, user_id=user_id, valor_real=1_000_000, evidencia={"k": 1})
    p1_db.commit()
    med_id_1 = r1["medicion_id"]
    r2 = psvc.register_result(p1_db, opp, user_id=user_id, valor_real=9_999_999, evidencia={"k": 9})
    p1_db.commit()
    assert r2["medicion_id"] == med_id_1


def test_p1id03_multiempresa(p1_db, client: TestClient):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    psvc.register_result(p1_db, opp, user_id=user_id, valor_real=1_000_000, evidencia={"x": 1})
    p1_db.commit()
    lb_id = json.loads(opp.resultado_json)["linea_base"]["id"]
    org_b = Organization(name=f"OrgB-P1ID03-{uuid.uuid4().hex[:6]}")
    p1_db.add(org_b)
    p1_db.flush()
    user_b = User(
        username=f"adminb-{uuid.uuid4().hex[:6]}",
        email=f"b-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        organization_id=org_b.id,
        role="admin",
        is_active=True,
    )
    p1_db.add(user_b)
    p1_db.commit()
    login = client.post("/api/auth/login", json={"username": user_b.username, "password": "Admin2026*"})
    headers_b = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.get(f"/api/lineas-base/{lb_id}", headers=headers_b)
    assert res.status_code == 404


def test_p1id03_rbac_sin_permiso(client: TestClient, p1_db):
    org_id, _ = _admin(p1_db)
    viewer = User(
        username=f"viewer-p1id03-{uuid.uuid4().hex[:6]}",
        email=f"v-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Viewer2026*"),
        organization_id=org_id,
        role="viewer",
        is_active=True,
    )
    p1_db.add(viewer)
    p1_db.commit()
    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "Viewer2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    opp = _pipeline(p1_db, org_id, viewer.id)
    p1_db.commit()
    if opp.estado == "PRIORIZADA":
        psvc.transition_state(p1_db, opp, "PENDIENTE_APROBACION", motivo="test")
        p1_db.commit()
    denied = client.post(
        f"/api/oportunidades/{opp.id}/resultado",
        headers=headers,
        json={"valor_real": 1000, "evidencia": {"k": 1}},
    )
    assert denied.status_code == 403


def test_p1id03_superadmin(client: TestClient, p1_db):
    org_id, _ = _admin(p1_db)
    sa = User(
        username=f"sa-p1id03-{uuid.uuid4().hex[:6]}",
        email=f"sa-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Super2026*"),
        organization_id=org_id,
        role="superadmin",
        is_active=True,
    )
    p1_db.add(sa)
    p1_db.commit()
    login = client.post("/api/auth/login", json={"username": sa.username, "password": "Super2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    opp = _pipeline(p1_db, org_id, sa.id)
    p1_db.commit()
    if opp.estado == "PRIORIZADA":
        psvc.transition_state(p1_db, opp, "PENDIENTE_APROBACION", motivo="test")
        p1_db.commit()
    approve = client.post(
        f"/api/oportunidades/{opp.id}/aprobar",
        headers=headers,
        json={"aprobado": True},
    )
    assert approve.status_code == 200
    activate = client.post(f"/api/oportunidades/{opp.id}/activar", headers=headers, json={})
    assert activate.status_code == 200
    result = client.post(
        f"/api/oportunidades/{opp.id}/resultado",
        headers=headers,
        json={"valor_real": 2_000_000, "evidencia": {"sa": True}},
    )
    assert result.status_code == 200
    body = result.json()["resultado"]
    assert body["linea_base"]["id"]


def test_p1id03_correlation_id(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    corr = opp.correlation_id or str(uuid.uuid4())
    opp.correlation_id = corr
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(p1_db, opp, user_id=user_id, valor_real=500_000, evidencia={"c": 1})
    p1_db.commit()
    assert res["correlation_id"] == corr
    assert res["learning_refs"]["correlation_id"] == corr


def test_p1id03_auditoria(p1_db):
    org_id, user_id = _admin(p1_db)
    before = p1_db.query(AuditLog).filter(AuditLog.action == "oportunidad.cierre_linea_base").count()
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    psvc.register_result(p1_db, opp, user_id=user_id, valor_real=700_000, evidencia={"a": 1})
    p1_db.commit()
    after = p1_db.query(AuditLog).filter(AuditLog.action == "oportunidad.cierre_linea_base").count()
    assert after > before


def test_p1id03_referencia_1260(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(p1_db, opp, user_id=user_id, valor_real=600_000, evidencia={"r": 1})
    p1_db.commit()
    refs = res["learning_refs"]
    assert refs["modulo_aprendizaje"] == "1260"
    assert refs["linea_base_id"]
    assert refs["impacto_id"]
    trace = psvc.get_full_trace(p1_db, opp.id, org_id)
    assert trace["learning_refs"]["linea_base_id"] == refs["linea_base_id"]


def test_p1id03_atribucion_inferencia(p1_db):
    org_id, user_id = _admin(p1_db)
    opp = _pipeline(p1_db, org_id, user_id)
    _approve_activate(p1_db, opp, user_id)
    res = psvc.register_result(p1_db, opp, user_id=user_id, valor_real=1_500_000, evidencia={"k": 1})
    p1_db.commit()
    assert res["atribucion_tipo"] == "INFERENCIA"
    assert opp.atribucion_nivel in psvc.ATRIBUCION_NIVELES


def test_p1id03_e2e_flujo_completo(client: TestClient, auth_headers, p1_db):
    """DETECTAR → APROBAR → VINCULAR LB → CERRAR → COMPARAR → CLASIFICAR → REF 1260."""
    org_id, user_id = _admin(p1_db)
    ref = f"e2e-p1id03-{uuid.uuid4().hex[:8]}"
    pipe = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=auth_headers,
        json={
            "tipo": "financiera",
            "dominio": "financiero",
            "evento": "e2e_p1id03",
            "payload": {
                "titulo": "E2E P1-ID-03",
                "indicadores": {"margen": 100_000},
                "valor_potencial": 3_000_000,
                "impacto_estimado": 3_500_000,
                "source_reference": ref,
            },
        },
    )
    assert pipe.status_code == 200
    opp_id = pipe.json()["opportunity_id"]
    opp = p1_db.query(Opportunity).get(opp_id)
    if opp.estado == "PRIORIZADA":
        psvc.transition_state(p1_db, opp, "PENDIENTE_APROBACION", motivo="e2e")
        p1_db.commit()
    approve = client.post(
        f"/api/oportunidades/{opp_id}/aprobar",
        headers=auth_headers,
        json={"aprobado": True, "motivo": "E2E"},
    )
    assert approve.status_code == 200
    lb_list = client.get(f"/api/lineas-base/oportunidad/{opp_id}", headers=auth_headers)
    assert lb_list.status_code == 200
    assert lb_list.json()["total"] >= 1
    activate = client.post(f"/api/oportunidades/{opp_id}/activar", headers=auth_headers, json={})
    assert activate.status_code == 200
    resultado = client.post(
        f"/api/oportunidades/{opp_id}/resultado",
        headers=auth_headers,
        json={
            "valor_real": 3_200_000,
            "valor_esperado": 3_000_000,
            "evidencia": {"informe": "e2e"},
        },
    )
    assert resultado.status_code == 200
    body = resultado.json()["resultado"]
    assert body["linea_base"]["id"]
    assert body["valor_clasificacion"] == RealValueNature.VERIFICADO
    assert body["diferencia"] == 200_000
    trace = client.get(f"/api/oportunidades/{opp_id}/trazabilidad", headers=auth_headers)
    assert trace.status_code == 200
    tr = trace.json()
    assert tr["cierre_linea_base"]["id"] == body["linea_base"]["id"]
    assert tr["learning_refs"]["modulo_aprendizaje"] == "1260"
    etapas = [t["etapa"] for t in tr["trazas"]]
    assert "CIERRE_LINEA_BASE" in etapas
