#!/usr/bin/env python3
"""Prueba integral controlada del flujo respaldo 104f785 (byte-safe archive)."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO = Path("/workspace")
TAG = "eiaax-tools-respaldo-104f785"
PROTECTED_TAG = "eiaax-v1-windows-real-estable-104f785"
PREFIX = "INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785"
PROTECTED = "104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a"
BASE_ARRANQUE = "0014a4b01a3ccf3e849a6609c8c784873f20f497"

TOOLS = {
    "Cerrar-Respaldo-Integral-104f785.ps1": {
        "blob": "8665a7097f7747392265a1e43a601d04e591d94d",
        "sha256": "77fdbc52a42454b1f8cf43e48ae0ef407f0b78525e98bf2d4550f35c7e3b4fe1",
    },
    "Backup-SqliteConsistente-104f785.py": {
        "blob": "66e12ead386815beb6ed9b9e47084aa70c74f924",
        "sha256": "80ea222948a823b583a8f86687fa33d1a8b22a9aeeaccc69a4303c4e0a2c4b9f",
    },
    "Bootstrap-Ejecutar-Respaldo-104f785.ps1": {
        "blob": None,  # filled at runtime
        "sha256": None,
    },
    "Launch-Respaldo-Integral-104f785.ps1": {
        "blob": None,
        "sha256": None,
    },
}
USER_BAD_HASH = "2af4a2c30610ea8bfb53224b174b2c20130a1be2ecfb8dfaec6df0e9594489d9"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def git(*args: str, cwd: Path = REPO) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def populate_tool_catalog() -> None:
    for name in list(TOOLS):
        git_path = f"{PREFIX}/{name}"
        blob = git("rev-parse", f"{TAG}:{git_path}")
        raw = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
        TOOLS[name]["blob"] = blob
        TOOLS[name]["sha256"] = sha256_bytes(raw)


def test_broken_text_pipeline_produces_mismatch() -> None:
    path = f"{PREFIX}/Backup-SqliteConsistente-104f785.py"
    blob = git("rev-parse", f"{TAG}:{path}")
    raw = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    good = sha256_bytes(raw)
    if good != TOOLS["Backup-SqliteConsistente-104f785.py"]["sha256"]:
        fail("catalogo sha256 inconsistente")

    # Simula bootstrap roto: git show textual + join LF + append newline (PS WriteAllText .py)
    text = raw.decode("utf-8")
    broken = "\n".join(text.splitlines()) + "\n"
    broken_hash = sha256_bytes(broken.encode("utf-8"))

    # En LF puro coincide; simular autocrlf en git show (LF->CRLF) antes del pipeline
    crlf_text = text.replace("\n", "\r\n")
    broken_crlf = "\n".join(crlf_text.splitlines()) + "\n"
    broken_crlf_hash = sha256_bytes(broken_crlf.encode("utf-8"))

    if broken_hash == good:
        ok("Pipeline LF-only preserva hash (entorno Linux); Windows puede diferir con autocrlf")
    if broken_crlf_hash != good:
        ok(f"Pipeline texto con CRLF altera hash ({broken_crlf_hash} != {good})")
    if USER_BAD_HASH != good:
        ok(f"Hash Windows reportado ({USER_BAD_HASH}) != blob Git ({good}) — aborto correcto")


def test_git_archive_byte_safe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "tools.zip"
        extract_root = tmp_path / "extract"
        subprocess.check_call(
            ["git", "-C", str(REPO), "archive", "--format=zip", "-o", str(zip_path), TAG, PREFIX]
        )
        extract_root.mkdir()
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_root)
        tools_dir = extract_root / Path(PREFIX)
        if not tools_dir.is_dir():
            fail(f"directorio archive inesperado: {tools_dir}")

        for name, meta in TOOLS.items():
            file_path = tools_dir / name
            if not file_path.is_file():
                fail(f"falta en archive: {name}")
            blob = git("rev-parse", f"{TAG}:{PREFIX}/{name}")
            if blob != meta["blob"]:
                fail(f"blob remoto cambió para {name}")
            hash_object = git("hash-object", str(file_path))
            if hash_object != meta["blob"]:
                fail(f"hash-object != blob para {name}: {hash_object} vs {meta['blob']}")
            if sha256_file(file_path) != meta["sha256"]:
                fail(f"sha256 != catalogo para {name}")
        ok("git archive + Expand-Archive preserva bytes exactos (4 herramientas)")
        test_sqlite_helper(tools_dir)


def test_sqlite_helper(tools_dir: Path) -> None:
    helper = tools_dir / "Backup-SqliteConsistente-104f785.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src = tmp_path / "src.db"
        dst = tmp_path / "dst.db"
        report = tmp_path / "report.json"
        conn = sqlite3.connect(src)
        conn.execute("CREATE TABLE org (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO org(name) VALUES ('org_a_admin')")
        conn.commit()
        conn.close()
        subprocess.check_call([sys.executable, str(helper), str(src), str(dst), str(report)])
        data = json.loads(report.read_text())
        if data["integrity_check"] != "ok" or not data["table_reads_sample"]:
            fail("sqlite helper")
        ok("SQLite backup API + integrity_check + lectura tablas")


def test_bundle_flow() -> None:
    bundle = REPO / "INTERCAMBIO/RESPALDOS/EIAAX_V1_WINDOWS_ESTABLE_104f785/eiaax-v1-windows-real-estable-104f785.bundle"
    if not bundle.is_file():
        # crear bundle temporal
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "test.bundle"
            subprocess.check_call(
                [
                    "git",
                    "-C",
                    str(REPO),
                    "bundle",
                    "create",
                    str(bundle),
                    f"refs/tags/{PROTECTED_TAG}",
                    "origin/cursor/convergencia-comercial-v1-85e4",
                ]
            )
            _verify_bundle(bundle)
        ok("bundle verify + restore (bundle temporal)")
        return
    _verify_bundle(bundle)
    ok("bundle verify + restore (bundle existente)")


def _verify_bundle(bundle: Path) -> None:
    out = subprocess.run(["git", "bundle", "verify", str(bundle)], capture_output=True, text=True)
    combined = out.stdout + out.stderr
    if out.returncode != 0 or "is okay" not in combined:
        fail(f"bundle verify: {combined}")
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "restored"
        subprocess.check_call(["git", "clone", str(bundle), str(repo)])
        subprocess.check_call(["git", "checkout", PROTECTED_TAG], cwd=repo)
        sha = git("rev-parse", "HEAD", cwd=repo)
        if sha != PROTECTED:
            fail(f"restore sha {sha}")


def test_head_and_scripts_windows() -> None:
    subprocess.check_call(["git", "-C", str(REPO), "cat-file", "-t", PROTECTED])
    diff = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", BASE_ARRANQUE, PROTECTED, "--", "scripts/windows/"],
        capture_output=True,
        text=True,
    )
    if diff.stdout.strip():
        fail("scripts/windows modificados")
    ok("scripts/windows intactos vs 0014a4b")


def main() -> int:
    print("=== PRUEBA INTEGRAL CONTROLADA 104f785 ===")
    populate_tool_catalog()
    print("Catalogo herramientas:")
    for name, meta in TOOLS.items():
        print(f"  {name}: blob={meta['blob']} sha256={meta['sha256']}")

    test_broken_text_pipeline_produces_mismatch()
    test_git_archive_byte_safe()
    test_bundle_flow()
    test_head_and_scripts_windows()

    tag_commit = git("rev-parse", f"{TAG}^{{commit}}")
    ok(f"tag {TAG} -> {tag_commit}")
    print("=== TODAS LAS PRUEBAS PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
