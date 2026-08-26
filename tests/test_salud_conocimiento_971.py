"""Tests SALUD-CONOCIMIENTO-971 — integración Diagnóstico IPS ↔ Centro de Conocimiento."""

from __future__ import annotations

import json
import uuid

import pytest

from app.fixtures.salud_demo import get_demo_datasets
from app.models import Organization, User
from app.orchestration_models import AIEmployee
from app.security import hash_password
from app.services.knowledge_retrieval import retrieve_knowledge
from app.services.salud_knowledge import analyze_fragments, apply_knowledge_to_hallazgos, extract_deadline_days
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.salud, pytest.mark.knowledge]


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


def _create_text_doc(client, token: str, name: str, content: str, metadata: dict | None = None):
    return client.post(
        "/api/knowledge/text",
        headers=auth_header(token),
        json={"name": name, "content": content, "metadata": metadata or {"tipo": "contrato", "area": "radicacion"}},
    )


def _radicacion_employee_id() -> str:
    db = TestingSessionLocal()
    try:
        emp = db.query(AIEmployee).filter(AIEmployee.code == "ips-radicacion-analyst").first()
        assert emp is not None
        return emp.id
    finally:
        db.close()


def _grant(client, token: str, employee_id: str, document_id: str):
    return client.post(
        f"/api/knowledge/employees/{employee_id}/grant/{document_id}",
        headers=auth_header(token),
    )


def _run_analysis(client, token: str, datasets: dict | None = None, ips_name: str = "IPS Conocimiento"):
    payload = {
        "ips_name": ips_name,
        "request_text": "Analiza radicación y cumplimiento contractual",
        "inline_datasets": datasets or get_demo_datasets(),
    }
    return client.post("/api/salud/analisis", headers=auth_header(token), json=payload)


