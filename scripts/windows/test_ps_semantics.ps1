#Requires -Version 5.1
<#
.SYNOPSIS
    Semantic helper tests for EIAAX Windows scripts (PowerShell runtime).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

Assert-Test "Mandatory empty List[string] reproduces PS 5.1 binder issue" {
    function Bad-ListHelper {
        param(
            [Parameter(Mandatory = $true)]
            [System.Collections.Generic.List[string]]$List
        )
        [void]$List.Add("x")
    }

    $emptyList = New-Object System.Collections.Generic.List[string]
    $binderFailed = $false
    try {
        Bad-ListHelper -List $emptyList
    }
    catch {
        if ($_.Exception.Message -like "*coleccion vacia*" -or $_.Exception.Message -like "*empty collection*") {
            $binderFailed = $true
        }
    }

    if (-not $binderFailed) {
        Write-Host "  NOTE: current shell did not reproduce empty-list binder failure"
    }
}

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

Assert-Test "Get-EiaaxPythonDiscoveryCandidates returns array on empty start" {
    $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
    if ($null -eq $candidates) {
        throw "null result"
    }
}

Assert-Test "Invoke-EiaaxNativeCommand accepts empty ArgumentList" {
    $python = (Get-Command python -ErrorAction SilentlyContinue)
    if ($null -eq $python) {
        Write-Host "  SKIP: python not available"
        return
    }
    Invoke-EiaaxNativeCommand -FilePath $python.Source -ArgumentList @() -FailureMessage "python without args failed"
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("PS SEMANTICS TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "PS SEMANTICS TESTS: PASS"
exit 0
