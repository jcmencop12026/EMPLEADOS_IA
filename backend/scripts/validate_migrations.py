#!/usr/bin/env python3
"""Validación CI de gobierno de migraciones (MIGRATIONS-CONTROL-001)."""
from __future__ import annotations

import sys

from scripts.migration_control import (
    assert_single_head,
    load_migration_ledger,
    validate_migration_ledger,
)


def main() -> int:
    ledger = load_migration_ledger()
    head = assert_single_head()
    report = validate_migration_ledger()
    print(f"Alembic head único: {head}")
    print(f"Ledger baseline_head: {ledger.get('baseline_head')}")
    print(f"Revisiones protegidas: {report['protected_count']}")
    print(f"Revisiones en repositorio: {report['repository_revision_count']}")
    upgrade_cfg = ledger.get("upgrade_from_baseline") or {}
    if upgrade_cfg.get("enabled"):
        print(f"Upgrade from baseline habilitado: {upgrade_cfg.get('baseline_revision')}")
    else:
        print("Upgrade from baseline N-1: mecanismo listo, baseline no certificado aún.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR validación migraciones: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
