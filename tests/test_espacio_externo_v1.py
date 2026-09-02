"""Espacio externo controlado V1 — empresa/prospecto/cliente."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.communications_models import CommMessage
from app.models import Organization, User
from app.orchestration_models import AIEmployee
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


def _setup_entidad_y_externo(client: TestClient, admin_headers: dict[str, str]) -> tuple[dict, dict, dict, str]:
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
    return exp, ent_body, ext_headers, entidad_id


def _publicar_paquete(client: TestClient, admin_headers: dict[str, str], entidad_id: str, paquete: str, *, audiencia: str | None = None) -> None:
    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=admin_headers).json()
    pub = next(p for p in detail["publicaciones"] if p["paquete"] == paquete)
    client.patch(
        f"/api/espacio-externo/publicaciones/{pub['id']}/estado",
        headers=admin_headers,
        json={"estado": "PREPARADO_PRESENTAR"},
    )
    payload: dict = {"estado": "PUBLICADO_EMPRESA", "destinatario": "contacto@acme.test"}
    if audiencia:
        payload["audiencia"] = audiencia
    res = client.patch(
        f"/api/espacio-externo/publicaciones/{pub['id']}/estado",
        headers=admin_headers,
        json=payload,
    )
    assert res.status_code == 200, res.text


def _promover_cliente(
    client: TestClient,
    admin_headers: dict[str, str],
    entidad_id: str,
    *,
    capacidades: list[str] | None = None,
) -> None:
    payload: dict = {"contrato_ref": "CTR-2026-001"}
    if capacidades:
        payload["capacidades"] = capacidades
    res = client.post(
        f"/api/espacio-externo/entidades/{entidad_id}/promover-cliente",
        headers=admin_headers,
        json=payload,
    )
    assert res.status_code == 200, res.text


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
    _exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    ctx = client.get("/api/espacio-externo/mi-espacio/inicio", headers=ext_headers)
    assert ctx.status_code == 200
    body = ctx.json()
    assert body["estado_relacion"] == "PROSPECTO_EVALUACION"
    assert "secciones" in body


def test_publicacion_bloquea_vista_sin_publicar(client: TestClient, auth_headers):
    exp, ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
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
    exp, ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
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
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
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
    _exp, ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    entidad_id = ent["entidad"]["id"]
    promo = client.post(
        f"/api/espacio-externo/entidades/{entidad_id}/promover-cliente",
        headers=auth_headers,
        json={"contrato_ref": "CTR-2026-001"},
    )
    assert promo.status_code == 200
    assert promo.json()["estado_relacion"] == "CLIENTE_CONTRATADO"
    assert promo.json()["contrato_ref"] == "CTR-2026-001"
    assert "RESULTADOS" in promo.json()["capacidades_contrato"]
    ctx = client.get("/api/espacio-externo/mi-espacio/inicio", headers=ext_headers)
    assert ctx.json()["estado_relacion"] == "CLIENTE_CONTRATADO"
    # Misma entidad, mismo usuario, sin duplicar org
    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()
    assert len(detail["accesos"]) == 1
    assert detail["accesos"][0]["activo"] is True


def test_promocion_conserva_entregas_y_publicacion(client: TestClient, auth_headers):
    exp, ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    client.post(f"/api/evaluaciones/{exp['id']}/informacion/sync", headers=auth_headers)
    item = client.get(f"/api/evaluaciones/{exp['id']}", headers=auth_headers).json()["informacion"][0]
    entrega = client.post(
        "/api/espacio-externo/mi-espacio/entregas",
        headers=ext_headers,
        json={"item_id": item["id"], "contenido": "Entrega previa promoción"},
    )
    assert entrega.status_code == 201
    _publicar_paquete(client, auth_headers, entidad_id, "RESULTADOS")
    _promover_cliente(client, auth_headers, entidad_id)
    info = client.get("/api/espacio-externo/mi-espacio/informacion", headers=ext_headers)
    assert any(e["contenido"] == "Entrega previa promoción" for e in info.json()["entregas"])
    vista = client.get("/api/espacio-externo/mi-espacio/vista-entidad?paquete=RESULTADOS", headers=ext_headers)
    assert vista.status_code == 200


def test_revocar_acceso_externo(client: TestClient, auth_headers):
    _exp, ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    entidad_id = ent["entidad"]["id"]
    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()
    acceso_id = detail["accesos"][0]["id"]
    rev = client.delete(f"/api/espacio-externo/accesos/{acceso_id}", headers=auth_headers)
    assert rev.status_code == 200
    blocked = client.get("/api/espacio-externo/mi-espacio/inicio", headers=ext_headers)
    assert blocked.status_code == 403
    # Dossier y acceso persisten para auditoría
    detail_after = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()
    assert detail_after["entidad"]["id"] == entidad_id
    assert detail_after["accesos"][0]["activo"] is False


def test_externo_no_accede_finops(client: TestClient, auth_headers):
    _exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    finops = client.get("/api/finops/dashboard", headers=ext_headers)
    assert finops.status_code == 403


def test_cliente_sin_contrato_implementacion(client: TestClient, auth_headers):
    _exp, _ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    _promover_cliente(client, auth_headers, entidad_id, capacidades=["RESULTADOS"])
    blocked = client.get("/api/espacio-externo/mi-espacio/implementacion", headers=ext_headers)
    assert blocked.status_code == 403


def test_cliente_implementacion_sin_economia(client: TestClient, auth_headers):
    _exp, _ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    proj = client.post(
        "/api/implementacion/proyectos",
        headers=auth_headers,
        json={"titulo": "Impl ACME"},
    )
    assert proj.status_code == 201
    proyecto_id = proj.json()["id"]
    client.post(
        f"/api/espacio-externo/entidades/{entidad_id}/link-proyecto",
        headers=auth_headers,
        json={"proyecto_id": proyecto_id},
    )
    _promover_cliente(
        client,
        auth_headers,
        entidad_id,
        capacidades=["IMPLEMENTACION", "RESULTADOS", "INFORMES", "SOPORTE"],
    )
    _publicar_paquete(client, auth_headers, entidad_id, "IMPLEMENTACION")
    res = client.get("/api/espacio-externo/mi-espacio/implementacion", headers=ext_headers)
    assert res.status_code == 200
    body = res.json()
    assert "margen" not in json.dumps(body).lower()
    assert "tco" not in json.dumps(body).lower()
    assert body["implementacion"]["avance_pct"] is not None


def test_cliente_empleados_ia_sin_secretos(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_id = db.query(User).filter(User.username == "admin").first().organization_id
        emp = AIEmployee(
            organization_id=org_id,
            code=f"EXT-{uuid.uuid4().hex[:6]}",
            name="Asistente ACME",
            specialty="Soporte",
            lifecycle_status="PRODUCTION",
            objective="Atención cliente",
            status="DISPONIBLE",
        )
        db.add(emp)
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    _exp, _ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    client.patch(
        f"/api/espacio-externo/entidades/{entidad_id}/contrato",
        headers=auth_headers,
        json={
            "capacidades": ["EMPLEADOS_IA", "RESULTADOS", "INFORMES", "SOPORTE"],
            "empleados_ia_ids": [emp_id],
        },
    )
    _promover_cliente(client, auth_headers, entidad_id)
    _publicar_paquete(client, auth_headers, entidad_id, "EMPLEADOS_IA")
    res = client.get("/api/espacio-externo/mi-espacio/empleados-ia", headers=ext_headers)
    assert res.status_code == 200
    payload = json.dumps(res.json())
    assert "instructions" not in payload.lower()
    assert "password" not in payload.lower()
    assert any(e["nombre"] == "Asistente ACME" for e in res.json()["empleados"])


def test_empleado_ia_otra_organizacion(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        other_org = Organization(name="Org IA", slug=f"ia-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(other_org)
        db.flush()
        foreign = AIEmployee(
            organization_id=other_org.id,
            code="FOREIGN-1",
            name="Empleado ajeno",
            specialty="X",
            lifecycle_status="PRODUCTION",
            status="DISPONIBLE",
        )
        db.add(foreign)
        db.commit()
        foreign_id = foreign.id
    finally:
        db.close()

    _exp, _ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    client.patch(
        f"/api/espacio-externo/entidades/{entidad_id}/contrato",
        headers=auth_headers,
        json={"capacidades": ["EMPLEADOS_IA", "RESULTADOS", "INFORMES", "SOPORTE"]},
    )
    _promover_cliente(client, auth_headers, entidad_id)
    _publicar_paquete(client, auth_headers, entidad_id, "EMPLEADOS_IA")
    blocked = client.get(f"/api/espacio-externo/mi-espacio/empleados-ia/{foreign_id}", headers=ext_headers)
    assert blocked.status_code in (403, 404)


def test_informe_no_publicado(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        org_id = admin.organization_id
        msg = CommMessage(
            organization_id=org_id,
            estado="BORRADOR",
            tipo_comunicacion="INFORME_MENSUAL",
            destinatario_tipo="EXTERNO",
            destinatario_externo="contacto@acme.test",
            contenido="Informe confidencial",
            asunto="Informe Q1",
        )
        db.add(msg)
        db.commit()
        msg_id = msg.id
    finally:
        db.close()

    _exp, _ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    _promover_cliente(client, auth_headers, entidad_id)
    _publicar_paquete(client, auth_headers, entidad_id, "INFORMES", audiencia="GERENCIA")
    blocked = client.get(f"/api/espacio-externo/mi-espacio/informes/{msg_id}", headers=ext_headers)
    assert blocked.status_code == 403


def test_soporte_otro_solicitante(client: TestClient, auth_headers):
    _exp, _ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    _promover_cliente(client, auth_headers, entidad_id)
    _publicar_paquete(client, auth_headers, entidad_id, "SOPORTE")
    caso = client.post(
        "/api/soporte/casos",
        headers=auth_headers,
        json={"asunto": "Caso interno", "descripcion": "Solo staff", "tipo": "SOLICITUD"},
    )
    assert caso.status_code == 201
    blocked = client.get(f"/api/espacio-externo/mi-espacio/soporte/casos/{caso.json()['id']}", headers=ext_headers)
    assert blocked.status_code == 403


def test_cliente_soporte_crear_y_listar(client: TestClient, auth_headers):
    _exp, _ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    _promover_cliente(client, auth_headers, entidad_id)
    _publicar_paquete(client, auth_headers, entidad_id, "SOPORTE")
    created = client.post(
        "/api/espacio-externo/mi-espacio/soporte/casos",
        headers=ext_headers,
        json={"asunto": "Ayuda portal", "descripcion": "No veo informes"},
    )
    assert created.status_code == 201
    listed = client.get("/api/espacio-externo/mi-espacio/soporte", headers=ext_headers)
    assert listed.status_code == 200
    assert any(c["asunto"] == "Ayuda portal" for c in listed.json()["casos"])


def test_publicacion_audiencia_unica_version(client: TestClient, auth_headers):
    _exp, _ent, _ext, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()
    pub = next(p for p in detail["publicaciones"] if p["paquete"] == "INFORMES")
    res = client.patch(
        f"/api/espacio-externo/publicaciones/{pub['id']}/estado",
        headers=auth_headers,
        json={"estado": "PUBLICADO_EMPRESA", "destinatario": "cfo@acme.test", "audiencia": "FINANCIERO"},
    )
    assert res.status_code == 200
    assert res.json()["audiencia"] == "FINANCIERO"
    assert res.json()["version"] >= 1
