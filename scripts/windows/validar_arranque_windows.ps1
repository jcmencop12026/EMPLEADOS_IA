#Requires -Version 5.1
<#
.SYNOPSIS
    Single entry point for the user to re-validate Windows startup scripts.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$validateScript = Join-Path $PSScriptRoot "validate_ps_parse.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $validateScript
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "Parser validation passed. Next step after git pull:"
Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\windows\preparar_demo_eiaax.ps1"
exit 0
