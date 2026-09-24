"""Inspeccion segura de usuario administrativo (sin exponer hash ni secretos)."""

from __future__ import annotations

import sys

from app.database import SessionLocal
from app.models import Organization, User


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"USUARIO: {username}")
            print("EXISTE: NO")
            return 1
        org = db.query(Organization).filter(Organization.id == user.organization_id).first()
        print(f"USUARIO: {user.username}")
        print(f"EXISTE: SI")
        print(f"ACTIVO: {'SI' if user.is_active else 'NO'}")
        print(f"ESTADO: {user.status}")
        print(f"ROL: {user.role}")
        print(f"EMAIL: {user.email or '-'}")
        print(f"ORGANIZACION: {org.name if org else '-'}")
        print(f"ORG_ESTADO: {org.status if org else '-'}")
        print(f"SUPERADMIN: {'SI' if user.role.lower() == 'superadmin' else 'NO'}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
