"""Espacio externo controlado V1 — empresa/prospecto/cliente."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.espacio_externo_models import EntidadEmpresaAcceso
from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.tenant, pytest.mark.evaluacion]


def _create_expediente(client: TestClient, headers: dict[str, str]) -> dict:
    res = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Eval prospecto externo",
            "entidad_nombre": "Prospecto ACME",
            "nivel": "PRELIMINAR",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _setup_entidad_y_externo(client: TestClient, admin_headers: dict[str, str]) -> tuple[dict, dict, dict]:
    exp = _create_expediente(client, admin_headers)
    ent = client.post(
        "/api/espacio-externo/entidades",
        headers=admin_headers,
        json={"expediente_id": exp["id"], "contacto_email": "contacto@acme.test"},
    )
    assert ent.status_code == 201, ent.text
    ent_body = ent.json()
    entidad_id = ent_body["entidad"]["id"]
    invite = client.post(
        f"/api/espacio-externo/entidades/{entidad_id}/accesos",
        headers=admin_headers,
        json={
            "email": f"prospecto-{uuid.uuid4().hex[:6]}@acme.test",
            "full_name": "Contacto ACME",
            "password": "Prospecto2026!",
        },
    )
    assert invite.status_code == 201, invite.text
    login = client.post(
        "/api/auth/login",
        json={"username": invite.json()["username"], "password": "Prospecto2026!"},
    )
    assert login.status_code == 200, login.text
    ext_headers = auth_header(login.json()["access_token"])
    return exp, ent_body, ext_headers


def test_crear_entidad_sin_duplicar(client: TestClient, auth_headers):
    exp = _create_expediente(client, auth_headers)
    r1 = client.post(
        "/api/espacio-externo/entidades",
        headers=auth_headers,
        json={"expediente_id": exp["id"]},
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/espacio-externo/entidades",
        headers=auth_headers,
        json={"expediente_id": exp["id"]},
    )
    assert r2.status_code == 201
    assert r2.json()["reused"] is True


def test_aislamiento_tenant_entidad(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        other_org = Organization(name="Otra Org", slug=f"otra-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(other_org)
        db.flush()
        other_user = User(
            organization_id=other_org.id,
            username=f"other-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("x"),
            role="admin",
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        other_headers = auth_header(
            client.post("/api/auth/login", json={"username": other_user.username, "password": "x"}).json()["access_token"]
        )
    finally:
        db.close()

    exp = _create_expediente(client, auth_headers)
    ent = client.post(
        "/api/espacio-externo/entidades",
        headers=auth_headers,
        json={"expediente_id": exp["id"]},
    ).json()
    entidad_id = ent["entidad"]["id"]
    forbidden = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=other_headers)
    assert forbidden.status_code in (403, 404)


def test_acceso_prospecto_portal(client: TestClient, auth_headers):
    _exp, _ent, ext_headers = _setup_entidad_y_externo(client, auth_headers)
    ctx = client.get("/api/espacio-externo/mi-espacio/inicio", headers=ext_headers)
    assert ctx.status_code == 200
    body = ctx.json()
    assert body["estado_relacion"] == "PROSPECTO_EVALUACION"
    assert "secciones" in body


def test_publicacion_bloquea_vista_sin_publicar(client: TestClient, auth_headers):
    exp, ent, ext_headers = _setup_entidad_y_externo(client, auth_headers)
    hall = client.post(
        f"/api/evaluaciones/{exp['id']}/evaluar",
        headers=auth_headers,
    )
    assert hall.status_code == 200
    vista_blocked = client.get(
        "/api/espacio-externo/mi-espacio/vista-entidad?paquete=RESULTADOS",
        headers=ext_headers,
    )
    assert vista_blocked.status_code == 403


def test_publicacion_y_vista_entidad(client: TestClient, auth_headers):
    exp, ent, ext_headers = _setup_entidad_y_externo(client, auth_headers)
    eval_res = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    assert eval_res.status_code == 200
    hallazgo = eval_res.json()["expediente"]["hallazgos"][0]
    client.post(
        f"/api/evaluaciones/{exp['id']}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": hallazgo["id"], "visible_entidad": True},
    )
    entidad_id = ent["entidad"]["id"]
    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()
    pub_resultados = next(p for p in detail["publicaciones"] if p["paquete"] == "RESULTADOS")
    # Crear publicación RESULTADOS si no existe
    if not pub_resultados:
        pytest.skip("Paquete RESULTADOS no inicializado")
    pub_id = pub_resultados["id"]
    client.patch(
        f"/api/espacio-externo/publicaciones/{pub_id}/estado",
        headers=auth_headers,
        json={"estado": "PREPARADO_PRESENTAR"},
    )
    pub = client.patch(
        f"/api/espacio-externo/publicaciones/{pub_id}/estado",
        headers=auth_headers,
        json={"estado": "PUBLICADO_EMPRESA", "destinatario": "contacto@acme.test"},
    )
    assert pub.status_code == 200
    vista = client.get(
        "/api/espacio-externo/mi-espacio/vista-entidad?paquete=RESULTADOS",
        headers=ext_headers,
    )
    assert vista.status_code == 200
    vista_body = vista.json()
    assert "notas_internas" not in str(vista_body)
    assert "valor_potencial" not in str(vista_body.get("vista", {}))


def test_entrega_y_validacion_informacion(client: TestClient, auth_headers):
    exp, _ent, ext_headers = _setup_entidad_y_externo(client, auth_headers)
    client.post(f"/api/evaluaciones/{exp['id']}/informacion/sync", headers=auth_headers)
    detail = client.get(f"/api/evaluaciones/{exp['id']}", headers=auth_headers).json()
    item = detail["informacion"][0]
    entrega = client.post(
        "/api/espacio-externo/mi-espacio/entregas",
        headers=ext_headers,
        json={"item_id": item["id"], "contenido": "Respuesta empresa prospecto", "fuente_tipo": "SUMINISTRADA_EMPRESA"},
    )
    assert entrega.status_code == 201
    assert entrega.json()["estado"] == "RECIBIDO"
    entrega_id = entrega.json()["id"]
    val = client.post(
        f"/api/espacio-externo/entregas/{entrega_id}/validar",
        headers=auth_headers,
        json={"estado": "VALIDADO", "marcar_suficiencia": True},
    )
    assert val.status_code == 200
    assert val.json()["suficiencia_minima_at"] is not None


def test_promover_prospecto_a_cliente_misma_entidad(client: TestClient, auth_headers):
    _exp, ent, ext_headers = _setup_entidad_y_externo(client, auth_headers)
    entidad_id = ent["entidad"]["id"]
    promo = client.post(
        f"/api/espacio-externo/entidades/{entidad_id}/promover-cliente",
        headers=auth_headers,
        json={"contrato_ref": "CTR-2026-001"},
    )
    assert promo.status_code == 200
    assert promo.json()["estado_relacion"] == "CLIENTE_CONTRATADO"
    assert promo.json()["contrato_ref"] == "CTR-2026-001"
    ctx = client.get("/api/espacio-externo/mi-espacio/inicio", headers=ext_headers)
    assert ctx.json()["estado_relacion"] == "CLIENTE_CONTRATADO"


def test_revocar_acceso_externo(client: TestClient, auth_headers):
    _exp, ent, ext_headers = _setup_entidad_y_externo(client, auth_headers)
    entidad_id = ent["entidad"]["id"]
    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()
    acceso_id = detail["accesos"][0]["id"]
    rev = client.delete(f"/api/espacio-externo/accesos/{acceso_id}", headers=auth_headers)
    assert rev.status_code == 200
    blocked = client.get("/api/espacio-externo/mi-espacio/inicio", headers=ext_headers)
    assert blocked.status_code == 403


def test_externo_no_accede_finops(client: TestClient, auth_headers):
    _exp, _ent, ext_headers = _setup_entidad_y_externo(client, auth_headers)
    finops = client.get("/api/finops/dashboard", headers=ext_headers)
    assert finops.status_code == 403
