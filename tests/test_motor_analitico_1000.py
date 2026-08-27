"""Tests MOTOR-ANALITICO-1000 — motor transversal de diagnóstico IPS."""

from __future__ import annotations

import uuid

import pytest

from app.fixtures.motor_analitico_datasets import get_case_request, get_motor_dataset, list_motor_cases
from app.models import Organization, User
from app.security import hash_password
from app.services.motor_analitico.pipeline import fingerprint_motor_result, run_motor_analitico
from app.services.salud_engine import get_diagnostico, run_ips_analysis
from app.services.salud_indicators import compute_all_indicators
from app.services.salud_normalization import profile_data_quality
from app.services.salud_specialist_selection import select_specialists
from conftest import TestingSessionLocal

pytestmark = [pytest.mark.salud]


@pytest.fixture
def motor_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _admin_ctx(motor_db):
    admin = motor_db.query(User).filter(User.username == "admin").first()
    assert admin is not None
    return admin.organization_id, admin.id


def _run_case_inline(db, org_id, user_id, case_id: str):
    return run_ips_analysis(
        db,
        organization_id=org_id,
        user_id=user_id,
        ips_name=f"IPS Motor {case_id}",
        request_text=get_case_request(case_id),
        inline_datasets=get_motor_dataset(case_id),
    )


def test_motor_cases_list():
    cases = list_motor_cases()
    ids = {c["id"] for c in cases}
    assert ids >= {"A", "B", "C", "D", "E", "CONSULTOR"}


def test_data_sufficiency_case_e():
    datasets = get_motor_dataset("E")
    profiles = {k: profile_data_quality(k, v) for k, v in datasets.items()}
    indicators = compute_all_indicators(datasets)
    motor = run_motor_analitico(
        datasets=datasets,
        data_profiles=profiles,
        indicators=indicators,
        hallazgos=[],
        propuestas=[],
        specialists={"asignaciones": [], "dominios": []},
        request_text=get_case_request("E"),
    )
    assert motor["suficiencia_datos"]["clasificacion"] == "INSUFICIENTE"
    assert motor["hipotesis"][0]["id"] == "H0"


def test_hypothesis_differs_case_a_vs_b(motor_db):
    org_id, user_id = _admin_ctx(motor_db)
    a = _run_case_inline(motor_db, org_id, user_id, "A")
    b = _run_case_inline(motor_db, org_id, user_id, "B")
    diag_a = get_diagnostico(motor_db, org_id, a.id)
    diag_b = get_diagnostico(motor_db, org_id, b.id)
    hyp_a = diag_a.get("hipotesis_principal", {}).get("id")
    hyp_b = diag_b.get("hipotesis_principal", {}).get("id")
    assert hyp_a != hyp_b or diag_a.get("hipotesis_principal", {}).get("titulo") != diag_b.get("hipotesis_principal", {}).get("titulo")


def test_anti_prefabricated_response(motor_db):
    org_id, user_id = _admin_ctx(motor_db)
    fingerprints = []
    for case_id in ("A", "B", "C", "D"):
        analysis = _run_case_inline(motor_db, org_id, user_id, case_id)
        diag = get_diagnostico(motor_db, org_id, analysis.id)
        motor = {
            "hipotesis_principal": diag.get("hipotesis_principal"),
            "priorizacion": diag.get("priorizacion"),
            "suficiencia_datos": diag.get("suficiencia_datos"),
            "finops": diag.get("finops"),
        }
        fingerprints.append(fingerprint_motor_result(motor))

    hyp_ids = [f["hipotesis_principal_id"] for f in fingerprints]
    assert len(set(hyp_ids)) >= 3, f"Hipótesis principales demasiado similares: {hyp_ids}"

    top_sets = [tuple(f["top_ranking_titulos"]) for f in fingerprints]
    assert len(set(top_sets)) >= 2, "Rankings idénticos entre casos distintos"

    titles_all = [h for f in fingerprints for h in f["top_ranking_titulos"] if h]
    assert len(set(titles_all)) >= 4, "Propuestas/hallazgos prefabricados repetidos"


