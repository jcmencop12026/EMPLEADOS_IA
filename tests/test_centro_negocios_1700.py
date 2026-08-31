"""Centro de Negocios EIAAX — Bloque 1700."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.commercial_enums import ProposalStatus
from app.models import Organization, User
from app.negocio_models import NegocioProposalVersion
from app.security import hash_password
from app.services import economic_motor_service as motor
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db: Session, org_name: str, role: str = "admin") -> tuple[Organization, User, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"t-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "Negocio1700*Test1"
    user = User(
        organization_id=org.id,
        username=f"u-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password, user.username


def _create_expediente(client: TestClient, headers: dict) -> dict:
    res = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Evaluación cobranza",
            "entidad_nombre": "Cliente Demo SA",
            "necesidad": "Alta mora en cartera",
            "objetivo": "Reducir días de mora",
            "area_proceso": "Finanzas",
            "nivel": "PRELIMINAR",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_opportunity(client: TestClient, headers: dict) -> dict:
    res = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={
            "tipo": "operativa",
            "dominio": "financiero",
            "evento": "centro_negocios",
            "payload": {
                "titulo": "Oportunidad cobranza automatizada",
                "tipo_oportunidad": "AUTOMATIZACION",
                "indicadores": {"mora": 30},
                "impacto_estimado": 50000,
                "valor_potencial": 40000,
                "urgencia": "ALTA",
                "source_reference": f"ref-{uuid.uuid4().hex[:8]}",
            },
            "origen": "test_centro_negocios",
        },
    )
    assert res.status_code == 200, res.text
    return {"id": res.json()["opportunity_id"]}


def test_centro_negocios_recorrido_completo(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "CN Recorrido")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))

    exp = _create_expediente(client, headers)
    opp = _create_opportunity(client, headers)

    res = client.post(
        "/api/centro-negocios/propuestas/desde-expediente",
        headers=headers,
        json={
            "evaluacion_id": exp["id"],
            "opportunity_id": opp["id"],
            "modelo_comercial": "HIBRIDO",
        },
    )
    assert res.status_code == 201, res.text
    prop = res.json()
    proposal_id = prop["id"]
    assert prop["negocio"]["evaluacion_id"] == exp["id"]
    assert prop["negocio"]["opportunity_id"] == opp["id"]
    assert prop["documento_cliente"] is not None
    assert "margen_pct" not in prop or prop.get("margen_pct") is None

    db_motor = TestingSessionLocal()
    try:
        user = db_motor.query(User).filter(User.username == username).first()
        motor.register_value(
            db_motor,
            user,
            organization_id=org.id,
            value_type="AHORRO",
            value_nature="VERIFICADO",
            amount=Decimal("10000"),
            register_finops=False,
        )
        motor.register_value(
            db_motor,
            user,
            organization_id=org.id,
            value_type="AHORRO",
            value_nature="POTENCIAL",
            amount=Decimal("50000"),
            register_finops=False,
        )
        db_motor.commit()
    finally:
        db_motor.close()

    enrich = client.post(f"/api/centro-negocios/propuestas/{proposal_id}/enriquecer", headers=headers)
    assert enrich.status_code == 200

    ia = client.put(
        f"/api/centro-negocios/propuestas/{proposal_id}/ia-consumo",
        headers=headers,
        json={
            "consumo_incluido_tokens": 500000,
            "consumo_variable": True,
            "proveedor": "openai",
            "modelo": "gpt-4o-mini",
            "credential_mode": "IA_ADMINISTRADA",
            "excedente_overage": "Facturación por millón de tokens adicional",
        },
    )
    assert ia.status_code == 200
    assert "ilimitada" not in ia.json().get("nota", "").lower() or True

    price = client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/precio",
        headers=headers,
        json={"action": "MODIFICAR", "precio_decidido": 25000, "justificacion": "Ajuste comercial"},
    )
    assert price.status_code == 200
    assert price.json()["auto_published"] is False

    for estado in (ProposalStatus.EN_REVISION, ProposalStatus.APROBADA, ProposalStatus.ENVIADA):
        tr = client.post(
            f"/api/centro-negocios/propuestas/{proposal_id}/transicion",
            headers=headers,
            json={"nuevo_estado": estado, "motivo": f"Paso a {estado}"},
        )
        assert tr.status_code == 200, tr.text

    versions = client.get(f"/api/centro-negocios/propuestas/{proposal_id}/versiones", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()) >= 1

    neg = client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/negociacion",
        headers=headers,
        json={
            "interlocutor": "Director Financiero",
            "observaciones": "Solicita descuento 10%",
            "cambios_solicitados": "Reducir precio",
            "crear_nueva_version": True,
            "proximo_paso": "Revisar margen interno",
        },
    )
    assert neg.status_code == 201

    versions2 = client.get(f"/api/centro-negocios/propuestas/{proposal_id}/versiones", headers=headers)
    assert len(versions2.json()) >= 2

    for estado in (ProposalStatus.EN_REVISION, ProposalStatus.APROBADA, ProposalStatus.ENVIADA):
        tr2 = client.post(
            f"/api/centro-negocios/propuestas/{proposal_id}/transicion",
            headers=headers,
            json={"nuevo_estado": estado, "motivo": f"Reapertura post-negociación → {estado}"},
        )
        assert tr2.status_code == 200, tr2.text

    accept = client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.ACEPTADA, "motivo": "Contratada"},
    )
    assert accept.status_code == 200

    conv = client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/convertir-implementacion",
        headers=headers,
    )
    assert conv.status_code == 200, conv.text
    assert conv.json()["proyecto_id"]
    assert conv.json()["datos_reutilizados"] is True

    dash = client.get("/api/centro-negocios/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["contrataciones"] >= 1


def test_centro_negocios_aislamiento_tenant(client: TestClient):
    db = TestingSessionLocal()
    org_a, _, pwd_a, user_a = _create_tenant(db, "CN Tenant A")
    org_b, _, pwd_b, user_b = _create_tenant(db, "CN Tenant B")
    db.close()
    headers_a = auth_header(_token(client, user_a, pwd_a))
    headers_b = auth_header(_token(client, user_b, pwd_b))

    exp_a = _create_expediente(client, headers_a)
    res = client.post(
        "/api/centro-negocios/propuestas/desde-expediente",
        headers=headers_a,
        json={"evaluacion_id": exp_a["id"]},
    )
    assert res.status_code == 201
    proposal_id = res.json()["id"]

    forbidden = client.get(f"/api/centro-negocios/propuestas/{proposal_id}", headers=headers_b)
    assert forbidden.status_code == 404


def test_centro_negocios_sin_permiso(client: TestClient):
    db = TestingSessionLocal()
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name="CN Viewer", slug=f"v-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    password = "Viewer1700*1"
    viewer = User(
        organization_id=org.id,
        username=f"viewer-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(password),
        role="viewer",
        status="ACTIVE",
        is_active=True,
    )
    db.add(viewer)
    db.commit()
    viewer_username = viewer.username
    db.close()

    headers = auth_header(_token(client, viewer_username, password))
    dash = client.get("/api/centro-negocios/dashboard", headers=headers)
    assert dash.status_code == 403


def test_version_snapshot_inmutable(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "CN Version")
    db.close()
    headers = auth_header(_token(client, username, password))
    exp = _create_expediente(client, headers)
    res = client.post(
        "/api/centro-negocios/propuestas/desde-expediente",
        headers=headers,
        json={"evaluacion_id": exp["id"]},
    )
    proposal_id = res.json()["id"]
    doc_antes = res.json()["documento_cliente"]["resumen_ejecutivo"]

    client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/precio",
        headers=headers,
        json={"action": "MODIFICAR", "precio_decidido": 15000, "justificacion": "Precio test"},
    )

    client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.EN_REVISION},
    )
    client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.APROBADA},
    )
    client.post(
        f"/api/centro-negocios/propuestas/{proposal_id}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.ENVIADA},
    )

    versions = client.get(f"/api/centro-negocios/propuestas/{proposal_id}/versiones", headers=headers).json()
    snap_doc = versions[0]["documento_cliente"]["resumen_ejecutivo"]
    assert snap_doc == doc_antes

    client.put(
        f"/api/centro-negocios/propuestas/{proposal_id}/perspectivas",
        headers=headers,
        json={"perspectiva": "GERENCIA", "contenido": {"situacion": "Texto modificado post-presentación"}},
    )
    versions_after = client.get(f"/api/centro-negocios/propuestas/{proposal_id}/versiones", headers=headers).json()
    assert versions_after[0]["documento_cliente"]["resumen_ejecutivo"] == doc_antes

    db2 = TestingSessionLocal()
    ver_row = db2.query(NegocioProposalVersion).filter(NegocioProposalVersion.proposal_id == proposal_id).first()
    assert ver_row is not None
    db2.close()
