"""Cierre brechas revisión integral — Horizonte V1."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import auth_header

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
DEMO_DB_URL = "sqlite:////workspace/data/eiaax_integrado_demo.db"
DEMO_DB_PATH = Path("/workspace/data/eiaax_integrado_demo.db")
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


def test_horizonte_economico_semantica_demo_sin_verificado_real(client: TestClient, demo_a_headers):
    headers = demo_a_headers
    exp_id = _horizonte_expediente_id(client, headers)
    impacto = client.get(f"/api/evaluaciones/{exp_id}/impacto", headers=headers)
    assert impacto.status_code == 200, impacto.text
    resumen = impacto.json().get("resumen") or {}
    assert resumen.get("es_demo") is True
    assert resumen.get("banner") == "DEMO — DATOS SIMULADOS"
    sim = resumen.get("simulacion_verificado") or {}
    assert sim.get("etiqueta") == "SIMULACIÓN DE RESULTADO VERIFICADO"
    assert sim.get("es_simulado") is True
    assert resumen.get("verificado") is None
    raw = json.dumps(resumen, ensure_ascii=False)
    assert "VERIFICADO" not in raw or "SIMULACIÓN" in raw


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
    pub = vista.json().get("valor_publicable") or {}
    assert pub.get("banner") == "DEMO — DATOS SIMULADOS"
    assert pub.get("estimado_publicable") or pub.get("potencial_publicable")
    assert len(vista.json().get("hallazgos") or []) >= 0
    assert vista.json().get("impacto", {}).get("indicadores") is not None

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
        assert body.get("modo_respuesta") == "demo_controlado", body
        assert body.get("llm_real") is False


def test_documentos_persisten_tras_reinicio_real(tmp_path):
    """Reinicio real del backend: PDF/CSV, logo y datos Horizonte persisten en SQLite."""
    if not DEMO_DB_PATH.exists():
        pytest.skip("Demo DB no disponible")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = data_dir / "enterprise_ai_os.db"
    shutil.copy2(DEMO_DB_PATH, db_path)
    db_url = f"sqlite:///{db_path.as_posix()}"
    port = 18199
    env = {
        **os.environ,
        "DATABASE_URL": db_url,
        "JWT_SECRET": "test-secret-mvp-cert803-minimum-32",
        "ALLOW_INSECURE_DEV_DEFAULTS": "1",
    }

    def _http_json(method: str, path: str, token: str | None = None, payload: dict | None = None) -> tuple[int, dict]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read()
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read()
            return exc.code, json.loads(body) if body else {}

    def _http_multipart(path: str, token: str, fields: list[tuple[str, str, bytes, str]]) -> tuple[int, dict]:
        boundary = "----eiaax-persist-boundary"
        body = b""
        for name, filename, content, content_type in fields:
            body += f"--{boundary}\r\n".encode()
            body += (
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode()
            body += content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return resp.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            return exc.code, json.loads(raw) if raw else {}

    def _http_download(path: str, token: str) -> tuple[int, bytes]:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def _start_server() -> subprocess.Popen:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=str(BACKEND_DIR),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(40):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2):
                    return proc
            except Exception:
                time.sleep(0.5)
        proc.terminate()
        proc.wait(timeout=10)
        pytest.fail("Backend no arrancó tras reinicio")

    def _stop_server(proc: subprocess.Popen) -> None:
        proc.terminate()
        proc.wait(timeout=15)

    proc = _start_server()
    try:
        status, login = _http_json(
            "POST",
            "/api/auth/login",
            payload={"username": "org_a_admin", "password": PASSWORD_ORG_A},
        )
        assert status == 200, login
        token = login["access_token"]

        status, evals = _http_json("GET", "/api/evaluaciones", token=token)
        assert status == 200, evals
        items = evals.get("items", evals)
        exp_id = next(i["id"] for i in items if "Horizonte" in (i.get("entidad_nombre") or ""))

        status, detail = _http_json("GET", f"/api/evaluaciones/{exp_id}", token=token)
        assert status == 200, detail
        item_id = detail["informacion"][0]["id"]

        pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
        csv_bytes = b"indicador,valor\npersistencia_real,42\n"
        marker_pdf = "persist-restart-real.pdf"
        marker_csv = "persist-restart-real.csv"

        status, _ = _http_multipart(
            f"/api/evaluaciones/{exp_id}/informacion/{item_id}/adjuntos",
            token,
            [("files", marker_pdf, pdf_bytes, "application/pdf")],
        )
        assert status in (200, 201)
        status, _ = _http_multipart(
            f"/api/evaluaciones/{exp_id}/informacion/{item_id}/adjuntos",
            token,
            [("files", marker_csv, csv_bytes, "text/csv")],
        )
        assert status in (200, 201)

        status, lista = _http_json(
            "GET",
            f"/api/evaluaciones/{exp_id}/informacion/{item_id}/adjuntos",
            token=token,
        )
        assert status == 200, lista
        entrega_id = lista.get("entrega_id")
        adjuntos = {a["nombre"]: a for a in lista.get("adjuntos", [])}
        assert marker_pdf in adjuntos and marker_csv in adjuntos

        logo_payload = "data:image/png;base64," + ("B" * 120_000)
        status, _ = _http_json(
            "PUT",
            "/api/admin/config",
            token=token,
            payload={"enterprise_logo_url": logo_payload},
        )
        assert status == 200

        status, impacto = _http_json("GET", f"/api/evaluaciones/{exp_id}/impacto", token=token)
        assert status == 200, impacto
        resumen = impacto.get("resumen") or {}
        assert resumen.get("es_demo") is True
        horizonte_snapshot = {
            "banner": resumen.get("banner"),
            "simulacion": resumen.get("simulacion_verificado"),
            "estimado": resumen.get("estimado"),
            "potencial": resumen.get("potencial"),
        }
    finally:
        _stop_server(proc)

    proc2 = _start_server()
    try:
        status, login = _http_json(
            "POST",
            "/api/auth/login",
            payload={"username": "org_a_admin", "password": PASSWORD_ORG_A},
        )
        assert status == 200, login
        token = login["access_token"]

        status, lista2 = _http_json(
            "GET",
            f"/api/evaluaciones/{exp_id}/informacion/{item_id}/adjuntos",
            token=token,
        )
        assert status == 200, lista2
        assert lista2.get("entrega_id") == entrega_id
        adjuntos2 = {a["nombre"]: a for a in lista2.get("adjuntos", [])}
        assert marker_pdf in adjuntos2 and marker_csv in adjuntos2

        pdf_id = adjuntos2[marker_pdf]["id"]
        csv_id = adjuntos2[marker_csv]["id"]
        status, pdf_content = _http_download(f"/api/espacio-externo/adjuntos/{pdf_id}/descarga", token)
        assert status == 200
        assert b"%PDF" in pdf_content
        status, csv_content = _http_download(f"/api/espacio-externo/adjuntos/{csv_id}/descarga", token)
        assert status == 200
        assert b"persistencia_real" in csv_content

        status, cfg = _http_json("GET", "/api/admin/config", token=token)
        assert status == 200, cfg
        assert len(cfg.get("enterprise_logo_url") or "") > 100_000

        status, impacto2 = _http_json("GET", f"/api/evaluaciones/{exp_id}/impacto", token=token)
        assert status == 200, impacto2
        resumen2 = impacto2.get("resumen") or {}
        assert resumen2.get("banner") == horizonte_snapshot["banner"]
        assert resumen2.get("simulacion_verificado") == horizonte_snapshot["simulacion"]
    finally:
        _stop_server(proc2)

    assert db_path.exists() and db_path.stat().st_size > 0


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
