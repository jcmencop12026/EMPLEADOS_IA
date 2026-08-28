from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import Organization, User
from app.security import hash_password
from app.seed_orchestration import bootstrap_orchestration
from app.seed_salud import bootstrap_salud
from app.services.admin_service import _generate_temp_password
from app.tenant_scope import ORG_STATUS_ACTIVE, ORG_STATUS_INACTIVE

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{1,78}$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_slug(slug: str) -> str:
    return slug.strip().lower()


def validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Identificador no válido. Use letras minúsculas, números y guiones (2-79 caracteres).",
        )


def validate_timezone(tz: str) -> None:
    try:
        ZoneInfo(tz)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Zona horaria no válida") from exc


def generate_unique_slug(db: Session, base_name: str, *, exclude_id: str | None = None) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-")[:60] or "empresa"
    candidate = base
    suffix = 1
    while True:
        query = db.query(Organization).filter(Organization.slug == candidate)
        if exclude_id:
            query = query.filter(Organization.id != exclude_id)
        if not query.first():
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def list_organizations(db: Session) -> list[Organization]:
    return db.query(Organization).order_by(Organization.created_at.asc()).all()


def get_organization_by_id(db: Session, org_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    return org


def create_organization(
    db: Session,
    *,
    name: str,
    slug: str,
    timezone: str,
    admin_username: str,
    admin_password: str | None,
    admin_email: str | None,
    admin_full_name: str | None,
    actor_id: str,
) -> dict:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El nombre de la empresa es obligatorio")

    normalized_slug = normalize_slug(slug)
    validate_slug(normalized_slug)
    validate_timezone(timezone)

    if db.query(Organization).filter(Organization.slug == normalized_slug).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El identificador de empresa ya existe")
    if db.query(Organization).filter(Organization.name == clean_name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una empresa con ese nombre")
    if db.query(User).filter(User.username == admin_username.strip()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El nombre de usuario del administrador ya existe")

    org = Organization(
        name=clean_name,
        slug=normalized_slug,
        status=ORG_STATUS_ACTIVE,
        timezone=timezone,
    )
    db.add(org)
    db.flush()

    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)

    temp_password = admin_password or _generate_temp_password()
    admin_user = User(
        organization_id=org.id,
        username=admin_username.strip(),
        password_hash=hash_password(temp_password),
        email=admin_email.strip() if admin_email else None,
        full_name=admin_full_name.strip() if admin_full_name else None,
        role="admin",
        status="ACTIVE",
        is_active=True,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(org)
    db.refresh(admin_user)

    write_audit(
        db,
        action="platform.organization.created",
        organization_id=org.id,
        user_id=actor_id,
        detail=json.dumps(
            {
                "organization_id": org.id,
                "slug": org.slug,
                "admin_username": admin_user.username,
            },
            ensure_ascii=False,
        ),
    )

    return {
        "organization": org,
        "admin_user": admin_user,
        "temporary_password": None if admin_password else temp_password,
    }


def set_organization_status(
    db: Session,
    *,
    org: Organization,
    status_value: str,
    actor_id: str,
) -> Organization:
    if status_value not in {ORG_STATUS_ACTIVE, ORG_STATUS_INACTIVE}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Estado no válido")
    org.status = status_value
    org.updated_at = _utcnow()
    db.commit()
    db.refresh(org)
    write_audit(
        db,
        action="platform.organization.status_changed",
        organization_id=org.id,
        user_id=actor_id,
        detail=json.dumps({"status": status_value, "slug": org.slug}, ensure_ascii=False),
    )
    return org
