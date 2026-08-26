"""CURSOR-840B v3 — corrupción SQLite, migración segura y matriz de duplicados."""
from __future__ import annotations

import os
import sqlite3
import tempfile
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from app.models import Organization, Permission, Role, RolePermission, User
from app.permissions import user_permissions
from app.security import hash_password
from conftest import TestingSessionLocal
from tests.test_admin_840 import _create_org_admin, _token


def _alembic_cfg(db_url: str) -> Config:
    backend = Path(__file__).resolve().parents[1] / "backend"
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _sqlite_path(db_url: str) -> str:
    return db_url.replace("sqlite:///", "")


def _bootstrap_permissions_on_url(db_url: str) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.seed_permissions import bootstrap_permissions

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    session = sessionmaker(bind=engine)()
    try:
        bootstrap_permissions(session)
    finally:
        session.close()
        engine.dispose()


@pytest.mark.parametrize(
    "corrupt_literal",
    ["'yes'", "'true'", "'t'", "'TRUE'", "'on'", "'2'", "'-1'", "'garbage'", "''"],
)
def test_migration_corrupt_is_active_normalized_to_inactive(monkeypatch, corrupt_literal):
    """Migración: valores corruptos vía UPDATE directo en SQLite → is_active=0 tras upgrade."""
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "a840c4d5e6f7")
        _bootstrap_permissions_on_url(db_url)
        role_id = str(uuid.uuid4())
        code = f"corrupt-mig-{uuid.uuid4().hex[:6]}"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) "
            f"VALUES ('{role_id}', NULL, '{code}', 'Corrupt', 0, 1)"
        )
        conn.execute(f"UPDATE roles SET is_active = {corrupt_literal} WHERE id = '{role_id}'")
        conn.commit()
        conn.close()

        command.upgrade(cfg, "b840c3e4f5a6")

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT is_active, typeof(is_active) FROM roles WHERE id = ?",
            (role_id,),
        ).fetchone()
        assert row is not None
        assert row[0] == 0
        assert row[1] == "integer"
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_migration_duplicate_corrupt_yes_becomes_inactive(monkeypatch):
    """Duplicados con is_active corrupto 'yes' → superviviente INACTIVO."""
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "a840c4d5e6f7")
        _bootstrap_permissions_on_url(db_url)
        conn = sqlite3.connect(db_path)
        view_id = conn.execute("SELECT id FROM permissions WHERE code='employee.view'").fetchone()[0]
        code = f"dup-corrupt-{uuid.uuid4().hex[:6]}"
        role_a = str(uuid.uuid4())
        role_b = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) "
            f"VALUES ('{role_a}', NULL, '{code}', 'A', 0, 1)"
        )
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) "
            f"VALUES ('{role_b}', NULL, '{code}', 'B', 0, 1)"
        )
        conn.execute(f"UPDATE roles SET is_active = 'yes' WHERE id = '{role_b}'")
        for rid in (role_a, role_b):
            conn.execute(
                "INSERT INTO role_permissions (id, role_id, permission_id) VALUES (?,?,?)",
                (str(uuid.uuid4()), rid, view_id),
            )
        conn.commit()
        conn.close()

        command.upgrade(cfg, "b840c3e4f5a6")

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT is_active FROM roles WHERE organization_id IS NULL AND code=?",
            (code,),
        ).fetchone()
        assert row[0] == 0
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_migration_canonical_integer_one_stays_active(monkeypatch):
    """Migración: entero canónico 1 permanece activo."""
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "a840c4d5e6f7")
        role_id = str(uuid.uuid4())
        code = f"canonical-mig-{uuid.uuid4().hex[:6]}"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) "
            "VALUES (?, NULL, ?, ?, 0, ?)",
            (role_id, code, "Canonical", 1),
        )
        conn.commit()
        conn.close()

        command.upgrade(cfg, "b840c3e4f5a6")

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT is_active FROM roles WHERE id = ?",
            (role_id,),
        ).fetchone()
        assert row[0] == 1
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.parametrize(
    "corrupt_value",
    ["yes", "TRUE", "2", "null", "", "on", "false", 0],
)
def test_sqlite_corrupt_is_active_persisted_denies(corrupt_value):
    """Valores corruptos insertados directamente en SQLite → DENY."""
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, f"Corrupt-{uuid.uuid4().hex[:6]}")
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        role = Role(
            organization_id=org.id,
            code=f"corrupt-{uuid.uuid4().hex[:6]}",
            name="Corrupt",
            is_system=False,
            is_active=True,
        )
        db.add(role)
        db.flush()
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        assert view_perm
        db.add(RolePermission(role_id=role.id, permission_id=view_perm.id))
        user = User(
            organization_id=org.id,
            username=f"corrupt-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Corrupt840*"),
            role=role.code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()

        bind = db.get_bind()
        raw = "NULL" if corrupt_value is None else repr(corrupt_value)
        with bind.connect() as conn:
            conn.execute(
                __import__("sqlalchemy").text(
                    f"UPDATE roles SET is_active = {raw} WHERE id = :id"
                ),
                {"id": role.id},
            )
            conn.commit()

        db.expire_all()
        perms = user_permissions(user, db)
        assert perms == set()
    finally:
        db.close()


