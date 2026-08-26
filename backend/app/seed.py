from sqlalchemy.orm import Session

from app.audit import write_audit
from app.config import settings
from app.models import Organization, User
from app.security import hash_password
from app.seed_orchestration import bootstrap_orchestration
from app.seed_permissions import bootstrap_permissions
from app.seed_salud import bootstrap_salud


def bootstrap(db: Session) -> None:
    org = db.query(Organization).first()
    if not org:
        org = Organization(name=settings.bootstrap_org_name)
        db.add(org)
        db.flush()

    admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
    if not admin:
        admin = User(
            organization_id=org.id,
            username=settings.bootstrap_admin_username,
            password_hash=hash_password(settings.bootstrap_admin_password),
            role="admin",
        )
        db.add(admin)
        db.commit()
        write_audit(
            db,
            action="bootstrap.admin_created",
            organization_id=org.id,
            user_id=admin.id,
            detail=f"Usuario {admin.username} y organización {org.name}",
        )
    else:
        db.commit()

    bootstrap_orchestration(db, org.id)
    bootstrap_permissions(db)
    bootstrap_salud(db, org.id)