def test_case_a_radicacion_signal(motor_db):
    org_id, user_id = _admin_ctx(motor_db)
    analysis = _run_case_inline(motor_db, org_id, user_id, "A")
    diag = get_diagnostico(motor_db, org_id, analysis.id)
    primary = diag.get("hipotesis_principal", {})
    assert primary.get("id") in ("H2", "H9", "H10")
    rad = diag["indicadores"]["radicacion"]
    assert rad["tiempo_promedio_factura_radicacion_dias"] > 10


def test_case_b_glosas_signal(motor_db):
    org_id, user_id = _admin_ctx(motor_db)
    analysis = _run_case_inline(motor_db, org_id, user_id, "B")
    diag = get_diagnostico(motor_db, org_id, analysis.id)
    primary = diag.get("hipotesis_principal", {})
    assert primary.get("id") in ("H3", "H4", "H5", "H10")
    assert diag["indicadores"]["glosas"]["porcentaje_glosa"] > 8


def test_case_c_pagador_signal(motor_db):
    org_id, user_id = _admin_ctx(motor_db)
    analysis = _run_case_inline(motor_db, org_id, user_id, "C")
    diag = get_diagnostico(motor_db, org_id, analysis.id)
    primary = diag.get("hipotesis_principal", {})
    assert primary.get("id") in ("H7", "H8")
    rad = diag["indicadores"]["radicacion"]
    assert rad["tiempo_promedio_factura_radicacion_dias"] <= 5


def test_case_e_insufficient(motor_db):
    org_id, user_id = _admin_ctx(motor_db)
    analysis = _run_case_inline(motor_db, org_id, user_id, "E")
    diag = get_diagnostico(motor_db, org_id, analysis.id)
    assert diag.get("suficiencia_datos", {}).get("clasificacion") == "INSUFICIENTE"


def test_motor_api_demo(client, auth_headers):
    res = client.get("/api/salud/motor/casos", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 5

    demo = client.get("/api/salud/motor/demo/A", headers=auth_headers)
    assert demo.status_code == 200
    assert "datasets" in demo.json()


def test_motor_analysis_api(client, auth_headers):
    demo = client.get("/api/salud/motor/demo/B", headers=auth_headers).json()
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS API Motor B",
        "request_text": demo["request_text"],
        "inline_datasets": demo["datasets"],
    })
    assert res.status_code == 200
    diag = client.get(f"/api/salud/diagnostico/{res.json()['id']}", headers=auth_headers).json()
    assert len(diag.get("hipotesis", [])) > 0
    assert diag.get("priorizacion", {}).get("ranking")
    assert diag.get("escenarios", {}).get("escenarios")


def test_natural_questions_motor(client, auth_headers):
    demo = client.get("/api/salud/motor/demo/C", headers=auth_headers).json()
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Preguntas",
        "request_text": demo["request_text"],
        "inline_datasets": demo["datasets"],
    })
    aid = res.json()["id"]
    q = client.post(f"/api/salud/pregunta/{aid}", headers=auth_headers, json={
        "pregunta": "¿Cuánto podría recuperar?",
    })
    assert q.status_code == 200
    body = q.json()
    assert "PROYECTADO" in body.get("clasificacion", "") or "recuperable" in body.get("respuesta", "").lower()


