"""BLOQUE 1200 — línea base, medición posterior e impacto."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import baseline_service as svc
from app.tenant_scope import ORG_STATUS_INACTIVE

pytestmark = [pytest.mark.operations]


@pytest.fixture
def lb_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _admin(db: Session) -> tuple[str, str]:
    user = db.query(User).filter(User.username == "admin").first()
    assert user
    return user.organization_id, user.id


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _payload_base(**overrides) -> dict:
    now = datetime.now(timezone.utc)
    data = {
        "indicador": "tiempo_respuesta",
        "descripcion": "Tiempo medio de respuesta",
        "unidad": "minutos",
        "valor_base": 120.0,
        "fecha_inicio_base": _iso(now - timedelta(days=60)),
        "fecha_fin_base": _iso(now - timedelta(days=30)),
        "direccion_indicador": "MENOR_ES_MEJOR",
        "impacto_esperado": 30.0,
        "estado": "ACTIVA",
    }
    data.update(overrides)
    return data


def test_1200_crear_linea_base_api(client: TestClient, auth_headers):
    res = client.post("/api/lineas-base", headers=auth_headers, json=_payload_base())
    assert res.status_code == 200
    body = res.json()
    assert body["indicador"] == "tiempo_respuesta"
    assert body["valor_base"] == 120.0
    assert body["estado"] == "ACTIVA"


def test_1200_medicion_y_variacion(client: TestClient, auth_headers):
    created = client.post("/api/lineas-base", headers=auth_headers, json=_payload_base()).json()
    now = datetime.now(timezone.utc)
    med = client.post(
        f"/api/lineas-base/{created['id']}/mediciones",
        headers=auth_headers,
        json={
            "valor_posterior": 90.0,
            "periodo_inicio": _iso(now - timedelta(days=15)),
            "periodo_fin": _iso(now),
            "evidencia": {"nota": "post intervención"},
        },
    )
    assert med.status_code == 200
    comp = med.json()["comparacion"]
    assert comp["variacion_absoluta"] == -30.0
    assert comp["variacion_porcentual"] == -25.0
    assert comp["evaluacion"] == "MEJORA"
    assert comp["tipo_impacto"] == "CAMBIO_OBSERVADO"


def test_1200_mayor_es_mejor(lb_db):
    org_id, user_id = _admin(lb_db)
    now = datetime.now(timezone.utc)
    lb = svc.create_linea_base(
        lb_db,
        organization_id=org_id,
        user_id=user_id,
        indicador="recaudo",
        valor_base=1000,
        fecha_inicio_base=now - timedelta(days=30),
        fecha_fin_base=now - timedelta(days=1),
        direccion_indicador="MAYOR_ES_MEJOR",
    )
    med, impacto = svc.register_medicion(
        lb_db,
        lb,
        user_id=user_id,
        valor_posterior=1200,
        periodo_inicio=now - timedelta(days=7),
        periodo_fin=now,
    )
    lb_db.commit()
    assert impacto.evaluacion == "MEJORA"
    assert float(impacto.variacion_absoluta) == 200.0


def test_1200_menor_es_mejor(lb_db):
    org_id, user_id = _admin(lb_db)
    now = datetime.now(timezone.utc)
    lb = svc.create_linea_base(
        lb_db,
        organization_id=org_id,
        user_id=user_id,
        indicador="costo",
        valor_base=500,
        fecha_inicio_base=now - timedelta(days=30),
        fecha_fin_base=now - timedelta(days=1),
        direccion_indicador="MENOR_ES_MEJOR",
    )
    _, impacto = svc.register_medicion(
        lb_db,
        lb,
        user_id=user_id,
        valor_posterior=600,
        periodo_inicio=now - timedelta(days=7),
        periodo_fin=now,
    )
    lb_db.commit()
    assert impacto.evaluacion == "DETERIORO"


def test_1200_informativo(lb_db):
    org_id, user_id = _admin(lb_db)
    now = datetime.now(timezone.utc)
    lb = svc.create_linea_base(
        lb_db,
        organization_id=org_id,
        user_id=user_id,
        indicador="volumen",
        valor_base=100,
        fecha_inicio_base=now - timedelta(days=30),
        fecha_fin_base=now - timedelta(days=1),
        direccion_indicador="INFORMATIVO",
    )
    _, impacto = svc.register_medicion(
        lb_db,
        lb,
        user_id=user_id,
        valor_posterior=110,
        periodo_inicio=now - timedelta(days=7),
        periodo_fin=now,
    )
    lb_db.commit()
    assert impacto.evaluacion == "INFORMATIVO"


def test_1200_impacto_esperado_vs_real(client: TestClient, auth_headers):
    created = client.post("/api/lineas-base", headers=auth_headers, json=_payload_base(impacto_esperado=40)).json()
    now = datetime.now(timezone.utc)
    med = client.post(
        f"/api/lineas-base/{created['id']}/mediciones",
        headers=auth_headers,
        json={
            "valor_posterior": 80.0,
            "periodo_inicio": _iso(now - timedelta(days=10)),
            "periodo_fin": _iso(now),
            "evidencia": {"doc": "informe"},
        },
    ).json()
    medicion_id = med["medicion"]["id"]
    validated = client.post(
        f"/api/lineas-base/{created['id']}/mediciones/{medicion_id}/validar",
        headers=auth_headers,
    )
    assert validated.status_code == 200
    impacto = validated.json()["impacto"]
    assert impacto["impacto_esperado"] == 40.0
    assert impacto["impacto_real"] == -40.0
    assert impacto["tipo_impacto"] == "IMPACTO_REAL"
    assert impacto["congelado"] is True


def test_1200_atribucion(client: TestClient, auth_headers):
    created = client.post("/api/lineas-base", headers=auth_headers, json=_payload_base()).json()
    now = datetime.now(timezone.utc)
    med = client.post(
        f"/api/lineas-base/{created['id']}/mediciones",
        headers=auth_headers,
        json={
            "valor_posterior": 95.0,
            "periodo_inicio": _iso(now - timedelta(days=5)),
            "periodo_fin": _iso(now),
            "evidencia": {"k": 1},
        },
    ).json()
    medicion_id = med["medicion"]["id"]
    attr = client.patch(
        f"/api/lineas-base/{created['id']}/mediciones/{medicion_id}/atribucion",
        headers=auth_headers,
        json={
            "atribucion_nivel": "PARCIALMENTE_ATRIBUIBLE",
            "atribucion_porcentaje": 60,
            "justificacion": "Evidencia parcial",
            "evidencia": {"fuente": "manual"},
        },
    )
    assert attr.status_code == 200
    assert attr.json()["atribucion_nivel"] == "PARCIALMENTE_ATRIBUIBLE"


def test_1200_oportunidad_vinculo(client: TestClient, auth_headers, lb_db):
    from app.services import proactive_service as psvc

    org_id, user_id = _admin(lb_db)
    result = psvc.run_proactive_pipeline(
        lb_db,
        organization_id=org_id,
        tipo="financiera",
        dominio="financiero",
        evento="lb_1200",
        payload={
            "titulo": "Oportunidad LB",
            "indicadores": {"x": 1},
            "source_reference": f"lb-{uuid.uuid4().hex[:8]}",
        },
        user_id=user_id,
    )
    lb_db.commit()
    opp_id = result["opportunity_id"]
    payload = _payload_base(opportunity_id=opp_id)
    res = client.post("/api/lineas-base", headers=auth_headers, json=payload)
    assert res.status_code == 200
    listed = client.get(f"/api/lineas-base/oportunidad/{opp_id}", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1


def test_1200_historial(lb_db):
    org_id, user_id = _admin(lb_db)
    now = datetime.now(timezone.utc)
    lb = svc.create_linea_base(
        lb_db,
        organization_id=org_id,
        user_id=user_id,
        indicador="kpi",
        valor_base=10,
        fecha_inicio_base=now - timedelta(days=30),
        fecha_fin_base=now - timedelta(days=1),
    )
    svc.register_medicion(
        lb_db,
        lb,
        user_id=user_id,
        valor_posterior=8,
        periodo_inicio=now - timedelta(days=7),
        periodo_fin=now,
    )
    lb_db.commit()
    hist = svc.get_historial(lb_db, lb.id, org_id)
    acciones = [h["accion"] for h in hist]
    assert "LINEA_BASE_CREADA" in acciones
    assert "MEDICION_REGISTRADA" in acciones


def test_1200_cross_tenant(client: TestClient, auth_headers, lb_db):
    org_b = Organization(name=f"OrgB-1200-{uuid.uuid4().hex[:6]}")
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    db.add(org_b)
    db.commit()
    now = datetime.now(timezone.utc)
    lb = svc.create_linea_base(
        db,
        organization_id=org_b.id,
        user_id=None,
        indicador="secreto",
        valor_base=1,
        fecha_inicio_base=now - timedelta(days=10),
        fecha_fin_base=now - timedelta(days=1),
    )
    db.commit()
    res = client.get(f"/api/lineas-base/{lb.id}", headers=auth_headers)
    assert res.status_code == 404
    db.close()


def test_1200_rbac_viewer(client: TestClient, lb_db):
    org_id, _ = _admin(lb_db)
    viewer = User(
        username=f"viewer-1200-{uuid.uuid4().hex[:6]}",
        email=f"v1200-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Viewer2026*"),
        organization_id=org_id,
        role="viewer",
        is_active=True,
    )
    lb_db.add(viewer)
    lb_db.commit()
    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "Viewer2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/lineas-base", headers=headers).status_code == 200
    denied = client.post("/api/lineas-base", headers=headers, json=_payload_base())
    assert denied.status_code == 403


def test_1200_empresa_inactiva(client: TestClient, auth_headers, lb_db):
    org_id, _ = _admin(lb_db)
    org = lb_db.query(Organization).filter(Organization.id == org_id).first()
    org.status = ORG_STATUS_INACTIVE
    lb_db.commit()
    res = client.get("/api/lineas-base", headers=auth_headers)
    assert res.status_code == 403


def test_1200_auditoria(client: TestClient, auth_headers, lb_db):
    from app.models import AuditLog

    before = lb_db.query(AuditLog).filter(AuditLog.action == "linea_base.creada").count()
    client.post("/api/lineas-base", headers=auth_headers, json=_payload_base(indicador="audit_test"))
    lb_db.expire_all()
    after = lb_db.query(AuditLog).filter(AuditLog.action == "linea_base.creada").count()
    assert after > before


def test_1200_calculo_unitario():
    abs_var, pct = svc.calculate_variation(100, 125)
    assert abs_var == 25
    assert pct == 25.0
    assert svc.evaluate_direction("MAYOR_ES_MEJOR", 100, 125) == "MEJORA"
    assert svc.evaluate_direction("MENOR_ES_MEJOR", 100, 125) == "DETERIORO"
    assert svc.evaluate_direction("INFORMATIVO", 100, 125) == "INFORMATIVO"
