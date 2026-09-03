"""Tests — Presentación ejecutiva real EIAAX (V1 continuación)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import evaluacion_service as ev_svc
from app.services import presentacion_publicacion_adapter as pub_adapter
from app.services import resultados_service as res_svc

pytestmark = [pytest.mark.operations]


@pytest.fixture
def sdb():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _tenant(db: Session) -> tuple[Organization, User]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-pres-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    admin = User(
        organization_id=org.id,
        username=f"adm-{uuid.uuid4().hex[:6]}",
        email=f"a-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return org, admin


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _expediente_real(db: Session, org: Organization, admin: User):
    exp = ev_svc.create_expediente(
        db,
        organization_id=org.id,
        user_id=admin.id,
        titulo="Evaluación real",
        entidad_nombre="Cliente Real SA",
        necesidad="Mejorar procesos",
        nivel="PRELIMINAR",
    )
    ev_svc.create_hallazgo(
        db,
        exp.id,
        org.id,
        user_id=admin.id,
        titulo="Hallazgo publicable",
        descripcion="Visible para entidad",
        tipo_contenido="HECHO",
        visible_entidad=True,
    )
    ev_svc.create_hallazgo(
        db,
        exp.id,
        org.id,
        user_id=admin.id,
        titulo="Nota interna",
        descripcion="No visible",
        tipo_contenido="INFERENCIA",
        visible_entidad=False,
    )
    res_svc.create_indicador(
        db,
        org.id,
        nombre="Eficiencia",
        unidad="%",
        valor_antes=50.0,
        valor_proyectado=70.0,
        expediente_id=exp.id,
        visible_entidad=True,
    )
    res_svc.generate_informe_impacto(
        db, org.id, admin.id, expediente_id=exp.id, visibilidad="VISIBLE_ENTIDAD"
    )
    db.commit()
    return exp


def test_presentacion_real_rechaza_viewer_sin_publicacion(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    viewer = User(
        organization_id=org.id,
        username=f"view-{uuid.uuid4().hex[:6]}",
        email=f"v-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="viewer",
        is_active=True,
    )
    sdb.add(viewer)
    sdb.commit()
    admin_headers = _login(client, admin.username)
    viewer_headers = _login(client, viewer.username)
    exp = _expediente_real(sdb, org, admin)

    res = client.get(f"/api/presentacion/{exp.id}?audiencia=GERENCIA", headers=viewer_headers)
    assert res.status_code == 403

    # Admin puede previsualizar en PRIVADO (workflow interno)
    preview = client.get(f"/api/presentacion/{exp.id}?audiencia=GERENCIA", headers=admin_headers)
    assert preview.status_code == 200


def test_presentacion_real_autorizada_publicada(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    exp = _expediente_real(sdb, org, admin)

    pub = client.put(
        f"/api/presentacion/{exp.id}/publicacion",
        headers=headers,
        json={"estado": "PUBLICADO_A_EMPRESA"},
    )
    assert pub.status_code == 200
    assert pub.json()["estado"] == "PUBLICADO_A_EMPRESA"

    res = client.get(f"/api/presentacion/{exp.id}?audiencia=GERENCIA", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["es_demo"] is False
    assert body["etiqueta"] == "PRESENTACIÓN EJECUTIVA"
    assert body["publicacion"]["estado"] == "PUBLICADO_A_EMPRESA"
    titulos = [s["titulo"] for s in body["secciones"]]
    assert "Qué encontramos" in titulos
    contenido = next(s["contenido"] for s in body["secciones"] if s["titulo"] == "Qué encontramos")
    assert "Hallazgo publicable" in contenido
    assert "Nota interna" not in str(body)


def test_presentacion_real_cuatro_audiencias(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    exp = _expediente_real(sdb, org, admin)
    client.put(
        f"/api/presentacion/{exp.id}/publicacion",
        headers=headers,
        json={"estado": "PUBLICADO_A_EMPRESA"},
    )

    for aud in ("GERENCIA", "OPERACION", "SISTEMAS", "FINANCIERO"):
        r = client.get(f"/api/presentacion/{exp.id}?audiencia={aud}", headers=headers)
        assert r.status_code == 200
        assert r.json()["audiencia"] == aud
        assert r.json().get("graficos", {}).get("series") is not None


def test_presentacion_real_pdf(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    exp = _expediente_real(sdb, org, admin)
    client.put(
        f"/api/presentacion/{exp.id}/publicacion",
        headers=headers,
        json={"estado": "PUBLICADO_A_EMPRESA"},
    )

    res = client.get(f"/api/presentacion/{exp.id}/pdf?audiencia=GERENCIA", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")


def test_demo_pdf_y_aislamiento_ruta_real(client: TestClient, sdb):
    from app.services import demo_comercial_service as demo_svc

    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    seed = client.post("/api/demo-comercial/semilla", headers=headers).json()
    demo_id = seed["expediente_id"]

    pdf = client.get(
        f"/api/demo-comercial/presentacion/{demo_id}/pdf?audiencia=GERENCIA",
        headers=headers,
    )
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")

    bloqueo = client.get(f"/api/presentacion/{demo_id}?audiencia=GERENCIA", headers=headers)
    assert bloqueo.status_code == 403


def test_publicacion_fail_closed_informe_interno(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    exp = ev_svc.create_expediente(
        sdb,
        organization_id=org.id,
        user_id=admin.id,
        titulo="Sin informe publicable",
        entidad_nombre="Otra SA",
        nivel="PRELIMINAR",
    )
    res_svc.generate_informe_impacto(
        sdb, org.id, admin.id, expediente_id=exp.id, visibilidad="INTERNO"
    )
    sdb.commit()

    res = client.put(
        f"/api/presentacion/{exp.id}/publicacion",
        headers=headers,
        json={"estado": "PUBLICADO_A_EMPRESA"},
    )
    assert res.status_code == 422


def test_informes_comerciales_config_adapter(client: TestClient, sdb):
    _, admin = _tenant(sdb)
    headers = _login(client, admin.username)

    created = client.post(
        "/api/presentacion/informes-comerciales/config",
        headers=headers,
        json={
            "nombre": "Resumen mensual",
            "audiencia": "GERENCIA",
            "periodicidad": "MENSUAL",
            "destinatarios": ["ceo@empresa.com"],
            "resumen": "Enlace seguro",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["estado"] == "PENDIENTE_INTEGRACION"
    assert body["integracion"]["contrato_event_type"] == "INFORME_COMERCIAL_PERIODICO"

    listed = client.get("/api/presentacion/informes-comerciales/config", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) >= 1


def test_proteccion_contenido_interno_en_presentacion(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    exp = _expediente_real(sdb, org, admin)
    client.put(
        f"/api/presentacion/{exp.id}/publicacion",
        headers=headers,
        json={"estado": "PUBLICADO_A_EMPRESA"},
    )
    res = client.get(f"/api/presentacion/{exp.id}?audiencia=GERENCIA", headers=headers)
    payload = str(res.json())
    for forbidden in ("prompts", "margen interno", "costos internos"):
        assert forbidden in res.json().get("proteccion_ip", {}).get("oculto", [])
    assert "Nota interna" not in payload


def test_preparado_para_presentar_permite_preview_interno(client: TestClient, sdb):
    org, admin = _tenant(sdb)
    headers = _login(client, admin.username)
    exp = _expediente_real(sdb, org, admin)
    client.put(
        f"/api/presentacion/{exp.id}/publicacion",
        headers=headers,
        json={"estado": "PREPARADO_PARA_PRESENTAR"},
    )
    res = client.get(f"/api/presentacion/{exp.id}?audiencia=OPERACION", headers=headers)
    assert res.status_code == 200
    assert res.json()["publicacion"]["estado"] == "PREPARADO_PARA_PRESENTAR"
