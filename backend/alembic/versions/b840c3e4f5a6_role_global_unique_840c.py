"""role_global_unique_840c

Revision ID: b840c3e4f5a6
Revises: a840c4d5e6f7
Create Date: 2026-08-24 18:30:00.000000

Consolidación segura de roles globales duplicados (CURSOR-840B v3):
- superviviente determinístico (created_at, id)
- permisos = intersección (mínimo privilegio)
- activo solo si TODOS los duplicados son canónicamente activos
- remapeo de role_permissions antes de eliminar
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b840c3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a840c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_canonical_active(raw) -> bool:
    return raw is True or raw == 1


def _normalize_corrupt_is_active(conn) -> None:
  conn.execute(
        sa.text(
            """
            UPDATE roles
            SET is_active = CASE
                WHEN is_active IN (1, '1', 'true', 'TRUE', 't', 'yes', 'YES') THEN 1
                ELSE 0
            END
            """
        )
    )


def _permission_ids(conn, role_id: str) -> set[str]:
    rows = conn.execute(
        sa.text("SELECT permission_id FROM role_permissions WHERE role_id = :role_id"),
        {"role_id": role_id},
    ).fetchall()
    return {str(row.permission_id) for row in rows}


def _set_role_permissions(conn, role_id: str, permission_ids: set[str]) -> None:
    conn.execute(
        sa.text("DELETE FROM role_permissions WHERE role_id = :role_id"),
        {"role_id": role_id},
    )
    for permission_id in sorted(permission_ids):
        conn.execute(
            sa.text(
                """
                INSERT OR IGNORE INTO role_permissions (id, role_id, permission_id)
                VALUES (lower(hex(randomblob(16))), :role_id, :permission_id)
                """
            ),
            {"role_id": role_id, "permission_id": permission_id},
        )


def _consolidate_global_duplicates_sqlite(conn) -> None:
    _normalize_corrupt_is_active(conn)

    duplicate_codes = conn.execute(
        sa.text(
            """
            SELECT code
            FROM roles
            WHERE organization_id IS NULL
            GROUP BY code
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    for entry in duplicate_codes:
        code = entry.code
        roles = conn.execute(
            sa.text(
                """
                SELECT id, is_active, created_at
                FROM roles
                WHERE organization_id IS NULL AND code = :code
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"code": code},
        ).fetchall()
        if len(roles) < 2:
            continue

        survivor = roles[0]
        survivor_id = str(survivor.id)
        merged_permissions = _permission_ids(conn, survivor_id)

        all_canonical_active = _is_canonical_active(survivor.is_active)
        for duplicate in roles[1:]:
            duplicate_id = str(duplicate.id)
            duplicate_permissions = _permission_ids(conn, duplicate_id)
            merged_permissions &= duplicate_permissions
            all_canonical_active = all_canonical_active and _is_canonical_active(duplicate.is_active)

            for permission_id in duplicate_permissions:
                conn.execute(
                    sa.text(
                        """
                        INSERT OR IGNORE INTO role_permissions (id, role_id, permission_id)
                        VALUES (lower(hex(randomblob(16))), :survivor_id, :permission_id)
                        """
                    ),
                    {"survivor_id": survivor_id, "permission_id": permission_id},
                )
            conn.execute(
                sa.text("DELETE FROM role_permissions WHERE role_id = :role_id"),
                {"role_id": duplicate_id},
            )
            conn.execute(
                sa.text("DELETE FROM roles WHERE id = :role_id"),
                {"role_id": duplicate_id},
            )

        _set_role_permissions(conn, survivor_id, merged_permissions)
        conn.execute(
            sa.text("UPDATE roles SET is_active = :active WHERE id = :role_id"),
            {"active": 1 if all_canonical_active else 0, "role_id": survivor_id},
        )


def _consolidate_global_duplicates_postgres(conn) -> None:
    _normalize_corrupt_is_active(conn)

    duplicate_codes = conn.execute(
        sa.text(
            """
            SELECT code
            FROM roles
            WHERE organization_id IS NULL
            GROUP BY code
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    for entry in duplicate_codes:
        code = entry.code
        roles = conn.execute(
            sa.text(
                """
                SELECT id, is_active, created_at
                FROM roles
                WHERE organization_id IS NULL AND code = :code
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"code": code},
        ).fetchall()
        if len(roles) < 2:
            continue

        survivor = roles[0]
        survivor_id = str(survivor.id)
        merged_permissions = _permission_ids(conn, survivor_id)
        all_canonical_active = _is_canonical_active(survivor.is_active)

        for duplicate in roles[1:]:
            duplicate_id = str(duplicate.id)
            duplicate_permissions = _permission_ids(conn, duplicate_id)
            merged_permissions &= duplicate_permissions
            all_canonical_active = all_canonical_active and _is_canonical_active(duplicate.is_active)

            conn.execute(
                sa.text(
                    """
                    INSERT INTO role_permissions (id, role_id, permission_id)
                    SELECT gen_random_uuid()::text, :survivor_id, permission_id
                    FROM role_permissions
                    WHERE role_id = :duplicate_id
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"survivor_id": survivor_id, "duplicate_id": duplicate_id},
            )
            conn.execute(
                sa.text("DELETE FROM role_permissions WHERE role_id = :role_id"),
                {"role_id": duplicate_id},
            )
            conn.execute(
                sa.text("DELETE FROM roles WHERE id = :role_id"),
                {"role_id": duplicate_id},
            )

        conn.execute(
            sa.text("DELETE FROM role_permissions WHERE role_id = :role_id"),
            {"role_id": survivor_id},
        )
        for permission_id in sorted(merged_permissions):
            conn.execute(
                sa.text(
                    """
                    INSERT INTO role_permissions (id, role_id, permission_id)
                    VALUES (gen_random_uuid()::text, :role_id, :permission_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"role_id": survivor_id, "permission_id": permission_id},
            )
        conn.execute(
            sa.text("UPDATE roles SET is_active = :active WHERE id = :role_id"),
            {"active": all_canonical_active, "role_id": survivor_id},
        )


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "sqlite":
        _consolidate_global_duplicates_sqlite(conn)
        conn.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_global_code "
                "ON roles (code) WHERE organization_id IS NULL"
            )
        )
    else:
        _consolidate_global_duplicates_postgres(conn)
        op.create_index(
            "uq_roles_global_code",
            "roles",
            ["code"],
            unique=True,
            postgresql_where=sa.text("organization_id IS NULL"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect == "sqlite":
        conn.execute(sa.text("DROP INDEX IF EXISTS uq_roles_global_code"))
    else:
        op.drop_index("uq_roles_global_code", table_name="roles")
