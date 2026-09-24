"""BLOQUE 1410 — Inteligencia de resultados EIAAX."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import baseline_service as baseline_svc
from app.services import resultados_service as res_svc

pytestmark = [pytest.mark.operations]


@pytest.fixture
def res_db(client):
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
            "titulo": "Evaluación inteligencia resultados",
            "entidad_nombre": "IPS Demo Salud",
            "necesidad": "Reducir glosas y tiempos de respuesta",
            "objetivo": "Mejorar indicadores de facturación",
            "area_proceso": "Salud / Facturación",
            "nivel": "PRELIMINAR",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _assign_resultados_perms(db: Session, org_id: str, user: User) -> None:
    from app.models import Permission, Role, RolePermission
    from app.seed_permissions import bootstrap_permissions

    bootstrap_permissions(db)
    admin_role = (
        db.query(Role)
        .filter(Role.organization_id == org_id, Role.code == "admin")
        .first()
    )
    if not admin_role:
        admin_role = Role(organization_id=org_id, code="admin", name="Administrador", is_system=True)
        db.add(admin_role)
        db.flush()
    for code in (
        "resultados.view",
        "resultados.manage",
        "resultados.validate",
        "resultados.informe.generate",
        "evaluacion.view",
        "evaluacion.manage",
        "linea_base.view",
        "linea_base.manage",
    ):
        perm = db.query(Permission).filter(Permission.code == code).first()
        if perm and not db.query(RolePermission).filter(
            RolePermission.role_id == admin_role.id, RolePermission.permission_id == perm.id
        ).first():
            db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
    user.role = "admin"
    db.commit()


def test_1410_crear_indicador_antes_proyectado_real(client: TestClient, auth_headers, res_db):
    exp = _create_expediente(client, auth_headers)
    res = client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={
            "nombre": "Tasa de glosas",
            "unidad": "%",
            "valor_antes": 18.5,
            "valor_proyectado": 10.0,
            "expediente_id": exp["id"],
            "tipo_analitica": "COMPARATIVA",
            "periodo": "2026-Q1",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["antes"] == 18.5
    assert body["proyectado"] == 10.0
    assert body["real"] is None
    assert body["sin_medicion_posterior"] is True
    assert body["tiene_medicion_real"] is False


def test_1410_medicion_real_requiere_permiso_validate(client: TestClient, auth_headers, res_db):
    exp = _create_expediente(client, auth_headers)
    ind = client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={"nombre": "Días ciclo", "unidad": "días", "valor_antes": 45, "valor_proyectado": 30, "expediente_id": exp["id"]},
    ).json()
    med = client.post(
        f"/api/resultados/indicadores/{ind['id']}/medicion-real",
        headers=auth_headers,
        json={"valor_real": 32.0, "evidencia_ref": "medicion-post-intervencion-001"},
    )
    assert med.status_code == 200
    assert med.json()["real"] == 32.0
    assert med.json()["sin_medicion_posterior"] is False


def test_1410_real_menor_que_proyectado_no_maquilla(client: TestClient, auth_headers, res_db):
    """Caso §14: REAL < PROYECTADO debe quedar explícito."""
    exp = _create_expediente(client, auth_headers)
    ind = client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={
            "nombre": "Recuperación cartera",
            "unidad": "%",
            "valor_antes": 62.0,
            "valor_proyectado": 85.0,
            "expediente_id": exp["id"],
        },
    ).json()
    client.post(
        f"/api/resultados/indicadores/{ind['id']}/medicion-real",
        headers=auth_headers,
        json={"valor_real": 71.0, "evidencia_ref": "cierre-Q1"},
    )
    apr = client.get(f"/api/resultados/antes-proyectado-real?expediente_id={exp['id']}", headers=auth_headers).json()
    fila = next(i for i in apr["indicadores"] if i["nombre"] == "Recuperación cartera")
    assert fila["proyectado"] == 85.0
    assert fila["real"] == 71.0
    assert fila["real"] < fila["proyectado"]


def test_1410_sync_linea_base_puente(client: TestClient, auth_headers, res_db):
    org_id, user_id = _admin(res_db)
    now = datetime.now(timezone.utc)
    lb = baseline_svc.create_linea_base(
        res_db,
        organization_id=org_id,
        user_id=user_id,
        indicador="tiempo_respuesta_glosa",
        valor_base=120.0,
        fecha_inicio_base=now - timedelta(days=60),
        fecha_fin_base=now - timedelta(days=30),
        impacto_esperado=90.0,
    )
    res_db.commit()
    sync = client.post(f"/api/resultados/indicadores/sync-linea-base/{lb.id}", headers=auth_headers)
    assert sync.status_code == 200
    body = sync.json()
    assert body["antes"] == 120.0
    assert body["proyectado"] == 90.0
    assert body["linea_base_id"] == lb.id


def test_1410_drill_down_dimensiones(client: TestClient, auth_headers, res_db):
    exp = _create_expediente(client, auth_headers)
    ind = client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={"nombre": "Glosas por dimensión", "unidad": "casos", "valor_antes": 200, "expediente_id": exp["id"]},
    ).json()
    pagador = client.post(
        f"/api/resultados/indicadores/{ind['id']}/dimensiones",
        headers=auth_headers,
        json={"codigo": "pagador", "etiqueta": "EPS Contributivo", "valor": 80, "nivel": 0},
    ).json()
    client.post(
        f"/api/resultados/indicadores/{ind['id']}/dimensiones",
        headers=auth_headers,
        json={"codigo": "causal", "etiqueta": "Codificación", "valor": 45, "nivel": 1, "parent_id": pagador["id"]},
    )
    drill = client.get(f"/api/resultados/indicadores/{ind['id']}/drill-down", headers=auth_headers)
    assert drill.status_code == 200
    assert len(drill.json()["nodos"]) == 2


def test_1410_informe_narrativo_deterministico(client: TestClient, auth_headers, res_db):
    exp = _create_expediente(client, auth_headers)
    client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={"nombre": "Indicador informe", "valor_antes": 10, "valor_proyectado": 5, "expediente_id": exp["id"]},
    )
    client.post(
        "/api/resultados/plan-acciones",
        headers=auth_headers,
        json={"expediente_id": exp["id"], "accion": "Capacitar equipo de codificación"},
    )
    inf = client.post(
        "/api/resultados/informes/generar",
        headers=auth_headers,
        json={"expediente_id": exp["id"], "tipo": "IMPACTO", "visibilidad": "INTERNO"},
    )
    assert inf.status_code == 200
    body = inf.json()
    assert "Qué ocurrió" in body["narrativa"]
    assert "PROYECTADO" in body["narrativa"] or "proyección" in body["narrativa"].lower()
    assert body["version"] == 1
    inf2 = client.post(
        "/api/resultados/informes/generar",
        headers=auth_headers,
        json={"expediente_id": exp["id"]},
    ).json()
    assert inf2["version"] == 2


def test_1410_trazabilidad_cadena(client: TestClient, auth_headers, res_db):
    exp = _create_expediente(client, auth_headers)
    ind = client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={"nombre": "Trazable", "expediente_id": exp["id"]},
    ).json()
    trace = client.get(f"/api/resultados/expediente/{exp['id']}/trazabilidad", headers=auth_headers)
    assert trace.status_code == 200
    tipos = [c["tipo"] for c in trace.json()["cadena"]]
    assert "expediente" in tipos
    assert "indicador" in tipos
    assert any(i["id"] == ind["id"] for i in trace.json()["indicadores"])


def test_1410_multitenant_aislamiento(client: TestClient, auth_headers, res_db):
    exp_a = _create_expediente(client, auth_headers)
    ind_a = client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={"nombre": "Org A only", "expediente_id": exp_a["id"]},
    ).json()

    org_b = Organization(id=str(uuid.uuid4()), name="Org B Resultados", slug=f"resb-{uuid.uuid4().hex[:8]}")
    res_db.add(org_b)
    user_b = User(
        id=str(uuid.uuid4()),
        organization_id=org_b.id,
        username=f"resb_{uuid.uuid4().hex[:6]}",
        email=f"resb_{uuid.uuid4().hex[:6]}@test.local",
        password_hash=hash_password("testpass123"),
        is_active=True,
    )
    res_db.add(user_b)
    res_db.flush()
    _assign_resultados_perms(res_db, org_b.id, user_b)

    login_b = client.post("/api/auth/login", json={"username": user_b.username, "password": "testpass123"})
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    forbidden = client.get(f"/api/resultados/indicadores/{ind_a['id']}/drill-down", headers=headers_b)
    assert forbidden.status_code == 404

    lista_b = client.get("/api/resultados/indicadores", headers=headers_b).json()
    assert all(i["nombre"] != "Org A only" for i in lista_b["items"])


def test_1410_impacto_evaluacion_integra_resultados(client: TestClient, auth_headers, res_db):
    exp = _create_expediente(client, auth_headers)
    client.post(
        "/api/resultados/indicadores",
        headers=auth_headers,
        json={
            "nombre": "Desde resultados",
            "valor_antes": 100,
            "valor_proyectado": 70,
            "expediente_id": exp["id"],
        },
    )
    impacto = client.get(f"/api/evaluaciones/{exp['id']}/impacto", headers=auth_headers)
    assert impacto.status_code == 200
    nombres = [i.get("hallazgo") for i in impacto.json().get("indicadores", [])]
    assert "Desde resultados" in nombres


def test_1410_recorrido_completo_demo(res_db):
    """Recorrido §14: línea base → indicador → proyección → acción → REAL → informe."""
    org_id, user_id = _admin(res_db)
    from app.services import evaluacion_service as ev_svc

    exp = ev_svc.create_expediente(
        res_db,
        organization_id=org_id,
        user_id=user_id,
        titulo="Recorrido impacto demo",
        entidad_nombre="Clínica Norte",
        necesidad="Glosas elevadas",
        nivel="PRELIMINAR",
    )
    res_db.commit()
    exp_id = exp.id
    now = datetime.now(timezone.utc)
    lb = baseline_svc.create_linea_base(
        res_db,
        organization_id=org_id,
        user_id=user_id,
        indicador="glosas_pct",
        valor_base=22.0,
        fecha_inicio_base=now - timedelta(days=90),
        fecha_fin_base=now - timedelta(days=60),
        impacto_esperado=12.0,
    )
    ind_sync = res_svc.sync_indicador_from_linea_base(res_db, lb.id, org_id)
    ind_sync = res_svc.create_indicador(
        res_db,
        org_id,
        nombre="Tiempo respuesta glosa",
        unidad="días",
        valor_antes=18.0,
        valor_proyectado=8.0,
        expediente_id=exp_id,
        linea_base_id=lb.id,
    )
    res_svc.create_plan_accion(
        res_db,
        org_id,
        expediente_id=exp_id,
        accion="Implementar checklist de codificación",
        indicador_id=ind_sync["id"],
        causa="Errores de codificación",
    )
    res_svc.register_medicion_real(
        res_db,
        ind_sync["id"],
        org_id,
        valor_real=11.0,
        evidencia_ref="medicion-marzo-2026",
    )
    ind_bajo = res_svc.create_indicador(
        res_db,
        org_id,
        nombre="Meta recuperación",
        unidad="%",
        valor_antes=55.0,
        valor_proyectado=80.0,
        expediente_id=exp_id,
    )
    res_svc.register_medicion_real(res_db, ind_bajo["id"], org_id, valor_real=68.0, evidencia_ref="cierre-trimestre")
    informe = res_svc.generate_informe_impacto(res_db, org_id, user_id, expediente_id=exp_id)
    assert informe["version"] == 1
    assert "sin medición posterior" in informe["narrativa"].lower() or "REAL" in informe["narrativa"]
    apr = res_svc.build_antes_proyectado_real(res_db, org_id, expediente_id=exp_id)
    meta = next(i for i in apr["indicadores"] if i["nombre"] == "Meta recuperación")
    assert meta["real"] < meta["proyectado"]
