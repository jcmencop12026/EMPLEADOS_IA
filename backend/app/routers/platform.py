from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, User
from app.permissions import require_permission
from app.schemas_platform import (
    PlatformOrganizationCreate,
    PlatformOrganizationCreateResponse,
    PlatformOrganizationOut,
    PlatformOrganizationStatusUpdate,
)
from app.services import tenant_service as svc

router = APIRouter(prefix="/api/platform", tags=["platform"])


def _org_out(db: Session, org: Organization) -> PlatformOrganizationOut:
    users_count = db.query(func.count(User.id)).filter(User.organization_id == org.id).scalar() or 0
    return PlatformOrganizationOut(
        id=org.id,
        name=org.name,
        slug=org.slug,
        status=org.status,
        timezone=org.timezone,
        created_at=org.created_at,
        updated_at=org.updated_at,
        users_count=users_count,
    )


@router.get("/organizations", response_model=list[PlatformOrganizationOut])
def list_organizations(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("platform.organization.view")),
):
    return [_org_out(db, org) for org in svc.list_organizations(db)]


@router.post("/organizations", response_model=PlatformOrganizationCreateResponse, status_code=201)
def create_organization(
    body: PlatformOrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("platform.organization.create")),
):
    result = svc.create_organization(
        db,
        name=body.name,
        slug=body.slug,
        timezone=body.timezone,
        admin_username=body.admin_username,
        admin_password=body.admin_password,
        admin_email=body.admin_email,
        admin_full_name=body.admin_full_name,
        actor_id=user.id,
    )
    org = result["organization"]
    admin = result["admin_user"]
    return PlatformOrganizationCreateResponse(
        organization=_org_out(db, org),
        admin_user_id=admin.id,
        admin_username=admin.username,
        temporary_password=result["temporary_password"],
    )


@router.get("/organizations/{org_id}", response_model=PlatformOrganizationOut)
def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("platform.organization.view")),
):
    org = svc.get_organization_by_id(db, org_id)
    return _org_out(db, org)


@router.post("/organizations/{org_id}/status", response_model=PlatformOrganizationOut)
def set_organization_status(
    org_id: str,
    body: PlatformOrganizationStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("platform.organization.manage")),
):
    org = svc.get_organization_by_id(db, org_id)
    updated = svc.set_organization_status(db, org=org, status_value=body.status, actor_id=user.id)
    return _org_out(db, updated)
