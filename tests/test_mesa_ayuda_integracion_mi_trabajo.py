"""MB-12 — Integración Mesa de Ayuda con Mi Trabajo."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.notifications import emit_event
from app.security import hash_password
from app.services import support_service as svc
from app.support_models import SupportCase

pytestmark = [pytest.mark.operations]


@pytest.fixture
def sdb():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _tenant(db: Session) -> tuple[Organization, User, User, User]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-mt-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    admin = User(
        organization_id=org.id,
        username=f"adm-{uuid.uuid4().hex[:6]}",
        email=f"a-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    agent = User(
        organization_id=org.id,
        username=f"agt-{uuid.uuid4().hex[:6]}",
        email=f"g-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="operator",
        is_active=True,
    )
    viewer = User(
        organization_id=org.id,
        username=f"view-{uuid.uuid4().hex[:6]}",
        email=f"v-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="viewer",
        is_active=True,
    )
    db.add_all([admin, agent, viewer])
    db.commit()
    return org, admin, agent, viewer


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_case(db: Session, org_id: str, admin: User, **kwargs) -> dict:
    payload = {
        "tipo": "SOLICITUD",
        "asunto": kwargs.get("asunto", "Caso prueba"),
        "descripcion": kwargs.get("descripcion", "Detalle"),
        "prioridad": kwargs.get("prioridad", "MEDIA"),
        **{k: v for k, v in kwargs.items() if k not in ("asunto", "descripcion", "prioridad")},
    }
    return svc.create_case_manual(db, org_id, admin, payload)


def _trabajo_items(client: TestClient, headers: dict) -> list[dict]:
    return client.get("/api/trabajo/items", headers=headers).json()["items"]


def _soporte_items(items: list[dict]) -> list[dict]:
    return [i for i in items if i.get("modulo") == "soporte"]


def test_caso_nuevo_accionable_para_asignador(client: TestClient, sdb):
    _, admin, _, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    case = _create_case(sdb, admin.organization_id, admin, asunto="Nuevo sin asignar")
    items = _soporte_items(_trabajo_items(client, headers))
    match = [i for i in items if i["metadata"]["case_id"] == case["id"]]
    assert len(match) == 1
    assert match[0]["tipo"] == "soporte_asignacion"
    assert match[0]["enlace"] == f"/soporte/casos/{case['id']}"
    assert match[0]["metadata"]["origen"] == "Mesa de Ayuda"


def test_caso_asignado_aparece_responsable(client: TestClient, sdb):
    _, admin, agent, _ = _tenant(sdb)
    case = _create_case(sdb, admin.organization_id, admin, asunto="Asignado")
    svc.assign_case(sdb, admin.organization_id, case["id"], admin, responsable_id=agent.id)
    agent_headers = _login(client, agent.username)
    items = _soporte_items(_trabajo_items(client, agent_headers))
    assert any(i["metadata"]["case_id"] == case["id"] for i in items)
    assert all(i["responsable_id"] == agent.id or i["tipo"] == "soporte_asignacion" for i in items if i["metadata"]["case_id"] == case["id"])


def test_caso_en_proceso_aparece(client: TestClient, sdb):
    _, admin, agent, _ = _tenant(sdb)
    case = _create_case(sdb, admin.organization_id, admin)
    svc.assign_case(sdb, admin.organization_id, case["id"], admin, responsable_id=agent.id)
    svc.update_status(sdb, admin.organization_id, case["id"], admin, estado="EN_PROCESO")
    headers = _login(client, agent.username)
    row = next(i for i in _soporte_items(_trabajo_items(client, headers)) if i["metadata"]["case_id"] == case["id"])
    assert row["estado_dominio"] == "EN_PROCESO"


def test_pendiente_usuario_solicitante(client: TestClient, sdb):
    _, admin, agent, viewer = _tenant(sdb)
    case = svc.create_case_manual(
        sdb,
        admin.organization_id,
        viewer,
        {"tipo": "CONSULTA", "asunto": "Info requerida", "descripcion": "Falta dato"},
    )
    svc.assign_case(sdb, admin.organization_id, case["id"], admin, responsable_id=agent.id)
    svc.update_status(sdb, admin.organization_id, case["id"], agent, estado="PENDIENTE_USUARIO")
    viewer_headers = _login(client, viewer.username)
    items = _soporte_items(_trabajo_items(client, viewer_headers))
    assert any(i["metadata"]["case_id"] == case["id"] for i in items)


def test_pendiente_tercero_responsable(client: TestClient, sdb):
    _, admin, agent, _ = _tenant(sdb)
    case = _create_case(sdb, admin.organization_id, admin)
    svc.assign_case(sdb, admin.organization_id, case["id"], admin, responsable_id=agent.id)
    svc.update_status(sdb, admin.organization_id, case["id"], admin, estado="PENDIENTE_TERCERO")
    headers = _login(client, agent.username)
    items = _soporte_items(_trabajo_items(client, headers))
    assert any(i["metadata"]["case_id"] == case["id"] for i in items)


@pytest.mark.parametrize("estado", ["RESUELTO", "CERRADO", "CANCELADO"])
def test_estados_cerrados_excluidos(client: TestClient, sdb, estado: str):
    _, admin, _, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    case = _create_case(sdb, admin.organization_id, admin)
    if estado == "RESUELTO":
        svc.resolve_case(sdb, admin.organization_id, case["id"], admin, resolucion="Listo")
    elif estado == "CERRADO":
        svc.resolve_case(sdb, admin.organization_id, case["id"], admin, resolucion="Listo")
        svc.close_case(sdb, admin.organization_id, case["id"], admin)
    else:
        svc.update_status(sdb, admin.organization_id, case["id"], admin, estado=estado)
    items = _soporte_items(_trabajo_items(client, headers))
    assert not any(i["metadata"]["case_id"] == case["id"] for i in items)


def test_sla_vigente_y_vencido(client: TestClient, sdb):
    org, admin, agent, _ = _tenant(sdb)
    svc.create_sla_policy(sdb, org.id, {"nombre": "Alta", "prioridad": "ALTA", "minutos_resolucion": 120})
    case_ok = _create_case(sdb, org.id, admin, prioridad="ALTA", asunto="SLA vigente")
    svc.assign_case(sdb, org.id, case_ok["id"], admin, responsable_id=agent.id)
    headers = _login(client, agent.username)
    row = next(i for i in _soporte_items(_trabajo_items(client, headers)) if i["metadata"]["case_id"] == case_ok["id"])
    assert row["metadata"]["sla_estado"] in ("DENTRO", "PROXIMO", "VENCIDO", "NO_APLICA")

    case = db_get_case(sdb, org.id, _create_case(sdb, org.id, admin, prioridad="ALTA", asunto="SLA vencido")["id"])
    svc.assign_case(sdb, org.id, case.id, admin, responsable_id=agent.id)
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    case.resolucion_limite = past
    case.fecha_limite = past
    sdb.commit()
    row2 = next(i for i in _soporte_items(_trabajo_items(client, headers)) if i["metadata"]["case_id"] == case.id)
    assert row2["tipo"] == "soporte_sla_vencido"
    assert row2["vencida"] is True


def db_get_case(db: Session, org_id: str, case_id: str) -> SupportCase:
    row = svc.get_case(db, org_id, case_id)
    assert row
    return row


def test_deduplicacion_820_soporte(client: TestClient, sdb):
    org, admin, agent, _ = _tenant(sdb)
    case = _create_case(sdb, org.id, admin, asunto="Dedup 820")
    svc.assign_case(sdb, org.id, case["id"], admin, responsable_id=agent.id)
    row = svc.get_case(sdb, org.id, case["id"])
    emit_event(
        "SUPPORT_CASE_ASSIGNED",
        org.id,
        source_type="support_case",
        source_id=case["id"],
        payload={
            "title": "Caso asignado",
            "message": "Se le asignó un caso",
            "recipient_user_id": agent.id,
            "case_id": case["id"],
            "correlation_id": row.correlation_id,
        },
        db=sdb,
        commit=True,
    )
    headers = _login(client, agent.username)
    items = _trabajo_items(client, headers)
    soporte = [i for i in items if i["metadata"].get("case_id") == case["id"]]
    notifs = [
        i
        for i in items
        if i["tipo"] == "notificacion"
        and (i.get("metadata", {}).get("case_id") == case["id"] or i.get("metadata", {}).get("source_id") == case["id"])
    ]
    assert len(soporte) >= 1
    assert len(notifs) == 0


def test_deduplicacion_casos_automaticos(sdb):
    org, admin, _, _ = _tenant(sdb)
    payload = {
        "tipo": "INCIDENTE",
        "asunto": "Auto dedup MT",
        "descripcion": "Fallo",
        "origen_tipo": "automation_failed",
        "origen_id": "job-mt-1",
    }
    a = svc.create_case_auto(sdb, org.id, payload, actor_id=admin.id)
    b = svc.create_case_auto(sdb, org.id, payload, actor_id=admin.id)
    assert a["id"] == b["id"]


def test_resumen_incluye_soporte(client: TestClient, sdb):
    _, admin, _, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    _create_case(sdb, admin.organization_id, admin)
    res = client.get("/api/trabajo/resumen", headers=headers)
    assert res.status_code == 200
    assert res.json()["pendientes"] >= 1


def test_filtro_modulo_y_case_id(client: TestClient, sdb):
    _, admin, _, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    case = _create_case(sdb, admin.organization_id, admin)
    mod = client.get("/api/trabajo/items?modulo=soporte", headers=headers).json()["items"]
    assert all(i["modulo"] == "soporte" for i in mod)
    one = client.get(f"/api/trabajo/items?case_id={case['id']}", headers=headers).json()["items"]
    assert len(one) == 1
    assert one[0]["metadata"]["case_id"] == case["id"]


def test_navegacion_enlace(client: TestClient, sdb):
    _, admin, _, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    case = _create_case(sdb, admin.organization_id, admin)
    row = next(i for i in _soporte_items(_trabajo_items(client, headers)) if i["metadata"]["case_id"] == case["id"])
    assert row["enlace"] == f"/soporte/casos/{case['id']}"
    detail = client.get(f"/api/soporte/casos/{case['id']}", headers=headers)
    assert detail.status_code == 200


def test_multiempresa(client: TestClient, sdb):
    org_a, admin_a, _, _ = _tenant(sdb)
    _, admin_b, _, _ = _tenant(sdb)
    case = _create_case(sdb, org_a.id, admin_a)
    headers_b = _login(client, admin_b.username)
    items = _soporte_items(_trabajo_items(client, headers_b))
    assert not any(i["metadata"]["case_id"] == case["id"] for i in items)
    res = client.get(f"/api/trabajo/items?case_id={case['id']}", headers=headers_b)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0


def test_rbac_viewer_no_ve_casos_ajenos(client: TestClient, sdb):
    _, admin, agent, viewer = _tenant(sdb)
    case = _create_case(sdb, admin.organization_id, admin, asunto="Solo admin")
    svc.assign_case(sdb, admin.organization_id, case["id"], admin, responsable_id=agent.id)
    viewer_headers = _login(client, viewer.username)
    items = _soporte_items(_trabajo_items(client, viewer_headers))
    assert not any(i["metadata"]["case_id"] == case["id"] for i in items)


def test_superadmin_trabajo_items(client: TestClient, auth_headers):
    res = client.get("/api/trabajo/items", headers=auth_headers)
    assert res.status_code == 200


def test_secretos_no_expuestos(client: TestClient, sdb):
    _, admin, _, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    case = _create_case(
        sdb,
        admin.organization_id,
        admin,
        asunto="password: secreto",
        descripcion="api_key=abc123 token xyz",
    )
    row = next(i for i in _soporte_items(_trabajo_items(client, headers)) if i["metadata"]["case_id"] == case["id"])
    assert "secreto" not in (row.get("asunto") or "")
    assert "abc123" not in (row.get("detalle") or "")


def test_fechas_timezone_naive_aware(sdb):
    org, admin, agent, _ = _tenant(sdb)
    case_dict = _create_case(sdb, org.id, admin, prioridad="ALTA")
    case = db_get_case(sdb, org.id, case_dict["id"])
    naive_limit = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    case.resolucion_limite = naive_limit
    case.fecha_limite = naive_limit
    sdb.commit()
    estado = svc.compute_sla_estado(case)
    assert estado in ("DENTRO", "PROXIMO", "VENCIDO", "NO_APLICA")


def test_trabajo_view_no_concede_resolve(client: TestClient, sdb):
    _, admin, _, viewer = _tenant(sdb)
    case = svc.create_case_manual(
        sdb,
        admin.organization_id,
        viewer,
        {"tipo": "CONSULTA", "asunto": "Mi caso", "descripcion": "Ayuda"},
    )
    viewer_headers = _login(client, viewer.username)
    assert client.get("/api/trabajo/items", headers=viewer_headers).status_code == 200
    denied = client.post(
        f"/api/soporte/casos/{case['id']}/resolver",
        headers=viewer_headers,
        json={"resolucion": "Intento"},
    )
    assert denied.status_code == 403
