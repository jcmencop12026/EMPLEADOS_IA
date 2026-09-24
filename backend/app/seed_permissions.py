"""Bootstrap de permisos y roles del sistema — CURSOR-840."""
from sqlalchemy.orm import Session

from app.models import Permission, Role, RolePermission
from app.permissions import ALL_PERMISSIONS, ROLE_PERMISSIONS_FALLBACK, SYSTEM_ROLE_CODES


ROLE_LABELS = {
    "admin": "Administrador",
    "operator": "Operador",
    "viewer": "Consulta",
    "superadmin": "Superadministrador de plataforma",
    "external_prospect": "Prospecto externo",
}


def bootstrap_permissions(db: Session) -> None:
    perm_by_code: dict[str, Permission] = {}
    for code, (module, description) in ALL_PERMISSIONS.items():
        row = db.query(Permission).filter(Permission.code == code).first()
        if not row:
            row = Permission(code=code, module=module, description=description)
            db.add(row)
            db.flush()
        perm_by_code[code] = row

    for code in SYSTEM_ROLE_CODES:
        role = (
            db.query(Role)
            .filter(Role.code == code, Role.organization_id.is_(None), Role.is_system.is_(True))
            .first()
        )
        if not role:
            role = Role(
                code=code,
                name=ROLE_LABELS.get(code, code.title()),
                description=f"Rol de sistema: {code}",
                is_system=True,
                is_active=True,
                organization_id=None,
            )
            db.add(role)
            db.flush()
        else:
            role.is_active = True

        desired = ROLE_PERMISSIONS_FALLBACK.get(code, set())
        existing = {
            link.permission_id
            for link in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()
        }
        for perm_code in desired:
            perm = perm_by_code.get(perm_code)
            if perm and perm.id not in existing:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()
