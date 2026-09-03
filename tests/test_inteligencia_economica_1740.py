"""Inteligencia económica EIAAX — Bloque 1740."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.economic_motor_enums import EconomicValueType
from app.inteligencia_economica_enums import TipoEscenarioComparacion
from app.inteligencia_economica_models import EconomicScenarioRun
from app.models import Organization, User
from app.orchestration_models import AIEmployee, EmployeeLimits
from app.security import hash_password
from app.services import economic_motor_service as motor
from app.services import inteligencia_economica_service as ie_svc
from app.valuation_enums import RealValueNature
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db: Session, org_name: str) -> tuple[Organization, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"t-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "IE1740*Test1"
    user = User(
        organization_id=org.id,
        username=f"u-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(password),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, password, user.username


def _employee(db: Session, org_id: str) -> AIEmployee:
    emp = AIEmployee(
        organization_id=org_id,
        code=f"EMP-{uuid.uuid4().hex[:4]}",
        name="Empleado IA test",
        specialty="general",
        lifecycle_status="ACTIVE",
        status="DISPONIBLE",
        is_active=True,
    )
    db.add(emp)
    db.flush()
    db.add(EmployeeLimits(employee_id=emp.id, daily_cost_limit=100.0))
    db.commit()
    return emp


def test_auditoria_lista_capacidades(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "IE-Audit")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/inteligencia-economica/auditoria", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "finops" in body
    assert "motor_economico" in body
    assert "brechas_cerradas_1740" in body


def test_valor_empresarial_excluye_potencial_de_realizado(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "IE-Valor")
    user = db.query(User).filter(User.username == username).first()
    motor.register_value(
        db,
        user,
        organization_id=org.id,
        value_type=EconomicValueType.AHORRO,
        value_nature=RealValueNature.POTENCIAL,
        amount=Decimal("5000"),
        register_finops=False,
    )
    motor.register_value(
        db,
        user,
        organization_id=org.id,
        value_type=EconomicValueType.AHORRO,
        value_nature=RealValueNature.VERIFICADO,
        amount=Decimal("123.45"),
        register_finops=False,
    )
    db.commit()
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/inteligencia-economica/valor-empresarial", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["resumen_naturaleza"]["valor_potencial"] == 5000.0
    assert body["resumen_naturaleza"]["valor_realizado"] == 123.45
    assert "POTENCIAL" in body["nota_potencial"]


def test_resultado_economico_casos_cero(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "IE-Cero")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/inteligencia-economica/resultado-economico?period_days=30", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["beneficio_neto"] == 0
    assert body["roi_pct"] is None
    assert body["payback_meses"] is None


def test_comparar_escenarios_seis_tipos(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "IE-Escenarios")
    db.close()
    headers = auth_header(_token(client, username, password))
    tipos = [e.value for e in TipoEscenarioComparacion]
    res = client.post(
        "/api/inteligencia-economica/escenarios/comparar",
        headers=headers,
        json={"personas": 10, "empleados_ia": 1, "escenarios": tipos, "persistir": True, "titulo": "Test 6 escenarios"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["escenarios"]) == 6
    assert body["run_id"]
    assert body["codigo"].startswith("SIM-")
    actual = next(e for e in body["escenarios"] if e["tipo"] == "ACTUAL")
    combinado = next(e for e in body["escenarios"] if e["tipo"] == "SOLUCION_COMBINADA")
    assert combinado["costo_total"] >= 0
    assert actual["personas"] == 10


def test_dimensionar_sin_despido_obligatorio(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "IE-Dim")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.post(
        "/api/inteligencia-economica/dimensionar",
        headers=headers,
        json={
            "personas_actual": 10,
            "personas_escenario": 7,
            "empleados_ia": 1,
            "modo": "CAPACIDAD_LIBERADA",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["impacto"]["no_implica_despido_obligatorio"] is True
    assert body["situacion_actual"]["personas"] == 10
    assert body["escenario"]["personas"] == 7


def test_economia_empleado(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "IE-Emp")
    emp = _employee(db, org.id)
    emp_id = emp.id
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get(f"/api/inteligencia-economica/empleados/{emp_id}/economia", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["employee_id"] == emp_id
    assert body["costo_real"] == 0


def test_economia_empresa(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "IE-Org")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/inteligencia-economica/empresa", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "presupuesto" in body
    assert "alertas" in body
    assert "resultado" in body


def test_precio_valor_borrador_no_auto_publicado(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "IE-Precio")
    user = db.query(User).filter(User.username == username).first()
    motor.register_value(
        db,
        user,
        organization_id=org.id,
        value_type=EconomicValueType.INGRESO_RECUPERADO,
        value_nature=RealValueNature.VERIFICADO,
        amount=Decimal("1000"),
        register_finops=False,
    )
    db.commit()
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.post(
        "/api/inteligencia-economica/precio-recomendado-valor",
        headers=headers,
        json={"fraccion_valor": 0.4, "margen_min": 0.2},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "BORRADOR"
    assert body["auto_publicado"] is False
    assert body["separacion"]["costo"] is not None
    assert body["separacion"]["valor"] == 1000.0


def test_comercial_interna_requiere_private(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "IE-Priv")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/inteligencia-economica/comercial-interna", headers=headers)
    assert res.status_code == 200
    assert res.json()["auto_publicado"] is False


def test_aislamiento_multiempresa(client: TestClient):
    db = TestingSessionLocal()
    org_a, pwd_a, user_a = _create_tenant(db, "IE-OrgA")
    org_b, pwd_b, user_b = _create_tenant(db, "IE-OrgB")
    user_obj = db.query(User).filter(User.username == user_a).first()
    ie_svc.comparar_escenarios(
        db,
        user_obj,
        org_a.id,
        {"personas": 5, "persistir": True, "titulo": "Solo A"},
    )
    db.commit()
    count_a = db.query(EconomicScenarioRun).filter(EconomicScenarioRun.organization_id == org_a.id).count()
    count_b = db.query(EconomicScenarioRun).filter(EconomicScenarioRun.organization_id == org_b.id).count()
    db.close()
    assert count_a == 1
    assert count_b == 0
    headers_b = auth_header(_token(client, user_b, pwd_b))
    runs_b = client.get("/api/inteligencia-economica/escenarios/runs", headers=headers_b)
    assert runs_b.status_code == 200
    assert runs_b.json() == []


def test_escenarios_negativos_y_decimales():
    db = TestingSessionLocal()
    org, _, _ = _create_tenant(db, "IE-Unit")
    result = ie_svc.comparar_escenarios(
        db,
        None,
        org.id,
        {
            "personas": 3,
            "costo_hora": 12.3456,
            "valor_hora": 0,
            "escenarios": ["ACTUAL"],
        },
    )
    actual = result["escenarios"][0]
    assert actual["costo_total"] >= 0
    assert isinstance(actual["costo_personas"], float)
    db.close()


def test_parse_run_resultados():
    parsed = ie_svc.parse_run_resultados('{"beneficio_neto": 10.5}')
    assert parsed["beneficio_neto"] == 10.5
    assert ie_svc.parse_run_resultados(None) is None
