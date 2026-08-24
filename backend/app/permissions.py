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

NOTIFICATION_PERMISSIONS = {
    "notification.view",
    "notification.manage",
    "notification.acknowledge",
    "alert_rule.view",
    "alert_rule.manage",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": EMPLOYEE_PERMISSIONS | NOTIFICATION_PERMISSIONS,
    "operator": {
        "employee.view",
        "employee.create",
        "employee.edit",
        "employee.test",
        "notification.view",
        "notification.acknowledge",
        "alert_rule.view",
    },
    "viewer": {"employee.view", "notification.view"},
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