def test_sqlite_canonical_active_allows_when_permission_present():
    db = TestingSessionLocal()
    try:
        org, _, _ = _create_org_admin(db, "Canonical Active")
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        role = Role(
            organization_id=org.id,
            code=f"canonical-{uuid.uuid4().hex[:6]}",
            name="Canonical",
            is_system=False,
            is_active=True,
        )
        db.add(role)
        db.flush()
        view_perm = db.query(Permission).filter(Permission.code == "employee.view").first()
        db.add(RolePermission(role_id=role.id, permission_id=view_perm.id))
        user = User(
            organization_id=org.id,
            username=f"canonical-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Canonical840*"),
            role=role.code,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.commit()

        bind = db.get_bind()
        role.is_active = True
        db.commit()
        db.expire_all()
        perms = user_permissions(user, db)
        assert "employee.view" in perms
    finally:
        db.close()


def _seed_role_pair(
    db: Session,
    *,
    org: Organization,
    code: str,
    role_a_active: bool,
    role_b_active: bool,
    role_a_perms: set[str],
    role_b_perms: set[str],
) -> tuple[Role, Role]:
    perms = {p.code: p for p in db.query(Permission).all()}
    role_a = Role(
        organization_id=None,
        code=code,
        name="A",
        is_system=False,
        is_active=role_a_active,
    )
    role_b = Role(
        organization_id=None,
        code=code,
        name="B",
        is_system=False,
        is_active=role_b_active,
    )
    db.add_all([role_a, role_b])
    db.flush()
    for perm_code in role_a_perms:
        db.add(RolePermission(role_id=role_a.id, permission_id=perms[perm_code].id))
    for perm_code in role_b_perms:
        db.add(RolePermission(role_id=role_b.id, permission_id=perms[perm_code].id))
    db.commit()
    return role_a, role_b


