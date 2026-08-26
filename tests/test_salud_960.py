"""Tests SALUD-960 — motor especializado IPS."""

import json
import uuid

import pytest

from app.fixtures.salud_demo import get_demo_datasets
from app.models import Organization, User
from app.security import hash_password
from app.services.salud_engine import run_ips_analysis
from app.services.salud_indicators import INSUFICIENTE, calc_facturacion, compute_all_indicators
from app.services.salud_normalization import normalize_record, profile_data_quality
from app.services.salud_specialist_selection import detect_required_domains, select_specialists
from conftest import TestingSessionLocal

pytestmark = [pytest.mark.salud]


@pytest.fixture
def demo_datasets():
    return get_demo_datasets()


@pytest.fixture
def salud_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_dataset_completo(demo_datasets):
    indicators = compute_all_indicators(demo_datasets)
    assert "facturacion" in indicators["disponibles"]
    assert "radicacion" in indicators["disponibles"]
    assert "glosas" in indicators["disponibles"]
    assert "cartera" in indicators["disponibles"]
    assert indicators["facturacion"]["valor_facturado"] > 0


def test_dataset_parcial():
    partial = {"facturacion": get_demo_datasets()["facturacion"]}
    indicators = compute_all_indicators(partial)
    assert indicators["facturacion"]["disponible"] is True
    assert indicators["radicacion"]["mensaje"] == INSUFICIENTE
    assert "radicacion" in indicators["no_disponibles"]


def test_campos_faltantes():
    records = [{"campo_desconocido": "x"}]
    quality = profile_data_quality("facturacion", records)
    assert quality["registros"] == 1
    assert len(quality["campos_faltantes"]) > 0
    assert quality["nivel_calidad"] in ("BAJA", "INSUFICIENTE")


def test_normalizacion():
    record = {"Fecha Factura": "2026-01-01", "Valor Facturado": 1000, "Nro Factura": "F-1"}
    norm = normalize_record("facturacion", record)
    assert norm["fecha_factura"] == "2026-01-01"
    assert norm["valor_facturado"] == 1000
    assert norm["numero_factura"] == "F-1"


def test_indicador_facturacion(demo_datasets):
    result = calc_facturacion(demo_datasets["facturacion"])
    assert result["disponible"] is True
    assert result["cantidad_facturas"] == 8
    assert result["valor_facturado"] == 276000000


def test_indicador_radicacion(demo_datasets):
    indicators = compute_all_indicators(demo_datasets)
    rad = indicators["radicacion"]
    assert rad["disponible"] is True
    assert rad["facturas_no_radicadas"] == 2


def test_indicador_glosas(demo_datasets):
    indicators = compute_all_indicators(demo_datasets)
    glosas = indicators["glosas"]
    assert glosas["disponible"] is True
    assert glosas["valor_glosado"] == 15700000


def test_indicador_cartera(demo_datasets):
    indicators = compute_all_indicators(demo_datasets)
    cartera = indicators["cartera"]
    assert cartera["disponible"] is True
    assert cartera["aging"]["91+"] == 38000000


def test_historico(salud_db, demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Demo",
        "request_text": "Analiza la situación financiera y operativa",
        "inline_datasets": demo_datasets,
    })
    assert res.status_code == 200
    analysis_id = res.json()["id"]

    res2 = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Demo",
        "request_text": "Segundo análisis",
        "inline_datasets": demo_datasets,
    })
    assert res2.status_code == 200

    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_headers)
    assert diag.status_code == 200
    hist = diag.json().get("comparacion_historica", {})
    assert "disponible" in hist


def test_hallazgo(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Hallazgo Test",
        "inline_datasets": demo_datasets,
    })
    analysis_id = res.json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_headers).json()
    assert len(diag["hallazgos"]) > 0
    h = diag["hallazgos"][0]
    assert "titulo" in h
    assert "confianza" in h
    assert h["confianza"] in ("ALTA", "MEDIA", "BAJA")
    assert "criterios_confianza" in h


def test_confianza_criterios(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Confianza",
        "inline_datasets": demo_datasets,
    })
    diag = client.get(f"/api/salud/diagnostico/{res.json()['id']}", headers=auth_headers).json()
    for h in diag["hallazgos"]:
        assert "criterios_confianza" in h
        assert "puntaje" in h["criterios_confianza"] or h["criterios_confianza"] == {}


def test_propuesta(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Propuesta",
        "inline_datasets": demo_datasets,
    })
    diag = client.get(f"/api/salud/diagnostico/{res.json()['id']}", headers=auth_headers).json()
    assert len(diag["oportunidades"]) > 0
    p = diag["oportunidades"][0]
    assert p["accion_propuesta"]
    assert "mejorar la gestión" not in p["accion_propuesta"].lower()


def test_priorizacion(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Prioridad",
        "inline_datasets": demo_datasets,
    })
    diag = client.get(f"/api/salud/diagnostico/{res.json()['id']}", headers=auth_headers).json()
    prioridades = [h.get("prioridad", 0) for h in diag["hallazgos"]]
    if len(prioridades) > 1:
        assert prioridades == sorted(prioridades, reverse=True)


