"""Tests capa transversal seguridad, gobierno de datos y trazabilidad EIAAX."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _create_tenant_user(
    db: Session,
    *,
    org_name: str,
    role: str = "admin",
    password: str = "EmpSeg*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"esg-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    uname = f"esg-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=uname,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def esg_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_clasificacion_transversal_alias(client: TestClient, token: str):
    headers = auth_header(token)
    obj_id = str(uuid.uuid4())
    res = client.post(
        "/api/empresa-seguridad/clasificaciones",
        headers=headers,
        json={
            "objeto_tipo": "documento",
            "objeto_id": obj_id,
            "codigo_clasificacion": "CONFIDENCIAL",
            "motivo": "Documento sensible",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["codigo"] == "CONFIDENCIAL"
    assert body["nombre"] == "Confidencial"

    alias = client.post(
        "/api/empresa-seguridad/clasificaciones",
        headers=headers,
        json={
            "objeto_tipo": "hallazgo",
            "objeto_id": str(uuid.uuid4()),
            "codigo_clasificacion": "INTERNA",
        },
    )
    assert alias.status_code == 201
    assert alias.json()["codigo"] == "INTERNO"


def test_visibilidad_niveles_transversal(client: TestClient, token: str):
    headers = auth_header(token)
    obj_id = str(uuid.uuid4())
    res = client.post(
        "/api/empresa-seguridad/visibilidad",
        headers=headers,
        json={
            "dominio": "hallazgo",
            "objeto_tipo": "hallazgo",
            "objeto_id": obj_id,
            "nivel_visibilidad": "VISIBLE_ENTIDAD",
            "motivo": "Compartir con entidad",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["nivel_visibilidad"] == "VISIBLE_ENTIDAD"
    assert body["version"] == 1

    res2 = client.post(
        "/api/empresa-seguridad/visibilidad",
        headers=headers,
        json={
            "dominio": "hallazgo",
            "objeto_tipo": "hallazgo",
            "objeto_id": obj_id,
            "nivel_visibilidad": "RESTRINGIDO",
            "motivo": "Restringir acceso",
        },
    )
    assert res2.status_code == 201
    assert res2.json()["estado_anterior"] == "VISIBLE_ENTIDAD"
    assert res2.json()["version"] == 2


def test_evidencia_vinculo(client: TestClient, token: str):
    headers = auth_header(token)
    corr = str(uuid.uuid4())
    obj_id = str(uuid.uuid4())
    res = client.post(
        "/api/empresa-seguridad/evidencias",
        headers=headers,
        json={
            "tipo_evidencia": "documento",
            "referencia": "knowledge/doc-123",
            "objeto_tipo": "decision",
            "objeto_id": obj_id,
            "rol_vinculo": "DECISION",
            "correlation_id": corr,
            "descripcion": "Documento soporte decisión",
        },
    )
    assert res.status_code == 201, res.text
    listed = client.get(
        f"/api/empresa-seguridad/evidencias?correlation_id={corr}",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_trazabilidad_por_correlation_id(client: TestClient, token: str):
    headers = auth_header(token)
    corr = str(uuid.uuid4())
    client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=headers,
        json={
            "tipo_accion": "PROPUESTA",
            "recurso_tipo": "plan",
            "descripcion": "Propuesta con trazabilidad",
            "correlation_id": corr,
        },
    )
    client.post(
        "/api/empresa-seguridad/evidencias",
        headers=headers,
        json={
            "tipo_evidencia": "referencia",
            "referencia": "evidencia-001",
            "objeto_tipo": "plan",
            "objeto_id": str(uuid.uuid4()),
            "rol_vinculo": "APROBACION",
            "correlation_id": corr,
        },
    )
    trace = client.get(f"/api/empresa-seguridad/trazabilidad/{corr}", headers=headers)
    assert trace.status_code == 200, trace.text
    body = trace.json()
    assert body["correlation_id"] == corr
    assert body["total_etapas"] >= 2


def test_auditoria_consulta_espanol(client: TestClient, token: str):
    headers = auth_header(token)
    client.post(
        "/api/empresa-seguridad/clasificaciones",
        headers=headers,
        json={
            "objeto_tipo": "informe",
            "objeto_id": str(uuid.uuid4()),
            "codigo_clasificacion": "PUBLICA",
        },
    )
    audit = client.get("/api/empresa-seguridad/auditoria/consulta?accion=empresa", headers=headers)
    assert audit.status_code == 200, audit.text
    rows = audit.json()
    assert len(rows) >= 1
    assert rows[0]["accion_etiqueta"]
    assert "fuente" in rows[0]

    legacy = client.get("/api/audit/logs?accion=empresa&limit=20", headers=headers)
    assert legacy.status_code == 200
    if legacy.json():
        assert legacy.json()[0].get("accion_etiqueta")


def test_centro_confianza_empresarial_grupos(client: TestClient, token: str):
    headers = auth_header(token)
    res = client.get("/api/empresa-seguridad/confianza", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["resumen"]["solo_evidencia_real"] is True
    assert len(body["grupos"]) >= 1
    estados = {c["estado"] for c in body["controles"]}
    assert estados.issubset({"IMPLEMENTADO", "CONFIGURADO", "PENDIENTE", "NO_DISPONIBLE"})
    pendientes = [c for c in body["controles"] if c["id"] == "catalogo_proveedores_ia"]
    assert len(pendientes) == 1
    assert pendientes[0]["estado"] == "PENDIENTE"


def test_cross_tenant_clasificacion_denied(client: TestClient, esg_db: Session):
    org_a, user_a, pass_a = _create_tenant_user(esg_db, org_name="EmpSeg A")
    org_b, user_b, pass_b = _create_tenant_user(esg_db, org_name="EmpSeg B")
    token_a = _token(client, user_a.username, pass_a)
    token_b = _token(client, user_b.username, pass_b)
    obj_id = str(uuid.uuid4())
    client.post(
        "/api/empresa-seguridad/clasificaciones",
        headers=auth_header(token_a),
        json={"objeto_tipo": "dato", "objeto_id": obj_id, "codigo_clasificacion": "RESTRINGIDA"},
    )
    cross = client.get(
        f"/api/empresa-seguridad/clasificaciones/dato/{obj_id}",
        headers=auth_header(token_b),
    )
    assert cross.status_code == 200
    assert cross.json() is None


def test_viewer_sin_asignar_clasificacion(client: TestClient, esg_db: Session):
    _, user, password = _create_tenant_user(esg_db, org_name="EmpSeg Viewer", role="viewer")
    token = _token(client, user.username, password)
    res = client.post(
        "/api/empresa-seguridad/clasificaciones",
        headers=auth_header(token),
        json={
            "objeto_tipo": "documento",
            "objeto_id": str(uuid.uuid4()),
            "codigo_clasificacion": "INTERNA",
        },
    )
    assert res.status_code == 403


def test_exportar_gobierno(client: TestClient, token: str):
    headers = auth_header(token)
    res = client.get("/api/empresa-seguridad/exportar?limit=50", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert "auditoria" in body
    assert "exportado_en" in body


def test_regresion_gobierno_operacional(client: TestClient, token: str):
    headers = auth_header(token)
    res = client.post(
        "/api/gobierno-operacional/acciones/evaluar",
        headers=headers,
        json={"tipo_accion": "LECTURA"},
    )
    assert res.status_code == 200
    assert res.json()["requiere_aprobacion_humana"] is False


def test_regresion_bp1_visibilidad(client: TestClient, auth_headers):
    """Regresión BP1 — visibilidad dual-write intacta."""
    from tests.test_bloque_producto_1_evaluacion import _create_expediente

    exp = _create_expediente(client, auth_headers)
    eval_res = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    assert eval_res.status_code == 200
    hallazgo_id = eval_res.json()["expediente"]["hallazgos"][0]["id"]
    vis = client.post(
        f"/api/evaluaciones/{exp['id']}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": hallazgo_id, "visible_entidad": True},
    )
    assert vis.status_code == 200
    gob_vis = client.get(
        "/api/gobierno-operacional/visibilidad?dominio=evaluacion",
        headers=auth_headers,
    )
    assert gob_vis.status_code == 200
    assert any(v["objeto_id"] == hallazgo_id for v in gob_vis.json())
