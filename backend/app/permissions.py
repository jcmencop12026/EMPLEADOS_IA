from fastapi import HTTPException, status

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

CAPABILITY_PERMISSIONS = {
    "capability.view",
    "capability.manage",
}

TOOL_PERMISSIONS = {
    "tool.view",
    "tool.manage",
}

KNOWLEDGE_PERMISSIONS = {
    "knowledge.view",
    "knowledge.manage",
}

TEST_LAB_PERMISSIONS = {
    "test_lab.view",
    "test_lab.run",
}

ALL_PERMISSIONS = (
    EMPLOYEE_PERMISSIONS
    | CAPABILITY_PERMISSIONS
    | TOOL_PERMISSIONS
    | KNOWLEDGE_PERMISSIONS
    | TEST_LAB_PERMISSIONS
)

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": ALL_PERMISSIONS,
    "operator": {
        "employee.view",
        "employee.create",
        "employee.edit",
        "employee.test",
        "capability.view",
        "tool.view",
        "knowledge.view",
        "test_lab.view",
        "test_lab.run",
    },
    "viewer": {
        "employee.view",
        "capability.view",
        "tool.view",
        "knowledge.view",
        "test_lab.view",
    },
}


def user_permissions(user: User) -> set[str]:
    return ROLE_PERMISSIONS.get(user.role, {"employee.view", "capability.view", "tool.view", "knowledge.view"})


def check_permission(user: User, permission: str) -> None:
    if permission not in user_permissions(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permiso denegado: {permission}",
        )
