#Requires -Version 5.1
<#
.SYNOPSIS
    Single entry point: validate parser and prepare the EIAAX Windows demo.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$prepareScript = Join-Path $PSScriptRoot "preparar_demo_eiaax.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $prepareScript
exit $LASTEXITCODE
