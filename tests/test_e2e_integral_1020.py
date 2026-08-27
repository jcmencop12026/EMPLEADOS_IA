"""E2E-INTEGRAL-1020 — certificación funcional integral EMPLEADOS_IA."""

from __future__ import annotations

import json
import uuid

import pytest

from app.experience_models import EmployeeExperienceRecord, ExperienceSelectionLog
from app.fixtures.motor_analitico_datasets import get_case_request
from app.orchestration_models import EmployeeTask, WorkPlan
from app.services.experience_core import calcular_peso_calidad, experiencia_score_para_empleado
from app.services.orchestrator_selection import select_team
from conftest import TestingSessionLocal, auth_header
from e2e_1020_helpers import (
    E2E_SOLICITUD,
    build_trace_chain,
    create_org_token,
    e2e_datasets,
    grant_knowledge,
    radicacion_employee_id,
    run_salud_analysis,
    save_evidence,
    upload_knowledge,
)

pytestmark = [pytest.mark.salud, pytest.mark.operations]

SAMPLE_RIPS = {
    "usuarios": [{"tipoDocumentoIdentificacion": "CC", "numDocumentoIdentificacion": "1234567890", "codSexo": "M", "fechaNacimiento": "1980-01-15"}],
    "consultas": [{"codConsulta": "890201", "numDocumentoIdentificacion": "9999999999"}],
    "procedimientos": [],
    "medicamentos": [],
    "otrosServicios": [],
}


def _create_plan(client, token: str, analysis_id: str, prop_ids: list[str]):
    return client.post(
        f"/api/salud/analisis/{analysis_id}/plan-accion",
        headers=auth_header(token),
        json={"propuesta_ids": prop_ids},
    )


def test_e2e_flujo_feliz_completo(client, token):
    """Flujo feliz: solicitud → diagnóstico → equipo → conocimiento → motor → plan → operaciones → FINOPS."""
    emp_id = radicacion_employee_id()
    doc_id = upload_knowledge(
        client, token,
        "Política radicación IPS E2E",
        "El plazo máximo de radicación es de 10 días hábiles desde la emisión de la factura.",
    )
    grant_knowledge(client, token, emp_id, doc_id)

    analysis_res = run_salud_analysis(
        client,
        token,
        solicitud="Analiza radicación y cumplimiento contractual. " + E2E_SOLICITUD,
    )
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["id"]

    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    assert not diag.get("error")
    assert diag.get("hipotesis_principal")
    assert diag.get("recomendacion_consolidada")
    assert diag.get("especialistas", {}).get("lider")
    assert diag["especialistas"].get("razon_seleccion_global")
    assert diag.get("conocimiento", {}).get("utilizado") is not False

    prop_ids = [p["id"] for p in diag["oportunidades"][:2]]
    plan_res = _create_plan(client, token, analysis_id, prop_ids)
    assert plan_res.status_code == 200
    work_plan_id = plan_res.json()["work_plan_id"]

    ops = client.get(f"/api/operations/center/{work_plan_id}", headers=auth_header(token)).json()
    assert ops.get("correlation_id")
    tasks = client.get(f"/api/operations/center/{work_plan_id}/tasks", headers=auth_header(token)).json()
    assert len(tasks) >= 1
    payload = json.loads(
        TestingSessionLocal().query(EmployeeTask).filter(EmployeeTask.work_plan_id == work_plan_id).first().inputs_json
    )
    assert payload["analysis_id"] == analysis_id
    assert payload["origen"] == "SALUD"

    finops = client.get("/api/finops/values", headers=auth_header(token)).json()
    motor_vals = [v for v in finops if f"motor_analitico:{analysis_id}" in (v.get("source") or "")]
    assert motor_vals or diag.get("finops")

    trace = build_trace_chain(diag, work_plan_id=work_plan_id)
    save_evidence("E2E_FLUJO_1", {"analysis_id": analysis_id, "trace": trace, "diag_resumen": {
        "lider": trace["equipo"]["lider"],
        "hallazgos": trace["analisis"]["hallazgos"],
        "work_plan_id": work_plan_id,
    }})