def test_tenant_isolation_motor(client):
    db = TestingSessionLocal()
    org_a = Organization(name=f"MotorA-{uuid.uuid4().hex[:6]}")
    org_b = Organization(name=f"MotorB-{uuid.uuid4().hex[:6]}")
    db.add_all([org_a, org_b])
    db.flush()
    user_a = User(
        organization_id=org_a.id,
        username=f"a-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Ta*12345"),
        role="admin",
        is_active=True,
    )
    user_b = User(
        organization_id=org_b.id,
        username=f"b-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Tb*12345"),
        role="admin",
        is_active=True,
    )
    db.add_all([user_a, user_b])
    db.commit()
    user_a_name = user_a.username
    user_b_name = user_b.username
    db.close()

    ta = client.post("/api/auth/login", json={"username": user_a_name, "password": "Ta*12345"}).json()["access_token"]
    tb = client.post("/api/auth/login", json={"username": user_b_name, "password": "Tb*12345"}).json()["access_token"]
    ha, hb = {"Authorization": f"Bearer {ta}"}, {"Authorization": f"Bearer {tb}"}

    demo = get_motor_dataset("A")
    ra = client.post("/api/salud/analisis", headers=ha, json={"ips_name": "A", "inline_datasets": demo}).json()
    denied = client.get(f"/api/salud/diagnostico/{ra['id']}", headers=hb)
    assert denied.status_code == 404


def test_specialist_selection_has_reason(motor_db):
    org_id, _ = _admin_ctx(motor_db)
    datasets = get_motor_dataset("D")
    specialists = select_specialists(motor_db, org_id, get_case_request("D"), list(datasets.keys()))
    assert specialists.get("asignaciones")
    for a in specialists["asignaciones"]:
        assert a.get("factors") is not None
        assert a["score"] > 0


def test_case_d_knowledge_conflicts_degrade_hypotheses():
    """D-04: conflictos documentales deben degradar hipótesis causales (10 vs 15 días)."""
    from app.services.motor_analitico.hypothesis_engine import generate_hypotheses

    datasets = get_motor_dataset("D")
    profiles = {k: profile_data_quality(k, v) for k, v in datasets.items()}
    indicators = compute_all_indicators(datasets)
    sufficiency = {"clasificacion": "SUFICIENTE", "dominios": list(datasets.keys())}
    knowledge_ctx = {
        "conflictos": [
            {
                "analisis": {
                    "limites_unicos": [10, 15],
                    "requiere_validacion": True,
                }
            }
        ],
        "requiere_validacion": True,
    }

    hypotheses = generate_hypotheses(
        indicators, datasets, sufficiency, hallazgos=[], knowledge_ctx=knowledge_ctx
    )
    h2 = next(h for h in hypotheses if h["id"] == "H2")
    assert h2["estado"] != "CONFIRMADA"
    assert any("contradict" in str(e).lower() for e in h2.get("evidencia_en_contra", []))
    assert any("documental" in str(i).lower() for i in h2.get("informacion_faltante", []))


def test_data_sufficiency_cash_question_without_cartera():
    """Caso E: pregunta de caja sin dataset de cartera → INSUFICIENTE."""
    from app.services.motor_analitico.data_sufficiency import assess_data_sufficiency

    profiles = {
        "facturacion": {
            "registros": 8,
            "completitud": 0.9,
            "nivel_calidad": "BUENA",
            "duplicados": 0,
            "inconsistencias": [],
            "fechas": {},
        }
    }
    indicators = {
        "facturacion": {"disponible": True},
        "cartera": {"disponible": False},
        "radicacion": {"disponible": False},
        "glosas": {"disponible": False},
        "pagos": {"disponible": False},
    }
    result = assess_data_sufficiency(
        profiles,
        indicators,
        "¿Por qué disminuyó nuestra caja y cuánto podríamos recuperar?",
    )
    assert result["clasificacion"] == "INSUFICIENTE"


def test_consultor_case_rich_output(motor_db):
    org_id, user_id = _admin_ctx(motor_db)
    analysis = _run_case_inline(motor_db, org_id, user_id, "CONSULTOR")
    diag = get_diagnostico(motor_db, org_id, analysis.id)
    assert len(diag.get("hallazgos", [])) >= 2
    assert diag.get("recomendacion_consolidada", {}).get("recomendacion")
    assert len(diag.get("alternativas", [])) >= 2
    assert diag.get("contrastes")