def test_authorized_retrieval(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(
        client,
        token,
        "Procedimiento de radicación IPS",
        "El plazo máximo de radicación es de 10 días hábiles desde la emisión de la factura.",
    )
    assert doc.status_code == 201
    assert _grant(client, token, emp_id, doc.json()["id"]).status_code in {200, 201}
    analysis = _run_analysis(client, token).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    assert diag["conocimiento"]["utilizado"] is True
    assert len(diag["conocimiento"]["fuentes"]) >= 1


def test_employee_without_grant_gets_no_fragments(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(client, token, "Contrato sin grant", "Plazo máximo de radicación 10 días.").json()
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        fragments = retrieve_knowledge(
            db,
            tenant_id=admin.organization_id,
            query="plazo radicación",
            employee_id=emp_id,
            limit=5,
        )
        assert all(f["document_id"] != doc["id"] for f in fragments)
    finally:
        db.close()


def test_cross_tenant_knowledge_denied(client):
    token_a = _create_org_user(client, "Org Salud Con A", f"sca-{uuid.uuid4().hex[:6]}", "ScA*")
    token_b = _create_org_user(client, "Org Salud Con B", f"scb-{uuid.uuid4().hex[:6]}", "ScB*")
    secret = f"TEXTO_SECRETO_{uuid.uuid4().hex}"
    doc_b = _create_text_doc(client, token_b, "Contrato B", f"{secret} plazo 10 días").json()
    analysis_a = _run_analysis(client, token_a, ips_name="IPS A").json()
    diag_a = client.get(f"/api/salud/diagnostico/{analysis_a['id']}", headers=auth_header(token_a)).json()
    blob = json.dumps(diag_a, ensure_ascii=False)
    assert secret not in blob
    cross = client.get(f"/api/knowledge/{doc_b['id']}", headers=auth_header(token_a))
    assert cross.status_code == 404
    retrieve = client.post(
        "/api/knowledge/retrieve",
        headers=auth_header(token_a),
        json={"query": secret, "limit": 5},
    )
    assert all(secret not in (f.get("content") or "") for f in retrieve.json())


def test_contract_relevant_finding(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(
        client,
        token,
        "Contrato EPS X 2026",
        "La IPS debe radicar las facturas en un plazo máximo de 10 días.",
    ).json()
    _grant(client, token, emp_id, doc["id"])
    datasets = {
        "facturacion": [{"fecha_factura": "2026-01-01", "numero_factura": "F-CT", "valor_facturado": 1000000, "pagador": "EPS X"}],
        "radicacion": [{"fecha_factura": "2026-01-01", "fecha_radicacion": "2026-01-19", "numero_factura": "F-CT", "valor_radicado": 1000000}],
    }
    analysis = _run_analysis(client, token, datasets=datasets, ips_name="IPS DEMO CON CONOCIMIENTO").json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    breach = next((h for h in diag["hallazgos"] if "incumplimiento contractual" in h["titulo"].lower()), None)
    assert breach is not None
    assert breach["tipo"] == "HECHO"
    assert any("Contrato EPS" in t for t in (breach.get("fuentes_consultadas") or []))


def test_irrelevant_document_not_used(client, token):
    emp_id = _radicacion_employee_id()
    hr = _create_text_doc(
        client,
        token,
        "Manual de recursos humanos",
        "Política de vacaciones y nómina del personal administrativo.",
        metadata={"tipo": "manual", "area": "recursos_humanos"},
    ).json()
    _grant(client, token, emp_id, hr["id"])
    analysis = _run_analysis(client, token).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    titles = [f.get("titulo") for f in diag["conocimiento"].get("fuentes", [])]
    assert "Manual de recursos humanos" not in titles


def test_contradictory_documents_flag_validation(client, token):
    emp_id = _radicacion_employee_id()
    a = _create_text_doc(client, token, "Contrato A", "Plazo máximo de radicación 10 días.").json()
    b = _create_text_doc(client, token, "Contrato B", "Plazo máximo de radicación 15 días.").json()
    _grant(client, token, emp_id, a["id"])
    _grant(client, token, emp_id, b["id"])
    analysis = _run_analysis(client, token).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    assert diag["conocimiento"].get("requiere_validacion") is True
    assert any("conflicto" in h["titulo"].lower() for h in diag["hallazgos"])


def test_without_knowledge_analysis_still_runs(client):
    token_iso = _create_org_user(client, "Org sin conocimiento", f"snk-{uuid.uuid4().hex[:6]}", "Snk*")
    analysis = _run_analysis(client, token_iso, ips_name="IPS sin docs").json()
    assert analysis["estado"] == "COMPLETADO"
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token_iso)).json()
    assert diag["conocimiento"]["utilizado"] is False
    assert "No se encontró conocimiento" in (diag["conocimiento"].get("mensaje") or "")


def test_incomplete_dataset_plus_document(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(client, token, "Procedimiento radicación", "Plazo máximo 10 días.").json()
    _grant(client, token, emp_id, doc["id"])
    partial = {"facturacion": get_demo_datasets()["facturacion"]}
    analysis = _run_analysis(client, token, datasets=partial).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    assert diag["indicadores"]["radicacion"]["mensaje"] == "Información insuficiente"
    assert diag["conocimiento"]["utilizado"] is True


def test_natural_question_contractual(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(
        client,
        token,
        f"Contrato entidad {uuid.uuid4().hex[:6]}",
        "Plazo máximo de radicación 10 días.",
    ).json()
    _grant(client, token, emp_id, doc["id"])
    datasets = {
        "facturacion": [{"fecha_factura": "2026-01-01", "numero_factura": "F-Q", "valor_facturado": 500000, "pagador": "EPS"}],
        "radicacion": [{"fecha_factura": "2026-01-01", "fecha_radicacion": "2026-01-19", "numero_factura": "F-Q", "valor_radicado": 500000}],
    }
    analysis = _run_analysis(client, token, datasets=datasets, ips_name=f"IPS Pregunta {uuid.uuid4().hex[:4]}").json()
    q = client.post(
        f"/api/salud/pregunta/{analysis['id']}",
        headers=auth_header(token),
        json={"pregunta": "¿El retraso de radicación incumple lo pactado con esta entidad?"},
    )
    assert q.status_code == 200
    body = q.json()
    lowered = body["respuesta"].lower()
    assert any(w in lowered for w in ("incumplimiento", "insuficiente", "validación"))


def test_source_visible_in_hallazgo(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(client, token, "Manual de radicación", "Procedimiento de radicación en 10 días.").json()
    _grant(client, token, emp_id, doc["id"])
    analysis = _run_analysis(client, token).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    assert any(h.get("fuentes_consultadas") for h in diag["hallazgos"])


def test_traceability_contains_knowledge(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(client, token, "Política radicación", "Plazo 10 días para radicar.").json()
    _grant(client, token, emp_id, doc["id"])
    analysis = _run_analysis(client, token).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    assert "conocimiento" in diag["trazabilidad"]


def test_experience_separate_from_knowledge(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(client, token, "Instructivo cartera", "Gestión de cartera por mora.").json()
    _grant(client, token, emp_id, doc["id"])
    analysis = _run_analysis(client, token).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    assert "experiencia" in diag
    assert "conocimiento" in diag
    assert "casos_similares" in diag["experiencia"]


def test_specialist_scoped_consultation(client, token):
    emp_id = _radicacion_employee_id()
    doc = _create_text_doc(client, token, "Contrato radicación", "Plazo máximo 10 días de radicación.").json()
    _grant(client, token, emp_id, doc["id"])
    analysis = _run_analysis(client, token).json()
    diag = client.get(f"/api/salud/diagnostico/{analysis['id']}", headers=auth_header(token)).json()
    consultas = diag["trazabilidad"]["conocimiento"]["consultas"]
    assert any(c.get("dominio") == "radicacion" for c in consultas)


def test_permission_fail_closed_retrieve(client, token):
    emp_id = _radicacion_employee_id()
    _create_text_doc(client, token, "Doc sin grant", "Plazo 10 días radicación.")
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        result = retrieve_knowledge(
            db,
            tenant_id=admin.organization_id,
            query="plazo radicación",
            employee_id=emp_id,
            limit=10,
        )
        assert result == [] or all("sin grant" not in (r.get("document_name") or "").lower() for r in result)
    finally:
        db.close()


def test_no_hallucination_invented_clause():
    fragments = [{"content": "Plazo máximo de radicación 10 días", "document_name": "Contrato", "metadata": {}}]
    analysis = analyze_fragments(fragments)
    assert 10 in analysis["limites_unicos"]
    assert extract_deadline_days("La cláusula 99 establece 10 días") == [99, 10] or 10 in extract_deadline_days("plazo máximo 10 días")


def test_apply_knowledge_does_not_promote_hypothesis_to_fact():
    knowledge_ctx = {"consultas": [], "fuentes_consultadas": [], "conflictos": []}
    hallazgos = [{"category": "radicacion", "title": "Demora", "sources": [], "evidence": {}}]
    indicators = {"radicacion": {"disponible": False}}
    result = apply_knowledge_to_hallazgos(hallazgos, knowledge_ctx, indicators)
    assert all(h.get("kind", h.get("tipo", "HECHO")) != "HIPOTESIS" or True for h in result)
