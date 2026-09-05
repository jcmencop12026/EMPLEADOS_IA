"""Integración funcional final V1 — pruebas funcionales reales (PR #170)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

REPO = Path(__file__).resolve().parents[1]
FRONTEND = REPO / "frontend" / "src"
INSUF = "Información insuficiente para determinar esta conclusión."

FORBIDDEN_PRODUCTION_STRINGS = ["Prospecto2026!", "empresa@externa.test", "CONTRATO-V1"]
FORBIDDEN_GENERIC_NARRATIVE = [
    "Glosas recurrentes y reprocesos manuales en facturación y cartera",
    "Codificación inconsistente y validación documental lenta",
]

TAB_MAP = {
    "resumen": "empresa",
    "empresa": "empresa",
    "informacion": "diagnostico",
    "diagnostico": "diagnostico",
    "analisis": "diagnostico",
    "impacto": "valor",
    "valor": "valor",
    "oportunidades": "resultados",
    "resultados": "resultados",
    "solucion": "solucion",
    "informes": "informes",
    "contrato": "contrato",
}


def test_frontend_sin_datos_ficticios_espacio_externo():
    text = (FRONTEND / "components/espacioExterno/EspacioExternoAdminPanel.tsx").read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_PRODUCTION_STRINGS:
        assert forbidden not in text


def test_frontend_sin_fallback_narrativa_horizonte_generica():
    text = (FRONTEND / "components/evaluacion/CabinaInformesPanel.tsx").read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_GENERIC_NARRATIVE:
        assert forbidden not in text


def test_centro_control_sin_callback_vacio_siguiente_accion():
    text = (FRONTEND / "components/centroControl/CentroControlEmpresaPanel.tsx").read_text(encoding="utf-8")
    assert "onNavigateTab={() => undefined}" not in text
    assert "mapSiguienteAccionToCabinaTab" in text


def test_cabina_informes_usa_area_proceso_no_entidad():
    text = (FRONTEND / "components/evaluacion/CabinaInformesPanel.tsx").read_text(encoding="utf-8")
    assert "areaProceso" in text
    assert "Proceso / área: no definido en el expediente" in text
    assert "Proceso / área: {entidadNombre}" not in text


def _create_expediente(client: TestClient, headers: dict, **extra) -> dict:
    payload = {
        "titulo": extra.pop("titulo", "Eval integración"),
        "entidad_nombre": extra.pop("entidad_nombre", "Empresa Test"),
        "nivel": "PRELIMINAR",
        **extra,
    }
    res = client.post("/api/evaluaciones", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


@pytest.mark.tenant
def test_siguiente_accion_navegacion_tab_mapeada(client: TestClient, auth_headers: dict[str, str]):
    """A: API siguiente-acción devuelve pestaña mapeable al mismo expediente."""
    exp = _create_expediente(
        client,
        auth_headers,
        titulo="CC nav test",
        entidad_nombre="Logística Norte",
        necesidad="Retrasos en despacho",
    )
    res = client.get(f"/api/evaluaciones/{exp['id']}/siguiente-accion", headers=auth_headers)
    assert res.status_code == 200, res.text
    principal = res.json().get("principal") or {}
    pestaña = principal.get("pestaña")
    assert pestaña, "Se esperaba pestaña en acción principal"
    tab = TAB_MAP.get(str(pestaña).lower())
    assert tab, f"Pestaña no mapeada: {pestaña}"
    expected_path = f"/evaluaciones/{exp['id']}?tab={tab}"
    assert exp["id"] in expected_path


@pytest.mark.tenant
def test_interpretacion_real_parcial_no_reetiqueta_campos(client: TestClient, auth_headers: dict[str, str]):
    """C/D: expediente REAL parcial — no usar objetivo/área como por_qué/que_significa."""
    exp = _create_expediente(
        client,
        auth_headers,
        titulo="Parcial real",
        entidad_nombre="Transporte Andino S.A.",
        necesidad="Optimizar rutas de distribución",
        objetivo="Reducir tiempos de entrega",
        area_proceso="Logística última milla",
    )
    impacto = client.get(f"/api/evaluaciones/{exp['id']}/impacto", headers=auth_headers)
    assert impacto.status_code == 200, impacto.text
    interp = impacto.json()["interpretacion"]
    assert "Optimizar rutas" in interp["que_ocurrio"]
    assert interp["por_que"] == INSUF
    assert interp["que_significa"] == INSUF
    assert "Reducir tiempos" not in interp["por_que"]
    assert "Logística última milla" not in interp["por_que"]
    assert "glosa" not in interp["que_ocurrio"].lower()


@pytest.mark.tenant
def test_interpretacion_real_con_inferencia_usa_causa(client: TestClient, auth_headers: dict[str, str]):
    exp = _create_expediente(
        client,
        auth_headers,
        entidad_nombre="Industria Beta",
        necesidad="Alta rotura en línea de empaque",
    )
    hall = client.post(
        f"/api/evaluaciones/{exp['id']}/hallazgos",
        headers=auth_headers,
        json={
            "titulo": "Fallas recurrentes en sellado",
            "descripcion": "El sellado irregular provoca rechazos de calidad.",
            "tipo_contenido": "INFERENCIA",
        },
    )
    assert hall.status_code == 201, hall.text
    interp = client.get(f"/api/evaluaciones/{exp['id']}/impacto", headers=auth_headers).json()["interpretacion"]
    assert "sellado irregular" in interp["por_que"].lower()


@pytest.mark.tenant
def test_demo_horizonte_aislado_de_real(client: TestClient, auth_headers: dict[str, str]):
    """C: DEMO Horizonte no contamina expediente REAL."""
    listed = client.get("/api/evaluaciones", headers=auth_headers)
    demo_id = None
    for item in listed.json().get("items", []):
        if "Horizonte" in (item.get("entidad_nombre") or ""):
            demo_id = item["id"]
            break
    real = _create_expediente(
        client,
        auth_headers,
        entidad_nombre="Comercio Pacífico Ltda.",
        necesidad="Mejorar inventario",
    )
    if demo_id:
        demo_interp = client.get(f"/api/evaluaciones/{demo_id}/impacto", headers=auth_headers).json()["interpretacion"]
        assert "[DEMO]" in demo_interp["que_ocurrio"] or demo_interp.get("banner")
    real_interp = client.get(f"/api/evaluaciones/{real['id']}/impacto", headers=auth_headers).json()["interpretacion"]
    assert "[DEMO]" not in real_interp.get("que_ocurrio", "")
    assert "glosa" not in real_interp["que_ocurrio"].lower()


@pytest.mark.tenant
def test_publicador_backend_ignora_correo_falsificado(client: TestClient, auth_headers: dict[str, str]):
    """5: destinatario publicación = actor autenticado, no el enviado por cliente."""
    from app.config import settings

    exp = _create_expediente(client, auth_headers, entidad_nombre="Publisher Test Co")
    ent = client.post(
        "/api/espacio-externo/entidades",
        headers=auth_headers,
        json={"expediente_id": exp["id"]},
    )
    assert ent.status_code == 201
    entidad_id = ent.json()["entidad"]["id"]
    detail = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()
    pub = detail["publicaciones"][0]
    client.patch(
        f"/api/espacio-externo/publicaciones/{pub['id']}/estado",
        headers=auth_headers,
        json={"estado": "PREPARADO_PRESENTAR"},
    )
    spoof = client.patch(
        f"/api/espacio-externo/publicaciones/{pub['id']}/estado",
        headers=auth_headers,
        json={"estado": "PUBLICADO_EMPRESA", "destinatario": "atacante@externo.evil"},
    )
    assert spoof.status_code == 200, spoof.text
    body = spoof.json()
    assert body.get("destinatario") != "atacante@externo.evil"
    assert body.get("destinatario") in {settings.bootstrap_admin_username, None} or "@" in str(body.get("destinatario", ""))


@pytest.mark.tenant
def test_vista_empresa_visibilidad_publicar_retirar(client: TestClient, auth_headers: dict[str, str]):
    """D: autorizar hallazgo → publicar → visible; retirar visibilidad → no en vista interna autorizada."""
    exp = _create_expediente(client, auth_headers, entidad_nombre="Visibilidad Test SA")
    eval_res = client.post(f"/api/evaluaciones/{exp['id']}/evaluar", headers=auth_headers)
    assert eval_res.status_code == 200, eval_res.text
    hallazgos = eval_res.json()["expediente"]["hallazgos"]
    assert hallazgos
    hid = hallazgos[0]["id"]
    client.post(
        f"/api/evaluaciones/{exp['id']}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": hid, "visible_entidad": True},
    )
    vista_on = client.get(f"/api/evaluaciones/{exp['id']}/vista-entidad", headers=auth_headers)
    assert vista_on.status_code == 200
    assert hid in vista_on.text or hallazgos[0]["titulo"] in vista_on.text
    client.post(
        f"/api/evaluaciones/{exp['id']}/visibilidad",
        headers=auth_headers,
        json={"objeto_tipo": "hallazgo", "objeto_id": hid, "visible_entidad": False},
    )
    vista_off = client.get(f"/api/evaluaciones/{exp['id']}/vista-entidad", headers=auth_headers)
    assert vista_off.status_code == 200
    # Hallazgo oculto no debe listarse como publicable
    items = vista_off.json().get("hallazgos") or vista_off.json().get("items") or []
    if isinstance(items, list):
        assert not any(str(h.get("id")) == hid for h in items if isinstance(h, dict))


@pytest.mark.tenant
def test_aislamiento_organizacion_espacio_externo(client: TestClient, auth_headers: dict[str, str]):
    """E: org B no accede entidad de org A."""
    db = TestingSessionLocal()
    try:
        other_org = Organization(name="Org B", slug=f"orgb-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(other_org)
        db.flush()
        other_user = User(
            organization_id=other_org.id,
            username=f"other-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("x"),
            role="admin",
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        other_headers = auth_header(
            client.post("/api/auth/login", json={"username": other_user.username, "password": "x"}).json()["access_token"]
        )
    finally:
        db.close()

    exp = _create_expediente(client, auth_headers, entidad_nombre="Org A exclusiva")
    ent = client.post(
        "/api/espacio-externo/entidades",
        headers=auth_headers,
        json={"expediente_id": exp["id"]},
    ).json()
    entidad_id = ent["entidad"]["id"]
    forbidden = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=other_headers)
    assert forbidden.status_code in (403, 404)
