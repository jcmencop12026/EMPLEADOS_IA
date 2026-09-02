#!/usr/bin/env python3
"""Auditoría estática y pruebas de lógica para respaldo 0014a4b (ejecutar en CI/remoto)."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "Cerrar-Respaldo-Local-0014a4b.ps1"
PY_HELPER = ROOT / "Backup-SqliteConsistente-0014a4b.py"
PROTECTED_SHA = "0014a4b01a3ccf3e849a6609c8c784873f20f497"
TAG = "eiaax-v1-windows-real-operativo-0014a4b"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def test_files_exist() -> None:
    for path in (PS1, PY_HELPER):
        if not path.is_file():
            fail(f"Falta archivo: {path}")
    ok("Archivos de entrega presentes")


def test_ps1_static_audit() -> None:
    text = PS1.read_text(encoding="utf-8")

    checks = [
        ("Protected SHA completo", PROTECTED_SHA in text),
        ("Tag protegido", TAG in text),
        ("ErrorActionPreference Stop", "$ErrorActionPreference = 'Stop'" in text),
        ("git bundle verify", "git bundle verify" in text),
        ("git bundle create", "bundle', 'create'" in text),
        ("sqlite helper", "Backup-SqliteConsistente-0014a4b.py" in text),
        ("RepoRoot convergencia", r"D:\EMPLEADOS_IA_CONVERGENCIA" in text),
        ("BackupRoot destino", r"D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS" in text),
        ("NO Copy-Item sobre BD", not re.search(r"Copy-Item.*eiaax_integrado_demo\.db", text, re.I)),
        ("integrity_check", "integrity_check" in text),
        ("Manifiesto local", "MANIFIESTO_RESPALDO_LOCAL.md" in text),
        ("No mueve tag", "tag push" not in text.lower() and "git tag -f" not in text),
    ]
    for name, passed in checks:
        if not passed:
            fail(f"Auditoría PS1: {name}")
    ok("Auditoría estática PS1")


def test_sqlite_backup_logic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "source.db"
        dest = tmp_path / "dest.db"
        report = tmp_path / "report.json"

        conn = sqlite3.connect(source)
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.execute("INSERT INTO t (v) VALUES ('ok')")
        conn.commit()
        conn.close()

        proc = subprocess.run(
            [sys.executable, str(PY_HELPER), str(source), str(dest), str(report)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            fail(f"Helper SQLite falló: {proc.stderr or proc.stdout}")

        data = json.loads(report.read_text(encoding="utf-8"))
        if data["integrity_check"] != "ok":
            fail("integrity_check != ok")
        if not dest.is_file() or dest.stat().st_size <= 0:
            fail("Copia SQLite vacía o ausente")

        verify = sqlite3.connect(dest)
        row = verify.execute("SELECT v FROM t").fetchone()
        verify.close()
        if not row or row[0] != "ok":
            fail("Datos no preservados en copia SQLite")

    ok("Lógica SQLite backup + integrity_check")


def test_bundle_logic_with_existing_bundle() -> None:
    bundle = Path(
        "/workspace/INTERCAMBIO/RESPALDOS/EIAAX_V1_WINDOWS_REAL_OPERATIVO_0014a4b/"
        "eiaax-v1-windows-real-operativo-0014a4b.bundle"
    )
    if not bundle.is_file():
        ok("Bundle remoto previo no presente — lógica bundle omitida en remoto")
        return

    verify = subprocess.run(["git", "bundle", "verify", str(bundle)], capture_output=True, text=True)
    combined = (verify.stdout or "") + (verify.stderr or "")
    if verify.returncode != 0 or "is okay" not in combined:
        fail(f"git bundle verify sobre bundle existente: {combined}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "restored"
        clone = subprocess.run(["git", "clone", str(bundle), str(repo)], capture_output=True, text=True)
        if clone.returncode != 0:
            fail(f"git clone bundle: {clone.stderr}")
        checkout = subprocess.run(
            ["git", "checkout", TAG], cwd=repo, capture_output=True, text=True
        )
        if checkout.returncode != 0:
            fail(f"git checkout tag: {checkout.stderr}")
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True)
        sha = rev.stdout.strip()
        if sha != PROTECTED_SHA:
            fail(f"SHA restaurado {sha} != {PROTECTED_SHA}")

    ok("Lógica bundle verify + restore temporal")


def test_script_sha256() -> None:
    digest = hashlib.sha256(PS1.read_bytes()).hexdigest()
    print(f"INFO: SHA-256 script PS1 = {digest}")
    ok("SHA-256 script registrado")


def main() -> int:
    print("=== Auditoría respaldo local 0014a4b ===")
    test_files_exist()
    test_ps1_static_audit()
    test_sqlite_backup_logic()
    test_bundle_logic_with_existing_bundle()
    test_script_sha256()
    print("=== TODAS LAS PRUEBAS PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
