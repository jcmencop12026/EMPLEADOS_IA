"""Pruebas API de puesta en marcha — recorridos demo Lote 3 (seed_lote3_demo)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from conftest import auth_header

DEMO_DB_URL = "sqlite:////workspace/data/eiaax_integrado_demo.db"
PASSWORD_ORG_A = "DemoA2026!"
PASSWORD_ORG_B = "DemoB2026!"


def _require_demo_database() -> None:
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url != DEMO_DB_URL:
        pytest.skip(f"Requiere DATABASE_URL={DEMO_DB_URL}")


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return auth_header(res.json()["access_token"])


def _headers_org_a_admin(client: TestClient) -> dict[str, str]:
    return _login(client, "org_a_admin", PASSWORD_ORG_A)


def _headers_org_b_admin(client: TestClient) -> dict[str, str]:
    return _login(client, "org_b_admin", PASSWORD_ORG_B)


def _headers_org_a_viewer(client: TestClient) -> dict[str, str]:
    return _login(client, "org_a_viewer", PASSWORD_ORG_A)


def _first_expediente_id(client: TestClient, headers: dict[str, str]) -> str:
    listed = client.get("/api/evaluaciones", headers=headers)
    assert listed.status_code == 200, listed.text
    payload = listed.json()
    items = payload.get("items", payload)
    assert items, "Se esperaba al menos un expediente en Org A demo"
    return items[0]["id"]


def _first_propuesta_id(client: TestClient, headers: dict[str, str]) -> str:
    pipeline = client.get("/api/centro-negocios/pipeline", headers=headers)
    assert pipeline.status_code == 200, pipeline.text
    items = pipeline.json()
    assert items, "Se esperaba al menos una propuesta en Org A demo"
    return items[0]["id"]


@pytest.fixture
def demo_a_headers(client: TestClient) -> dict[str, str]:
    _require_demo_database()
    return _headers_org_a_admin(client)


def test_login_org_a_admin_and_org_b_admin(client: TestClient):
    _require_demo_database()
    ha = _headers_org_a_admin(client)
    hb = _headers_org_b_admin(client)
    me_a = client.get("/api/auth/me", headers=ha)
    me_b = client.get("/api/auth/me", headers=hb)
    assert me_a.status_code == 200
    assert me_b.status_code == 200
    assert me_a.json()["username"] == "org_a_admin"
    assert me_b.json()["username"] == "org_b_admin"
    assert me_a.json()["organization_id"] != me_b.json()["organization_id"]


def test_recorrido_a_evaluacion_centro_negocios_propuesta_detalle(client: TestClient, demo_a_headers):
    expediente_id = _first_expediente_id(client, demo_a_headers)
    propuesta_id = _first_propuesta_id(client, demo_a_headers)

    evaluacion = client.get(f"/api/evaluaciones/{expediente_id}", headers=demo_a_headers)
    assert evaluacion.status_code == 200, evaluacion.text
    eva_body = evaluacion.json()
    assert eva_body["codigo"].startswith("EVA-")
    assert eva_body["hallazgos"]

    centro = client.get("/api/centro-negocios/dashboard", headers=demo_a_headers)
    assert centro.status_code == 200, centro.text
    centro_body = centro.json()
    assert "propuestas_activas" in centro_body or "oportunidades_total" in centro_body

    detalle = client.get(f"/api/centro-negocios/propuestas/{propuesta_id}/detalle", headers=demo_a_headers)
    assert detalle.status_code == 200, detalle.text
    det_body = detalle.json()
    assert det_body.get("id") == propuesta_id or det_body.get("proposal_id") == propuesta_id
    negocio = det_body.get("negocio") or {}
    assert negocio.get("evaluacion_id") == expediente_id or det_body.get("evaluacion_id") == expediente_id


def test_recorrido_b_transformacion_dossier(client: TestClient, demo_a_headers):
    expediente_id = _first_expediente_id(client, demo_a_headers)

    dossier = client.get("/api/transformacion/dossier", headers=demo_a_headers)
    assert dossier.status_code == 200, dossier.text
    dossier_body = dossier.json()
    assert dossier_body.get("id") or dossier_body.get("etapa_actual")

    recorrido = client.get("/api/transformacion/recorrido", headers=demo_a_headers)
    assert recorrido.status_code == 200, recorrido.text
    rec_body = recorrido.json()
    assert rec_body.get("pasos") or rec_body.get("suficiencia")

    rec_exp = client.get(
        f"/api/transformacion/recorrido?expediente_id={expediente_id}",
        headers=demo_a_headers,
    )
    assert rec_exp.status_code == 200, rec_exp.text


def test_recorrido_c_gobierno_solicitud_approve_reject(client: TestClient, demo_a_headers):
    propuesta_id = _first_propuesta_id(client, demo_a_headers)

    reject_created = client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=demo_a_headers,
        json={
            "tipo_accion": "PROPUESTA",
            "recurso_tipo": "propuesta_comercial",
            "recurso_id": propuesta_id,
            "descripcion": "Solicitud demo para rechazo",
            "motivo_solicitud": "Flujo demo Lote 3 — rechazo",
            "criticidad": "LOW",
        },
    )
    assert reject_created.status_code == 201, reject_created.text
    reject_id = reject_created.json()["id"]
    assert reject_created.json()["estado"] == "PENDIENTE"

    rejected = client.post(
        f"/api/gobierno-operacional/solicitudes/{reject_id}/decidir",
        headers=demo_a_headers,
        json={"decision": "reject", "motivo": "Rechazado en prueba demo"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["estado"] == "RECHAZADA"

    approve_created = client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=demo_a_headers,
        json={
            "tipo_accion": "PROPUESTA",
            "recurso_tipo": "propuesta_comercial",
            "recurso_id": propuesta_id,
            "descripcion": "Solicitud demo para aprobación",
            "motivo_solicitud": "Flujo demo Lote 3 — aprobación",
            "criticidad": "MEDIUM",
        },
    )
    assert approve_created.status_code == 201, approve_created.text
    approve_id = approve_created.json()["id"]

    approved = client.post(
        f"/api/gobierno-operacional/solicitudes/{approve_id}/decidir",
        headers=demo_a_headers,
        json={"decision": "approve", "motivo": "Aprobado en prueba demo"},
    )
    assert approved.status_code == 200, approved.text
    final = approved.json()
    assert final["estado"] in ("APROBADA", "EJECUTADA")
    assert final["aprobado_por"] is not None


def test_recorrido_d_resultados_indicadores_antes_proyectado_real(client: TestClient, demo_a_headers):
    expediente_id = _first_expediente_id(client, demo_a_headers)

    apr = client.get(
        f"/api/resultados/antes-proyectado-real?expediente_id={expediente_id}",
        headers=demo_a_headers,
    )
    assert apr.status_code == 200, apr.text
    body = apr.json()
    indicadores = body.get("indicadores") or body
    assert isinstance(indicadores, list)
    assert indicadores, "Se esperaba indicador demo con medición real"
    fila = next(i for i in indicadores if i.get("nombre") == "Tiempo medio de aprobación")
    assert fila["antes"] == 48.0
    assert fila["proyectado"] == 24.0
    assert fila["real"] == 22.5


def test_recorrido_e_support_case_and_communications(client: TestClient, demo_a_headers):
    casos = client.get("/api/soporte/casos", headers=demo_a_headers)
    assert casos.status_code == 200, casos.text
    cases = casos.json()
    assert cases, "Se esperaba caso de soporte demo"
    caso = next(c for c in cases if "demo" in c.get("asunto", "").lower())
    assert caso["id"]

    detalle = client.get(f"/api/soporte/casos/{caso['id']}", headers=demo_a_headers)
    assert detalle.status_code == 200, detalle.text

    plantillas = client.get("/api/comunicaciones/plantillas", headers=demo_a_headers)
    assert plantillas.status_code == 200, plantillas.text
    assert plantillas.json(), "Se esperaban plantillas bootstrap demo"

    canales = client.get("/api/comunicaciones/canales", headers=demo_a_headers)
    assert canales.status_code == 200, canales.text
    assert canales.json()

    resumen = client.get("/api/comunicaciones/centro-informacion/resumen", headers=demo_a_headers)
    assert resumen.status_code == 200, resumen.text


def test_recorrido_g_org_b_cannot_read_org_a_expediente(client: TestClient, demo_a_headers):
    expediente_id = _first_expediente_id(client, demo_a_headers)
    headers_b = _headers_org_b_admin(client)

    forbidden = client.get(f"/api/evaluaciones/{expediente_id}", headers=headers_b)
    assert forbidden.status_code in (403, 404), forbidden.text


def test_vista_entidad_viewer_cannot_see_internal_economics(client: TestClient, demo_a_headers):
    expediente_id = _first_expediente_id(client, demo_a_headers)
    headers_viewer = _headers_org_a_viewer(client)

    admin_detail = client.get(f"/api/evaluaciones/{expediente_id}", headers=demo_a_headers)
    assert admin_detail.status_code == 200, admin_detail.text

    viewer_detail = client.get(f"/api/evaluaciones/{expediente_id}", headers=headers_viewer)
    assert viewer_detail.status_code in (403, 404), viewer_detail.text

    vista_admin = client.get(f"/api/evaluaciones/{expediente_id}/vista-entidad", headers=demo_a_headers)
    assert vista_admin.status_code == 200, vista_admin.text
    vista_body = vista_admin.json()
    assert "notas_internas" not in vista_body
    assert vista_body.get("valor_potencial") is None

    motor = client.get("/api/motor-economico/vista-entidad", headers=demo_a_headers)
    if motor.status_code == 200:
        motor_body = motor.json()
        assert motor_body.get("economia_privada_incluida") is False
        valores = motor_body.get("valores") or {}
        assert "valor_potencial" not in valores or valores.get("valor_potencial") is None
