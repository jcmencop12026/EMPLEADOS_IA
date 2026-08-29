from fastapi import HTTPException, status

from app.models import Organization

ORG_STATUS_ACTIVE = "ACTIVE"
ORG_STATUS_INACTIVE = "INACTIVE"


def ensure_organization_active(org: Organization | None) -> None:
    if org is None or org.status != ORG_STATUS_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La empresa está inactiva o no está disponible.",
        )
