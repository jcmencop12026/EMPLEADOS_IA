from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Role, User
from app.permissions import require_permission
from app.schemas_admin import (
    OrgConfigOut,
    OrgConfigUpdate,
    OrganizationAdminOut,
    OrganizationUpdate,
    PasswordResetRequest,
    PasswordResetResponse,
    RoleCreate,
    RoleOut,
    RolePermissionsUpdate,
    RoleUpdate,
    SecuritySummaryOut,
    UserCreate,
    UserOut,
    UserStatusUpdate,
    UserUpdate,
)
from app.services import admin_service as svc

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.user.view")),
):
    return svc.list_users(db, user.organization_id, q=q, status_filter=status)


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.user.create")),
):
    return svc.create_user(
        db,
        org_id=user.organization_id,
        actor_id=user.id,
        username=body.username,
        password=body.password,
        role=body.role,
        email=str(body.email) if body.email else None,
        full_name=body.full_name,
        actor=user,
    )


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.user.view")),
):
    return svc.get_user_in_org(db, user_id, user.organization_id)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.user.edit")),
):
    target = svc.get_user_in_org(db, user_id, user.organization_id)
    return svc.update_user(
        db,
        user=target,
        actor_id=user.id,
        email=str(body.email) if body.email is not None else None,
        full_name=body.full_name,
        role=body.role,
        actor=user,
    )


@router.post("/users/{user_id}/status", response_model=UserOut)
def set_user_status(
    user_id: str,
    body: UserStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.user.activate")),
):
    perm = "admin.user.deactivate" if body.status != "ACTIVE" else "admin.user.activate"
    from app.permissions import check_permission

    check_permission(user, perm, db)
    target = svc.get_user_in_org(db, user_id, user.organization_id)
    return svc.set_user_status(db, user=target, actor_id=user.id, status_value=body.status)


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_password(
    user_id: str,
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.user.reset_password")),
):
    target = svc.get_user_in_org(db, user_id, user.organization_id)
    temp = svc.reset_user_password(db, user=target, actor_id=user.id, new_password=body.new_password)
    return PasswordResetResponse(temporary_password=temp)


@router.get("/roles/permission-matrix")
def permission_matrix(db: Session = Depends(get_db), user: User = Depends(require_permission("admin.role.view"))):
    return svc.permission_matrix(db, user.organization_id)


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), user: User = Depends(require_permission("admin.role.view"))):
    return svc.list_roles(db, user.organization_id)


@router.post("/roles", response_model=RoleOut, status_code=201)
def create_role(
    body: RoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.role.create")),
):
    return svc.create_role(
        db,
        org_id=user.organization_id,
        actor_id=user.id,
        code=body.code,
        name=body.name,
        description=body.description,
    )


@router.put("/roles/{role_id}", response_model=RoleOut)
def update_role(
    role_id: str,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.role.edit")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    return svc.update_role(
        db,
        role=role,
        org_id=user.organization_id,
        actor_id=user.id,
        name=body.name,
        description=body.description,
        is_active=body.is_active,
    )


@router.put("/roles/{role_id}/permissions", response_model=RoleOut)
def update_role_permissions(
    role_id: str,
    body: RolePermissionsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.role.assign_permissions")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    return svc.assign_role_permissions(
        db,
        role=role,
        org_id=user.organization_id,
        actor_id=user.id,
        permission_codes=body.permission_codes,
        actor=user,
    )


@router.get("/organization", response_model=OrganizationAdminOut)
def get_organization(db: Session = Depends(get_db), user: User = Depends(require_permission("admin.organization.view"))):
    return svc.get_organization(db, user.organization_id)


@router.put("/organization", response_model=OrganizationAdminOut)
def update_organization(
    body: OrganizationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.organization.edit")),
):
    org = svc.get_organization(db, user.organization_id)
    return svc.update_organization(db, org=org, actor_id=user.id, name=body.name, timezone=body.timezone)


@router.get("/config", response_model=OrgConfigOut)
def get_config(db: Session = Depends(get_db), user: User = Depends(require_permission("admin.config.view"))):
    org = svc.get_organization(db, user.organization_id)
    return svc.get_org_config(org)


@router.put("/config", response_model=OrgConfigOut)
def update_config(
    body: OrgConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("admin.config.edit")),
):
    org = svc.get_organization(db, user.organization_id)
    return svc.update_org_config(db, org=org, actor_id=user.id, config=body.model_dump(exclude_unset=True))


@router.get("/security", response_model=SecuritySummaryOut)
def security_summary(db: Session = Depends(get_db), user: User = Depends(require_permission("admin.security.view"))):
    return svc.security_summary(db, user.organization_id)
