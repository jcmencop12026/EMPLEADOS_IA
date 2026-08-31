#Requires -Version 5.1
<#
.SYNOPSIS
  Inspect admin user in CERT PostgreSQL via backend container (no secrets printed).
.DESCRIPTION
  Copies backend/scripts/inspect_admin_user.py into the container and runs it.
  Uses docker cp of a real Python file (avoids PowerShell encoding/quoting issues).
.PARAMETER HotfixRoot
  Path to hotfix worktree (default: auto from script location, e.g. D:\EMPLEADOS_IA_V1_HOTFIX)
.PARAMETER Username
  Username to inspect (default: admin)
.PARAMETER BackendContainer
  Backend container name (default: empleados_ia_cert-backend-1)
#>
param(
    [string]$HotfixRoot = "",
    [string]$Username = "admin",
    [string]$BackendContainer = "empleados_ia_cert-backend-1"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_V1CertCommon.ps1"

$docker = Get-V1CertDockerExe
$root = Resolve-V1CertHotfixRoot -HotfixRoot $HotfixRoot
$pyFile = Join-Path $root "backend\scripts\inspect_admin_user.py"

Assert-V1CertContainerRunning -Docker $docker -ContainerName $BackendContainer

Write-Host "=== Admin inspection (no secrets) ===" -ForegroundColor Cyan
Write-Host "HotfixRoot: $root"
Write-Host "Container:  $BackendContainer"
Write-Host "Username:   $Username"

$code = Invoke-V1CertCopiedPython -Docker $docker -ContainerName $BackendContainer -LocalPythonFile $pyFile -PythonArgs @($Username)
if ($code -ne 0) { exit $code }

Write-Host ""
Write-Host "=== Backend health ===" -ForegroundColor Cyan
& $docker exec -i $BackendContainer curl -fsS http://127.0.0.1:8000/health/ready
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "INSPECT: PASS" -ForegroundColor Green
