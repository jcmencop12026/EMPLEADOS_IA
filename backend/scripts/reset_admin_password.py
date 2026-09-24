"""Restablecimiento seguro de contrasena administrativa (prompt oculto, hash oficial)."""

from __future__ import annotations

import getpass
import sys

from app.audit import write_audit
from app.database import SessionLocal
from app.models import Organization, User
from app.security import hash_password


def _read_password() -> str:
    pw1 = getpass.getpass("Nueva contrasena: ")
    pw2 = getpass.getpass("Confirmar contrasena: ")
    if pw1 != pw2:
        print("ERROR: las contrasenas no coinciden.", file=sys.stderr)
        raise SystemExit(2)
    if len(pw1) < 8:
        print("ERROR: la contrasena debe tener al menos 8 caracteres.", file=sys.stderr)
        raise SystemExit(2)
    return pw1


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    new_password = _read_password()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        org = db.query(Organization).first()
        if not user:
            if not org:
                print("ERROR: no hay organizacion en la base de datos.", file=sys.stderr)
                return 1
            user = User(
                organization_id=org.id,
                username=username,
                password_hash=hash_password(new_password),
                role="superadmin",
                status="ACTIVE",
                is_active=True,
            )
            db.add(user)
            action = "bootstrap.admin_created"
            detail = f"Usuario {username} creado por script de recuperacion"
        else:
            user.password_hash = hash_password(new_password)
            user.is_active = True
            user.status = "ACTIVE"
            if user.role == "admin":
                user.role = "superadmin"
            action = "auth.password_reset"
            detail = f"Contrasena restablecida para {username}"
        db.commit()
        write_audit(
            db,
            action=action,
            organization_id=user.organization_id,
            user_id=user.id,
            detail=detail,
        )
        db.commit()
        print("OK: acceso administrativo restablecido.")
        print(f"USUARIO: {username}")
        print(f"ROL: {user.role}")
        print(f"ACTIVO: {'SI' if user.is_active else 'NO'}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
