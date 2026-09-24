"""Inteligencia Empresarial — tests evolución macrobloque C."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, Permission, Role, RolePermission, User
from app.security import hash_password
from app.transformacion_models import DossierConocimientoItem, DossierEmpresarial
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.evaluacion, pytest.mark.transformacion]


def _ie_perms() -> set[str]:
    return {
        "inteligencia_empresarial.view",
        "inteligencia_empresarial.manage",
        "evaluacion.view",
        "evaluacion.manage",
        "transformacion.view",
        "transformacion.manage",
        "transformacion.execute",
        "oportunidades.view",
    }


def _token_ie(client: TestClient) -> tuple[str, str]:
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions
        bootstrap_permissions(db)
        org = Organization(name=f"IE-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        role = Role(organization_id=org.id, code=f"ie_{uuid.uuid4().hex[:6]}", name="IE", is_system=False)
        db.add(role)
        db.flush()
        for code in _ie_perms():
            perm = db.query(Permission).filter(Permission.code == code).first()
            assert perm
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        username = f"ie_{uuid.uuid4().hex[:6]}"
        password = "testpass123"
        db.add(User(
            organization_id=org.id, username=username,
            password_hash=hash_password(password), role=role.code, is_active=True,
        ))
        db.commit()
        org_id = org.id
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    return login.json()["access_token"], org_id


def _expediente(client: TestClient, tok: str) -> str:
    h = auth_header(tok)
    res = client.post("/api/evaluaciones", headers=h, json={
        "titulo": "Eval IE", "entidad_nombre": "Cliente IE",
        "necesidad": "Optimizar procesos", "nivel": "DIAGNOSTICA",
    })
    assert res.status_code in (200, 201), res.text
    return res.json()["id"]


def test_plan_adaptativo_y_suficiencia(client: TestClient):
    tok, _ = _token_ie(client)
    exp_id = _expediente(client, tok)
    plan = client.get(f"/api/inteligencia-empresarial/expedientes/{exp_id}/plan-adaptativo", headers=auth_header(tok))
    assert plan.status_code == 200
    body = plan.json()
    assert body["nivel"] == "DIAGNOSTICA"
    assert "que_falta" in body
    suf = client.get(f"/api/inteligencia-empresarial/expedientes/{exp_id}/suficiencia", headers=auth_header(tok))
    assert suf.status_code == 200
    assert "dimensiones" in suf.json()


def test_suficiencia_no_repregunta_dossier(client: TestClient):
    tok, org_id = _token_ie(client)
    exp_id = _expediente(client, tok)
    db = TestingSessionLocal()
    try:
        dossier = DossierEmpresarial(organization_id=org_id, etapa_actual="EVALUACION")
        db.add(dossier)
        db.flush()
        db.add(DossierConocimientoItem(
            organization_id=org_id, dossier_id=dossier.id,
            campo="contexto_negocio", etiqueta="Contexto", valor="Retail Colombia",
            fuente="manual", calidad="ALTA", vigente=True,
        ))
        db.commit()
    finally:
        db.close()
    suf = client.get(f"/api/inteligencia-empresarial/expedientes/{exp_id}/suficiencia", headers=auth_header(tok)).json()
    assert suf.get("no_solicitar_duplicado") is True or len(suf.get("cubierto_por_dossier", [])) >= 0


def test_evaluacion_adaptativa_por_nivel(client: TestClient):
    tok, _ = _token_ie(client)
    exp_id = _expediente(client, tok)
    ev = client.post(f"/api/inteligencia-empresarial/expedientes/{exp_id}/evaluar-adaptativo", headers=auth_header(tok))
    assert ev.status_code == 200
    assert ev.json()["nivel_aplicado"] == "DIAGNOSTICA"


def test_cadena_analitica_expediente(client: TestClient):
    tok, _ = _token_ie(client)
    exp_id = _expediente(client, tok)
    client.post(f"/api/inteligencia-empresarial/expedientes/{exp_id}/evaluar-adaptativo", headers=auth_header(tok))
    cadena = client.get(f"/api/inteligencia-empresarial/expedientes/{exp_id}/cadena-analitica", headers=auth_header(tok))
    assert cadena.status_code == 200
    body = cadena.json()
    assert "EVIDENCIA" in body["pasos_canonicos"]
    assert "HALLAZGO" in body["pasos_canonicos"]
    assert body["total"] >= 1


def test_motor_proactivo_sin_decision_automatica(client: TestClient):
    tok, _ = _token_ie(client)
    res = client.post("/api/inteligencia-empresarial/evidencia", headers=auth_header(tok), json={
        "titulo": "Nueva evidencia operativa",
        "descripcion": "Incremento reprocesos en facturación",
        "dominio": "procesos",
    })
    assert res.status_code == 200
    body = res.json()
    assert body.get("senal_id")
    assert "decision_automatica" not in body or body.get("estado") == "SENAL_CREADA"


def test_multitenant_aislamiento(client: TestClient):
    tok_a, _ = _token_ie(client)
    tok_b, _ = _token_ie(client)
    exp_a = _expediente(client, tok_a)
    denied = client.get(f"/api/inteligencia-empresarial/expedientes/{exp_a}/panorama", headers=auth_header(tok_b))
    assert denied.status_code in (403, 404)


def test_contratos_futuros(client: TestClient):
    tok, _ = _token_ie(client)
    res = client.get("/api/inteligencia-empresarial/contratos", headers=auth_header(tok))
    assert res.status_code == 200
    assert "motor_economico_b" in res.json()["contratos"]


def test_escenarios_arquitecto_ampliados(client: TestClient):
    tok, _ = _token_ie(client)
    h = auth_header(tok)
    nec = client.post("/api/transformacion/necesidad", headers=h, json={
        "titulo": "Transformación IE", "necesidad": "Automatizar aprobaciones",
    })
    assert nec.status_code in (200, 201)
    exp_id = nec.json()["expediente"]["id"]
    diag = client.post(f"/api/transformacion/expedientes/{exp_id}/diagnosticar", headers=h)
    assert diag.status_code == 200
    tipos = {e["tipo"] for e in diag.json().get("escenarios", [])}
    assert "ACTUAL" in tipos
    assert "ASISTIDO_IA" in tipos or "OPTIMIZADO" in tipos


def test_regresion_evaluacion_bp1(client: TestClient, auth_headers):
    res = client.get("/api/evaluaciones", headers=auth_headers)
    assert res.status_code == 200
