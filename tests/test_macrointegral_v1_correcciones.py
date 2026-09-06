"""Macrobloque integral V1 — regresiones de revisión humana (PR #171)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FRONTEND = REPO / "frontend" / "src"


def test_oportunidad_detail_sin_window_prompt():
    text = (FRONTEND / "pages/OportunidadDetailPage.tsx").read_text(encoding="utf-8")
    assert "window.prompt" not in text
    assert "prompt(" not in text
    assert "ValuationFormsPanel" in text
    assert "StructuredEvidenceView" in text


def test_oportunidad_labels_traduce_codigos():
    text = (FRONTEND / "lib/oportunidadLabels.ts").read_text(encoding="utf-8")
    assert "SOLICITAR_DATOS" in text
    assert "OPORTUNIDAD_CREADA" in text
    assert "TRANSICION_DATOS_INSUFICIENTES" in text
    assert "Requiere más información" in text


def test_login_usa_brand_corporativo_no_hero():
    text = (FRONTEND / "pages/LoginPage.tsx").read_text(encoding="utf-8")
    mark = (FRONTEND / "components/identity/EnterpriseMark.tsx").read_text(encoding="utf-8")
    assert "EnterpriseMark" in text
    assert "useLoginIdentity" in text
    assert 'level="ex08"' not in text
    assert "eiaax-v1-experience" in text
    assert "BrandMark" not in mark
    assert "data-brand=\"tenant\"" in mark
    assert "data-brand=\"eiaax-text\"" in mark


def test_login_identity_endpoint_expone_logo_configurado(client):
    from app.models import Organization
    from conftest import TestingSessionLocal
    from app.services import admin_service as admin_svc
    from app.cert_branding import CERT_BRANDING_CONFIG

    db = TestingSessionLocal()
    try:
        org = db.query(Organization).first()
        assert org is not None
        admin_svc.update_org_config(db, org=org, actor_id="test", config=CERT_BRANDING_CONFIG)
        r = client.get("/api/public/login-identity")
        assert r.status_code == 200
        body = r.json()
        assert body.get("has_configured_logo") is True
        assert body.get("logo_url")
    finally:
        db.close()


def test_espacio_externo_no_crear_entidad_si_existe():
    text = (FRONTEND / "components/espacioExterno/EspacioExternoAdminPanel.tsx").read_text(encoding="utf-8")
    assert "Vincular entidad externa" in text
    assert "Entidad externa vinculada" in text


def test_operacion_panel_scoping_expediente():
    text = (FRONTEND / "components/evaluacion/EmpresaOperacionPanel.tsx").read_text(encoding="utf-8")
    assert "expedienteId" in text
    assert "Recursos disponibles de la organización" in text
    assert "EXECUTION_STATUS" in text


@pytest.mark.tenant
def test_aislamiento_oportunidades_entre_organizaciones(client, auth_headers):
    """Org A no debe ver oportunidades de org B."""
    from conftest import TestingSessionLocal, auth_header
    from app.models import Organization, User
    from app.security import hash_password
    import uuid

    db = TestingSessionLocal()
    try:
        org_b = Organization(name="Org Macro B", slug=f"macro-b-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(org_b)
        db.flush()
        user_b = User(
            organization_id=org_b.id,
            username=f"macro_b_{uuid.uuid4().hex[:6]}",
            email=f"macro_b_{uuid.uuid4().hex[:6]}@test.local",
            password_hash=hash_password("TestB2026!"),
            role="admin",
            is_active=True,
        )
        db.add(user_b)
        db.commit()
        login_b = client.post("/api/auth/login", json={"username": user_b.username, "password": "TestB2026!"})
        assert login_b.status_code == 200, login_b.text
        headers_b = auth_header(login_b.json()["access_token"])
    finally:
        db.close()

    res_a = client.get("/api/oportunidades", headers=auth_headers)
    assert res_a.status_code == 200
    ids_a = {item["id"] for item in res_a.json().get("items", res_a.json())}

    res_b = client.get("/api/oportunidades", headers=headers_b)
    assert res_b.status_code == 200
    ids_b = {item["id"] for item in res_b.json().get("items", res_b.json())}

    overlap = ids_a & ids_b
    assert not overlap, f"Oportunidades compartidas entre orgs: {overlap}"
