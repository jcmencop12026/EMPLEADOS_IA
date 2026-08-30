#Requires -Version 5.1
<#
.SYNOPSIS
  Restablece contraseña admin de forma segura (prompt oculto dentro del contenedor).
  NO imprime la contraseña. NO la guarda en archivos.
.PARAMETER Username
  Usuario a restablecer (default: admin)
.PARAMETER BackendContainer
  Nombre del contenedor backend (default: empleados_ia_cert-backend-1)
#>
param(
    [string]$Username = "admin",
    [string]$BackendContainer = "empleados_ia_cert-backend-1"
)

$ErrorActionPreference = "Stop"
$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"

if (-not (Test-Path $docker)) {
    Write-Error "Docker no encontrado en: $docker"
}

$running = & $docker inspect -f "{{.State.Running}}" $BackendContainer 2>$null
if ($running -ne "true") {
    Write-Error "Contenedor $BackendContainer no está en ejecución."
}

Write-Host "Se solicitará la NUEVA contraseña dentro del contenedor (entrada oculta)." -ForegroundColor Yellow
Write-Host "No se mostrará ni guardará en este script." -ForegroundColor Yellow

& $docker exec -it $BackendContainer python -m scripts.reset_admin_password $Username
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Verificación post-reset (sin contraseña) ===" -ForegroundColor Cyan
& $docker exec -i $BackendContainer python -m scripts.inspect_admin_user $Username

Write-Host "`nPruebe login en: http://localhost:5180/login (o puerto FRONTEND configurado)" -ForegroundColor Green
Write-Host "USUARIO: $Username" -ForegroundColor Green
Write-Host "CONTRASEÑA: la nueva que estableció localmente (no se muestra aquí)." -ForegroundColor Green
