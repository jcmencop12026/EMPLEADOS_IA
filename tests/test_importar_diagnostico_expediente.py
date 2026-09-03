"""P0 — Importación hallazgos diagnóstico 1220 → expediente."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.evaluacion_models import EvaluacionHallazgo
from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


def _tenant() -> tuple[Organization, User]:
    db = TestingSessionLocal()
    try:
        from app.seed_orchestration import bootstrap_orchestration
        from app.seed_permissions import bootstrap_permissions

        org = Organization(name=f"Org-diag-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        bootstrap_permissions(db)
        bootstrap_orchestration(db, org.id)
        admin = User(
            organization_id=org.id,
            username=f"adm-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Admin2026*"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return org, admin
    finally:
        db.close()


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _seed_signal_for_diagnostic(client: TestClient, headers: dict[str, str]) -> None:
    code = f"diag-{uuid.uuid4().hex[:6]}"
    src = client.post(
        "/api/inteligencia-externa/fuentes",
        headers=headers,
        json={
            "code": code,
            "name": f"Fuente {code}",
            "source_type": "MERCADO",
            "ingestion_channel": "CARGA MANUAL",
            "sector": "salud",
            "pais_region": "Colombia",
            "confiabilidad": 0.8,
        },
    )
    assert src.status_code == 201, src.text
    ing = client.post(
        "/api/inteligencia-externa/ingesta",
        headers=headers,
        json={
            "source_code": code,
            "hecho_observado": "Glosas recurrentes en facturación IPS",
            "evento": "glosas_facturacion",
            "dominio": "facturacion",
            "classification": "OPORTUNIDAD",
            "referencia": f"ref-{uuid.uuid4().hex[:8]}",
        },
    )
    assert ing.status_code == 201, ing.text


def test_importar_diagnostico_sin_duplicar(client: TestClient):
    _, admin = _tenant()
    headers = _login(client, admin.username)

    exp = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Eval import diag",
            "entidad_nombre": "IPS Test",
            "necesidad": "Reprocesos facturación",
            "nivel": "DIAGNOSTICA",
        },
    )
    assert exp.status_code in (200, 201)
    exp_id = exp.json()["id"]

    _seed_signal_for_diagnostic(client, headers)
    diag = client.post("/api/diagnosticos/generar", headers=headers, json={})
    assert diag.status_code in (200, 201), diag.text
    diag_id = diag.json()["id"]
    assert len(diag.json().get("hallazgos", [])) >= 1

    first = client.post(
        f"/api/flujo-comercial/expedientes/{exp_id}/importar-diagnostico",
        headers=headers,
        params={"diagnostic_id": diag_id},
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["diagnostic_id"] == diag_id
    assert len(body["importados"]) >= 1

    db = TestingSessionLocal()
    try:
        count_after_first = (
            db.query(EvaluacionHallazgo)
            .filter(EvaluacionHallazgo.expediente_id == exp_id)
            .count()
        )
    finally:
        db.close()

    second = client.post(
        f"/api/flujo-comercial/expedientes/{exp_id}/importar-diagnostico",
        headers=headers,
        params={"diagnostic_id": diag_id},
    )
    assert second.status_code == 200
    assert second.json()["omitidos"] >= len(body["importados"])

    db = TestingSessionLocal()
    try:
        assert (
            db.query(EvaluacionHallazgo)
            .filter(EvaluacionHallazgo.expediente_id == exp_id)
            .count()
            == count_after_first
        )
    finally:
        db.close()

    cadena = client.get(
        f"/api/inteligencia-empresarial/expedientes/{exp_id}/cadena-analitica",
        headers=headers,
    )
    assert cadena.status_code == 200
    assert cadena.json()["total"] >= 1


def test_importar_diagnostico_aislamiento_org(client: TestClient):
    _, admin_a = _tenant()
    _, admin_b = _tenant()
    headers_a = _login(client, admin_a.username)
    headers_b = _login(client, admin_b.username)

    exp_res = client.post(
        "/api/evaluaciones",
        headers=headers_a,
        json={"titulo": "Eval A", "entidad_nombre": "Empresa A", "necesidad": "Test", "nivel": "PRELIMINAR"},
    )
    assert exp_res.status_code in (200, 201)
    exp = exp_res.json()
    _seed_signal_for_diagnostic(client, headers_a)
    diag_res = client.post("/api/diagnosticos/generar", headers=headers_a, json={})
    assert diag_res.status_code in (200, 201), diag_res.text
    diag = diag_res.json()

    denied = client.post(
        f"/api/flujo-comercial/expedientes/{exp['id']}/importar-diagnostico",
        headers=headers_b,
        params={"diagnostic_id": diag["id"]},
    )
    assert denied.status_code in (403, 404)
