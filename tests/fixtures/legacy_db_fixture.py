"""Fixture programático de BD legacy determinista (CURSOR-805D)."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


def build_programmatic_legacy_db(path: Path, *, extended: bool = False) -> dict[str, int]:
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
        CREATE TABLE audit_logs (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            organization_id VARCHAR(36),
            user_id VARCHAR(36),
            action VARCHAR(120) NOT NULL,
            detail TEXT,
            created_at DATETIME NOT NULL
        );
        CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);
        """
    )

    if extended:
        conn.executescript(
            """
            CREATE TABLE partners (id VARCHAR(36) PRIMARY KEY, name VARCHAR(200) NOT NULL);
            CREATE TABLE roles (id VARCHAR(36) PRIMARY KEY, code VARCHAR(80) NOT NULL);
            CREATE TABLE permissions (id VARCHAR(36) PRIMARY KEY, code VARCHAR(80) NOT NULL);
            CREATE TABLE employees (id VARCHAR(36) PRIMARY KEY, name VARCHAR(200) NOT NULL);
            CREATE TABLE products (id VARCHAR(36) PRIMARY KEY, code VARCHAR(80) NOT NULL);
            CREATE TABLE data_sources (id VARCHAR(36) PRIMARY KEY, name VARCHAR(200) NOT NULL);
            CREATE TABLE report_definitions (id VARCHAR(36) PRIMARY KEY, code VARCHAR(80) NOT NULL);
            CREATE TABLE role_permissions (role_id VARCHAR(36), permission_id VARCHAR(36));
            CREATE TABLE organization_products (organization_id VARCHAR(36), product_id VARCHAR(36));
            CREATE TABLE employee_capabilities (employee_id VARCHAR(36), capability_id VARCHAR(36));
            """
        )

    org1, org2 = _uuid(), _uuid()
    user1 = _uuid()
    cap1 = _uuid()
    audit1 = _uuid()
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
    conn.execute(
        "INSERT INTO audit_logs VALUES (?,?,?,?,?,?)",
        (audit1, org1, user1, "legacy.action", "evento histórico", now),
    )

    counts = {
        "organizations": 2,
        "users": 1,
        "capabilities": 1,
        "ai_employees": 0,
        "tools": 0,
        "audit_logs": 1,
    }

    if extended:
        role_id, perm_id, prod_id = _uuid(), _uuid(), _uuid()
        conn.execute("INSERT INTO partners VALUES (?,?)", (_uuid(), "Partner Legacy"))
        conn.execute("INSERT INTO roles VALUES (?,?)", (role_id, "admin"))
        conn.execute("INSERT INTO permissions VALUES (?,?)", (perm_id, "read"))
        conn.execute("INSERT INTO employees VALUES (?,?)", (_uuid(), "Empleado histórico"))
        conn.execute("INSERT INTO products VALUES (?,?)", (prod_id, "PROD-1"))
        conn.execute("INSERT INTO data_sources VALUES (?,?)", (_uuid(), "DS-1"))
        conn.execute("INSERT INTO report_definitions VALUES (?,?)", (_uuid(), "RPT-1"))
        conn.execute("INSERT INTO role_permissions VALUES (?,?)", (role_id, perm_id))
        conn.execute("INSERT INTO organization_products VALUES (?,?)", (org1, prod_id))
        counts.update({
            "partners": 1,
            "roles": 1,
            "permissions": 1,
            "employees": 1,
            "products": 1,
            "data_sources": 1,
            "report_definitions": 1,
            "role_permissions": 1,
            "organization_products": 1,
        })

    conn.commit()
    conn.close()
    return counts