def test_caso_experiencia(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Experiencia",
        "inline_datasets": demo_datasets,
    })
    assert res.status_code == 200
    casos = client.get("/api/salud/casos-similares?tipo_problema=diagnostico", headers=auth_headers)
    assert casos.status_code == 200


def test_feedback_humano(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Feedback",
        "inline_datasets": demo_datasets,
    })
    diag = client.get(f"/api/salud/diagnostico/{res.json()['id']}", headers=auth_headers).json()
    hallazgo_id = diag["hallazgos"][0]["id"]
    fb = client.post("/api/salud/feedback", headers=auth_headers, json={
        "target_type": "hallazgo",
        "target_id": hallazgo_id,
        "feedback_type": "CORRECTO",
        "comment": "Hallazgo validado",
    })
    assert fb.status_code == 200


def test_resultado_posterior(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Resultado",
        "inline_datasets": demo_datasets,
    })
    diag = client.get(f"/api/salud/diagnostico/{res.json()['id']}", headers=auth_headers).json()
    prop_id = diag["oportunidades"][0]["id"]
    result = client.post(f"/api/salud/propuestas/{prop_id}/resultado", headers=auth_headers, json={
        "meta": "Reducir factura→radicación a <7 días",
        "resultado": "8.1 días",
        "outcome": "MEJORO",
    })
    assert result.status_code == 200
    assert result.json()["outcome"] == "MEJORO"


def test_seleccion_especialistas(salud_db):
    from app.models import User
    admin = salud_db.query(User).filter(User.username == "admin").first()
    plan = select_specialists(
        salud_db, admin.organization_id,
        "Analiza la situación financiera y operativa de esta IPS.",
        ["facturacion", "radicacion", "glosas", "cartera"],
    )
    assert len(plan["dominios"]) > 0
    assert len(plan["asignaciones"]) > 0
    assert plan["consolidador"] is not None


def test_detect_domains():
    domains = detect_required_domains(
        "Analiza glosas y cartera de la IPS",
        ["glosas", "cartera"],
    )
    assert "glosas" in domains
    assert "cartera" in domains


def test_tenant_isolation(demo_datasets, auth_headers, client, salud_db):
    org2 = Organization(name=f"Org-{uuid.uuid4().hex[:6]}")
    salud_db.add(org2)
    salud_db.flush()
    user2 = User(
        organization_id=org2.id,
        username=f"user2-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Test2026*"),
        role="admin",
    )
    salud_db.add(user2)
    salud_db.commit()

    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Org1",
        "inline_datasets": demo_datasets,
    })
    analysis_id = res.json()["id"]

    login2 = client.post("/api/auth/login", json={"username": user2.username, "password": "Test2026*"})
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=headers2)
    assert diag.status_code == 404


def test_permisos_viewer_denied(demo_datasets, client, salud_db):
    org = salud_db.query(Organization).first()
    viewer = User(
        organization_id=org.id,
        username=f"viewer-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("View2026*"),
        role="viewer",
    )
    salud_db.add(viewer)
    salud_db.commit()

    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "View2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    res = client.post("/api/salud/analisis", headers=headers, json={
        "ips_name": "IPS Viewer",
        "inline_datasets": demo_datasets,
    })
    assert res.status_code == 403

    diag = client.get("/api/salud/demo/datasets", headers=headers)
    assert diag.status_code == 200


def test_no_alucinacion_datos():
    indicators = compute_all_indicators({})
    assert indicators["facturacion"]["mensaje"] == INSUFICIENTE
    assert indicators["radicacion"]["mensaje"] == INSUFICIENTE


def test_plan_accion(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Plan",
        "inline_datasets": demo_datasets,
    })
    analysis_id = res.json()["id"]
    diag = client.get(f"/api/salud/diagnostico/{analysis_id}", headers=auth_headers).json()
    prop_ids = [p["id"] for p in diag["oportunidades"][:2]]
    plan = client.post(f"/api/salud/analisis/{analysis_id}/plan-accion", headers=auth_headers, json={
        "propuesta_ids": prop_ids,
    })
    assert plan.status_code == 200
    assert len(plan.json()["tareas"]) == 2


def test_pregunta_natural(demo_datasets, auth_headers, client):
    res = client.post("/api/salud/analisis", headers=auth_headers, json={
        "ips_name": "IPS Pregunta",
        "inline_datasets": demo_datasets,
    })
    analysis_id = res.json()["id"]
    q = client.post(f"/api/salud/pregunta/{analysis_id}", headers=auth_headers, json={
        "pregunta": "¿Por qué tengo menos caja si facturé más?",
    })
    assert q.status_code == 200
    assert "evidencia" in q.json()


def test_demo_datasets_endpoint(auth_headers, client):
    res = client.get("/api/salud/demo/datasets", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "facturacion" in data
    assert len(data["facturacion"]) > 0


def test_migracion_upgrade_downgrade():
    """Verifica que la migración 960a1 existe y es reversible."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "backend/alembic/versions/960a1b2c3d4e_salud_ips_engine_960.py"
    spec = importlib.util.spec_from_file_location("salud_migration_960", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.revision == "960a1b2c3d4e"
    assert mod.down_revision == "5b2eb2437398"
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)
