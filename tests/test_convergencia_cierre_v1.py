"""Cierre convergencia maestro V1 — configuración, consola, cabina, empleado y solicitud."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "frontend" / "src"


def test_config_tabs_y_logo_upload():
    page = (FRONT / "pages" / "admin" / "AdminConfigPage.tsx").read_text(encoding="utf-8")
    logo = (FRONT / "components" / "admin" / "EnterpriseLogoField.tsx").read_text(encoding="utf-8")
    assert 'id: "identidad"' in page
    assert "EnterpriseLogoField" in page
    assert "Subir archivo" in logo
    assert "BrandMark" in page


def test_centro_control_consola_maestra():
    cockpit = (FRONT / "components" / "centroControl" / "CentroControlCockpit.tsx").read_text(encoding="utf-8")
    master = (FRONT / "components" / "centroControl" / "CentroControlMasterAccess.tsx").read_text(encoding="utf-8")
    cc = (FRONT / "pages" / "CentroControlPage.tsx").read_text(encoding="utf-8")
    assert "CentroControlMasterAccess" in cockpit
    assert "Consola maestra" in master
    assert "cc-salud-inline" in cc or "Salud de servicios" in cc


def test_cabina_paneles_enriquecidos():
    page = (FRONT / "pages" / "EvaluacionConsolePage.tsx").read_text(encoding="utf-8")
    assert "CabinaValorPanel" in page
    assert "CabinaContratoPanel" in page
    assert "CabinaInformesPanel" in page


def test_empleado_ficha_lifecycle():
    page = (FRONT / "pages" / "EmployeeDetailPage.tsx").read_text(encoding="utf-8")
    lib = (FRONT / "lib" / "employeeLifecycle.ts").read_text(encoding="utf-8")
    assert "resolveEmployeeLifecycleStage" in page
    assert "employee-dossier" in page
    assert "employee-actions-hierarchy" in page
    assert "nextActionKey" in lib


def test_nueva_solicitud_paradigma_necesidad():
    page = (FRONT / "pages" / "OperationsCenterPage.tsx").read_text(encoding="utf-8")
    assert "¿Qué necesita hacer hoy?" in page
    assert "Propuesta de EIAAX" in page
    assert "Autorizar y ejecutar" in page
    assert "Ejecutar análisis" not in page
    assert 'className={`btn ${mode === "rips"' not in page


def test_login_forgot_bajo_entrar():
    page = (FRONT / "pages" / "LoginPage.tsx").read_text(encoding="utf-8")
    entra_idx = page.index("Entrar")
    forgot_idx = page.index("¿Olvidó su contraseña?")
    assert forgot_idx > entra_idx
    assert "resolverá internamente" in page


def test_cabina_acciones_externas_import():
    page = (FRONT / "pages" / "EvaluacionConsolePage.tsx").read_text(encoding="utf-8")
    assert "AccionesExternasPanel" in page
    assert 'from "../components/evaluacion/AccionesExternasPanel"' in page


def test_operaciones_consola_complementaria():
    page = (FRONT / "pages" / "OperationsHubPage.tsx").read_text(encoding="utf-8")
    assert "Centro de Operaciones" in page
    assert "ops-console-strip" in page
    assert "Nueva solicitud" in page
