"""BLOQUE PRODUCTO 1 — Expediente de evaluación EIAAX."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.evaluacion_models import EvaluacionHallazgo
from app.models import Organization, User
from app.security import hash_password
from app.services import evaluacion_service as svc

pytestmark = [pytest.mark.evaluacion]


@pytest.fixture
def eval_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _admin(db: Session) -> tuple[str, str]:
    user = db.query(User).filter(User.username == "admin").first()
    assert user
    return user.organization_id, user.id


def _create_expediente(client: TestClient, headers: dict[str, str]) -> dict:
    res = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Evaluación proceso cobranza",
            "entidad_nombre": "Cliente Demo SA",
            "necesidad": "Alta mora en cartera",
            "objetivo": "Reducir días de mora en 30%",
            "area_proceso": "Finanzas / Cobranza",
            "nivel": "PRELIMINAR",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_bloque1_crear_expediente_con_informacion_adaptativa(client: TestClient, auth_headers, eval_db):
    body = _create_expediente(client, auth_headers)
    assert body["codigo"].startswith("EVA-")
    assert body["entidad_nombre"] == "Cliente Demo SA"
    assert len(body["informacion"]) >= 3
    assert body["porcentaje_informacion"] >= 0


def test_bloque1_evaluacion_preliminar_genera_hallazgos(client: TestClient, auth_headers, eval_db):
    exp = _create_expediente(client, auth_headers)
    item = next(i for i in exp["informacion"] if i["campo"] == "contexto_negocio")
    client.patch(
        f"/api/evaluaciones/{exp['id']}/informacion/{item['id']}",
        headers=auth_headers,
        json={"respuesta": "Empresa de servicios B2B, 200 empleados"},
    )
    res = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["hallazgos_creados"] >= 1
    hallazgos = data["expediente"]["hallazgos"]
    assert any(h["es_problema_original"] for h in hallazgos)


def test_bloque1_visibilidad_backend_y_vista_entidad(client: TestClient, auth_headers, eval_db):
    exp = _create_expediente(client, auth_headers)
    eval_res = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    hallazgo = eval_res.json()["expediente"]["hallazgos"][0]

    vis = client.post(
        f"/api/evaluaciones/{exp['id']}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": hallazgo["id"], "visible_entidad": True},
    )
    assert vis.status_code == 200
    assert vis.json()["visible_entidad"] is True

    vista = client.get(f"/api/evaluaciones/{exp['id']}/vista-entidad", headers=auth_headers)
    assert vista.status_code == 200
    vista_body = vista.json()
    assert "notas_internas" not in vista_body
    assert "valor_potencial" not in vista_body or vista_body.get("valor_potencial") is None
    visible_titles = [h["titulo"] for h in vista_body.get("hallazgos", [])]
    assert hallazgo["titulo"] in visible_titles

    trace = client.get(f"/api/evaluaciones/{exp['id']}/trazabilidad", headers=auth_headers)
    assert trace.status_code == 200
    assert len(trace.json()["visibilidad"]) >= 1


def test_bloque1_multitenant_aislamiento(client: TestClient, auth_headers, eval_db):
    exp_a = _create_expediente(client, auth_headers)

    org_b = Organization(
        id=str(uuid.uuid4()),
        name="Org B Eval",
        slug=f"evb-{uuid.uuid4().hex[:8]}",
    )
    eval_db.add(org_b)
    user_b = User(
        id=str(uuid.uuid4()),
        organization_id=org_b.id,
        username=f"userb_{uuid.uuid4().hex[:6]}",
        email=f"userb_{uuid.uuid4().hex[:6]}@test.local",
        password_hash=hash_password("testpass123"),
        is_active=True,
    )
    eval_db.add(user_b)
    eval_db.flush()

    from app.models import Permission, Role, RolePermission
    from app.seed_permissions import bootstrap_permissions

    bootstrap_permissions(eval_db)
    admin_role = (
        eval_db.query(Role)
        .filter(Role.organization_id == org_b.id, Role.code == "admin")
        .first()
    )
    if not admin_role:
        admin_role = Role(organization_id=org_b.id, code="admin", name="Administrador", is_system=True)
        eval_db.add(admin_role)
        eval_db.flush()
    for code in ("evaluacion.view", "evaluacion.manage", "evaluacion.evaluate", "evaluacion.visibility", "evaluacion.vista_entidad"):
        perm = eval_db.query(Permission).filter(Permission.code == code).first()
        if perm and not eval_db.query(RolePermission).filter(RolePermission.role_id == admin_role.id, RolePermission.permission_id == perm.id).first():
            eval_db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
    user_b.role = "admin"
    eval_db.commit()

    login_b = client.post("/api/auth/login", json={"username": user_b.username, "password": "testpass123"})
    assert login_b.status_code == 200
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    forbidden = client.get(f"/api/evaluaciones/{exp_a['id']}", headers=headers_b)
    assert forbidden.status_code == 404

    exp_b = client.post(
        "/api/evaluaciones",
        headers=headers_b,
        json={"titulo": "Eval B", "entidad_nombre": "Entidad B", "nivel": "PRELIMINAR"},
    )
    assert exp_b.status_code == 201
    assert exp_b.json()["entidad_nombre"] == "Entidad B"


def test_bloque1_preguntar_sin_proveedor_estado_controlado(client: TestClient, auth_headers, eval_db):
    exp = _create_expediente(client, auth_headers)
    res = client.post(
        f"/api/evaluaciones/{exp['id']}/preguntar",
        headers=auth_headers,
        json={"mensaje": "¿Qué falta?", "accion": "informacion_faltante"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["estado"] in ("sin_proveedor", "ok")
    if body["estado"] == "sin_proveedor":
        assert body["respuesta"] is None
        assert "proveedor" in body["mensaje"].lower()


def test_bloque1_rbac_sin_permiso(client: TestClient, eval_db):
    org_id, _ = _admin(eval_db)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        username=f"noview_{uuid.uuid4().hex[:6]}",
        email=f"noview_{uuid.uuid4().hex[:6]}@test.local",
        password_hash=hash_password("testpass123"),
        is_active=True,
        role="viewer",
    )
    eval_db.add(user)
    eval_db.commit()
    login = client.post("/api/auth/login", json={"username": user.username, "password": "testpass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.get("/api/evaluaciones", headers=headers)
    assert res.status_code == 403


def test_bloque1_e2e_recorrido_completo(client: TestClient, auth_headers, eval_db):
    """Recorrido: crear → info parcial → evaluar → visibilidad → vista entidad."""
    exp = _create_expediente(client, auth_headers)
    for item in exp["informacion"][:2]:
        client.patch(
            f"/api/evaluaciones/{exp['id']}/informacion/{item['id']}",
            headers=auth_headers,
            json={"respuesta": f"Respuesta test {item['campo']}"},
        )
    eval_res = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    assert eval_res.status_code == 200
    hallazgos = eval_res.json()["expediente"]["hallazgos"]
    assert hallazgos

    h = hallazgos[0]
    client.post(
        f"/api/evaluaciones/{exp['id']}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": h["id"], "visible_entidad": True},
    )
    vista = client.get(f"/api/evaluaciones/{exp['id']}/vista-entidad", headers=auth_headers).json()
    assert len(vista.get("hallazgos", [])) >= 1

    impacto = client.get(f"/api/evaluaciones/{exp['id']}/impacto", headers=auth_headers)
    assert impacto.status_code == 200
    assert "indicadores" in impacto.json()

    opp = client.post(
        f"/api/evaluaciones/{exp['id']}/oportunidades/crear",
        headers=auth_headers,
        json={"hallazgo_id": h["id"]},
    )
    assert opp.status_code == 201


def test_bloque1_servicio_persistencia(eval_db):
    org_id, user_id = _admin(eval_db)
    exp = svc.create_expediente(
        eval_db,
        organization_id=org_id,
        user_id=user_id,
        titulo="Test servicio",
        entidad_nombre="Entidad Svc",
        necesidad="Problema svc",
        nivel="DIAGNOSTICA",
    )
    eval_db.commit()
    loaded = svc._get_expediente(eval_db, exp.id, org_id)
    assert loaded.codigo.startswith("EVA-")
    items = eval_db.query(EvaluacionHallazgo).filter(EvaluacionHallazgo.expediente_id == exp.id).count()
    assert items == 0
    svc.ejecutar_evaluacion_preliminar(eval_db, exp.id, org_id, user_id=user_id)
    eval_db.commit()
    items = eval_db.query(EvaluacionHallazgo).filter(EvaluacionHallazgo.expediente_id == exp.id).count()
    assert items >= 1
