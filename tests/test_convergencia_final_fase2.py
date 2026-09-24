"""Convergencia final Fase 2 — pruebas focales."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "frontend" / "src" / "App.tsx"
PERMISSIONS = ROOT / "frontend" / "src" / "auth" / "permissions.ts"
CC_SERVICE = ROOT / "backend" / "app" / "services" / "control_center_service.py"
CC_ADAPTERS = ROOT / "backend" / "app" / "services" / "control_center_adapters.py"

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


def test_convergencia_ruta_centro_control_alias():
    app = APP_TSX.read_text(encoding="utf-8")
    perms = PERMISSIONS.read_text(encoding="utf-8")
    assert '<Route index element={<HomePage />} />' in app
    assert 'path="centro-control" element={<HomePage />}' in app
    assert '"/centro-control": ["control_center.view"]' in perms


def test_convergencia_kpi_organizaciones_enlace():
    service = CC_SERVICE.read_text(encoding="utf-8")
    assert "/administracion/empresas" in service
    assert "/administracion/organizaciones" not in service


def test_convergencia_mi_trabajo_adapter_usa_viewer(client: TestClient, auth_headers):
    """Mi Trabajo en CC debe usar usuario autenticado (adaptador acepta viewer)."""
    adapters = CC_ADAPTERS.read_text(encoding="utf-8")
    assert "viewer = user if isinstance(user, User)" in adapters
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    mt = res.json().get("mi_trabajo")
    assert mt is not None
    assert isinstance(mt, dict)


def test_convergencia_preserva_p1_cc_salud_canonica(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    salud = res.json()["salud_plataforma"]
    assert salud["status"] in ("up", "degraded", "down")
    assert "components" in salud


def test_convergencia_sin_dashboard_page_import():
    app = APP_TSX.read_text(encoding="utf-8")
    assert "DashboardPage" not in app
