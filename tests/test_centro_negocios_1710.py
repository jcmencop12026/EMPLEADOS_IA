"""Centro de Negocios EIAAX — Cierre integral 1710."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.commercial_enums import ProposalStatus
from app.models import Organization, User
from app.negocio_enums import ApprovalLevel
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
    password = "Negocio1710*Test1"
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


def _expediente(client, headers):
    res = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Eval cobranza",
            "entidad_nombre": "Cliente Demo SA",
            "necesidad": "Alta mora",
            "nivel": "PRELIMINAR",
        },
    )
    assert res.status_code == 201
    return res.json()


def _propuesta(client, headers, eval_id):
    res = client.post(
        "/api/centro-negocios/propuestas/desde-expediente",
        headers=headers,
        json={"evaluacion_id": eval_id, "modelo_comercial": "HIBRIDO"},
    )
    assert res.status_code == 201
    return res.json()


def _precio(client, headers, pid, monto=20000):
    res = client.post(
        f"/api/centro-negocios/propuestas/{pid}/precio",
        headers=headers,
        json={"action": "MODIFICAR", "precio_decidido": monto, "justificacion": "Test"},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _approve_all(client, headers, pid):
    for nivel in (ApprovalLevel.REVISOR, ApprovalLevel.APROBADOR_COMERCIAL):
        res = client.post(
            f"/api/centro-negocios/propuestas/{pid}/aprobaciones",
            headers=headers,
            json={"nivel": nivel, "comentario": "OK"},
        )
        assert res.status_code == 200, res.text


def _advance_to_aprobada(client, headers, pid):
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.EN_REVISION})
    _approve_all(client, headers, pid)
    res = client.post(
        f"/api/centro-negocios/propuestas/{pid}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.APROBADA},
    )
    assert res.status_code == 200, res.text


def test_presentacion_rechazada_sin_aprobaciones(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "CN Rechazo Pres")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _propuesta(client, headers, _expediente(client, headers)["id"])
    pid = prop["id"]
    _precio(client, headers, pid)
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.EN_REVISION})
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.APROBADA})
    denied = client.post(
        f"/api/centro-negocios/propuestas/{pid}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.ENVIADA},
    )
    assert denied.status_code == 422
    assert "Aprobaciones pendientes" in denied.json()["detail"]


def test_pdf_generado_y_sin_datos_internos(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "CN PDF")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _propuesta(client, headers, _expediente(client, headers)["id"])
    pid = prop["id"]
    _precio(client, headers, pid)
    _advance_to_aprobada(client, headers, pid)
    present = client.post(
        f"/api/centro-negocios/propuestas/{pid}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.ENVIADA},
    )
    assert present.status_code == 200, present.text
    body = present.json()
    assert "margen_pct" not in body or body.get("margen_pct") is None
    versions = client.get(f"/api/centro-negocios/propuestas/{pid}/versiones", headers=headers).json()
    assert versions[0]["pdf_document_id"]
    pdf = client.get(f"/api/centro-negocios/documentos/{versions[0]['pdf_document_id']}/pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:4] == b"%PDF"


def test_fases_precio_separadas(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant(db, "CN Fases")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _propuesta(client, headers, _expediente(client, headers)["id"])
    pid = prop["id"]
    _precio(client, headers, pid, 18000)
    det = client.get(f"/api/centro-negocios/propuestas/{pid}/detalle", headers=headers).json()
    fases = {f["fase"] for f in det["fases_precio"]}
    assert "APROBADO" in fases


def test_economia_privada_403_sin_permiso(client: TestClient):
    db = TestingSessionLocal()
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name="CN Priv", slug=f"p-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    pwd = "Viewer1710*1"
    viewer = User(
        organization_id=org.id,
        username=f"v-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(pwd),
        role="viewer",
        status="ACTIVE",
        is_active=True,
    )
    db.add(viewer)
    db.commit()
    vname = viewer.username
    db.close()
    denied = client.get("/api/centro-negocios/dashboard", headers=auth_header(_token(client, vname, pwd)))
    assert denied.status_code == 403


def test_sincronizacion_oportunidad(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "CN Sync")
    db.close()
    headers = auth_header(_token(client, username, password))
    opp = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={
            "tipo": "operativa",
            "dominio": "financiero",
            "evento": "sync_test",
            "payload": {
                "titulo": "Opp sync",
                "tipo_oportunidad": "AUTOMATIZACION",
                "impacto_estimado": 1000,
                "source_reference": f"ref-{uuid.uuid4().hex[:8]}",
            },
            "origen": "test",
        },
    ).json()
    prop = client.post(
        "/api/centro-negocios/propuestas/desde-expediente",
        headers=headers,
        json={"evaluacion_id": _expediente(client, headers)["id"], "opportunity_id": opp["opportunity_id"]},
    ).json()
    pid = prop["id"]
    sync = client.post(f"/api/centro-negocios/propuestas/{pid}/sincronizar", headers=headers, json={"direction": "both"})
    assert sync.status_code == 200
    log = client.get(f"/api/centro-negocios/propuestas/{pid}/detalle", headers=headers).json()["sync_log"]
    assert isinstance(log, list)


def test_contratacion_requiere_version_presentada(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "CN Contract")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _propuesta(client, headers, _expediente(client, headers)["id"])
    pid = prop["id"]
    bad = client.post(f"/api/centro-negocios/propuestas/{pid}/contratar", headers=headers, json={})
    assert bad.status_code == 422


def test_negociacion_nueva_version_reset_aprobaciones(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "CN Neg")
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _propuesta(client, headers, _expediente(client, headers)["id"])
    pid = prop["id"]
    _precio(client, headers, pid)
    _advance_to_aprobada(client, headers, pid)
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.ENVIADA})
    client.post(
        f"/api/centro-negocios/propuestas/{pid}/negociacion",
        headers=headers,
        json={"observaciones": "Cambio", "crear_nueva_version": True},
    )
    # Tras nueva versión queda en BORRADOR — no puede presentarse sin re-aprobaciones
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.EN_REVISION})
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.APROBADA})
    present = client.post(
        f"/api/centro-negocios/propuestas/{pid}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.ENVIADA},
    )
    assert present.status_code == 422


def test_potencial_no_en_documento_cliente(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant(db, "CN Pot")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    prop = _propuesta(client, headers, _expediente(client, headers)["id"])
    doc = prop["documento_cliente"]
    assert doc.get("economia_privada_incluida") is False
    assert "POTENCIAL" in (doc.get("nota_potencial") or "")


def test_aislamiento_tenant_detalle(client: TestClient):
    db = TestingSessionLocal()
    _, _, pwd_a, user_a = _create_tenant(db, "CN A")
    _, _, pwd_b, user_b = _create_tenant(db, "CN B")
    db.close()
    ha = auth_header(_token(client, user_a, pwd_a))
    hb = auth_header(_token(client, user_b, pwd_b))
    pid = _propuesta(client, ha, _expediente(client, ha)["id"])["id"]
    assert client.get(f"/api/centro-negocios/propuestas/{pid}/detalle", headers=hb).status_code == 404


def test_politica_aprobacion_configurable(client: TestClient):
    db = TestingSessionLocal()
    _, _, password, username = _create_tenant(db, "CN Policy")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.put(
        "/api/centro-negocios/politica-aprobacion",
        headers=headers,
        json={"levels": ["REVISOR"], "enabled": True},
    )
    assert res.status_code == 200
    prop = _propuesta(client, headers, _expediente(client, headers)["id"])
    pid = prop["id"]
    _precio(client, headers, pid)
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.EN_REVISION})
    client.post(f"/api/centro-negocios/propuestas/{pid}/aprobaciones", headers=headers, json={"nivel": "REVISOR"})
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": ProposalStatus.APROBADA})
    present = client.post(
        f"/api/centro-negocios/propuestas/{pid}/transicion",
        headers=headers,
        json={"nuevo_estado": ProposalStatus.ENVIADA},
    )
    assert present.status_code == 200, present.text
