#Requires -Version 5.1
<#
.SYNOPSIS
  Inspecciona usuario admin en PostgreSQL vía contenedor backend (sin exponer hash).
.PARAMETER Username
  Usuario a inspeccionar (default: admin)
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

Write-Host "=== Inspección usuario (sin secretos) ===" -ForegroundColor Cyan
& $docker exec -i $BackendContainer python -m scripts.inspect_admin_user $Username
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Health backend ===" -ForegroundColor Cyan
& $docker exec -i $BackendContainer curl -fsS http://127.0.0.1:8000/health/ready | Out-Host