def test_migration_duplicate_same_permissions(monkeypatch):
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "a840c4d5e6f7")
        _bootstrap_permissions_on_url(db_url)
        conn = sqlite3.connect(db_path)
        view_id = conn.execute("SELECT id FROM permissions WHERE code='employee.view'").fetchone()[0]
        code = f"dup-a-{uuid.uuid4().hex[:6]}"
        role_a = str(uuid.uuid4())
        role_b = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) VALUES (?,?,?,?,?,?)",
            (role_a, None, code, "A", 0, 1),
        )
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) VALUES (?,?,?,?,?,?)",
            (role_b, None, code, "B", 0, 1),
        )
        for rid in (role_a, role_b):
            conn.execute(
                "INSERT INTO role_permissions (id, role_id, permission_id) VALUES (?,?,?)",
                (str(uuid.uuid4()), rid, view_id),
            )
        conn.commit()
        conn.close()

        command.upgrade(cfg, "b840c3e4f5a6")

        conn = sqlite3.connect(db_path)
        survivors = conn.execute(
            "SELECT id FROM roles WHERE organization_id IS NULL AND code=?",
            (code,),
        ).fetchall()
        assert len(survivors) == 1
        survivor_id = survivors[0][0]
        perm_codes = {
            row[0]
            for row in conn.execute(
                """
                SELECT p.code FROM role_permissions rp
                JOIN permissions p ON p.id = rp.permission_id
                WHERE rp.role_id = ?
                """,
                (survivor_id,),
            )
        }
        assert perm_codes == {"employee.view"}
        orphans = conn.execute(
            "SELECT COUNT(*) FROM role_permissions WHERE role_id NOT IN (SELECT id FROM roles)"
        ).fetchone()[0]
        assert orphans == 0
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_migration_duplicate_different_permissions_least_privilege(monkeypatch):
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "a840c4d5e6f7")
        _bootstrap_permissions_on_url(db_url)
        conn = sqlite3.connect(db_path)
        view_id = conn.execute("SELECT id FROM permissions WHERE code='employee.view'").fetchone()[0]
        admin_id = conn.execute("SELECT id FROM permissions WHERE code='admin.user.view'").fetchone()[0]
        code = f"dup-b-{uuid.uuid4().hex[:6]}"
        role_a = str(uuid.uuid4())
        role_b = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) VALUES (?,?,?,?,?,?)",
            (role_a, None, code, "A", 0, 1),
        )
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) VALUES (?,?,?,?,?,?)",
            (role_b, None, code, "B", 0, 1),
        )
        conn.execute(
            "INSERT INTO role_permissions (id, role_id, permission_id) VALUES (?,?,?)",
            (str(uuid.uuid4()), role_a, view_id),
        )
        conn.execute(
            "INSERT INTO role_permissions (id, role_id, permission_id) VALUES (?,?,?)",
            (str(uuid.uuid4()), role_b, admin_id),
        )
        conn.commit()
        conn.close()

        command.upgrade(cfg, "b840c3e4f5a6")

        conn = sqlite3.connect(db_path)
        survivors = conn.execute(
            "SELECT id, is_active FROM roles WHERE organization_id IS NULL AND code=?",
            (code,),
        ).fetchall()
        assert len(survivors) == 1
        survivor_id, is_active = survivors[0]
        perm_count = conn.execute(
            "SELECT COUNT(*) FROM role_permissions WHERE role_id=?",
            (survivor_id,),
        ).fetchone()[0]
        assert perm_count == 0
        assert is_active == 1
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_migration_duplicate_one_inactive_becomes_inactive(monkeypatch):
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "a840c4d5e6f7")
        _bootstrap_permissions_on_url(db_url)
        conn = sqlite3.connect(db_path)
        view_id = conn.execute("SELECT id FROM permissions WHERE code='employee.view'").fetchone()[0]
        code = f"dup-c-{uuid.uuid4().hex[:6]}"
        role_a = str(uuid.uuid4())
        role_b = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) VALUES (?,?,?,?,?,?)",
            (role_a, None, code, "A", 0, 1),
        )
        conn.execute(
            "INSERT INTO roles (id, organization_id, code, name, is_system, is_active) VALUES (?,?,?,?,?,?)",
            (role_b, None, code, "B", 0, 0),
        )
        for rid in (role_a, role_b):
            conn.execute(
                "INSERT INTO role_permissions (id, role_id, permission_id) VALUES (?,?,?)",
                (str(uuid.uuid4()), rid, view_id),
            )
        conn.commit()
        conn.close()

        command.upgrade(cfg, "b840c3e4f5a6")

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT is_active FROM roles WHERE organization_id IS NULL AND code=?",
            (code,),
        ).fetchone()
        assert row[0] == 0
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_migration_roundtrip_upgrade_downgrade_upgrade(monkeypatch):
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "head")
        _bootstrap_permissions_on_url(db_url)
        command.downgrade(cfg, "a840c4d5e6f7")
        command.upgrade(cfg, "head")

        conn = sqlite3.connect(db_path)
        indexes = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert "uq_roles_global_code" in indexes
        orphans = conn.execute(
            "SELECT COUNT(*) FROM role_permissions WHERE role_id NOT IN (SELECT id FROM roles)"
        ).fetchone()[0]
        assert orphans == 0
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
