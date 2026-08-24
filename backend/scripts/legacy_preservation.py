"""Preservación, inventario y exportación de BD SQLite legacy (CURSOR-805D)."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.schema_repair import SchemaRepairError, verify_backup_file

LEGACY_MARKER_TABLES = frozenset({
    "organizations",
    "users",
    "capabilities",
    "audit_logs",
    "employee_capabilities",
    "partners",
    "roles",
    "permissions",
    "employees",
    "products",
    "data_sources",
    "report_definitions",
    "role_permissions",
    "organization_products",
})


class LegacyPreservationError(SchemaRepairError):
    pass


@dataclass
class PreservationReport:
    legacy_path: str
    sha256: str
    size_bytes: int
    integrity: str
    inventory_path: str
    inventory_csv_path: str
    export_dir: str
    tables_with_data: list[str] = field(default_factory=list)
    total_records: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "legacy_path": self.legacy_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "integrity": self.integrity,
            "inventory_path": self.inventory_path,
            "inventory_csv_path": self.inventory_csv_path,
            "export_dir": self.export_dir,
            "tables_with_data": self.tables_with_data,
            "total_records": self.total_records,
        }


def legacy_root(data_dir: Path) -> Path:
    return data_dir / "LEGACY"


def legacy_export_dir(data_dir: Path) -> Path:
    return legacy_root(data_dir) / "EXPORT"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_table_metadata(conn: sqlite3.Connection, table: str) -> dict[str, Any]:
    row_count = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    columns = [
        {
            "name": r[1],
            "type": r[2],
            "notnull": bool(r[3]),
            "default": r[4],
            "pk": bool(r[5]),
        }
        for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    ]
    primary_keys = [c["name"] for c in columns if c["pk"]]
    foreign_keys = [
        {
            "from": r[3],
            "to_table": r[2],
            "to_column": r[4],
            "on_update": r[5],
            "on_delete": r[6],
        }
        for r in conn.execute(f"PRAGMA foreign_key_list([{table}])").fetchall()
    ]
    indexes = [
        {
            "name": r[1],
            "unique": bool(r[2]),
            "origin": r[3],
            "partial": r[4],
        }
        for r in conn.execute(f"PRAGMA index_list([{table}])").fetchall()
    ]
    return {
        "table": table,
        "row_count": row_count,
        "columns": columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "indexes": indexes,
    }


def build_full_inventory(db_path: Path) -> dict[str, Any]:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return {"tables": [], "summary": {"table_count": 0, "total_records": 0, "tables_with_data": []}}

    conn = sqlite3.connect(db_path)
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        entries = [inventory_table_metadata(conn, t) for t in tables]
        with_data = [e["table"] for e in entries if e["row_count"] > 0]
        total = sum(e["row_count"] for e in entries)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_db": str(db_path),
            "tables": entries,
            "summary": {
                "table_count": len(entries),
                "total_records": total,
                "tables_with_data": with_data,
            },
        }
    finally:
        conn.close()


def write_inventory_files(inventory: dict[str, Any], legacy_dir: Path) -> tuple[Path, Path]:
    legacy_dir.mkdir(parents=True, exist_ok=True)
    json_path = legacy_dir / "LEGACY_INVENTORY.json"
    csv_path = legacy_dir / "LEGACY_INVENTORY.csv"
    json_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["table", "row_count", "columns", "primary_keys", "foreign_keys", "indexes"])
        for entry in inventory.get("tables", []):
            writer.writerow([
                entry["table"],
                entry["row_count"],
                json.dumps(entry["columns"], ensure_ascii=False),
                json.dumps(entry["primary_keys"], ensure_ascii=False),
                json.dumps(entry["foreign_keys"], ensure_ascii=False),
                json.dumps(entry["indexes"], ensure_ascii=False),
            ])
    return json_path, csv_path


def export_legacy_tables(db_path: Path, export_dir: Path, inventory: dict[str, Any]) -> list[str]:
    export_dir.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    conn = sqlite3.connect(db_path)
    try:
        for entry in inventory.get("tables", []):
            if entry["row_count"] <= 0:
                continue
            table = entry["table"]
            rows = conn.execute(f"SELECT * FROM [{table}]").fetchall()
            col_names = [d[0] for d in conn.execute(f"SELECT * FROM [{table}] LIMIT 0").description]
            records = [dict(zip(col_names, row)) for row in rows]

            json_path = export_dir / f"{table}.json"
            json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

            csv_path = export_dir / f"{table}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=col_names)
                writer.writeheader()
                for record in records:
                    writer.writerow({k: record.get(k) for k in col_names})
            exported.append(table)
    finally:
        conn.close()
    return exported


def find_preserved_legacy_by_sha256(data_dir: Path, sha256: str) -> Path | None:
    legacy_dir = legacy_root(data_dir)
    if not legacy_dir.exists():
        return None
    target = sha256.lower()
    for candidate in legacy_dir.glob("*_LEGACY_*.db"):
        if _sha256_file(candidate).lower() == target:
            return candidate
    return None


def _load_existing_inventory(legacy_dir: Path) -> dict[str, Any] | None:
    json_path = legacy_dir / "LEGACY_INVENTORY.json"
    if not json_path.exists():
        return None
    return json.loads(json_path.read_text(encoding="utf-8"))


def preserve_legacy_database(source_path: Path, data_dir: Path | None = None) -> PreservationReport:
    """Copia verificada a data/LEGACY/, inventario y export. Idempotente por SHA256."""
    if not source_path.exists() or source_path.stat().st_size == 0:
        raise LegacyPreservationError(f"BD legacy no existe o está vacía: {source_path}")

    base_data = data_dir or source_path.parent
    legacy_dir = legacy_root(base_data)
    legacy_dir.mkdir(parents=True, exist_ok=True)

    source_sha = _sha256_file(source_path)
    existing = find_preserved_legacy_by_sha256(base_data, source_sha)
    if existing:
        verify_info = verify_backup_file(existing, source_path)
        inventory = _load_existing_inventory(legacy_dir) or build_full_inventory(existing)
        json_path = legacy_dir / "LEGACY_INVENTORY.json"
        csv_path = legacy_dir / "LEGACY_INVENTORY.csv"
        if not json_path.exists() or not csv_path.exists():
            json_path, csv_path = write_inventory_files(inventory, legacy_dir)
        exported = [
            p.stem
            for p in legacy_export_dir(base_data).glob("*.json")
        ]
        summary = inventory.get("summary", {})
        return PreservationReport(
            legacy_path=str(existing),
            sha256=verify_info["sha256"],
            size_bytes=verify_info["size"],
            integrity=verify_info["integrity"],
            inventory_path=str(json_path),
            inventory_csv_path=str(csv_path),
            export_dir=str(legacy_export_dir(base_data)),
            tables_with_data=exported,
            total_records=summary.get("total_records", 0),
        )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = legacy_dir / f"{source_path.stem}_LEGACY_{ts}.db"
    shutil.copy2(source_path, dest)
    verify_info = verify_backup_file(dest, source_path)

    inventory = build_full_inventory(dest)
    json_path, csv_path = write_inventory_files(inventory, legacy_dir)
    exported = export_legacy_tables(dest, legacy_export_dir(base_data), inventory)

    summary = inventory["summary"]
    return PreservationReport(
        legacy_path=str(dest),
        sha256=verify_info["sha256"],
        size_bytes=verify_info["size"],
        integrity=verify_info["integrity"],
        inventory_path=str(json_path),
        inventory_csv_path=str(csv_path),
        export_dir=str(legacy_export_dir(base_data)),
        tables_with_data=exported,
        total_records=summary["total_records"],
    )


def verify_legacy_unchanged(legacy_path: Path, expected_sha256: str) -> bool:
    if not legacy_path.exists():
        return False
    return _sha256_file(legacy_path) == expected_sha256
