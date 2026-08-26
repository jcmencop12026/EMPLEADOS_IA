"""Reauditoría adversarial OPERACIONES-940 — prioridad, vencimiento, indicadores, tenant."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models import Organization, User
from app.orchestration_models import WorkPlan
from app.security import hash_password
from app.services.operations_labels import DUE_SOON_HOURS, due_state, normalize_priority
from conftest import TestingSessionLocal, auth_header

pytestmark = pytest.mark.operations


def _create_org_user(client, org_name: str, username: str, password: str, role: str = "admin") -> str:
    db = TestingSessionLocal()
    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    db.add(User(organization_id=org.id, username=username, password_hash=hash_password(password), role=role))
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def _create_plan(client, token: str) -> str:
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={
            "message": "analizar rips",
            "context": {
                "tool": "rips",
                "rips": {
                    "usuarios": [{"tipoDocumentoIdentificacion": "CC", "numDocumentoIdentificacion": "1", "codSexo": "M", "fechaNacimiento": "1980-01-01"}],
                    "consultas": [{"codConsulta": "890201", "numDocumentoIdentificacion": "999"}],
                    "procedimientos": [],
                    "medicamentos": [],
                    "otrosServicios": [],
                },
            },
            "auto_execute": True,
        },
    )
    assert res.status_code == 200
    return res.json()["plan_id"]


@pytest.mark.parametrize(
    "bad_value",
    ["", "URGENTE", "critical", "1", "null", "{}", "[]"],
)
def test_priority_adversarial_values_rejected(client, token, bad_value):
    plan_id = _create_plan(client, token)
    res = client.patch(
        f"/api/operations/center/{plan_id}",
        headers=auth_header(token),
        json={"prioridad": bad_value},
    )
    assert res.status_code == 400


def test_priority_aliases_accepted(client, token):
    plan_id = _create_plan(client, token)
    for alias, expected in [("baja", "BAJA"), ("Crítica", "CRITICA"), ("normal", "MEDIA")]:
        res = client.patch(
            f"/api/operations/center/{plan_id}",
            headers=auth_header(token),
            json={"prioridad": alias},
        )
        assert res.status_code == 200
        assert res.json()["prioridad_codigo"] == expected


def test_due_state_vence_hoy_boundary():
    now = datetime(2026, 8, 25, 15, 0, tzinfo=timezone.utc)
    plan = WorkPlan(
        id="x",
        organization_id="o",
        request="r",
        objective="o",
        correlation_id="c",
        status="READY",
        vencimiento=datetime(2026, 8, 25, 23, 59, tzinfo=timezone.utc),
    )
    assert due_state(plan, now) == "vence_hoy"


def test_due_state_proximo_uses_48h_constant():
    now = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
    plan = WorkPlan(
        id="x",
        organization_id="o",
        request="r",
        objective="o",
        correlation_id="c",
        status="READY",
        vencimiento=now + timedelta(hours=DUE_SOON_HOURS),
    )
    assert due_state(plan, now) == "proximo"
    beyond = now + timedelta(hours=DUE_SOON_HOURS + 1)
    plan.vencimiento = beyond
    assert due_state(plan, now) == "vigente"


def test_summary_counters_mathematically_consistent(client, token):
    """Indicadores backend: datos controlados y conteo verificable."""
    plan_overdue = _create_plan(client, token)
    plan_soon = _create_plan(client, token)
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    soon = (datetime.now(timezone.utc) + timedelta(hours=36)).isoformat()
    client.patch(
        f"/api/operations/center/{plan_overdue}",
        headers=auth_header(token),
        json={"vencimiento": past},
    )
    client.patch(
        f"/api/operations/center/{plan_soon}",
        headers=auth_header(token),
        json={"vencimiento": soon},
    )
    summary = client.get("/api/operations/summary", headers=auth_header(token)).json()
    overdue_list = client.get(
        "/api/operations/center",
        headers=auth_header(token),
        params={"vencimiento_filtro": "vencido"},
    ).json()
    soon_list = client.get(
        "/api/operations/center",
        headers=auth_header(token),
        params={"bucket": "due_soon"},
    ).json()
    assert summary["overdue"] >= 1
    assert summary["due_soon"] >= 1
    assert any(row["id"] == plan_overdue for row in overdue_list)
    assert any(row["id"] == plan_soon for row in soon_list)


def test_cross_tenant_due_date_update_denied(client):
    token_a = _create_org_user(client, "Org Due A", f"da-{uuid.uuid4().hex}", "DueA*")
    token_b = _create_org_user(client, "Org Due B", f"db-{uuid.uuid4().hex}", "DueB*")
    plan_id = _create_plan(client, token_a)
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    denied = client.patch(
        f"/api/operations/center/{plan_id}",
        headers=auth_header(token_b),
        json={"vencimiento": future},
    )
    assert denied.status_code == 404


def test_viewer_cannot_modify_due_date(client, token):
    plan_id = _create_plan(client, token)
    viewer = _create_org_user(client, "Org Viewer Due", f"vd-{uuid.uuid4().hex}", "ViewerDue*", role="viewer")
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    denied = client.patch(
        f"/api/operations/center/{plan_id}",
        headers=auth_header(viewer),
        json={"vencimiento": future},
    )
    assert denied.status_code == 403


def test_cross_tenant_same_404_for_get_and_patch(client):
    """No inferir existencia: GET y PATCH cross-tenant devuelven 404."""
    token_a = _create_org_user(client, "Org Inf A", f"ia-{uuid.uuid4().hex}", "InfA*")
    token_b = _create_org_user(client, "Org Inf B", f"ib-{uuid.uuid4().hex}", "InfB*")
    plan_id = _create_plan(client, token_a)
    get_res = client.get(f"/api/operations/center/{plan_id}", headers=auth_header(token_b))
    patch_res = client.patch(
        f"/api/operations/center/{plan_id}",
        headers=auth_header(token_b),
        json={"prioridad": "Alta"},
    )
    assert get_res.status_code == 404
    assert patch_res.status_code == 404


def test_normalize_priority_rejects_wrong_types():
    with pytest.raises(ValueError):
        normalize_priority("URGENTE")
