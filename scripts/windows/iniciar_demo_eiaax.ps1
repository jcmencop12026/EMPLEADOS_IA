#Requires -Version 5.1
<#
.SYNOPSIS
    Inicia backend y frontend de la demo EIAAX.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendScript = Join-Path $PSScriptRoot "iniciar_backend_demo.ps1"
$frontendScript = Join-Path $PSScriptRoot "iniciar_frontend_demo.ps1"

& $backendScript
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Start-Sleep -Seconds 2
& $frontendScript
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "EIAAX demo en ejecución."
Write-Host "URL: http://127.0.0.1:5180"
Write-Host "Login: org_a_admin / DemoA2026!"
Write-Host "Detener: scripts\windows\detener_demo_eiaax.ps1"
