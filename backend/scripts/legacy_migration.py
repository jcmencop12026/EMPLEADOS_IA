"""Compatibilidad hacia db_startup (CURSOR-805D). La migración automática legacy→actual está abandonada."""
from __future__ import annotations

from scripts.db_startup import (  # noqa: F401
    DbStartupError,
    create_fresh_database,
    database_url_to_path,
    detect_db_scenario,
    inventory_legacy_db,
    prepare_database,
    run_bootstrap,
)

# Alias históricos (805C)
LegacyMigrationError = DbStartupError


def migrate_legacy_database(
    database_url: str,
    *,
    skip_backup: bool = False,
    perform_swap: bool = True,
) -> dict:
    """Delega en prepare_database. perform_swap ignorado (sin migración automática)."""
    _ = skip_backup, perform_swap
    return prepare_database(database_url)
