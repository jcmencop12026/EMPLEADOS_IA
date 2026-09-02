#!/usr/bin/env python3
"""Backup SQLite consistente EIAAX 104f785 — backup API + integrity + lectura tablas."""
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
        fail("Uso: Backup-SqliteConsistente-104f785.py <origen.db> <destino.db> <informe.json>")

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

        tables = [
            row[0]
            for row in verify_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        if not tables:
            fail("La copia no contiene tablas de usuario")

        table_reads = {}
        for table in tables[:20]:
            try:
                count = verify_conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                table_reads[table] = int(count)
            except sqlite3.Error as exc:
                fail(f"No se pudo leer tabla {table}: {exc}")
    finally:
        verify_conn.close()

    report = {
        "source": str(source),
        "destination": str(destination),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "integrity_check": "ok",
        "tables_found": len(tables),
        "table_reads_sample": table_reads,
        "wal_present": wal.is_file(),
        "shm_present": shm.is_file(),
        "method": "sqlite3.Connection.backup()",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
