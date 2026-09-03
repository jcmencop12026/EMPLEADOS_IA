#!/usr/bin/env python3
"""Prueba aislamiento git.exe del motor de errores PS 5.1 (semántica cmd.exe)."""
from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/workspace")
TOOLS_DIR = REPO / "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def make_native_stub(tmp: Path, name: str, exit_code: int) -> Path:
    """Ejecutable que escribe stderr y devuelve exit code (simula git fetch informativo)."""
    path = tmp / name
    path.write_text(
        "#!/bin/sh\n"
        'echo "From https://github.com/example/repo" 1>&2\n'
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def run_cmd_isolated(workdir: Path, executable: Path) -> int:
    """
    Semántica equivalente a:
      cmd /d /c "cd /d <workdir> && <exe> 2>nul"
    En Linux: sh -c con redirección stderr y propagación de exit code.
  """
    cmd = f'cd "{workdir}" && "{executable}" 2>/dev/null'
    proc = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True)
    return proc.returncode


def test_stderr_exit0_continues(tmp: Path) -> None:
    stub = make_native_stub(tmp, "native_ok", 0)
    code = run_cmd_isolated(tmp, stub)
    if code != 0:
        fail(f"caso A (stderr+exit0): esperado 0, obtuvo {code}")
    ok("caso A: stderr informativo + exit 0 -> continúa (exit 0)")


def test_stderr_exit_nonzero_aborts(tmp: Path) -> None:
    stub = make_native_stub(tmp, "native_fail", 1)
    code = run_cmd_isolated(tmp, stub)
    if code == 0:
        fail("caso B (stderr+exit!=0): esperado !=0, obtuvo 0")
    ok(f"caso B: stderr + exit {code} -> aborta (exit != 0)")


def test_cmd_chain_and_short_circuit(tmp: Path) -> None:
    ok_stub = make_native_stub(tmp, "step_ok", 0)
    fail_stub = make_native_stub(tmp, "step_fail", 2)
    chain_ok = f'"{ok_stub}" 2>/dev/null && "{ok_stub}" 2>/dev/null'
    proc = subprocess.run(["sh", "-c", chain_ok], capture_output=True, text=True)
    if proc.returncode != 0:
        fail("cadena && con dos exit 0 debería devolver 0")
    ok("cadena &&: dos pasos exit 0 -> exit 0")

    chain_fail = f'"{ok_stub}" 2>/dev/null && "{fail_stub}" 2>/dev/null'
    proc = subprocess.run(["sh", "-c", chain_fail], capture_output=True, text=True)
    if proc.returncode == 0:
        fail("cadena && debería abortar en paso fallido")
    ok(f"cadena &&: paso fallido -> exit {proc.returncode} (no continúa)")


def test_command_entry_pattern() -> None:
    comando = (TOOLS_DIR / "COMANDO_WINDOWS_UNA_LINEA.txt").read_text(encoding="utf-8").strip()
    forbidden = [
        "git fetch origin",
        "2>&1 | Out-Null",
        "2>$null",
        "iex",
        "git show",
    ]
    for token in forbidden:
        if token in comando and token != "git fetch origin":
            fail(f"COMANDO contiene patrón prohibido: {token}")
    if "git fetch origin" in comando and "cmd /d /c" not in comando:
        fail("git fetch directo en PowerShell sin cmd /d /c")
    if "cmd /d /c" not in comando:
        fail("COMANDO no aísla git via cmd /d /c")
    if "&&" not in comando:
        fail("COMANDO no usa errorlevel cmd (&&)")
    if "$LASTEXITCODE" not in comando:
        fail("COMANDO no valida $LASTEXITCODE tras cmd")
    ok(f"COMANDO entrada ({len(comando)} chars) usa cmd /d /c + $LASTEXITCODE")


def test_launcher_uses_cmd_isolation() -> None:
    launch = (TOOLS_DIR / "Launch-Respaldo-Integral-104f785.ps1").read_text(encoding="utf-8")
    if "cmd /d /c" not in launch:
        fail("Launch no usa cmd /d /c")
    if "2>&1 | Out-Null" in launch:
        fail("Launch aún usa tubería PS 2>&1 | Out-Null con git")
    if "Invoke-GitCmd" not in launch:
        fail("Launch sin Invoke-GitCmd")
    ok("Launch aísla git.exe via cmd /d /c + exit code")


def test_bootstrap_uses_cmd_isolation() -> None:
    bootstrap = (TOOLS_DIR / "Bootstrap-Ejecutar-Respaldo-104f785.ps1").read_text(encoding="utf-8")
    if "cmd /d /c" not in bootstrap:
        fail("Bootstrap no usa cmd /d /c")
    if "2>&1 | Out-Null" in bootstrap:
        fail("Bootstrap aún usa tubería PS 2>&1 | Out-Null con git")
    ok("Bootstrap aísla git.exe via cmd /d /c + exit code")


def test_real_git_fetch_semantics() -> None:
    """git fetch tag existente: exit 0 aunque stderr informativo (simulado por stub)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_stderr_exit0_continues(tmp_path)
        test_stderr_exit_nonzero_aborts(tmp_path)
        test_cmd_chain_and_short_circuit(tmp_path)


def main() -> int:
    print("=== AUDITORIA GIT AISLADO PS 5.1 (incidente #4) ===")
    test_command_entry_pattern()
    test_launcher_uses_cmd_isolation()
    test_bootstrap_uses_cmd_isolation()
    test_real_git_fetch_semantics()
    print("=== AUTOCONTROL GIT AISLADO PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
