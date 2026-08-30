"""Gate consolidado post-6D — correcciones P1 A/B/C/D."""

from __future__ import annotations

import json
import threading
import uuid

import pytest
from fastapi.testclient import TestClient

from app.employee_audit_models import EmployeeAuditFinding, EmployeeImprovementTrace
from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.optimization_models import OptimizacionItem, OptimizacionRecomendacion
from app.orchestration_models import AIEmployee, EmployeeLimits, WorkPlan
from app.security import hash_password
from app.config import settings
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.operations]


def _admin_user(db):
    return db.query(User).filter(User.username == settings.bootstrap_admin_username).first()


def _employee_with_failures(db, org_id: str, user_id: str, code: str) -> str:
    emp = AIEmployee(
        organization_id=org_id,
        code=code,
        name=f"Gate {code}",
        specialty="DOCINT",
        lifecycle_status="ACTIVE",
        status="DISPONIBLE",
        is_active=True,
    )
    db.add(emp)
    db.flush()
    db.add(EmployeeLimits(employee_id=emp.id, daily_cost_limit=100.0))
    for i in range(6):
        db.add(
            WorkPlan(
                organization_id=org_id,
                user_id=user_id,
                employee_id=emp.id,
                correlation_id=f"corr-gate-{code}-{i}",
                request="fail",
                objective="fail",
                status="FAILED",
                error="err",
            )
        )
    db.commit()
    return emp.id


def _run_audit(client, token, emp_id: str):
    return client.post(
        "/api/empleados-auditor/ejecutar",
        headers=auth_header(token),
        json={"employee_id": emp_id},
    )


def _open_finding(db, org_id: str, emp_id: str) -> EmployeeAuditFinding:
    finding = (
        db.query(EmployeeAuditFinding)
        .filter(
            EmployeeAuditFinding.organization_id == org_id,
            EmployeeAuditFinding.employee_id == emp_id,
            EmployeeAuditFinding.status == "ABIERTO",
        )
        .first()
    )
    assert finding is not None
    return finding


def test_g1_deviation_requires_explicit_authorization(client: TestClient, token: str):
    """G1: operación distinta a recomendación exige decisión explícita."""
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"g1-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding_id = _open_finding(db, org_id, emp_id).id
        assert _open_finding(db, org_id, emp_id).recommended_action == "SOLICITAR_REVISION_HUMANA"
    finally:
        db.close()

    trace_id = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    ).json()["trace_id"]

    denied = client.post(
        f"/api/empleados-auditor/mejoras/{trace_id}/ejecutar",
        headers=auth_header(token),
        json={"operation": "capacitar", "payload": {"training_type": "INSTRUCTIONS", "reason": "x"}},
    )
    assert denied.status_code == 400
    assert "authorize_deviation" in denied.json()["detail"].lower() or "difere" in denied.json()["detail"].lower()

    allowed = client.post(
        f"/api/empleados-auditor/mejoras/{trace_id}/ejecutar",
        headers=auth_header(token),
        json={
            "operation": "capacitar",
            "payload": {
                "authorize_deviation": True,
                "deviation_justification": "Decisión humana: capacitar antes de solicitar aprobación",
                "training_type": "INSTRUCTIONS",
                "reason": "Capacitación previa autorizada",
                "source": "test-g1",
            },
        },
    )
    assert allowed.status_code == 200
    body = allowed.json()
    assert body.get("human_decision", {}).get("is_deviation") is True
    assert body.get("auto_execution_blocked") is True


def test_g2_solicitar_aprobacion_transitions_trabajo(client: TestClient, token: str):
    """G2: hallazgo auditor no duplica obligación con aprobación pendiente."""
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"g2-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding_id = _open_finding(db, org_id, emp_id).id
    finally:
        db.close()

    trace_id = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    ).json()["trace_id"]

    exec_res = client.post(
        f"/api/empleados-auditor/mejoras/{trace_id}/ejecutar",
        headers=auth_header(token),
        json={
            "operation": "solicitar_aprobacion",
            "payload": {"kind": "PUBLISH", "reason": "Aprobación por hallazgo gate G2"},
        },
    )
    assert exec_res.status_code == 200

    items = client.get("/api/trabajo/items", headers=auth_header(token)).json()["items"]
    auditor_rows = [
        i for i in items
        if i.get("metadata", {}).get("finding_id") == finding_id or i.get("source_id") == finding_id
    ]
    approval_rows = [
        i for i in items
        if i["tipo"] == "aprobacion" and i.get("metadata", {}).get("auditor_finding_id") == finding_id
    ]
    assert len(auditor_rows) == 0
    assert len(approval_rows) == 1
    assert approval_rows[0]["metadata"].get("workflow_stage") == "SOLICITUD_APROBACION"


