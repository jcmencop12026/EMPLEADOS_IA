#!/usr/bin/env python3
"""Simula entrada Windows: materializar solo Launch via git archive y verificar bytes."""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path("/workspace")
TAG = "eiaax-tools-respaldo-104f785"
LAUNCH_GIT = (
    "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/"
    "Launch-Respaldo-Integral-104f785.ps1"
)
EXPECTED_BLOB = "72146cb321f3430df1e240a1fec189f714fdbd51"
EXPECTED_SHA256 = "9a8910b7289c9ee5e1d5046b30bde1ca101dd1deb34b8470389e22c7a7a5c95e"
PROTECTED = "104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a"

COMMAND = (
    'Set-Location D:\\EMPLEADOS_IA_CONVERGENCIA; '
    'git fetch origin tag eiaax-tools-respaldo-104f785 2>$null; '
    'git archive --format=zip -o $env:TEMP\\eiaax_r104f785.zip '
    'eiaax-tools-respaldo-104f785 '
    'INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/Launch-Respaldo-Integral-104f785.ps1; '
    'Expand-Archive -Force $env:TEMP\\eiaax_r104f785.zip $env:TEMP\\eiaax_r104f785; '
    'powershell -NoProfile -ExecutionPolicy Bypass -File '
    '"$env:TEMP\\eiaax_r104f785\\INTERCAMBIO\\SALIDA\\EIAAX_RESPALDO_ESTABLE_104f785\\'
    'Launch-Respaldo-Integral-104f785.ps1"'
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def main() -> int:
    print("=== AUDITORIA COMANDO CORTO 104f785 ===")
    print(f"Longitud comando: {len(COMMAND)} caracteres")

    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{TAG}:{LAUNCH_GIT}"], text=True
    ).strip()
    if blob != EXPECTED_BLOB:
        fail(f"blob launcher cambió: {blob}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "eiaax_r104f785.zip"
        extract = tmp_path / "eiaax_r104f785"
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
                LAUNCH_GIT,
            ]
        )
        extract.mkdir()
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract)
        launch = extract / LAUNCH_GIT
        if not launch.is_file():
            fail(f"launcher no extraído: {launch}")
        data = launch.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != EXPECTED_SHA256:
            fail(f"sha256 launcher: {sha}")
        hash_object = subprocess.check_output(
            ["git", "-C", str(REPO), "hash-object", str(launch)], text=True
        ).strip()
        if hash_object != EXPECTED_BLOB:
            fail(f"hash-object: {hash_object}")

    ok("Materialización byte-safe solo Launch (git archive archivo único)")
    ok(f"Comando corto ({len(COMMAND)} chars) — sin iex, sin bloques {{}}")

    # Launch interno delega a bootstrap (probado en auditar_integral)
    subprocess.check_call(
        [sys.executable, str(REPO / "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/auditar_integral_byte_safe_104f785.py")]
    )
    ok("Flujo integral launcher->bootstrap (auditoría existente)")

    head = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", "origin/cursor/convergencia-comercial-v1-85e4"],
        text=True,
    ).strip()
    if head != PROTECTED:
        fail("HEAD protegido remoto")
    ok("Producto protegido intacto en origin")

    print("=== AUTOCONTROL PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
