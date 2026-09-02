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

Write-Host ""
Write-Host "=== validate_ps_parse.ps1 (production shell) ==="
Invoke-EiaaxPowerShellParserValidation -ScriptsDir $PSScriptRoot

$tests = @(
    "test_parser_aggregate.ps1",
    "test_ps_semantics.ps1",
    "test_git_sync.ps1",
    "test_python_discovery.ps1",
    "test_python_resolution_scenario.ps1",
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
    $testExitCode = Invoke-EiaaxPowerShellFile -FilePath $testPath
    if ($testExitCode -ne 0) {
        Exit-EiaaxFailure -Message ("Development test failed: " + $testName + " (exit " + $testExitCode + ")")
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "EIAAX -- SUITE DESARROLLO WINDOWS COMPLETADA"
Write-Host "============================================================"
exit 0
