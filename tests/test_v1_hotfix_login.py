"""Pruebas hotfix login V1 — api.ts y scripts de recuperación."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
API_TS = ROOT / "frontend" / "src" / "api.ts"
LOGIN_TSX = ROOT / "frontend" / "src" / "pages" / "LoginPage.tsx"


def test_api_ts_reads_body_before_error_handling():
    src = API_TS.read_text(encoding="utf-8")
    text_idx = src.index("const text = await res.text()")
    not_ok_idx = src.index("if (!res.ok)")
    assert text_idx < not_ok_idx, "text debe leerse antes de evaluar !res.ok"


def test_login_page_password_toggle():
    src = LOGIN_TSX.read_text(encoding="utf-8")
    assert "showPassword" in src
    assert 'aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}' in src
    assert "¿Olvidó su contraseña?" in src


def test_login_wrong_password_returns_401(client: TestClient):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password-xyz"})
    assert res.status_code == 401


def test_reset_admin_script_exists():
    assert (ROOT / "backend" / "scripts" / "reset_admin_password.py").is_file()
    assert (ROOT / "backend" / "scripts" / "inspect_admin_user.py").is_file()
