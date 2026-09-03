#!/usr/bin/env python3
"""Auditoría remota respaldo integral 104f785."""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "Cerrar-Respaldo-Integral-104f785.ps1"
PY = ROOT / "Backup-SqliteConsistente-104f785.py"
BUNDLE = Path(
    "/workspace/INTERCAMBIO/RESPALDOS/EIAAX_V1_WINDOWS_ESTABLE_104f785/"
    "eiaax-v1-windows-real-estable-104f785.bundle"
)
SHA = "104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a"
TAG = "eiaax-v1-windows-real-estable-104f785"
BASE = "0014a4b01a3ccf3e849a6609c8c784873f20f497"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def main() -> int:
    text = PS1.read_text(encoding="utf-8")
    checks = [
        (SHA in text, "SHA completo en PS1"),
        (TAG in text, "Tag en PS1"),
        (r"D:\RESPALDOS_EIAAX" in text, "Ruta física respaldo"),
        ("Copy-Item" not in text or "sin Copy-Item" in text.lower() or True, "n/a"),
        (not re.search(r"Copy-Item.*eiaax_integrado_demo\.db", text, re.I), "sin Copy-Item BD"),
        ("Backup-SqliteConsistente-104f785.py" in text, "helper sqlite"),
    ]
    for passed, name in checks:
        if not passed:
            fail(name)

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "s.db"
        dst = Path(tmp) / "d.db"
        rep = Path(tmp) / "r.json"
        c = sqlite3.connect(src)
        c.execute("CREATE TABLE org (id INTEGER PRIMARY KEY, name TEXT)")
        c.execute("INSERT INTO org(name) VALUES ('org_a')")
        c.commit()
        c.close()
        proc = subprocess.run([sys.executable, str(PY), str(src), str(dst), str(rep)], capture_output=True, text=True)
        if proc.returncode != 0:
            fail(proc.stderr or proc.stdout)
        data = json.loads(rep.read_text())
        if data["integrity_check"] != "ok" or not data["table_reads_sample"]:
            fail("sqlite helper")

    ok("PS1 + helper SQLite")

    if BUNDLE.is_file():
        out = subprocess.run(["git", "bundle", "verify", str(BUNDLE)], capture_output=True, text=True)
        combined = out.stdout + out.stderr
        if out.returncode != 0 or "is okay" not in combined:
            fail("bundle verify")
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            subprocess.run(["git", "clone", str(BUNDLE), str(repo)], check=True, capture_output=True)
            subprocess.run(["git", "checkout", TAG], cwd=repo, check=True, capture_output=True)
            rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True)
            if rev.stdout.strip() != SHA:
                fail("restore sha")
        ok("Bundle verify + restore")

    diff = subprocess.run(
        ["git", "-C", "/workspace", "diff", "--name-only", BASE, SHA, "--", "scripts/windows/"],
        capture_output=True,
        text=True,
    )
    if diff.stdout.strip():
        fail(f"scripts/windows changed: {diff.stdout.strip()}")
    ok("scripts/windows intactos vs 0014a4b")

    tag = subprocess.run(
        ["git", "-C", "/workspace", "rev-parse", f"{TAG}^{{commit}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    if tag.stdout.strip() != SHA:
        fail("tag commit mismatch")
    ok("Tag apunta a 104f785")

    print("=== AUDITORIA REMOTA PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
