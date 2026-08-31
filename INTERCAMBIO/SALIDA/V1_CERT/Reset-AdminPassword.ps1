#Requires -Version 5.1
<#
.SYNOPSIS
  Securely reset admin password (hidden prompt inside container).
.DESCRIPTION
  Copies backend/scripts/reset_admin_password.py into the container and runs it with -it.
  Password is entered via getpass inside the container (not visible in process args).
  Uses docker cp of a real Python file (no inline shell Python).
.PARAMETER HotfixRoot
  Path to hotfix worktree (default: auto)
.PARAMETER Username
  Username to reset (default: admin)
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
$pyFile = Join-Path $root "backend\scripts\reset_admin_password.py"

Assert-V1CertContainerRunning -Docker $docker -ContainerName $BackendContainer

Write-Host "=== Secure password reset ===" -ForegroundColor Cyan
Write-Host "You will be prompted for a NEW password inside the container (hidden input)."
Write-Host "Password is NOT stored in this script, Git, or logs."
Write-Host "HotfixRoot: $root"
Write-Host "Container:  $BackendContainer"
Write-Host "Username:   $Username"
Write-Host ""

$code = Invoke-V1CertCopiedPython -Docker $docker -ContainerName $BackendContainer -LocalPythonFile $pyFile -PythonArgs @($Username) -Interactive
if ($code -ne 0) {
    Write-Host "RESET: FAIL (exit $code)" -ForegroundColor Red
    exit $code
}

Write-Host ""
Write-Host "=== Post-reset verification ===" -ForegroundColor Cyan
$inspectFile = Join-Path $root "backend\scripts\inspect_admin_user.py"
$vcode = Invoke-V1CertCopiedPython -Docker $docker -ContainerName $BackendContainer -LocalPythonFile $inspectFile -PythonArgs @($Username)
if ($vcode -ne 0) { exit $vcode }

Write-Host ""
Write-Host "RESET: PASS" -ForegroundColor Green
Write-Host "USER: $Username"
Write-Host "PASSWORD: the new password you entered locally (not shown here)."
