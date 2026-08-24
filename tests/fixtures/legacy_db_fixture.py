"""Fixture programático de BD legacy determinista (CURSOR-805C)."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


def build_programmatic_legacy_db(path: Path) -> dict[str, int]:
    """Crea BD legacy con anomalías históricas reproducibles."""
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    conn.executescript(
        """
        PRAGMA foreign_keys=OFF;
        CREATE TABLE organizations (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            created_at DATETIME NOT NULL
        );
        CREATE TABLE users (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            organization_id VARCHAR(36) NOT NULL,
            username VARCHAR(80) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(40) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL
        );
        -- capabilities legacy: sin requires_approval, con status NOT NULL extra
        CREATE TABLE capabilities (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            organization_id VARCHAR(36) NOT NULL,
            code VARCHAR(80) NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            risk_level VARCHAR(20) NOT NULL,
            status VARCHAR(40) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL
        );
        CREATE TABLE ai_employees (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            organization_id VARCHAR(36) NOT NULL,
            name VARCHAR(200) NOT NULL,
            specialty VARCHAR(120) NOT NULL,
            status VARCHAR(40) NOT NULL,
            model_provider VARCHAR(80),
            model_name VARCHAR(120),
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL
        );
        CREATE TABLE tools (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            organization_id VARCHAR(36) NOT NULL,
            capability_id VARCHAR(36) NOT NULL,
            code VARCHAR(80) NOT NULL,
            name VARCHAR(200) NOT NULL,
            executor_type VARCHAR(30) NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            status VARCHAR(40) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL
        );
        CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);
        """
    )

    org1, org2 = _uuid(), _uuid()
    user1 = _uuid()
    cap1 = _uuid()
    now = _now()

    conn.execute("INSERT INTO organizations VALUES (?,?,?)", (org1, "Org Legacy A", now))
    conn.execute("INSERT INTO organizations VALUES (?,?,?)", (org2, "Org Legacy B", now))
    conn.execute(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
        (user1, org1, "legacy-admin", "hash", "admin", 1, now),
    )
    conn.execute(
        "INSERT INTO capabilities VALUES (?,?,?,?,?,?,?,?,?)",
        (cap1, org1, "docint", "DOCINT Legacy", "Cap legacy", "medium", "ACTIVE", 1, now),
    )
    conn.commit()
    conn.close()

    return {
        "organizations": 2,
        "users": 1,
        "capabilities": 1,
        "ai_employees": 0,
        "tools": 0,
    }
