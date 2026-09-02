#Requires -Version 5.1
<#
.SYNOPSIS
    Regression tests for non-blocking service startup orchestration.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$helpers = Join-Path $PSScriptRoot "EiaaxDemo.TestHelpers.ps1"
. $helpers

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$failed = 0

function Assert-Test {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host ("TEST: " + $Name)
    try {
        & $Action
        Write-Host ("  PASS")
    }
    catch {
        $script:failed++
        Write-Host ("  FAIL: " + $_.Exception.Message)
    }
}

Assert-Test "iniciar_demo uses in-process script invocation for backend/frontend" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "iniciar_demo_eiaax.ps1") -Raw
    if ($content -notmatch "Invoke-EiaaxScriptInProcess") {
        throw "iniciar_demo_eiaax.ps1 must use Invoke-EiaaxScriptInProcess"
    }
    if ($content -match 'Invoke-EiaaxPowerShellFile -FilePath \$backendScript') {
        throw "backend must not use nested Invoke-EiaaxPowerShellFile"
    }
    if ($content -notmatch "\[4/7\.3\] Iniciando frontend") {
        throw "missing frontend checkpoint"
    }
}

Assert-Test "arrancar uses in-process invocation for start script" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "arrancar_convergencia_windows.ps1") -Raw
    if ($content -notmatch 'Invoke-EiaaxScriptInProcess -FilePath \$startScript') {
        throw "arrancar must start demo in-process"
    }
}

Assert-Test "Start-EiaaxManagedProcess detaches service with start /B" {
    $content = Get-Content -LiteralPath $common -Raw
    if ($content -notmatch 'start "EIAAX_') {
        throw "managed process must detach services with start /B"
    }
    if ($content -notmatch '/B cmd /c') {
        throw "managed process must launch detached cmd"
    }
}

Assert-Test "Invoke-EiaaxPowerShellFile redirects output to avoid nested -Wait deadlock" {
    $content = Get-Content -LiteralPath $common -Raw
    if ($content -notmatch "RedirectStandardOutput") {
        throw "task PowerShell invocations must redirect stdout"
    }
    if ($content -notmatch "RedirectStandardError") {
        throw "task PowerShell invocations must redirect stderr"
    }
}

Assert-Test "frontend refuses npm.ps1 for service start" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "iniciar_frontend_demo.ps1") -Raw
    if ($content -notmatch "Refusing npm\.ps1") {
        throw "frontend must refuse npm.ps1 launcher"
    }
}

Assert-Test "health helpers use bounded timeout loops" {
    $content = Get-Content -LiteralPath $common -Raw
    foreach ($name in @("Test-EiaaxHealth", "Test-EiaaxFrontendReady", "Test-EiaaxFrontendProxyHealth", "Wait-EiaaxListenerPid")) {
        if ($content -notmatch ("function " + $name)) {
            throw ("missing function " + $name)
        }
    }
    if ($content -notmatch "Wait-EiaaxListenerPid[\s\S]*TimeoutSec") {
        throw "Wait-EiaaxListenerPid must accept timeout"
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("SERVICE STARTUP TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "SERVICE STARTUP TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
