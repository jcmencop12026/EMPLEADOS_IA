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

SALUD_PERMISSIONS = {
    "salud.cargar_datos",
    "salud.ejecutar_analisis",
    "salud.consultar_diagnostico",
    "salud.aceptar_recomendaciones",
    "salud.administrar_experiencia",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": EMPLOYEE_PERMISSIONS | SALUD_PERMISSIONS,
    "operator": {
        "employee.view",
        "employee.create",
        "employee.edit",
        "employee.test",
        "salud.cargar_datos",
        "salud.ejecutar_analisis",
        "salud.consultar_diagnostico",
        "salud.aceptar_recomendaciones",
    },
    "viewer": {"employee.view", "salud.consultar_diagnostico"},
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
