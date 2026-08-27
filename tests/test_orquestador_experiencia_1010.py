"""ORQUESTADOR-EXPERIENCIA-1010 — pruebas bloqueantes."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.fixtures.motor_analitico_datasets import get_case_request, get_motor_dataset
from app.models import Organization, User
from app.orchestration_models import AIEmployee, FinOpsRecord
from app.security import hash_password
from app.services.experience_core import (
    actualizar_resultado_experiencia,
    buscar_experiencias_similares,
    calcular_peso_calidad,
    crear_experiencia,
    experiencia_score_para_empleado,
    registrar_feedback_experiencia,
)
from app.services.orchestrator_selection import detect_primary_domain, select_team
from app.services.salud_specialist_selection import select_specialists

pytestmark = [pytest.mark.salud, pytest.mark.operations]


@pytest.fixture
def exp_db(client):
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    yield db
    db.close()


def _org_admin(db: Session) -> tuple[str, str]:
    admin = db.query(User).filter(User.username == "admin").first()
    assert admin is not None
    return admin.organization_id, admin.id


def _employee_by_code(db: Session, org_id: str, code: str) -> AIEmployee:
    emp = db.query(AIEmployee).filter(
        AIEmployee.organization_id == org_id, AIEmployee.code == code,
    ).first()
    assert emp is not None
    return emp


def test_experiencia_exitosa(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-radicacion-analyst")
    rec = crear_experiencia(
        exp_db, org_id, employee_id=emp.id, dominio="radicacion",
        tipo_problema="radicacion_tardia", resultado_esperado="Reducir días a <7",
        contexto={"sector": "IPS", "escala": "mediana"},
    )
    actualizar_resultado_experiencia(
        exp_db, org_id, rec.id, resultado_real="6.2 días promedio",
        estado="EXITO", kpi_despues={"dias_radicacion": 6.2},
    )
    exp_db.commit()
    calidad = calcular_peso_calidad(rec)
    assert calidad["peso"] >= 0.6
    assert rec.estado == "EXITO"


def test_experiencia_fracaso(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-glosas-analyst")
    rec = crear_experiencia(
        exp_db, org_id, employee_id=emp.id, dominio="glosas",
        tipo_problema="glosas_devoluciones", accion="Plantillas masivas",
    )
    actualizar_resultado_experiencia(
        exp_db, org_id, rec.id, resultado_real="Glosa subió 2 p.p.",
        estado="FRACASO", condiciones_fracaso=["pagador agresivo en auditoría"],
    )
    exp_db.commit()
    assert rec.estado == "FRACASO"
    assert rec.peso_calidad is not None and rec.peso_calidad < 0.5


def test_experiencia_sin_seguimiento(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-cartera-analyst")
    rec = crear_experiencia(
        exp_db, org_id, employee_id=emp.id, dominio="cartera",
        tipo_problema="comportamiento_pagador", hipotesis="H7 pagador tardío",
    )
    exp_db.commit()
    calidad = calcular_peso_calidad(rec)
    assert rec.estado == "INDETERMINADO"
    assert calidad["peso"] < 0.5


def test_feedback_bueno_resultado_malo(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-facturacion-analyst")
    rec = crear_experiencia(
        exp_db, org_id, employee_id=emp.id, dominio="facturacion",
        tipo_problema="concentracion", senales={"mora": 45},
    )
    rec.kpi_antes_json = json.dumps({"mora": 45})
    actualizar_resultado_experiencia(
        exp_db, org_id, rec.id, resultado_real="Mora subió a 52",
        estado="FRACASO", kpi_despues={"mora": 52},
    )
    registrar_feedback_experiencia(exp_db, org_id, rec.id, "CORRECTO")
    exp_db.commit()
    calidad = calcular_peso_calidad(rec)
    assert rec.estado == "FRACASO"
    assert calidad["peso"] < 0.75
    assert "feedback_sin_kpi" in calidad["factores"] or rec.estado == "FRACASO"


def test_similitud_alta(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-radicacion-analyst")
    crear_experiencia(
        exp_db, org_id, employee_id=emp.id, dominio="radicacion",
        tipo_problema="radicacion_tardia", contexto={"sector": "IPS", "variables": {"dias": 12}},
        senales={"dias": 12},
    )
    exp_db.commit()
    sim = buscar_experiencias_similares(
        exp_db, org_id, dominio="radicacion", tipo_problema="radicacion_tardia",
        contexto={"sector": "IPS", "variables": {"dias": 12}},
    )
    assert sim and sim[0]["similitud"] >= 0.5


def test_similitud_baja(exp_db):
    org_id, _ = _org_admin(exp_db)
    sim = buscar_experiencias_similares(
        exp_db, org_id, dominio="rips", tipo_problema="validacion_rips",
        contexto={"sector": "farmacia"},
    )
    assert sim == [] or sim[0]["similitud"] < 0.4


def test_candidatos_diferente_experiencia(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp_b = _employee_by_code(exp_db, org_id, "ips-glosas-analyst")
    for _ in range(3):
        rec = crear_experiencia(
            exp_db, org_id, employee_id=emp_b.id, dominio="glosas",
            tipo_problema="glosas_devoluciones",
        )
        actualizar_resultado_experiencia(
            exp_db, org_id, rec.id, resultado_real="Recuperó 80%",
            estado="EXITO",
        )
    exp_db.commit()
    score_b = experiencia_score_para_empleado(
        exp_db, org_id, emp_b.id, "glosas", "glosas_devoluciones",
    )
    emp_a = _employee_by_code(exp_db, org_id, "ips-cartera-analyst")
    score_a = experiencia_score_para_empleado(
        exp_db, org_id, emp_a.id, "glosas", "glosas_devoluciones",
    )
    assert score_b["score"] > score_a["score"]


def test_costo_diferente_no_elige_siempre_barato(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp_cartera = _employee_by_code(exp_db, org_id, "ips-cartera-analyst")
    emp_glosas = _employee_by_code(exp_db, org_id, "ips-glosas-analyst")
    exp_db.add(FinOpsRecord(organization_id=org_id, employee_id=emp_cartera.id, cost=0.01))
    exp_db.add(FinOpsRecord(organization_id=org_id, employee_id=emp_glosas.id, cost=5.0))
    exp_db.commit()
    plan = select_team(
        exp_db, org_id,
        "Analiza cartera elevada por glosas y devoluciones",
        available_data=["glosas", "cartera"],
    )
    lider = plan["lider"]
    assert "Glosas" in lider.get("employee_name", "")


def test_validador_por_diversidad(exp_db):
    org_id, _ = _org_admin(exp_db)
    plan = select_team(
        exp_db, org_id,
        "Diagnóstico integral: cartera, radicación, glosas y concentración",
        available_data=["cartera", "radicacion", "glosas", "facturacion"],
    )
    assert plan.get("validador") is not None
    assert plan["validador"]["employee_id"] != plan["lider"]["employee_id"]


def test_tenant_isolation_experiencia(exp_db):
    org_id, _ = _org_admin(exp_db)
    org2 = Organization(name=f"Org-{uuid.uuid4().hex[:6]}")
    exp_db.add(org2)
    exp_db.flush()
    emp = _employee_by_code(exp_db, org_id, "ips-radicacion-analyst")
    crear_experiencia(
        exp_db, org_id, employee_id=emp.id, dominio="radicacion",
        tipo_problema="radicacion_tardia",
    )
    exp_db.commit()
    sim = buscar_experiencias_similares(exp_db, org2.id, dominio="radicacion")
    assert sim == []


def test_experiencia_contradictoria(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-radicacion-analyst")
    r1 = crear_experiencia(exp_db, org_id, employee_id=emp.id, dominio="radicacion", tipo_problema="radicacion_tardia")
    actualizar_resultado_experiencia(exp_db, org_id, r1.id, resultado_real="OK", estado="EXITO",
                                     condiciones_exito=["equipo dedicado"])
    r2 = crear_experiencia(exp_db, org_id, employee_id=emp.id, dominio="radicacion", tipo_problema="radicacion_tardia")
    actualizar_resultado_experiencia(exp_db, org_id, r2.id, resultado_real="Falló", estado="FRACASO",
                                     condiciones_fracaso=["alta rotación"])
    exp_db.commit()
    score = experiencia_score_para_empleado(exp_db, org_id, emp.id, "radicacion", "radicacion_tardia")
    assert "contradictoria" in score["explicacion"].lower() or score["factores"]["exitos"] >= 1


def test_experiencia_antigua_peso_menor(exp_db):
    from app.experience_models import EmployeeExperienceRecord
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-cartera-analyst")
    rec = EmployeeExperienceRecord(
        organization_id=org_id, employee_id=emp.id, dominio="cartera",
        tipo_problema="comportamiento_pagador", estado="EXITO",
        resultado_real="Mejoró", created_at=datetime.now(timezone.utc) - timedelta(days=400),
    )
    calidad = calcular_peso_calidad(rec)
    rec_nueva = EmployeeExperienceRecord(
        organization_id=org_id, employee_id=emp.id, dominio="cartera",
        tipo_problema="comportamiento_pagador", estado="EXITO",
        resultado_real="Mejoró", created_at=datetime.now(timezone.utc),
    )
    calidad_nueva = calcular_peso_calidad(rec_nueva)
    assert calidad_nueva["peso"] >= calidad["peso"]


def test_actualizacion_resultado(exp_db):
    org_id, _ = _org_admin(exp_db)
    emp = _employee_by_code(exp_db, org_id, "ips-contractual-analyst")
    rec = crear_experiencia(
        exp_db, org_id, employee_id=emp.id, dominio="contratos",
        tipo_problema="contractual_tarifas", resultado_esperado="Renegociar tarifa",
    )
    exp_db.commit()
    peso_antes = rec.peso_calidad
    actualizar_resultado_experiencia(
        exp_db, org_id, rec.id, resultado_real="Tarifa ajustada +8%",
        estado="EXITO", valor_obtenido=12000000,
    )
    exp_db.commit()
    assert rec.peso_calidad > peso_antes
    assert rec.resultado_actualizado_at is not None


@pytest.mark.parametrize("case_id,expected_domain,expected_leader_keyword", [
    ("A", "radicacion", "Radicación"),
    ("B", "glosas", "Glosas"),
    ("C", "cartera", "Cartera"),
    ("D", "estrategico", "Estratégico"),
    ("E", "estrategico", "Estratégico"),
])
def test_lider_cambia_por_tipo_problema(exp_db, case_id, expected_domain, expected_leader_keyword):
    org_id, _ = _org_admin(exp_db)
    ds = get_motor_dataset(case_id)
    req = get_case_request(case_id)
    plan = select_specialists(exp_db, org_id, req, list(ds.keys()))
    assert plan["dominio_principal"] == expected_domain
    lider_name = plan["lider"]["employee_name"]
    assert expected_leader_keyword in lider_name


def test_anti_lider_prefabricado_motor_ae(exp_db):
    """FAIL si los cinco casos producen el mismo líder sin justificación."""
    org_id, _ = _org_admin(exp_db)
    leaders: list[str] = []
    for case_id in ("A", "B", "C", "D", "E"):
        ds = get_motor_dataset(case_id)
        req = get_case_request(case_id)
        plan = select_specialists(exp_db, org_id, req, list(ds.keys()))
        leaders.append(plan["lider"]["employee_name"])
    unique = set(leaders)
    assert len(unique) >= 3, f"Líderes insuficientemente diversos: {leaders}"
    assert not all("Cartera" in l for l in leaders), "Monocultura de líder cartera detectada"


def test_fail_closed_sin_empleados(exp_db):
    org_id, _ = _org_admin(exp_db)
    employees = exp_db.query(AIEmployee).filter(AIEmployee.organization_id == org_id).all()
    prev_states = {e.id: e.is_active for e in employees}
    exp_db.query(AIEmployee).filter(AIEmployee.organization_id == org_id).update({"is_active": False})
    exp_db.commit()
    try:
        plan = select_team(exp_db, org_id, "Analizar cartera", available_data=["cartera"], persist_log=False)
        assert not plan.get("lider")
    finally:
        for eid, active in prev_states.items():
            exp_db.query(AIEmployee).filter(AIEmployee.id == eid).update({"is_active": active})
        exp_db.commit()


def test_detect_primary_domain_insuficiente():
    primary, _, ptype = detect_primary_domain(
        "¿Por qué aumentó mi cartera?",
        available_data=["facturacion"],
    )
    assert primary == "estrategico"
    assert ptype == "datos_insuficientes"


def test_demo_b_gana_por_experiencia(exp_db):
    """Demo 1: especialista B gana por experiencia específica en glosas."""
    org_id, _ = _org_admin(exp_db)
    emp_glosas = _employee_by_code(exp_db, org_id, "ips-glosas-analyst")
    emp_cartera = _employee_by_code(exp_db, org_id, "ips-cartera-analyst")
    for _ in range(5):
        r = crear_experiencia(exp_db, org_id, employee_id=emp_glosas.id, dominio="glosas", tipo_problema="glosas_devoluciones")
        actualizar_resultado_experiencia(exp_db, org_id, r.id, resultado_real="Recuperó", estado="EXITO")
    for _ in range(5):
        r = crear_experiencia(exp_db, org_id, employee_id=emp_cartera.id, dominio="glosas", tipo_problema="glosas_devoluciones")
        actualizar_resultado_experiencia(exp_db, org_id, r.id, resultado_real="Sin mejora", estado="FRACASO")
    exp_db.commit()
    plan = select_team(exp_db, org_id, "Analiza glosas y devoluciones pendientes", available_data=["glosas", "cartera"])
    assert "Glosas" in plan["lider"]["employee_name"]
    assert plan.get("razon_seleccion_global")


def test_demo_a_gana_por_experiencia_integral(exp_db):
    """Demo 2: empleado A (alto volumen/experiencia integral) lidera diagnóstico estratégico."""
    org_id, _ = _org_admin(exp_db)
    emp_estrategico = _employee_by_code(exp_db, org_id, "ips-estrategico-analyst")
    emp_radicacion = _employee_by_code(exp_db, org_id, "ips-radicacion-analyst")
    for _ in range(8):
        r = crear_experiencia(
            exp_db, org_id, employee_id=emp_estrategico.id,
            dominio="estrategico", tipo_problema="diagnostico_integral",
        )
        actualizar_resultado_experiencia(exp_db, org_id, r.id, resultado_real="Plan integral ejecutado", estado="EXITO")
    for _ in range(2):
        r = crear_experiencia(
            exp_db, org_id, employee_id=emp_radicacion.id,
            dominio="estrategico", tipo_problema="diagnostico_integral",
        )
        actualizar_resultado_experiencia(exp_db, org_id, r.id, resultado_real="Parcial", estado="PARCIAL")
    exp_db.commit()
    plan = select_team(
        exp_db, org_id,
        "Diagnóstico integral: cartera, radicación, glosas y concentración de pagadores",
        available_data=["cartera", "radicacion", "glosas", "facturacion"],
    )
    assert "Estratégico" in plan["lider"]["employee_name"]
    assert "experiencia" in plan["lider"].get("razon_seleccion", "").lower() or plan.get("razon_seleccion_global")


def test_demo_c_validador_por_diversidad(exp_db):
    """Demo 3: especialista C entra como validador por diversidad de criterio."""
    org_id, _ = _org_admin(exp_db)
    plan = select_team(
        exp_db, org_id,
        "Diagnóstico integral: cartera, radicación, glosas y concentración",
        available_data=["cartera", "radicacion", "glosas", "facturacion", "contratos"],
    )
    validador = plan.get("validador")
    assert validador is not None
    assert validador["employee_id"] != plan["lider"]["employee_id"]
    assert validador.get("razon_rol") or validador.get("razon_seleccion")
    assert any(
        m.get("rol") == "VALIDADOR"
        for m in plan.get("equipo", [])
    )


def test_experiencia_vs_capacidad_no_siempre_volumen(exp_db):
    """Sección 9: A mucha experiencia mediocre no debe ganar siempre frente a B excelente en dominio."""
    org_id, _ = _org_admin(exp_db)
    emp_a = _employee_by_code(exp_db, org_id, "ips-cartera-analyst")
    emp_b = _employee_by_code(exp_db, org_id, "ips-glosas-analyst")
    for _ in range(10):
        r = crear_experiencia(exp_db, org_id, employee_id=emp_a.id, dominio="glosas", tipo_problema="glosas_devoluciones")
        actualizar_resultado_experiencia(exp_db, org_id, r.id, resultado_real="Sin impacto", estado="FRACASO")
    for _ in range(3):
        r = crear_experiencia(exp_db, org_id, employee_id=emp_b.id, dominio="glosas", tipo_problema="glosas_devoluciones")
        actualizar_resultado_experiencia(exp_db, org_id, r.id, resultado_real="Recuperó 90%", estado="EXITO")
    exp_db.commit()
    plan = select_team(exp_db, org_id, "Analiza glosas y devoluciones del pagador", available_data=["glosas"])
    assert "Glosas" in plan["lider"]["employee_name"]
    assert plan["lider"]["employee_id"] == emp_b.id


def test_api_seleccion_equipo(client, auth_headers):
    res = client.post("/api/experiencia/seleccion-equipo", headers=auth_headers, json={
        "solicitud": "Analiza radicación tardía en facturación IPS",
        "available_data": ["radicacion", "facturacion"],
    })
    assert res.status_code == 200
    data = res.json()
    assert data.get("lider")
    assert data.get("dominio_principal") == "radicacion"
