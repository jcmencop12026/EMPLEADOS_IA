"""Corrección focal post-6E — P1 Centro de Control (presentación / localización)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "frontend" / "src" / "styles.css"
LABELS = ROOT / "frontend" / "src" / "lib" / "labels.ts"
CC_PAGE = ROOT / "frontend" / "src" / "pages" / "CentroControlPage.tsx"

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


def test_p1_cc_01_metrics_grid_css_present():
    """P1-CC-01: metrics-grid debe tener layout CSS efectivo."""
    css = STYLES.read_text(encoding="utf-8")
    assert ".metrics-grid" in css
    assert "display: grid" in css
    assert ".metric-card" in css
    assert ".metric-label" in css
    assert "flex-direction: column" in css


def test_p1_cc_01_centro_control_resumen_structure():
    """P1-CC-01: Resumen ejecutivo conserva estructura de KPI."""
    page = CC_PAGE.read_text(encoding="utf-8")
    assert 'className="metrics-grid"' in page
    assert 'className="metric-card cc-metric-card"' in page
    assert 'className="metric-label"' in page
    assert "Resumen ejecutivo" in page


def test_p1_cc_02_health_status_labels():
    """P1-CC-02: traducción presentacional de estados de salud."""
    labels = LABELS.read_text(encoding="utf-8")
    assert "formatHealthStatus" in labels
    assert 'up: "Operativa"' in labels
    assert 'down: "No disponible"' in labels
    assert 'degraded: "Degradada"' in labels

    page = CC_PAGE.read_text(encoding="utf-8")
    assert "formatHealthStatus" in page
    assert "<dd>{data.salud_plataforma.status as string}</dd>" not in page


def test_p1_cc_03_audit_action_labels():
    """P1-CC-03: auditoría reciente usa etiqueta humana."""
    labels = LABELS.read_text(encoding="utf-8")
    assert '"auth.login": "Inicio de sesión"' in labels
    assert "formatAuditAction" in labels

    page = CC_PAGE.read_text(encoding="utf-8")
    assert "formatAuditAction(row.accion)" in page
    assert "{row.accion}" not in page


def test_p1_cc_02_salud_api_status_canonical_unchanged(client: TestClient, auth_headers):
    """P1-CC-02: valor canónico API permanece en inglés."""
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    salud = res.json().get("salud_plataforma")
    assert salud is not None
    assert salud["status"] in ("up", "degraded", "down")


def test_p1_cc_03_auditoria_canonical_unchanged(client: TestClient, auth_headers):
    """P1-CC-03: código canónico de auditoría no se altera en API."""
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    rows = res.json().get("auditoria_reciente") or []
    for row in rows:
        assert isinstance(row.get("accion"), str)
