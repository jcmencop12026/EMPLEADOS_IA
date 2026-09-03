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
EXPECTED_BLOB = "8091c1f934e640306b42c401bf56ff1cd1486b98"
EXPECTED_SHA256 = "a1caf4dc9b8e525cf3c4e6436a628a0204a5f2cd0c2073b25c8815cb8a1ab826"
PROTECTED = "104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a"

COMMAND = (
    REPO / "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/COMANDO_WINDOWS_UNA_LINEA.txt"
).read_text(encoding="utf-8").strip()


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def main() -> int:
    print("=== AUDITORIA COMANDO CORTO 104f785 ===")
    print(f"Longitud comando: {len(COMMAND)} caracteres")

    launch_path = REPO / LAUNCH_GIT
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "hash-object", str(launch_path)], text=True
    ).strip()
    if blob != EXPECTED_BLOB:
        fail(f"blob launcher cambió: {blob} (esperado {EXPECTED_BLOB})")

    sha = hashlib.sha256(launch_path.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA256:
        fail(f"sha256 launcher: {sha}")

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
                "HEAD",
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
        if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
            fail("sha256 post-archive no coincide")
        hash_object = subprocess.check_output(
            ["git", "-C", str(REPO), "hash-object", str(launch)], text=True
        ).strip()
        if hash_object != EXPECTED_BLOB:
            fail(f"hash-object: {hash_object}")

    ok("Materialización byte-safe solo Launch (git archive archivo único)")
    forbidden = (" exit ", " exit 1", "if (", "try {", "catch {")
    for token in forbidden:
        if token in COMMAND:
            fail(f"COMANDO contiene patrón prohibido: {token.strip()}")
    if not COMMAND.startswith("cmd /d /c"):
        fail("COMANDO padre debe ser únicamente cmd /d /c")
    if COMMAND.count("&&") < 3:
        fail("COMANDO sin cadena && completa fetch->archive->expand->launcher")
    ok(f"Comando corto ({len(COMMAND)} chars) — todo encapsulado en cmd /d /c, sin exit/if/try")

    subprocess.check_call(
        [
            sys.executable,
            str(REPO / "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/auditar_git_aislado_ps51_104f785.py"),
        ]
    )
    ok("Aislamiento git + casos stderr/exit code")

    subprocess.check_call(
        [
            sys.executable,
            str(REPO / "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/auditar_integral_byte_safe_104f785.py"),
        ]
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
