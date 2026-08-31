#Requires -Version 5.1
<#
.SYNOPSIS
  PASO 1: Inspect admin, reset password securely, validate login API.
.PARAMETER HotfixRoot
  e.g. D:\EMPLEADOS_IA_V1_HOTFIX
.PARAMETER BackendUrl
  e.g. http://localhost:18010
#>
param(
    [string]$HotfixRoot = "",
    [string]$BackendUrl = "http://localhost:18010",
    [string]$Username = "admin",
    [string]$BackendContainer = "empleados_ia_cert-backend-1"
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot

Write-Host "========== PASO 1: RECUPERAR / VALIDAR ADMIN ==========" -ForegroundColor Cyan

& "$here\Inspect-AdminUser.ps1" -HotfixRoot $HotfixRoot -Username $Username -BackendContainer $BackendContainer
if ($LASTEXITCODE -ne 0) {
    Write-Host "STOP: inspect failed. Check container $BackendContainer is running." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "If admin is missing or inactive, run reset now." -ForegroundColor Yellow
$answer = Read-Host "Reset password now? (S/N)"
if ($answer -match '^[Ss]') {
    & "$here\Reset-AdminPassword.ps1" -HotfixRoot $HotfixRoot -Username $Username -BackendContainer $BackendContainer
    if ($LASTEXITCODE -ne 0) {
        Write-Host "STOP: reset failed." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
& "$here\Test-LoginApi.ps1" -BackendUrl $BackendUrl -Username $Username
if ($LASTEXITCODE -ne 0) {
    Write-Host "STOP: login test failed. Re-run reset if needed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "PASO 1: PASS" -ForegroundColor Green
Write-Host "Expected: admin active, role superadmin, login API OK."
Write-Host "If login UI still fails, run PASO 2 (frontend hotfix)."
