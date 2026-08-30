#Requires -Version 5.1
<#
.SYNOPSIS
  Restablece contraseña admin en el SHA certificado e8cb853 SIN requerir scripts nuevos en imagen.
  Usa módulos oficiales ya presentes en el contenedor backend.
  NO imprime ni guarda la contraseña.
#>
param(
    [string]$Username = "admin",
    [string]$BackendContainer = "empleados_ia_cert-backend-1"
)

$ErrorActionPreference = "Stop"
$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"

$py = @"
import getpass, sys
from app.database import SessionLocal
from app.models import User, Organization
from app.security import hash_password
from app.audit import write_audit

username = sys.argv[1] if len(sys.argv) > 1 else "admin"
pw1 = getpass.getpass("Nueva contraseña: ")
pw2 = getpass.getpass("Confirmar contraseña: ")
if pw1 != pw2:
    print("ERROR: no coinciden", file=sys.stderr)
    sys.exit(2)
if len(pw1) < 8:
    print("ERROR: mínimo 8 caracteres", file=sys.stderr)
    sys.exit(2)

db = SessionLocal()
user = db.query(User).filter(User.username == username).first()
org = db.query(Organization).first()
if not user:
    if not org:
        print("ERROR: sin organización", file=sys.stderr)
        sys.exit(1)
    user = User(organization_id=org.id, username=username, password_hash=hash_password(pw1), role="superadmin", status="ACTIVE", is_active=True)
    db.add(user)
    action = "bootstrap.admin_created"
else:
    user.password_hash = hash_password(pw1)
    user.is_active = True
    user.status = "ACTIVE"
    if user.role == "admin":
        user.role = "superadmin"
    action = "auth.password_reset"
db.commit()
write_audit(db, action=action, organization_id=user.organization_id, user_id=user.id, detail=f"Recuperación segura {username}")
db.commit()
print("OK: acceso restablecido")
print(f"USUARIO: {username}")
print(f"ROL: {user.role}")
"@

Write-Host "Restablecimiento seguro (SHA certificado, sin modificar imagen)..." -ForegroundColor Cyan
& $docker exec -it $BackendContainer python -c $py $Username
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
