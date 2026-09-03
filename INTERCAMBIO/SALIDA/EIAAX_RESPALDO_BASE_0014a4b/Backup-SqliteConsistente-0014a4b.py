#!/usr/bin/env python3
"""Backup SQLite consistente para EIAAX 0014a4b — usa sqlite3.Connection.backup()."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def fail(message: str, code: int = 1) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(code)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 4:
        fail("Uso: Backup-SqliteConsistente-0014a4b.py <origen.db> <destino.db> <informe.json>")

    source = Path(sys.argv[1]).resolve()
    destination = Path(sys.argv[2]).resolve()
    report_path = Path(sys.argv[3]).resolve()

    if not source.is_file():
        fail(f"Origen no encontrado: {source}")

    wal = source.with_suffix(source.suffix + "-wal")
    shm = source.with_suffix(source.suffix + "-shm")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    source_conn = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    dest_conn = sqlite3.connect(str(destination))
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()

    verify_conn = sqlite3.connect(str(destination))
    try:
        integrity = verify_conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            fail(f"PRAGMA integrity_check distinto de ok: {integrity}")
    finally:
        verify_conn.close()

    report = {
        "source": str(source),
        "destination": str(destination),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "integrity_check": "ok",
        "wal_present": wal.is_file(),
        "shm_present": shm.is_file(),
        "wal_path": str(wal) if wal.is_file() else None,
        "shm_path": str(shm) if shm.is_file() else None,
        "method": "sqlite3.Connection.backup()",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
