from fastapi import Depends, HTTPException, status

from app.models import User

EMPLOYEE_PERMISSIONS = {
    "employee.view",
    "employee.create",
    "employee.edit",
    "employee.test",
    "employee.certify",
    "employee.publish",
    "employee.activate",
    "employee.admin",
}

FINOPS_PERMISSIONS = {
    "finops.view",
    "finops.manage",
    "finops.budget",
    "finops.rates",
}

ALL_PERMISSIONS = EMPLOYEE_PERMISSIONS | FINOPS_PERMISSIONS

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": ALL_PERMISSIONS,
    "operator": {
        "employee.view",
        "employee.create",
        "employee.edit",
        "employee.test",
        "finops.view",
        "finops.manage",
        "finops.budget",
    },
    "viewer": {"employee.view", "finops.view"},
}


def user_permissions(user: User) -> set[str]:
    return ROLE_PERMISSIONS.get(user.role, {"employee.view"})


def require_permission(permission: str):
    def checker(user: User = Depends(lambda: None)) -> User:
        from app.deps import get_current_user
        raise NotImplementedError

    return checker


def check_permission(user: User, permission: str) -> None:
    if permission not in user_permissions(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permiso denegado: {permission}",
        )
