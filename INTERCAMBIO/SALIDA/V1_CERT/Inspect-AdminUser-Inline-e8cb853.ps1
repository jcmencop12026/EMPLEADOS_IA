#Requires -Version 5.1
param(
    [string]$Username = "admin",
    [string]$BackendContainer = "empleados_ia_cert-backend-1"
)

$ErrorActionPreference = "Stop"
$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"

$py = @"
from app.database import SessionLocal
from app.models import User, Organization
db = SessionLocal()
u = db.query(User).filter(User.username == '$Username').first()
if not u:
    print('EXISTE: NO')
else:
    o = db.query(Organization).filter(Organization.id == u.organization_id).first()
    print(f'USUARIO: {u.username}')
    print(f'EXISTE: SI')
    print(f'ACTIVO: {"SI" if u.is_active else "NO"}')
    print(f'ESTADO: {u.status}')
    print(f'ROL: {u.role}')
    print(f'SUPERADMIN: {"SI" if u.role.lower()=="superadmin" else "NO"}')
    print(f'ORG_ESTADO: {o.status if o else "—"}')
"@

& $docker exec -i $BackendContainer python -c $py
