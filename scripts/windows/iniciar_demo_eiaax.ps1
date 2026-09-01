#Requires -Version 5.1
<#
.SYNOPSIS
    Start backend and frontend for the EIAAX demo.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendScript = Join-Path $PSScriptRoot "iniciar_backend_demo.ps1"
$frontendScript = Join-Path $PSScriptRoot "iniciar_frontend_demo.ps1"

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $backendScript
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Start-Sleep -Seconds 2

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $frontendScript
if ($LASTEXITCODE -ne 0) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "detener_demo_eiaax.ps1") | Out-Null
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "EIAAX demo is running."
Write-Host "URL: http://127.0.0.1:5180"
Write-Host "Demo user: org_a_admin (password in backend\scripts\credentials.example)"
Write-Host "Stop: scripts\windows\detener_demo_eiaax.ps1"
exit 0
