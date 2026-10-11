from sqlalchemy.orm import Session

from app.audit import write_audit
from app.config import DEFAULT_BOOTSTRAP_PASSWORD, settings
from app.models import Organization, User
from app.security import hash_password
from app.seed_orchestration import bootstrap_orchestration
from app.seed_permissions import bootstrap_permissions
from app.seed_salud import bootstrap_salud


def _bootstrap_password_allowed() -> bool:
    if settings.allow_insecure_dev_bootstrap:
        return True
    return settings.bootstrap_admin_password != DEFAULT_BOOTSTRAP_PASSWORD


def _ensure_user(
    db: Session,
    *,
    org_id: str,
    username: str,
    password: str,
    role: str,
    created_by_id: str | None,
    audit_action: str,
) -> User | None:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return existing
    row = User(
        organization_id=org_id,
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action=audit_action,
        organization_id=org_id,
        user_id=created_by_id or row.id,
        detail=f"Usuario {row.username} rol={role}",
    )
    return row


def bootstrap(db: Session) -> None:
    org = db.query(Organization).first()
    if not org:
        org = Organization(name=settings.bootstrap_org_name)
        db.add(org)
        db.flush()

    admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
    if not admin and _bootstrap_password_allowed():
        admin = User(
            organization_id=org.id,
            username=settings.bootstrap_admin_username,
            password_hash=hash_password(settings.bootstrap_admin_password),
            role="admin",
        )
        db.add(admin)
        db.flush()
        write_audit(
            db,
            action="bootstrap.admin_created",
            organization_id=org.id,
            user_id=admin.id,
            detail=f"Usuario {admin.username} y organización {org.name}",
        )
    bootstrap_orchestration(db, org.id)
    bootstrap_permissions(db)
    bootstrap_salud(db, org.id)

    creator_id = admin.id if admin else None
    if settings.bootstrap_owner_username and settings.bootstrap_owner_password:
        owner_name = settings.bootstrap_owner_username.strip()
        if owner_name and (
            not admin or owner_name.lower() != settings.bootstrap_admin_username.lower()
        ):
            _ensure_user(
                db,
                org_id=org.id,
                username=owner_name,
                password=settings.bootstrap_owner_password,
                role="admin",
                created_by_id=creator_id,
                audit_action="bootstrap.owner_created",
            )
    if settings.bootstrap_auditor_username and settings.bootstrap_auditor_password:
        auditor_name = settings.bootstrap_auditor_username.strip()
        if auditor_name:
            _ensure_user(
                db,
                org_id=org.id,
                username=auditor_name,
                password=settings.bootstrap_auditor_password,
                role="auditor",
                created_by_id=creator_id,
                audit_action="bootstrap.auditor_created",
            )

    db.commit()
