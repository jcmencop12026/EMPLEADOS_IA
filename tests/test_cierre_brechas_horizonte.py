"""Cierre brechas revisión integral — Horizonte V1."""

from __future__ import annotations

import io
import json
import os

import pytest
from fastapi.testclient import TestClient

from conftest import auth_header

DEMO_DB_URL = "sqlite:////workspace/data/eiaax_integrado_demo.db"
PASSWORD_ORG_A = "DemoA2026!"


def _require_demo_database() -> None:
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url != DEMO_DB_URL:
        pytest.skip(f"Requiere DATABASE_URL={DEMO_DB_URL}")


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return auth_header(res.json()["access_token"])


def _headers_org_a_admin(client: TestClient) -> dict[str, str]:
    return _login(client, "org_a_admin", PASSWORD_ORG_A)


def _headers_org_b_admin(client: TestClient) -> dict[str, str]:
    return _login(client, "org_b_admin", "DemoB2026!")


def _first_expediente_id(client: TestClient, headers: dict) -> str:
    listed = client.get("/api/evaluaciones", headers=headers)
    assert listed.status_code == 200, listed.text
    items = listed.json().get("items", listed.json())
    assert items, "Se esperaba al menos un expediente"
    return items[0]["id"]


@pytest.fixture
def demo_a_headers(client: TestClient) -> dict[str, str]:
    _require_demo_database()
    return _headers_org_a_admin(client)


FORBIDDEN_VISTA_KEYS = {
    "notas_internas",
    "margen",
    "precio_sugerido",
    "costo_interno",
    "prompt",
    "scoring",
    "economia_privada",
}


def _horizonte_expediente_id(client: TestClient, headers: dict) -> str:
    res = client.get("/api/evaluaciones", headers=headers)
    assert res.status_code == 200, res.text
    for item in res.json().get("items", []):
        if "Horizonte" in (item.get("entidad_nombre") or ""):
            return item["id"]
    return _first_expediente_id(client, headers)


def _first_informacion_item_id(client: TestClient, headers: dict, expediente_id: str) -> str:
    detail = client.get(f"/api/evaluaciones/{expediente_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    items = detail.json().get("informacion") or []
    assert items, "Sin ítems de información en expediente"
    return items[0]["id"]


def test_logo_backend_accepts_optimized_data_url(client: TestClient, demo_a_headers):
    headers = demo_a_headers
    payload = "data:image/png;base64," + ("A" * 350_000)
    res = client.put(
        "/api/admin/config",
        headers=headers,
        json={"enterprise_logo_url": payload},
    )
    assert res.status_code == 200, res.text
    got = client.get("/api/admin/config", headers=headers)
    assert got.status_code == 200
    assert len(got.json().get("enterprise_logo_url") or "") > 300_000


def test_horizonte_economico_seed_idempotente(client: TestClient, demo_a_headers):
    headers = demo_a_headers
    cc = client.get("/api/centro-control/resumen-ejecutivo", headers=headers)
    assert cc.status_code == 200, cc.text
    body = cc.json()
    valor = body.get("valor_consolidado") or body.get("resumen_ejecutivo", {}).get("valor") or {}
    assert valor.get("estimado") or valor.get("potencial") or valor.get("verificado"), (
        "CC sin contenido económico demo"
    )


def test_upload_pdf_y_csv_horizonte(client: TestClient, demo_a_headers):
    headers = demo_a_headers
    exp_id = _horizonte_expediente_id(client, headers)
    item_id = _first_informacion_item_id(client, headers, exp_id)

    pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    csv_bytes = b"indicador,valor\nhoras_reproceso,320\n"

    up_pdf = client.post(
        f"/api/evaluaciones/{exp_id}/informacion/{item_id}/adjuntos",
        headers=headers,
        files=[("files", ("evidencia-demo.pdf", io.BytesIO(pdf_bytes), "application/pdf"))],
    )
    assert up_pdf.status_code in (200, 201), up_pdf.text

    up_csv = client.post(
        f"/api/evaluaciones/{exp_id}/informacion/{item_id}/adjuntos",
        headers=headers,
        files=[("files", ("medicion-demo.csv", io.BytesIO(csv_bytes), "text/csv"))],
    )
    assert up_csv.status_code in (200, 201), up_csv.text

    lista = client.get(
        f"/api/evaluaciones/{exp_id}/informacion/{item_id}/adjuntos",
        headers=headers,
    )
    assert lista.status_code == 200, lista.text
    nombres = {a["nombre"] for a in lista.json().get("adjuntos", [])}
    assert "evidencia-demo.pdf" in nombres
    assert "medicion-demo.csv" in nombres

    adj_id = next(a["id"] for a in lista.json()["adjuntos"] if a["nombre"] == "evidencia-demo.pdf")
    dl = client.get(f"/api/espacio-externo/adjuntos/{adj_id}/descarga", headers=headers)
    assert dl.status_code == 200
    assert b"%PDF" in dl.content


def test_vista_entidad_no_expone_datos_internos(client: TestClient, demo_a_headers):
    headers = demo_a_headers
    exp_id = _horizonte_expediente_id(client, headers)
    vista = client.get(f"/api/evaluaciones/{exp_id}/vista-entidad", headers=headers)
    assert vista.status_code == 200, vista.text
    raw = json.dumps(vista.json(), ensure_ascii=False).lower()
    for key in FORBIDDEN_VISTA_KEYS:
        assert key not in raw, f"Vista entidad filtra mal: {key}"
    assert vista.json().get("valor_potencial") is None

    headers_b = _headers_org_b_admin(client)
    forbidden = client.get(f"/api/evaluaciones/{exp_id}/vista-entidad", headers=headers_b)
    assert forbidden.status_code in (403, 404)


def test_ask_eiaax_demo_horizonte_contexto(client: TestClient, demo_a_headers):
    headers = demo_a_headers
    exp_id = _horizonte_expediente_id(client, headers)
    preguntas = [
        "¿qué falta?",
        "¿qué encontró EIAAX?",
        "¿cuál es la oportunidad prioritaria?",
        "¿cuánto podría valer?",
        "¿qué debemos decidir?",
        "¿qué verá la empresa?",
    ]
    for q in preguntas:
        res = client.post(
            f"/api/evaluaciones/{exp_id}/preguntar",
            headers=headers,
            json={"mensaje": q},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body.get("mensaje"), f"Sin respuesta para: {q}"


def test_oportunidades_demo_variedad(client: TestClient, demo_a_headers):
    headers = demo_a_headers
    res = client.get("/api/oportunidades", headers=headers)
    assert res.status_code == 200, res.text
    items = res.json().get("items") or res.json()
    if isinstance(items, dict):
        items = items.get("items", [])
    assert len(items) >= 3, "Se requieren al menos 3 oportunidades demo"
    tipos = {str(o.get("tipo", "")).upper() for o in items[:6]}
    assert len(tipos) >= 2, f"Poca variedad en tipos: {tipos}"
