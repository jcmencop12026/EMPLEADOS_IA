"""Integración funcional final V1 — navegación CC, narrativa sin ficticios, espacio externo."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[1]
FRONTEND = REPO / "frontend" / "src"

FORBIDDEN_PRODUCTION_STRINGS = [
    "Prospecto2026!",
    "empresa@externa.test",
    "CONTRATO-V1",
]

FORBIDDEN_GENERIC_NARRATIVE = [
    "Glosas recurrentes y reprocesos manuales en facturación y cartera",
    "Codificación inconsistente y validación documental lenta",
]


def test_frontend_sin_datos_ficticios_espacio_externo():
    panel = FRONTEND / "components" / "espacioExterno" / "EspacioExternoAdminPanel.tsx"
    text = panel.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_PRODUCTION_STRINGS:
        assert forbidden not in text, f"Cadena ficticia en producción: {forbidden}"


def test_frontend_sin_fallback_narrativa_horizonte_generica():
    panel = FRONTEND / "components" / "evaluacion" / "CabinaInformesPanel.tsx"
    text = panel.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_GENERIC_NARRATIVE:
        assert forbidden not in text, f"Fallback narrativo genérico: {forbidden}"


def test_centro_control_sin_callback_vacio_siguiente_accion():
    panel = FRONTEND / "components" / "centroControl" / "CentroControlEmpresaPanel.tsx"
    text = panel.read_text(encoding="utf-8")
    assert "onNavigateTab={() => undefined}" not in text
    assert "mapSiguienteAccionToCabinaTab" in text


def test_siguiente_accion_tab_map_centralizado():
    lib = FRONTEND / "lib" / "siguienteAccionTabMap.ts"
    assert lib.is_file()
    text = lib.read_text(encoding="utf-8")
    assert "oportunidades: \"resultados\"" in text
    assert "cabinaTabPath" in text


@pytest.mark.tenant
def test_impacto_non_demo_sin_narrativa_medica(client: TestClient, auth_headers: dict[str, str]):
    created = client.post(
        "/api/evaluaciones",
        headers=auth_headers,
        json={
            "titulo": "Eval transporte integración",
            "entidad_nombre": "Transporte Andino S.A.",
            "necesidad": "Optimizar rutas de distribución",
            "nivel": "PRELIMINAR",
        },
    )
    assert created.status_code == 201, created.text
    exp_id = created.json()["id"]
    impacto = client.get(f"/api/evaluaciones/{exp_id}/impacto", headers=auth_headers)
    assert impacto.status_code == 200, impacto.text
    interp = impacto.json().get("interpretacion") or {}
    blob = " ".join(str(v) for v in interp.values()).lower()
    assert "glosa" not in blob
    assert "cartera" not in blob
    assert "facturación" not in blob and "facturacion" not in blob
    assert "insuficiente" in blob.lower() or "optimizar rutas" in blob.lower()


@pytest.mark.tenant
def test_siguiente_accion_expediente_responde_pestana(client: TestClient, auth_headers: dict[str, str]):
    listed = client.get("/api/evaluaciones", headers=auth_headers)
    assert listed.status_code == 200
    items = listed.json().get("items", [])
    assert items
    exp_id = items[0]["id"]
    res = client.get(f"/api/evaluaciones/{exp_id}/siguiente-accion", headers=auth_headers)
    assert res.status_code == 200, res.text
    principal = res.json().get("principal") or {}
    pestaña = principal.get("pestaña")
    if pestaña:
        known = {
            "resumen", "empresa", "informacion", "diagnostico", "analisis",
            "impacto", "valor", "oportunidades", "resultados", "solucion",
            "informes", "contrato", "operacion", "vista-empresa",
        }
        assert pestaña.lower() in known


@pytest.mark.tenant
def test_vista_entidad_no_expone_internos(client: TestClient, auth_headers: dict[str, str]):
    created = client.post(
        "/api/evaluaciones",
        headers=auth_headers,
        json={
            "titulo": "Eval vista entidad",
            "entidad_nombre": "Empresa Vista Test",
            "nivel": "PRELIMINAR",
        },
    )
    assert created.status_code == 201
    exp_id = created.json()["id"]
    res = client.get(f"/api/evaluaciones/{exp_id}/vista-entidad", headers=auth_headers)
    assert res.status_code == 200, res.text
    blob = res.text.lower()
    for key in ("margen", "precio_sugerido", "prompt", "scoring", "economia_privada"):
        assert key not in blob
