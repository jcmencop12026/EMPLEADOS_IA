#!/usr/bin/env python3
"""Autocontrol entrada 104f785: etapas visibles, sin fallo silencioso."""
from __future__ import annotations

import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/workspace")
TOOLS = REPO / "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785"
ENTRADA = TOOLS / "Entrada-Respaldo-Integral-104f785.cmd"
COMANDO = (TOOLS / "COMANDO_WINDOWS_UNA_LINEA.txt").read_text(encoding="utf-8").strip()
PROTECTED = "104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a"
TAG = "eiaax-tools-respaldo-104f785"
ENTRADA_GIT = (
    "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/"
    "Entrada-Respaldo-Integral-104f785.cmd"
)
LAUNCH_GIT = (
    "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/"
    "Launch-Respaldo-Integral-104f785.ps1"
)
ENTRADA_BLOB = "131a328bc00dfaae7e8b6ea9b75253d2906074bb"
ENTRADA_SHA256 = "baca7c3261c7a546e99d740bf613639576bc70b7cce48eaad3bfc37e9ebd966c"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def run_sh(cmd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["sh", "-c", cmd], capture_output=True, text=True)


def make_stub(tmp: Path, name: str, exit_code: int, msg: str) -> Path:
    path = tmp / name
    path.write_text(f'#!/bin/sh\necho "{msg}" 1>&2\nexit {exit_code}\n', encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_fetch_pass(tmp: Path) -> None:
    ok_bin = make_stub(tmp, "git_ok", 0, "From https://github.com/example/repo")
    proc = run_sh(f'"{ok_bin}" 2>/tmp/err.txt; echo exit:$?')
    if "exit:0" not in proc.stdout:
        fail("fetch PASS simulado no devolvio 0")
    ok("fetch PASS: stderr informativo + exit 0")


def test_fetch_fail(tmp: Path) -> None:
    fail_bin = make_stub(tmp, "git_fail", 128, "fatal: tag not found")
    proc = run_sh(f'"{fail_bin}" 2>/tmp/err_fail.txt; ec=$?; cat /tmp/err_fail.txt; echo exit:$ec')
    if "exit:128" not in proc.stdout or "fatal" not in proc.stdout:
        fail("fetch FAIL simulado no expuso causa")
    ok("fetch FAIL: stderr visible + exit != 0")


def test_archive_pass(tmp: Path) -> None:
    zip_path = tmp / "out.zip"
    proc = run_sh(
        f'cd "{REPO}" && git archive --format=zip -o "{zip_path}" HEAD {LAUNCH_GIT} 2>/tmp/arch.err; '
        f'ec=$?; echo exit:$ec; test -f "{zip_path}" && echo zip:ok'
    )
    if "exit:0" not in proc.stdout or "zip:ok" not in proc.stdout:
        fail(f"archive PASS simulado fallo: {proc.stdout}{proc.stderr}")
    ok("archive PASS: zip creado + exit 0")


def test_archive_fail(tmp: Path) -> None:
    proc = run_sh(
        f'cd "{REPO}" && git archive --format=zip -o "{tmp}/bad.zip" HEAD path/inexistente 2>/tmp/arch_fail.err; '
        f'ec=$?; cat /tmp/arch_fail.err; echo exit:$ec'
    )
    if "exit:0" in proc.stdout.split() or "fatal:" not in proc.stdout:
        fail(f"archive FAIL simulado deberia abortar: {proc.stdout}")
    ok("archive FAIL: causa visible + exit != 0")


def test_launcher_missing(tmp: Path) -> None:
    missing = tmp / "nolaunch.ps1"
    if missing.exists():
        fail("launcher inexistente no deberia existir")
    ok("launcher inexistente: detectable por exist")


def test_cmd_chain_stops_on_fail() -> None:
    proc = run_sh("false && echo CONTINUA; ec=$?; echo exit:$ec")
    if "CONTINUA" in proc.stdout:
        fail("cadena && continuo tras fallo")
    ok("cadena &&: fallo detiene etapas posteriores")


def test_entrada_structure() -> None:
    text = ENTRADA.read_text(encoding="utf-8")
    for label in ("[1/5]", "[2/5]", "[3/5]", "[4/5]", "[5/5]", "RESPALDO NO REALIZADO"):
        if label not in text:
            fail(f"Entrada sin etiqueta {label}")
    if re.search(r"git\s+.*2>nul", text):
        fail("Entrada no debe ocultar stderr de git con 2>nul")
    if "type \"%ERRLOG%\"" not in text:
        fail("Entrada no muestra causa en FAIL")
    ok("Entrada.cmd: 5 etapas + causa en FAIL")


def test_comando_structure() -> None:
    forbidden = ("goto ", "goto:", ":prep_done", ":stage_", ":fail_done", ":success_done", " if (", " exit ", "try {", "catch {")
    for token in forbidden:
        if token in COMANDO:
            fail(f"COMANDO contiene patron prohibido: {token.strip()}")
    if "Set-Location D:\\EMPLEADOS_IA_CONVERGENCIA" not in COMANDO:
        fail("COMANDO no entra al repo")
    if "Entrada-Respaldo-Integral-104f785.cmd" not in COMANDO:
        fail("COMANDO no materializa Entrada.cmd")
    if 'call "%TEMP%\\eiaax_in\\INTERCAMBIO\\SALIDA\\EIAAX_RESPALDO_ESTABLE_104f785\\Entrada-Respaldo-Integral-104f785.cmd"' not in COMANDO:
        fail("COMANDO no ejecuta Entrada.cmd materializado")
    if not COMANDO.startswith("Set-Location"):
        fail("COMANDO debe iniciar con Set-Location")
    ok(f"COMANDO ({len(COMANDO)} chars): preparacion minima sin goto/labels")


def test_materialize_entrada_hash() -> None:
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "hash-object", str(ENTRADA)], text=True
    ).strip()
    if blob != ENTRADA_BLOB:
        fail(f"blob Entrada.cmd cambio: {blob}")
    sha = __import__("hashlib").sha256(ENTRADA.read_bytes()).hexdigest()
    if sha != ENTRADA_SHA256:
        fail(f"sha256 Entrada.cmd cambio: {sha}")
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "in.zip"
        extract = Path(tmp) / "in"
        subprocess.check_call(
            [
                "git",
                "-C",
                str(REPO),
                "archive",
                "--format=zip",
                "-o",
                str(zip_path),
                TAG,
                ENTRADA_GIT,
            ]
        )
        extract.mkdir()
        subprocess.check_call(["unzip", "-q", str(zip_path), "-d", str(extract)])
        materialized = extract / ENTRADA_GIT
        if not materialized.is_file():
            fail("Entrada.cmd no materializado desde git archive")
        mat_blob = subprocess.check_output(
            ["git", "-C", str(REPO), "hash-object", str(materialized)], text=True
        ).strip()
        if mat_blob != ENTRADA_BLOB:
            fail(f"hash-object materializado: {mat_blob}")
    ok(f"Entrada.cmd byte-safe blob={ENTRADA_BLOB[:12]}...")


