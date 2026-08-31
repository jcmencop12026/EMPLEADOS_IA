"""Certificación Agente C — BP1 recorrido empresarial E2E (instrumentación)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, Permission, Role, RolePermission, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.evaluacion, pytest.mark.tenant]


def _create_expediente(client: TestClient, headers: dict[str, str], **extra) -> dict:
    payload = {
        "titulo": "Cert BP1 Cobranza",
        "entidad_nombre": "Entidad Cert SA",
        "necesidad": "Alta mora",
        "objetivo": "Reducir mora 30%",
        "area_proceso": "Finanzas",
        "nivel": "PRELIMINAR",
        **extra,
    }
    res = client.post("/api/evaluaciones", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_bp1_recorrido_empresarial_completo(client: TestClient, auth_headers):
    """ENTIDAD → ... → SIGUIENTE ACCIÓN (API runtime encadenado)."""
    # ENTIDAD + NECESIDAD + crear expediente
    exp = _create_expediente(client, auth_headers)
    exp_id = exp["id"]
    assert exp["entidad_nombre"] == "Entidad Cert SA"
    assert exp["necesidad"] == "Alta mora"

    # INFORMACIÓN adaptativa — estados RECIBIDO/PENDIENTE/INCOMPLETO
    info = exp["informacion"]
    assert len(info) >= 3
    estados = {i["estado"] for i in info}
    assert estados & {"PENDIENTE", "INCOMPLETO", "OPCIONAL", "RECIBIDO"}
    first = info[0]
    assert first.get("por_que") and first.get("explicacion")

    client.patch(
        f"/api/evaluaciones/{exp_id}/informacion/{first['id']}",
        headers=auth_headers,
        json={"respuesta": "Contexto parcial certificación"},
    )

    # EVALUACIÓN preliminar con info incompleta
    eval_res = client.post(f"/api/evaluaciones/{exp_id}/evaluar", headers=auth_headers)
    assert eval_res.status_code == 200
    expediente = eval_res.json()["expediente"]
    hallazgos = expediente["hallazgos"]
    assert hallazgos

    # HALLAZGO + problema original vs adicional
    assert any(h["es_problema_original"] for h in hallazgos)

    # IMPACTO — PROYECTADO etiquetado
    impacto = client.get(f"/api/evaluaciones/{exp_id}/impacto", headers=auth_headers).json()
    assert "PROYECTADO" in impacto.get("nota", "").upper() or impacto.get("indicadores") is not None

    # OPORTUNIDAD desde hallazgo
    h = hallazgos[0]
    opp = client.post(
        f"/api/evaluaciones/{exp_id}/oportunidades/crear",
        headers=auth_headers,
        json={"hallazgo_id": h["id"]},
    )
    assert opp.status_code == 201

    # VISIBILIDAD + VISTA ENTIDAD
    client.post(
        f"/api/evaluaciones/{exp_id}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": h["id"], "visible_entidad": True},
    )
    vista = client.get(f"/api/evaluaciones/{exp_id}/vista-entidad", headers=auth_headers).json()
    assert "notas_internas" not in vista
    visible = [x["titulo"] for x in vista.get("hallazgos", [])]
    assert h["titulo"] in visible

    client.post(
        f"/api/evaluaciones/{exp_id}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": h["id"], "visible_entidad": False},
    )
    vista2 = client.get(f"/api/evaluaciones/{exp_id}/vista-entidad", headers=auth_headers).json()
    assert h["titulo"] not in [x["titulo"] for x in vista2.get("hallazgos", [])]

    # PREGUNTAR EIAAX — sin proveedor controlado
    ask = client.post(
        f"/api/evaluaciones/{exp_id}/preguntar",
        headers=auth_headers,
        json={"mensaje": "¿Qué falta?", "accion": "informacion_faltante"},
    ).json()
    assert ask["estado"] in ("sin_proveedor", "ok")
    if ask["estado"] == "sin_proveedor":
        assert ask.get("respuesta") is None

    # CC + Mi Trabajo accesibles (regresión UX)
    assert client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers).status_code == 200
    assert client.get("/api/trabajo/items", headers=auth_headers).status_code == 200


def test_bp1_niveles_diagnostica_y_profunda(client: TestClient, auth_headers):
    for nivel in ("DIAGNOSTICA", "PROFUNDA"):
        exp = _create_expediente(client, auth_headers, titulo=f"Nivel {nivel}", nivel=nivel)
        campos = {i["campo"] for i in exp["informacion"]}
        assert len(campos) >= 3


def test_bp1_vista_entidad_multitenant_a_y_b(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a_id, _, user_a_name, pwd_a = _create_tenant_pair(db, "BP1 Org A")
        org_b_id, _, user_b_name, pwd_b = _create_tenant_pair(db, "BP1 Org B")
    finally:
        db.close()

    exp_a = client.post(
        "/api/evaluaciones",
        headers=_hdr(client, user_a_name, pwd_a),
        json={"titulo": "Eval A", "entidad_nombre": "Ent A", "nivel": "PRELIMINAR"},
    ).json()
    exp_b = client.post(
        "/api/evaluaciones",
        headers=_hdr(client, user_b_name, pwd_b),
        json={"titulo": "Eval B", "entidad_nombre": "Ent B", "nivel": "PRELIMINAR"},
    ).json()

    assert client.get(f"/api/evaluaciones/{exp_a['id']}", headers=_hdr(client, user_b_name, pwd_b)).status_code == 404
    assert client.get(f"/api/evaluaciones/{exp_b['id']}", headers=_hdr(client, user_a_name, pwd_a)).status_code == 404


def _hdr(client: TestClient, username: str, password: str) -> dict[str, str]:
    tok = client.post("/api/auth/login", json={"username": username, "password": password}).json()["access_token"]
    return auth_header(tok)


def _create_tenant_pair(db: Session, org_name: str):
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=org_name, slug=f"bp1-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    pwd = "Bp1Tenant*1"
    username = f"bp1-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(pwd),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.flush()
    from app.models import Permission, Role, RolePermission

    role = Role(organization_id=org.id, code="admin", name="Admin", is_system=True)
    db.add(role)
    db.flush()
    for code in (
        "evaluacion.view", "evaluacion.manage", "evaluacion.evaluate",
        "evaluacion.visibility", "evaluacion.vista_entidad",
    ):
        perm = db.query(Permission).filter(Permission.code == code).first()
        if perm:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.commit()
    return org.id, user.id, username, pwd
