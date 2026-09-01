#Requires -Version 5.1
<#
.SYNOPSIS
    Optional development test suite for EIAAX Windows scripts.
    NOT invoked by production preparer or validar_arranque_windows.ps1.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$tests = @(
    "test_ps_semantics.ps1",
    "test_python_discovery.ps1",
    "test_convergence_atomic.ps1",
    "test_ps_alembic.ps1",
    "test_preparador_productivo.ps1"
)

foreach ($testName in $tests) {
    $testPath = Join-Path $PSScriptRoot $testName
    if (-not (Test-Path -LiteralPath $testPath)) {
        Exit-EiaaxFailure -Message ("Missing development test: " + $testName)
    }

    Write-Host ""
    Write-Host ("=== " + $testName + " ===")
    Invoke-EiaaxPowerShellFile -FilePath $testPath
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message ("Development test failed: " + $testName)
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "EIAAX -- SUITE DESARROLLO WINDOWS COMPLETADA"
Write-Host "============================================================"
exit 0
