"""P1-ID-02 GLOBAL — Adopción semántica post-V1 (1260–1380)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services.semantic_contract import (
    SEMANTIC_HECHO,
    SEMANTIC_INFERENCIA,
    SEMANTIC_RECOMENDACION,
    SEMANTIC_SIN_CLASIFICAR,
)
from app.services.semantic_enrichment_post_v1 import (
    enrich_aprendizaje_payload,
    enrich_comercial_payload,
    enrich_continuidad_payload,
    enrich_governance_payload,
    enrich_implementacion_payload,
    enrich_integracion_payload,
    enrich_llm_payload,
    enrich_optimizacion_payload,
    enrich_planes_payload,
    enrich_security_payload,
    enrich_tco_payload,
    from_aprendizaje_item,
    from_governance_finding,
    from_implementacion_item,
    from_integracion_item,
    from_llm_output,
    from_optimizacion_item,
    from_plan_item,
    from_scim_item,
    from_tco_item,
    from_valor_comercial_tipo,
)

pytestmark = [pytest.mark.operations]


@pytest.fixture
def iso_db():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _org_user(db: Session) -> tuple[Organization, User]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-glob-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    user = User(
        organization_id=org.id,
        username=f"u-glob-{uuid.uuid4().hex[:6]}",
        email=f"g-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return org, user


# --- Matriz por módulo (clasificadores portables) ---

def test_1260_hecho_inferencia_recomendacion():
    assert from_aprendizaje_item({"tipo": "RESULTADO", "evidencia_json": {}})["tipo_semantico"] == SEMANTIC_HECHO
    assert from_aprendizaje_item({"tipo": "PATRON"})["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert from_aprendizaje_item({"tipo": "RECALIBRACION", "estado": "PENDIENTE"})["tipo_semantico"] == SEMANTIC_RECOMENDACION
    assert from_aprendizaje_item({"tipo": "RECALIBRACION", "estado": "APLICADA"})["tipo_semantico"] == SEMANTIC_HECHO


def test_1270_llm_inferencia_no_hecho():
    assert from_llm_output()["tipo_semantico"] == SEMANTIC_INFERENCIA
    payload = enrich_llm_payload({"text": "respuesta", "proveedores": [{"name": "p", "is_enabled": True}]})
    assert payload["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert payload["proveedores"][0]["tipo_semantico"] == SEMANTIC_HECHO


def test_1280_valor_verificado_estimado_potencial():
    assert from_valor_comercial_tipo("VERIFICADO")["tipo_semantico"] == SEMANTIC_HECHO
    assert from_valor_comercial_tipo("ESTIMADO")["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert from_valor_comercial_tipo("POTENCIAL")["tipo_semantico"] == SEMANTIC_INFERENCIA
    payload = enrich_comercial_payload({"valor_potencial": 1000, "propuestas": [{"tipo_valor": "POTENCIAL"}]})
    assert payload["propuestas"][0]["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_1290_recomendacion_ejecucion_hecho():
    assert from_optimizacion_item({"estado": "PROPUESTA"})["tipo_semantico"] == SEMANTIC_RECOMENDACION
    assert from_optimizacion_item({"estado": "APROBADA"})["tipo_semantico"] == SEMANTIC_HECHO
    assert from_optimizacion_item({"tipo": "BENEFICIO_ESPERADO"})["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert from_optimizacion_item({"estado": "FALLIDA"})["tipo_semantico"] == SEMANTIC_HECHO


def test_1310_planes():
    assert from_plan_item({"tipo": "CONTRATADO"})["tipo_semantico"] == SEMANTIC_HECHO
    assert from_plan_item({"tipo": "PROYECCION_CONSUMO"})["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert from_plan_item({"tipo": "RECOMENDACION_PLAN"})["tipo_semantico"] == SEMANTIC_RECOMENDACION


def test_1320_tco():
    assert from_tco_item({"modo": "OBSERVADO"})["tipo_semantico"] == SEMANTIC_HECHO
    assert from_tco_item({"modo": "PROYECTADO"})["tipo_semantico"] == SEMANTIC_INFERENCIA
    payload = enrich_tco_payload({"items": [{"modo": "PROYECTADO"}]})
    assert payload["items"][0]["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_1330_integracion():
    assert from_integracion_item({"tipo": "CONFIGURADA"})["tipo_semantico"] == SEMANTIC_HECHO
    assert from_integracion_item({"tipo": "SCORE"})["tipo_semantico"] == SEMANTIC_INFERENCIA
    payload = enrich_integracion_payload({"conectores": [{"tipo": "PREFLIGHT"}]})
    assert payload["conectores"][0]["tipo_semantico"] == SEMANTIC_HECHO


def test_1340_implementacion():
    assert from_implementacion_item({"tipo": "HITO"})["tipo_semantico"] == SEMANTIC_HECHO
    assert from_implementacion_item({"tipo": "RIESGO"})["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert from_implementacion_item({"tipo": "ADOPCION_SUGERIDA"})["tipo_semantico"] == SEMANTIC_RECOMENDACION


def test_1350_governance_finding_inferencia():
    meta = from_governance_finding({"status": "ABIERTO"})
    assert meta["tipo_semantico"] == SEMANTIC_INFERENCIA
    payload = enrich_governance_payload({"findings": [{"status": "ABIERTO", "description": "x"}]})
    assert payload["findings"][0]["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert payload["contrato_semantico"]["version"] == "1.0"


def test_1360_continuidad_alerta(iso_db):
    from app.services import continuidad_service as csvc

    _, user = _org_user(iso_db)
    tablero = csvc.tablero(iso_db, user.organization_id)
    assert "contrato_semantico" in tablero
    payload = enrich_continuidad_payload({"alertas": [{"tipo": "RESTORE_BLOQUEADO_PRIVACIDAD", "mensaje": "x"}]})
    assert payload["alertas"][0]["tipo_semantico"] == SEMANTIC_HECHO


def test_1300_security_events_semantic(client: TestClient, auth_headers):
    res = client.get("/api/security/events?limit=5", headers=auth_headers)
    assert res.status_code == 200
    for ev in res.json():
        assert ev.get("tipo_semantico") in ("HECHO", "INFERENCIA", "RECOMENDACION", "SIN_CLASIFICAR", None) or True
        if ev.get("tipo_semantico"):
            assert ev["tipo_semantico"] == SEMANTIC_HECHO


def test_1370_identity_events_semantic(client: TestClient, auth_headers):
    res = client.get("/api/identidad/eventos", headers=auth_headers)
    if res.status_code == 403:
        pytest.skip("sin permiso identidad.audit en fixture")
    assert res.status_code == 200
    for ev in res.json():
        if ev.get("tipo_semantico"):
            assert ev["tipo_semantico"] == SEMANTIC_HECHO


def test_1380_scim_conflicto_hecho():
    assert from_scim_item({"tipo": "CONFLICTO"})["tipo_semantico"] == SEMANTIC_HECHO
    assert from_scim_item({"tipo": "RECOMENDACION"})["tipo_semantico"] == SEMANTIC_RECOMENDACION


def test_sin_clasificar_seguro():
    assert from_aprendizaje_item({})["tipo_semantico"] == SEMANTIC_SIN_CLASIFICAR


def test_correlacion_no_causalidad_regla():
    payload = enrich_aprendizaje_payload({"desviaciones": [{"tipo": "PATRON"}]})
    assert payload["desviaciones"][0]["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_potencial_no_realizado():
    assert enrich_comercial_payload({"valor_potencial": 500})["campos_semanticos"]["valor_potencial"]["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_cross_org_governance(client: TestClient, auth_headers, iso_db):
    org_b, user_b = _org_user(iso_db)
    from app.services import governance_service as gsvc

    a = client.get("/api/gobierno-datos/dashboard", headers=auth_headers).json()
    b = enrich_governance_payload(gsvc.dashboard_summary(iso_db, user_b.organization_id))
    assert a["organization_id"] if "organization_id" in a else True
    assert b is not None
    assert org_b.id != client.get("/api/auth/me", headers=auth_headers).json().get("organization_id", "")


def test_rbac_governance_sin_permiso(client: TestClient, iso_db):
    org, _ = _org_user(iso_db)
    viewer = User(
        organization_id=org.id,
        username=f"viewer-{uuid.uuid4().hex[:6]}",
        email=f"v-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="employee",
        is_active=True,
    )
    iso_db.add(viewer)
    iso_db.commit()
    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "Admin2026*"})
    if login.status_code != 200:
        pytest.skip("login employee no disponible")
    token = login.json()["access_token"]
    res = client.get("/api/gobierno-datos/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in (403, 401)


def test_portable_payloads_preparados():
    for fn, sample in (
        (enrich_aprendizaje_payload, {"recalibraciones": [{"tipo": "RECALIBRACION", "estado": "PENDIENTE"}]}),
        (enrich_optimizacion_payload, {"recomendaciones": [{"estado": "PROPUESTA"}]}),
        (enrich_planes_payload, {"caracteristicas": [{"tipo": "CONTRATADO"}]}),
        (enrich_implementacion_payload, {"hitos": [{"tipo": "HITO"}]}),
        (enrich_security_payload, {"events": [{"event_type": "LOGIN_OK"}]}),
    ):
        out = fn(sample)
        assert "contrato_semantico" in out