def test_g3_dedup_oportunidad_vs_1290_humana(client: TestClient, auth_headers):
    """G3: oportunidad en ejecución humana 1290 no duplica oportunidad_aprobacion."""
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        opp = Opportunity(
            organization_id=admin.organization_id,
            codigo=f"OPP-G3-{uuid.uuid4().hex[:4]}",
            tipo="financiera",
            dominio="financiero",
            titulo="Oportunidad gate G3",
            valor_potencial=1000,
            costo_estimado=100,
            impacto_estimado=500,
            confianza=0.8,
            urgencia="MEDIA",
            riesgo="MEDIO",
            estado="PENDIENTE_APROBACION",
        )
        db.add(opp)
        db.flush()
        rec = OptimizacionRecomendacion(
            organization_id=admin.organization_id,
            codigo=f"OPT-G3-{uuid.uuid4().hex[:6]}",
            estado="APROBADA",
            objetivo="MAXIMIZAR_VALOR",
            es_simulacion=False,
            trazabilidad_json=json.dumps({
                "ejecucion": {
                    "execution_status": "PENDIENTE_EJECUCION_HUMANA",
                    "execution_type": "HUMANA_EXTERNA",
                    "correlation_id": f"corr-g3-{uuid.uuid4().hex[:8]}",
                    "oportunidades": [{"opportunity_id": opp.id, "orden": 1}],
                }
            }),
            created_by=admin.id,
        )
        db.add(rec)
        db.flush()
        db.add(OptimizacionItem(
            organization_id=admin.organization_id,
            recomendacion_id=rec.id,
            opportunity_id=opp.id,
            orden=1,
            seleccionado=True,
        ))
        db.commit()
        opp_id = opp.id
        rec_id = rec.id
    finally:
        db.close()

    items = client.get("/api/trabajo/items", headers=auth_headers).json()["items"]
    opp_rows = [i for i in items if i["tipo"] == "oportunidad_aprobacion" and i["source_id"] == opp_id]
    opt_rows = [i for i in items if i["tipo"] == "optimizacion_pendiente_humana" and i["source_id"] == rec_id]
    assert len(opp_rows) == 0
    assert len(opt_rows) == 1


def test_g4_automatica_no_autoaprueba_oportunidad(client: TestClient, auth_headers):
    """G4: AUTOMÁTICA no sustituye aprobación humana de oportunidad."""
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        opp = Opportunity(
            organization_id=admin.organization_id,
            codigo=f"OPP-G4-{uuid.uuid4().hex[:4]}",
            tipo="financiera",
            dominio="financiero",
            titulo="Oportunidad gate G4",
            valor_potencial=1000,
            costo_estimado=100,
            impacto_estimado=500,
            confianza=0.8,
            urgencia="MEDIA",
            riesgo="MEDIO",
            estado="PENDIENTE_APROBACION",
        )
        db.add(opp)
        db.flush()
        rec = OptimizacionRecomendacion(
            organization_id=admin.organization_id,
            codigo=f"OPT-G4-{uuid.uuid4().hex[:6]}",
            estado="APROBADA",
            objetivo="MAXIMIZAR_VALOR",
            es_simulacion=False,
            factible=True,
            created_by=admin.id,
        )
        db.add(rec)
        db.flush()
        db.add(OptimizacionItem(
            organization_id=admin.organization_id,
            recomendacion_id=rec.id,
            opportunity_id=opp.id,
            orden=1,
            seleccionado=True,
        ))
        db.commit()
        rec_id = rec.id
    finally:
        db.close()

    res = client.post(
        f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
        headers=auth_headers,
        json={"tipo_ejecucion": "AUTOMATICA"},
    )
    assert res.status_code in (400, 422)
    detail = str(res.json().get("detail", "")).lower()
    assert "aprobación humana" in detail or "aprobacion humana" in detail or "no está autorizada" in detail


def test_g8_support_assignable_agents(client: TestClient, token: str):
    """G8: selector de usuarios asignables en soporte."""
    res = client.get("/api/soporte/agentes-asignables", headers=auth_header(token))
    assert res.status_code == 200
    agents = res.json()
    assert isinstance(agents, list)
    assert len(agents) >= 1
    assert all("nombre" in a and "username" in a and "id" in a for a in agents)


def test_concurrency_auditor_factory_no_double_execution(client: TestClient, token: str):
    """P2-C: acciones simultáneas no generan doble ejecución."""
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"conc-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding_id = _open_finding(db, org_id, emp_id).id
    finally:
        db.close()

    trace_id = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    ).json()["trace_id"]

    results: list[int] = []
    errors: list[str] = []

    def _exec(key: str):
        r = client.post(
            f"/api/empleados-auditor/mejoras/{trace_id}/ejecutar",
            headers=auth_header(token),
            json={
                "operation": "solicitar_aprobacion",
                "payload": {"kind": "PUBLISH", "reason": f"conc {key}"},
                "idempotency_key": key,
            },
        )
        results.append(r.status_code)
        if r.status_code >= 400:
            errors.append(str(r.json().get("detail", "")))

    t1 = threading.Thread(target=_exec, args=("conc-a",))
    t2 = threading.Thread(target=_exec, args=("conc-b",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(results) == 2
    assert results.count(200) <= 1
    assert all(code in (200, 400) for code in results)

    db = TestingSessionLocal()
    try:
        trace = db.query(EmployeeImprovementTrace).filter(EmployeeImprovementTrace.id == trace_id).first()
        assert trace is not None
        assert trace.status in ("COMPLETED", "IN_PROGRESS", "FAILED")
    finally:
        db.close()


def test_validate_migrations_runs_without_pythonpath():
    """G6: validate_migrations ejecutable desde backend/ sin PYTHONPATH."""
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "scripts/validate_migrations.py"],
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1] / "backend"),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Alembic head único" in proc.stdout
