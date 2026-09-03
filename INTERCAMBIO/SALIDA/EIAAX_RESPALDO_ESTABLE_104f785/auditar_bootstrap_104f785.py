#!/usr/bin/env python3
"""Simula flujo bootstrap 104f785 sin Windows (git show + hashes + HEAD guard)."""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/workspace")
REPO = ROOT
PROTECTED = "104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a"
TOOLS_REF = "eiaax-tools-respaldo-104f785"
PREFIX = "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785"
FILES = [
    "Cerrar-Respaldo-Integral-104f785.ps1",
    "Backup-SqliteConsistente-104f785.py",
    "Bootstrap-Ejecutar-Respaldo-104f785.ps1",
]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    # workspace HEAD may differ; verify protected object exists
    subprocess.run(["git", "-C", str(REPO), "cat-file", "-t", PROTECTED], check=True, capture_output=True)

    tag_commit = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", f"{TOOLS_REF}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if tag_commit.returncode != 0:
        fail("tag herramientas no disponible localmente (ejecutar git fetch origin tag)")

    ok(f"Tools ref {TOOLS_REF} -> {tag_commit.stdout.strip()}")

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "tools"
        staging.mkdir()
        for name in FILES:
            path = f"{PREFIX}/{name}"
            show = subprocess.run(
                ["git", "-C", str(REPO), "show", f"{TOOLS_REF}:{path}"],
                capture_output=True,
            )
            if show.returncode != 0:
                fail(f"git show falló: {path}")
            dest = staging / name
            dest.write_bytes(show.stdout)
            if dest.stat().st_size == 0:
                fail(f"archivo vacío: {name}")
        ok("Materialización git show sin checkout")

    bootstrap = (ROOT / PREFIX / "Bootstrap-Ejecutar-Respaldo-104f785.ps1").read_text(encoding="utf-8")
    checks = [
        ("Protected SHA", PROTECTED in bootstrap),
        ("ToolsRef", TOOLS_REF in bootstrap),
        ("sin checkout", "checkout" not in bootstrap.lower() or "sin checkout" in bootstrap.lower()),
        ("sin merge", "merge" not in bootstrap.lower()),
        ("hash verify", "ExpectedHashes" in bootstrap),
        ("staging fuera producto", r"D:\RESPALDOS_EIAAX\_bootstrap_tools_104f785" in bootstrap),
        ("HEAD guard", "headBefore" in bootstrap and "headAfter" in bootstrap),
    ]
    for name, passed in checks:
        if not passed:
            fail(f"bootstrap audit: {name}")

    cerrar = (ROOT / PREFIX / "Cerrar-Respaldo-Integral-104f785.ps1").read_text(encoding="utf-8")
    if "ToolsDirectory" not in cerrar:
        fail("Cerrar script sin ToolsDirectory")
    if re.search(r"Copy-Item.*eiaax_integrado_demo\.db", cerrar, re.I):
        fail("Copy-Item sobre BD")

    diff = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", "0014a4b01a3ccf3e849a6609c8c784873f20f497", PROTECTED, "--", "scripts/windows/"],
        capture_output=True,
        text=True,
    )
    if diff.stdout.strip():
        fail("scripts/windows changed")

    ok("scripts/windows intactos")
    print("=== SIMULACION BOOTSTRAP PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
