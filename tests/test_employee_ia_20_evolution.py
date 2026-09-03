"""Tests — Empleado IA 2.0 evolución aislada."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services.employee_20_autonomy import AutonomyBlockedError, apply_autonomy_to_decision
from app.services.authorization import ExecutionDecision

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


@pytest.fixture
def sdb():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _tenant(db: Session) -> tuple[Organization, User]:
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-e20-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    admin = User(
        organization_id=org.id,
        username=f"adm-{uuid.uuid4().hex[:6]}",
        email=f"a-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return org, admin


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_employee(client: TestClient, headers: dict[str, str]) -> str:
    res = client.post(
        "/api/agent-factory/employees",
        headers=headers,
        json={"name": "Empleado E20", "specialty": "DOCINT", "template_code": "analista-documental"},
    )
    assert res.status_code == 200
    return res.json()["id"]


def test_inventario_endpoint(client: TestClient, token):
    from conftest import auth_header

    res = client.get("/api/empleados-ia-20/inventario", headers=auth_header(token))
    assert res.status_code == 200
    body = res.json()
    assert "reutiliza" in body
    assert "AIEmployee" in str(body["reutiliza"])


def test_ficha_laboral_crud(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    emp_id = _create_employee(client, headers)

    ficha = client.get(f"/api/empleados-ia-20/employees/{emp_id}/ficha", headers=headers)
    assert ficha.status_code == 200
    assert ficha.json()["nombre"] == "Empleado E20"
    assert ficha.json()["ciclo_vida"]["fase_mision"] in ("BORRADOR", "CONFIGURACION")

    updated = client.put(
        f"/api/empleados-ia-20/employees/{emp_id}/ficha",
        headers=headers,
        json={
            "mision": "Automatizar análisis documental",
            "autonomia": "PREPARA",
            "funciones": ["Clasificar", "Validar"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["autonomia"] == "PREPARA"
    assert "Clasificar" in updated.json()["funciones"]


def test_supervision_y_evaluacion(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    emp_id = _create_employee(client, headers)

    ev = client.post(
        f"/api/empleados-ia-20/employees/{emp_id}/indicadores",
        headers=headers,
        json={
            "codigo": "precision",
            "nombre": "Precisión",
            "valor_esperado": 90,
            "valor_real": 60,
        },
    )
    assert ev.status_code == 200
    assert ev.json()["alerta"] == "BAJO_RENDIMIENTO"

    sup = client.post(
        f"/api/empleados-ia-20/employees/{emp_id}/supervision",
        headers=headers,
        json={"event_type": "ERROR", "descripcion": "Fallo de prueba"},
    )
    assert sup.status_code == 200

    eval_res = client.get(f"/api/empleados-ia-20/employees/{emp_id}/evaluacion", headers=headers)
    assert eval_res.status_code == 200
    assert "BAJO_RENDIMIENTO:precision" in eval_res.json()["hallazgos"]


def test_aprendizaje_controlado_sin_autoedit(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    emp_id = _create_employee(client, headers)

    prop = client.post(
        f"/api/empleados-ia-20/employees/{emp_id}/aprendizaje",
        headers=headers,
        json={
            "observacion": "Errores en codificación",
            "propuesta": "Ajustar reglas de validación",
            "causa_probable": "Conocimiento insuficiente",
        },
    )
    assert prop.status_code == 200
    pid = prop.json()["id"]

    decide = client.post(
        f"/api/empleados-ia-20/aprendizaje/{pid}/decidir",
        headers=headers,
        json={"aprobar": True, "notas": "Probar en sandbox"},
    )
    assert decide.status_code == 200
    assert decide.json()["estado"] == "EN_PRUEBA"
    assert "No se modifica" in decide.json()["nota"]


def test_resultados_contrato(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    emp_id = _create_employee(client, headers)

    link = client.post(
        f"/api/empleados-ia-20/employees/{emp_id}/resultados-contrato",
        headers=headers,
        json={"resultado_ref": "exec-001", "indicador_codigo": "precision", "valor_ref": 0.82},
    )
    assert link.status_code == 200
    assert link.json()["contrato"] == "employee_20_results_v1"

    contract = client.get(
        f"/api/empleados-ia-20/employees/{emp_id}/resultados-contrato",
        headers=headers,
    )
    assert contract.status_code == 200
    assert len(contract.json()["enlaces"]) >= 1


def test_autonomy_recomienda_blocks_execution(sdb):
    from app.enums import EmployeeMaturity
    from app.orchestration_models import AIEmployee
    from app.employee_20_models import EmployeeLaborProfile

    org, _ = _tenant(sdb)
    emp = AIEmployee(
        organization_id=org.id,
        code="test-e20",
        name="Test",
        specialty="DOCINT",
        maturity=EmployeeMaturity.AUTONOMOUS_CONTROLLED,
        shadow_mode=False,
    )
    sdb.add(emp)
    sdb.flush()
    profile = EmployeeLaborProfile(
        organization_id=org.id,
        employee_id=emp.id,
        autonomy_level="RECOMIENDA",
    )
    sdb.add(profile)
    sdb.commit()

    with pytest.raises(AutonomyBlockedError):
        apply_autonomy_to_decision(sdb, org.id, emp, ExecutionDecision.ALLOW)


def test_autonomy_shadow_requires_approval(sdb):
    from app.enums import EmployeeMaturity
    from app.orchestration_models import AIEmployee

    org, _ = _tenant(sdb)
    emp = AIEmployee(
        organization_id=org.id,
        code="shadow-e20",
        name="Shadow",
        specialty="DOCINT",
        maturity=EmployeeMaturity.SHADOW,
        shadow_mode=True,
    )
    sdb.add(emp)
    sdb.commit()

    decision = apply_autonomy_to_decision(sdb, org.id, emp, ExecutionDecision.ALLOW)
    assert decision == ExecutionDecision.REQUIRES_APPROVAL


def test_cc_signals_adapter(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    res = client.get("/api/empleados-ia-20/senal-centro-control", headers=headers)
    assert res.status_code == 200
    assert res.json()["adapter"] == "employee_20_cc_signals_v1"
    assert res.json()["integrado"] is False


def test_multitenant_isolation_ficha(client: TestClient, sdb):
    org_a, admin_a = _tenant(sdb)
    org_b, admin_b = _tenant(sdb)
    headers_a = _login(client, admin_a.username)
    headers_b = _login(client, admin_b.username)
    emp_a = _create_employee(client, headers_a)

    cross = client.get(f"/api/empleados-ia-20/employees/{emp_a}/ficha", headers=headers_b)
    assert cross.status_code == 404
