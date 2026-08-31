"""BLOQUE PRODUCTO 2 — capacidades externas, PIIAX prep, impacto, agente."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services.evaluacion_intent_service import classify_intent

pytestmark = [pytest.mark.evaluacion]


@pytest.fixture
def bp2_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _create_exp(client: TestClient, headers: dict) -> dict:
    res = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Eval BP2",
            "entidad_nombre": "Cliente BP2",
            "necesidad": "Necesidad analizar fuentes externas",
            "objetivo": "Integrar datos",
            "nivel": "DIAGNOSTICA",
        },
    )
    assert res.status_code == 201
    return res.json()


def test_bp2_catalogo_capacidades(client: TestClient, auth_headers):
    res = client.get("/api/evaluaciones/capacidades", headers=auth_headers)
    assert res.status_code == 200
    caps = res.json()["capacidades"]
    assert any(c["codigo"] == "consultar_datos" for c in caps)


def test_bp2_piiax_no_conectado(client: TestClient, auth_headers):
    res = client.get("/api/evaluaciones/integracion/piiax", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["disponible"] is False
    assert "PIIAX" in body["mensaje"]


def test_bp2_accion_externa_piiax_no_disponible(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    hall = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    assert hall.status_code == 200
    hallazgo_id = hall.json()["expediente"]["hallazgos"][0]["id"]

    crear = client.post(
        f"/api/evaluaciones/{exp['id']}/acciones",
        headers=auth_headers,
        json={
            "capacidad": "consultar_datos",
            "tipo_accion": "LECTURA",
            "titulo": "Analizar fuentes",
            "hallazgo_id": hallazgo_id,
            "solicitar": True,
        },
    )
    assert crear.status_code == 201
    accion = crear.json()
    assert accion["estado"] in ("PIIAX_NO_DISPONIBLE", "PENDIENTE_APROBACION", "SOLICITADA")
    assert accion["correlation_id"]


def test_bp2_aprobacion_ejecucion(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    crear = client.post(
        f"/api/evaluaciones/{exp['id']}/acciones",
        headers=auth_headers,
        json={
            "capacidad": "ejecutar_proceso",
            "tipo_accion": "EJECUCION",
            "titulo": "Ejecutar sincronización",
            "solicitar": False,
        },
    )
    assert crear.status_code == 201
    accion_id = crear.json()["id"]

    solicitar = client.post(
        f"/api/evaluaciones/{exp['id']}/acciones/{accion_id}/solicitar",
        headers=auth_headers,
    )
    assert solicitar.status_code == 200
    assert solicitar.json()["estado"] == "PENDIENTE_APROBACION"

    aprobar = client.post(
        f"/api/evaluaciones/{exp['id']}/acciones/{accion_id}/aprobar",
        headers=auth_headers,
        json={"aprobado": True},
    )
    assert aprobar.status_code == 200
    assert aprobar.json()["estado"] in ("PIIAX_NO_DISPONIBLE", "SOLICITADA")


def test_bp2_resultado_compatible(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    crear = client.post(
        f"/api/evaluaciones/{exp['id']}/acciones",
        headers=auth_headers,
        json={
            "capacidad": "consultar_datos",
            "tipo_accion": "LECTURA",
            "titulo": "Consulta test",
        },
    )
    accion_id = crear.json()["id"]
    res = client.post(
        f"/api/evaluaciones/{exp['id']}/acciones/{accion_id}/resultado",
        headers=auth_headers,
        json={
            "resultado_resumen": "Datos recibidos correctamente",
            "evidencia_ref": "ref-test-001",
            "estado": "COMPLETADA",
        },
    )
    assert res.status_code == 200
    assert res.json()["estado"] == "COMPLETADA"


def test_bp2_indicadores_impacto(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    crear = client.post(
        f"/api/evaluaciones/{exp['id']}/indicadores",
        headers=auth_headers,
        json={
            "nombre": "Días de mora",
            "unidad": "días",
            "valor_antes": "90",
            "valor_proyectado": "60",
            "valor_real": "45",
        },
    )
    assert crear.status_code == 201

    impacto = client.get(f"/api/evaluaciones/{exp['id']}/impacto", headers=auth_headers)
    assert impacto.status_code == 200
    body = impacto.json()
    assert body["tiene_graficos"] is True


def test_bp2_intencion_clasificacion():
    r_ext = classify_intent(
        "consultar datos del ERP externo",
        accion_sugerida=None,
        porcentaje_informacion=80,
        tiene_proveedor_llm=True,
        piiax_disponible=False,
        info_pendiente_count=0,
    )
    assert r_ext["intencion"] == "D"


def test_bp2_preguntar_intencion(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    res = client.post(
        f"/api/evaluaciones/{exp['id']}/preguntar",
        headers=auth_headers,
        json={"mensaje": "¿Qué información falta?", "accion": "informacion_faltante"},
    )
    assert res.status_code == 200
    assert res.json()["intencion"]["intencion"] in ("A", "B", "C", "D", "E", "F", "G", "H")


def test_bp2_intencion_g_oportunidad():
    r = classify_intent(
        "identificar oportunidad de mejora",
        accion_sugerida="identificar_oportunidades",
        porcentaje_informacion=70,
        tiene_proveedor_llm=True,
        piiax_disponible=False,
        info_pendiente_count=0,
    )
    assert r["intencion"] == "G"


def test_bp2_intencion_h_tarea():
    r = classify_intent(
        "asignar tarea de seguimiento al responsable",
        accion_sugerida=None,
        porcentaje_informacion=70,
        tiene_proveedor_llm=True,
        piiax_disponible=False,
        info_pendiente_count=0,
    )
    assert r["intencion"] == "H"


def test_bp2_motor_siguiente_accion(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    res = client.get(f"/api/evaluaciones/{exp['id']}/siguiente-accion", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "principal" in body
    assert body["principal"]["codigo"] in (
        "solicitar_informacion", "ejecutar_evaluacion", "continuar_evaluacion", "sin_accion",
    )


def test_bp2_proveedores_externos(client: TestClient, auth_headers):
    res = client.get("/api/evaluaciones/proveedores-externos", headers=auth_headers)
    assert res.status_code == 200
    provs = res.json()["proveedores"]
    assert any(p["codigo"] == "PIIAX" for p in provs)
    piiax = next(p for p in provs if p["codigo"] == "PIIAX")
    assert piiax["estado_es"] == "NO DISPONIBLE"


def test_bp2_estado_es_en_accion(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    crear = client.post(
        f"/api/evaluaciones/{exp['id']}/acciones",
        headers=auth_headers,
        json={
            "capacidad": "consultar_datos",
            "tipo_accion": "LECTURA",
            "titulo": "Estado ES test",
            "solicitar": True,
        },
    )
    assert crear.status_code == 201
    assert "estado_es" in crear.json()
    assert crear.json()["estado_es"] in ("NO DISPONIBLE", "EN COLA", "ESPERANDO APROBACION", "PENDIENTE")


def test_bp2_eiaax_sin_piiax_recorrido_interno(client: TestClient, auth_headers):
    """EIAAX funciona sin PIIAX: evaluación → hallazgo → oportunidad."""
    exp = _create_exp(client, auth_headers)
    ev = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    assert ev.status_code == 200
    hallazgos = ev.json()["expediente"]["hallazgos"]
    assert len(hallazgos) >= 1
    opp = client.post(
        f"/api/evaluaciones/{exp['id']}/oportunidades/crear",
        headers=auth_headers,
        json={"hallazgo_id": hallazgos[0]["id"]},
    )
    assert opp.status_code == 201
    assert opp.json().get("opportunity_id")


def test_bp2_trazabilidad_acciones(client: TestClient, auth_headers):
    exp = _create_exp(client, auth_headers)
    client.post(
        f"/api/evaluaciones/{exp['id']}/acciones",
        headers=auth_headers,
        json={"capacidad": "consultar_datos", "tipo_accion": "LECTURA", "titulo": "Trazabilidad test", "solicitar": True},
    )
    trace = client.get(f"/api/evaluaciones/{exp['id']}/trazabilidad", headers=auth_headers)
    assert trace.status_code == 200
    assert "acciones_externas" in trace.json()


def test_bp2_multitenant_acciones(client: TestClient, auth_headers, bp2_db):
    exp_a = _create_exp(client, auth_headers)
    org_b = Organization(id=str(uuid.uuid4()), name="Org BP2 B", slug=f"bp2b-{uuid.uuid4().hex[:8]}")
    bp2_db.add(org_b)
    user_b = User(
        id=str(uuid.uuid4()),
        organization_id=org_b.id,
        username=f"bp2b_{uuid.uuid4().hex[:6]}",
        email=f"bp2b_{uuid.uuid4().hex[:6]}@test.local",
        password_hash=hash_password("testpass123"),
        is_active=True,
        role="admin",
    )
    bp2_db.add(user_b)
    bp2_db.commit()
    from app.seed_permissions import bootstrap_permissions
    bootstrap_permissions(bp2_db)
    bp2_db.commit()

    login = client.post("/api/auth/login", json={"username": user_b.username, "password": "testpass123"})
    headers_b = {"Authorization": f"Bearer {login.json()['access_token']}"}
    forbidden = client.get(f"/api/evaluaciones/{exp_a['id']}/acciones", headers=headers_b)
    assert forbidden.status_code == 404
