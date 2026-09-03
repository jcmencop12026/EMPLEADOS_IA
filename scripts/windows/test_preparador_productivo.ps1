#Requires -Version 5.1
<#
.SYNOPSIS
    Regression: production preparer must not invoke development autotest suites.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$preparer = Join-Path $PSScriptRoot "preparar_demo_eiaax.ps1"
$validator = Join-Path $PSScriptRoot "validar_arranque_windows.ps1"
$preparerText = Get-Content -LiteralPath $preparer -Raw
$validatorText = Get-Content -LiteralPath $validator -Raw

$forbiddenInPreparer = @(
    "test_python_discovery.ps1",
    "test_ps_semantics.ps1",
    "test_ps_alembic.ps1",
    "Python discovery self-test failed",
    "PowerShell semantics self-test failed",
    "PowerShell Alembic collection self-test failed"
)

$failed = 0
foreach ($pattern in $forbiddenInPreparer) {
    if ($preparerText -match [regex]::Escape($pattern)) {
        Write-Host ("FAIL: preparar_demo_eiaax.ps1 references dev autotest: " + $pattern)
        $failed++
    }
}

if ($preparerText -notmatch "Confirm-EiaaxProductionPrerequisites") {
    Write-Host "FAIL: preparar_demo_eiaax.ps1 missing Confirm-EiaaxProductionPrerequisites"
    $failed++
}

if ($validatorText -notmatch "preparar_demo_eiaax.ps1") {
    Write-Host "FAIL: validar_arranque_windows.ps1 must delegate to preparar_demo_eiaax.ps1"
    $failed++
}

if ($failed -gt 0) {
    Write-Host ("PREPARADOR PRODUCTIVO REGRESSION: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "PREPARADOR PRODUCTIVO REGRESSION: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