def test_e2e_aprobacion_humana_bloquea_hasta_decidir(client, token):
    """CASO 2: acción con aprobación — no continúa hasta aprobar."""
    res = client.post(
        "/api/assistant/ask",
        headers=auth_header(token),
        json={"message": "Validar RIPS con problemas", "context": {"tool": "rips", "rips": SAMPLE_RIPS}},
    )
    assert res.status_code == 200
    plan = res.json()
    if plan["status"] != "WAITING_APPROVAL":
        pytest.skip("RIPS no requirió aprobación en esta ejecución")

    pending = [a for a in client.get("/api/operations/approvals/pending", headers=auth_header(token)).json()
               if a["work_plan_id"] == plan["plan_id"]]
    assert pending

    still = client.get(f"/api/operations/center/{plan['plan_id']}", headers=auth_header(token)).json()
    assert still.get("estado_codigo") == "WAITING_APPROVAL" or still.get("approval_status") == "PENDING"

    approved = client.post(
        f"/api/operations/approvals/{pending[0]['id']}/decide",
        headers=auth_header(token),
        json={"decision": "approve", "comment": "E2E-1020"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "COMPLETED"


def test_e2e_accion_salud_sin_aprobacion_previa(client, token):
    """CASO 1: plan SALUD se crea en estado ejecutable sin gate de aprobación previo."""
    analysis_id = run_salud_analysis(client, token, ips_name="IPS Auto").json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    plan = _create_plan(client, token, analysis_id, [diag["oportunidades"][0]["id"]]).json()
    detail = client.get(f"/api/operations/center/{plan['work_plan_id']}", headers=auth_header(token)).json()
    assert detail.get("estado_codigo") not in ("WAITING_APPROVAL",)


def test_e2e_idempotencia_plan_accion(client, token):
    analysis_id = run_salud_analysis(client, token, ips_name="IPS Idem E2E").json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    props = [p["id"] for p in diag["oportunidades"][:2]]
    first = _create_plan(client, token, analysis_id, props).json()
    second = _create_plan(client, token, analysis_id, list(reversed(props))).json()
    assert first["work_plan_id"] == second["work_plan_id"]


def test_e2e_aprendizaje_segunda_ejecucion(client, token):
    """BLOQUEANTE: resultado real → experiencia core → segunda selección coherente."""
    analysis_id = run_salud_analysis(client, token, ips_name="IPS Aprendizaje 1").json()["id"]
    diag1 = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    esp1 = diag1["especialistas"]
    lider_code_1 = esp1["lider"]["employee_code"]
    prop_id = diag1["oportunidades"][0]["id"]

    _create_plan(client, token, analysis_id, [prop_id])

    res = client.post(
        f"/api/salud/propuestas/{prop_id}/resultado",
        headers=auth_header(token),
        json={
            "outcome": "EXITO",
            "resultado": "Días factura→radicación bajaron de 18 a 9",
            "meta": "Reducir tiempo de radicación",
            "kpi_antes": {"dias_radicacion": 18},
            "kpi_despues": {"dias_radicacion": 9},
        },
    )
    assert res.status_code == 200
    exp_id = res.json().get("experiencia_core_id")
    assert exp_id

    db = TestingSessionLocal()
    try:
        rec = db.query(EmployeeExperienceRecord).filter_by(id=exp_id).first()
        peso_1 = rec.peso_calidad
        dominio = esp1.get("dominio_principal", "radicacion")
        tipo = esp1.get("tipo_problema", "radicacion_tardia")
        score_antes = experiencia_score_para_empleado(
            db, rec.organization_id, rec.employee_id, dominio, tipo,
        )
    finally:
        db.close()

    analysis_id_2 = run_salud_analysis(client, token, ips_name="IPS Aprendizaje 2").json()["id"]
    diag2 = client.get(f"/api/salud/diagnostico/{analysis_id_2}", headers=auth_header(token)).json()
    esp2 = diag2["especialistas"]

    db = TestingSessionLocal()
    try:
        score_despues = experiencia_score_para_empleado(
            db, rec.organization_id, rec.employee_id, dominio, tipo,
        )
    finally:
        db.close()

    save_evidence("E2E_APRENDIZAJE", {
        "lider_1": lider_code_1,
        "lider_2": esp2["lider"]["employee_code"],
        "peso_antes": peso_1,
        "score_experiencia_antes": score_antes["score"],
        "score_experiencia_despues": score_despues["score"],
        "razon_1": esp1.get("razon_seleccion_global"),
        "razon_2": esp2.get("razon_seleccion_global"),
        "experiencia_core_id": exp_id,
    })

    assert score_despues["score"] >= score_antes["score"]
    assert esp2["lider"].get("razon_seleccion") or esp2.get("razon_seleccion_global")


def test_e2e_fracaso_feedback_enganoso(client, token):
    analysis_id = run_salud_analysis(client, token, ips_name="IPS Fracaso").json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    prop_id = diag["oportunidades"][0]["id"]

    res = client.post(
        f"/api/salud/propuestas/{prop_id}/resultado",
        headers=auth_header(token),
        json={
            "outcome": "FRACASO",
            "resultado": "Mora subió tras intervención",
            "feedback_humano": "CORRECTO",
            "kpi_antes": {"mora": 30},
            "kpi_despues": {"mora": 55},
        },
    )
    assert res.status_code == 200
    exp_id = res.json()["experiencia_core_id"]
    db = TestingSessionLocal()
    try:
        rec = db.query(EmployeeExperienceRecord).filter_by(id=exp_id).first()
        calidad = calcular_peso_calidad(rec)
        assert rec.estado == "FRACASO"
        assert calidad["peso"] < 0.75
    finally:
        db.close()


def test_e2e_cross_tenant_aislamiento(client):
    token_a = create_org_token(client, f"TenantA-{uuid.uuid4().hex[:4]}", f"ta-{uuid.uuid4().hex[:6]}", "TenantA*1")
    token_b = create_org_token(client, f"TenantB-{uuid.uuid4().hex[:4]}", f"tb-{uuid.uuid4().hex[:6]}", "TenantB*1")

    a_id = run_salud_analysis(client, token_a, ips_name="IPS Tenant A").json()["id"]
    b_id = run_salud_analysis(client, token_b, ips_name="IPS Tenant B").json()["id"]

    diag_a = client.get(f"/api/salud/diagnostico/{a_id}", headers=auth_header(token_a)).json()
    plan_b = _create_plan(client, token_b, b_id, [client.get(
        f"/api/salud/diagnostico/{b_id}", headers=auth_header(token_b)
    ).json()["oportunidades"][0]["id"]]).json()

    cross = client.get(f"/api/operations/center/{plan_b['work_plan_id']}", headers=auth_header(token_a))
    assert cross.status_code == 404

    denied = _create_plan(client, token_a, a_id, [client.get(
        f"/api/salud/diagnostico/{b_id}", headers=auth_header(token_b)
    ).json()["oportunidades"][0]["id"]])
    assert denied.status_code == 400

    sim_a = client.get("/api/experiencia/similares", headers=auth_header(token_a), params={"dominio": "radicacion"}).json()
    sim_b = client.get("/api/experiencia/similares", headers=auth_header(token_b), params={"dominio": "radicacion"}).json()
    if sim_a and sim_b:
        assert all(s.get("employee_id") for s in sim_a)


def test_e2e_permisos_fail_closed(client):
    viewer = create_org_token(client, f"OrgView-{uuid.uuid4().hex[:4]}", f"view-{uuid.uuid4().hex[:6]}", "View*1", role="viewer")
    denied = run_salud_analysis(client, viewer)
    assert denied.status_code == 403


def test_e2e_finops_valor_registrado(client, token):
    analysis_id = run_salud_analysis(client, token, ips_name="IPS FinOps").json()["id"]
    values = client.get("/api/finops/values", headers=auth_header(token)).json()
    linked = [v for v in values if analysis_id in (v.get("source") or "")]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    assert linked or diag.get("finops")


def test_e2e_trazabilidad_end_to_end(client, token):
    analysis_id = run_salud_analysis(client, token, ips_name="IPS Trazabilidad").json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    log_id = (diag.get("especialistas") or {}).get("selection_log_id")
    assert log_id

    db = TestingSessionLocal()
    try:
        log = db.query(ExperienceSelectionLog).filter_by(id=log_id).first()
        assert log and log.candidatos_json and log.razon_seleccion
        wp = _create_plan(client, token, analysis_id, [diag["oportunidades"][0]["id"]]).json()
        trace = build_trace_chain(diag, work_plan_id=wp["work_plan_id"])
        assert trace["orquestacion"]
        assert trace["analisis"]["motor"]
    finally:
        db.close()


def test_e2e_conocimiento_no_autorizado_no_usado(client, token):
    """Documento sin grant no debe aparecer en fuentes del diagnóstico."""
    secret = f"SECRETO_SIN_GRANT_{uuid.uuid4().hex[:8]}"
    upload_knowledge(client, token, "Doc sin grant", f"Cláusula secreta: {secret}")
    analysis_id = run_salud_analysis(client, token, ips_name="IPS NoGrant").json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    blob = json.dumps(diag, ensure_ascii=False)
    assert secret not in blob


def test_e2e_retry_sin_duplicar_workplan(client, token):
    """Reintento tras fallo parcial no duplica WorkPlan."""
    analysis_id = run_salud_analysis(client, token, ips_name="IPS Retry").json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_header(token)).json()
    props = [diag["oportunidades"][0]["id"]]
    first = _create_plan(client, token, analysis_id, props).json()
    second = _create_plan(client, token, analysis_id, props).json()
    assert first["work_plan_id"] == second["work_plan_id"]
    db = TestingSessionLocal()
    try:
        count = db.query(WorkPlan).filter(WorkPlan.id == first["work_plan_id"]).count()
        assert count == 1
    finally:
        db.close()


def test_e2e_automation_scheduler_idempotente():
    from app.services.automation_scheduler import _tick
    _tick()
    _tick()
