"""Convergencia maestro V1 — navegación, empresas operativas y centro de control contextual."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "frontend" / "src"


def test_menu_reorganizado_empresarial():
    menu = (FRONT / "navigation" / "menu.ts").read_text(encoding="utf-8")
    assert 'id: "empresas"' in menu
    assert 'to: "/empresas"' in menu
    assert "Guía rápida" in menu
    assert 'id: "trabajo"' in menu
    assert "Diagnóstico IPS" in menu


def test_rutas_empresas_y_guia():
    app = (FRONT / "App.tsx").read_text(encoding="utf-8")
    perms = (FRONT / "auth" / "permissions.ts").read_text(encoding="utf-8")
    assert 'path="empresas"' in app
    assert "EmpresasProspectosPage" in app
    assert 'path="ayuda/guia"' in app
    assert '"/empresas": ["evaluacion.view"]' in perms


def test_centro_control_contexto_expediente():
    page = (FRONT / "pages" / "CentroControlPage.tsx").read_text(encoding="utf-8")
    assert "CentroControlEmpresaPanel" in page
    assert 'searchParams.get("expediente")' in page
    assert "Ver como empresa" in page


def test_cabina_kpi_strip_compacta():
    page = (FRONT / "pages" / "EvaluacionConsolePage.tsx").read_text(encoding="utf-8")
    assert "executive-kpi-strip" in page
    assert "metrics-grid" not in page


def test_maturity_labels_espanol():
    labels = (FRONT / "lib" / "labels.ts").read_text(encoding="utf-8")
    assert "AUTONOMOUS_CONTROLLED" in labels
    assert "Autónomo controlado" in labels


def test_diagnostico_ips_demo_en_laboratorio():
    page = (FRONT / "pages" / "DiagnosticoIpsPage.tsx").read_text(encoding="utf-8")
    assert "Laboratorio / casos demo" in page
    assert "Flujo productivo" in page
