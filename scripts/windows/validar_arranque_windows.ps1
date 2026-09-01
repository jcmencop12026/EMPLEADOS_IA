#Requires -Version 5.1
<#
.SYNOPSIS
    Single entry point: validate parser and prepare the EIAAX Windows demo.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$prepareScript = Join-Path $PSScriptRoot "preparar_demo_eiaax.ps1"
Invoke-EiaaxPowerShellFile -FilePath $prepareScript
exit $LASTEXITCODE
