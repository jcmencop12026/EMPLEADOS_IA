"""Borrado seguro de la organización demo — solo DEMO EMPLEADOS IA."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.database import Base
from app.demo_integral.constants import DEMO_ORG_NAME, DEMO_ORG_SLUG
from app.models import Organization, User


class DemoPurgeAbortError(RuntimeError):
    """Se aborta el borrado para proteger organizaciones no demo."""


def _resolve_demo_org(db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.slug == DEMO_ORG_SLUG).first()
    if not org:
        raise DemoPurgeAbortError("Organización demo no encontrada — nada que borrar")
    if org.slug != DEMO_ORG_SLUG:
        raise DemoPurgeAbortError("ABORT: slug no coincide con demo autorizada")
    if org.name != DEMO_ORG_NAME:
        raise DemoPurgeAbortError(
            f"ABORT: el slug {DEMO_ORG_SLUG} no pertenece a '{DEMO_ORG_NAME}' (es '{org.name}')"
        )
    return org


def purge_demo_integral(db: Session) -> dict[str, Any]:
    """Elimina únicamente la organización DEMO EMPLEADOS IA y sus datos."""
    org = _resolve_demo_org(db)
    org_id = org.id

    other_users = (
        db.query(User)
        .filter(User.organization_id == org_id)
        .count()
    )
    if other_users == 0 and org.name != DEMO_ORG_NAME:
        raise DemoPurgeAbortError("ABORT: validación de nombre falló")

    deleted_counts: dict[str, int] = {}
    for table in reversed(Base.metadata.sorted_tables):
        if "organization_id" not in table.c:
            continue
        result = db.execute(table.delete().where(table.c.organization_id == org_id))
        deleted_counts[table.name] = result.rowcount or 0

    # Usuarios y roles ligados a la org
    user_count = db.query(User).filter(User.organization_id == org_id).delete()
    deleted_counts["users"] = user_count

    from app.models import Role

    role_count = db.query(Role).filter(Role.organization_id == org_id).delete()
    deleted_counts["roles"] = role_count

    db.delete(org)
    db.commit()

    return {
        "status": "purged",
        "organization_slug": DEMO_ORG_SLUG,
        "organization_name": DEMO_ORG_NAME,
        "deleted_tables": deleted_counts,
    }