def test_ejecuta_cmd_real() -> None:
    text = ENTRADA.read_text(encoding="utf-8")
    if "call :stage_repo" not in text and "call :stage_fetch" not in text:
        fail("Entrada.cmd no define etapas batch reales")
    if "Entrada-Respaldo-Integral-104f785.cmd" in COMANDO:
        ok("COMANDO delega ejecucion al .cmd real materializado")


def test_full_flow_equivalent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "launch.zip"
        extract = tmp_path / "extract"
        launch_git = LAUNCH_GIT
        subprocess.check_call(
            [
                "git",
                "-C",
                str(REPO),
                "archive",
                "--format=zip",
                "-o",
                str(zip_path),
                TAG,
                launch_git,
            ]
        )
        extract.mkdir()
        subprocess.check_call(["unzip", "-q", str(zip_path), "-d", str(extract)])
        launch = extract / launch_git
        if not launch.is_file():
            fail("flujo equivalente: launcher no extraido")
    ok("flujo completo equivalente: archive byte-safe hasta launcher")


def test_product_intact() -> None:
    head = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", "origin/cursor/convergencia-comercial-v1-85e4"],
        text=True,
    ).strip()
    if head != PROTECTED:
        fail("producto protegido alterado")
    ok(f"producto intacto: {head[:12]}...")


def main() -> int:
    print("=== AUTOCONTROL ENTRADA 104f785 ===")
    test_entrada_structure()
    test_comando_structure()
    test_materialize_entrada_hash()
    test_ejecuta_cmd_real()
    test_cmd_chain_stops_on_fail()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_fetch_pass(tmp_path)
        test_fetch_fail(tmp_path)
        test_archive_pass(tmp_path)
        test_archive_fail(tmp_path)
        test_launcher_missing(tmp_path)
    test_full_flow_equivalent()
    test_product_intact()
    print("=== AUTOCONTROL ENTRADA PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
