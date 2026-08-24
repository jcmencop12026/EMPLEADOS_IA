from fastapi import Depends, HTTPException, status

from app.deps import get_current_user
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

OPERATIONS_PERMISSIONS = {
    "operations.view",
    "operations.execute",
    "operations.approve",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": EMPLOYEE_PERMISSIONS | OPERATIONS_PERMISSIONS,
    "operator": {
        "employee.view",
        "employee.create",
        "employee.edit",
        "employee.test",
        "operations.view",
        "operations.execute",
        "operations.approve",
    },
    "viewer": {
        "employee.view",
        "operations.view",
    },
}


def user_permissions(user: User) -> set[str]:
    return ROLE_PERMISSIONS.get(user.role, {"employee.view"})


def check_permission(user: User, permission: str) -> None:
    if permission not in user_permissions(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permiso denegado: {permission}",
        )


def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        check_permission(user, permission)
        return user

    return checker
