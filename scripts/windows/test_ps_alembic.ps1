#Requires -Version 5.1
<#
.SYNOPSIS
    Regression tests for Alembic verification and PS 5.1 collection semantics.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

Assert-Test "Get-EiaaxCollectionCount on null returns 0" {
    if ((Get-EiaaxCollectionCount $null) -ne 0) {
        throw "Expected 0 for null"
    }
}

Assert-Test "Get-EiaaxCollectionCount on scalar Where-Object result (PS 5.1 bug)" {
    $scalar = "1770a1b2c3d4e (head)"
    $filtered = $scalar | Where-Object { $_ -match '\(head\)' }
    if ($filtered -is [System.Array]) {
        throw "Expected scalar from single-match Where-Object"
    }
    try {
        $broken = $filtered.Count
        throw "Scalar unexpectedly exposed Count=$broken"
    }
    catch {
        if ($_.Exception.Message -notlike "*Count*") {
            throw
        }
    }
    if ((Get-EiaaxCollectionCount $filtered) -ne 1) {
        throw "Expected count 1 via helper"
    }
}

Assert-Test "Get-EiaaxCollectionCount on empty pipeline result returns 0" {
    $empty = @("no-head-line") | Where-Object { $_ -match '\(head\)' }
    if ((Get-EiaaxCollectionCount $empty) -ne 0) {
        throw "Expected 0 for empty pipeline result"
    }
}

Assert-Test "Get-EiaaxCollectionCount on multi-element array" {
    $items = @("a", "b", "c")
    if ((Get-EiaaxCollectionCount $items) -ne 3) {
        throw "Expected 3"
    }
}

Assert-Test "Get-EiaaxAlembicHeadRevisions parses zero heads" {
    $revs = Get-EiaaxAlembicHeadRevisions -Output "no revisions here`n"
    if ((Get-EiaaxCollectionCount $revs) -ne 0) {
        throw "Expected 0 head revisions"
    }
}

Assert-Test "Get-EiaaxAlembicHeadRevisions parses single head" {
    $revs = Get-EiaaxAlembicHeadRevisions -Output "1770a1b2c3d4e (head)`n"
    if ((Get-EiaaxCollectionCount $revs) -ne 1) {
        throw "Expected 1 head revision"
    }
    if ($revs[0] -ne "1770a1b2c3d4e") {
        throw ("Unexpected revision: " + $revs[0])
    }
}

Assert-Test "Get-EiaaxAlembicHeadRevisions parses multiple heads" {
    $output = @(
        "111111111111 (head)",
        "222222222222 (head)"
    ) -join "`n"
    $revs = Get-EiaaxAlembicHeadRevisions -Output $output
    if ((Get-EiaaxCollectionCount $revs) -ne 2) {
        throw "Expected 2 head revisions"
    }
}

Assert-Test "Get-EiaaxAlembicCurrentRevisions parses single current line" {
    $revs = Get-EiaaxAlembicCurrentRevisions -Output "1770a1b2c3d4e (head)`n"
    if ((Get-EiaaxCollectionCount $revs) -ne 1) {
        throw "Expected 1 current revision"
    }
    if ($revs[0] -ne "1770a1b2c3d4e") {
        throw ("Unexpected current revision: " + $revs[0])
    }
}

Assert-Test "Single-head pipeline count does not throw (regression 66db838)" {
    $headsOutput = "1770a1b2c3d4e (head)`n"
    $headLines = $headsOutput -split "`r?`n" | Where-Object { $_ -match '\(head\)' }
    $headCount = Get-EiaaxCollectionCount $headLines
    if ($headCount -gt 1) {
        throw "Expected not to fail on single head line"
    }
}

function Get-EiaaxTestPythonExecutable {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -eq $python) {
        throw "python not found for external command regression tests"
    }
    return $python.Source
}

Assert-Test "Invoke-EiaaxExternalCommand tolerates stderr INFO with ExitCode 0 under Stop" {
    $python = Get-EiaaxTestPythonExecutable
    $snippet = "import sys; sys.stderr.write('INFO [alembic.runtime.migration] Context impl SQLiteImpl.\n')"
    $result = Invoke-EiaaxExternalCommand -FilePath $python -ArgumentList @("-c", $snippet)
    if ($result.ExitCode -ne 0) {
        throw ("Expected ExitCode 0, got " + $result.ExitCode + " Output=" + $result.Output)
    }
    if ($result.Output -notmatch "Context impl SQLiteImpl") {
        throw ("Expected Alembic INFO line in output: " + $result.Output)
    }
}

Assert-Test "Invoke-EiaaxExternalCommand combines stdout and stderr with ExitCode 0" {
    $python = Get-EiaaxTestPythonExecutable
    $snippet = "import sys; print('stdout marker'); sys.stderr.write('stderr marker\n')"
    $result = Invoke-EiaaxExternalCommand -FilePath $python -ArgumentList @("-c", $snippet)
    if ($result.ExitCode -ne 0) {
        throw ("Expected ExitCode 0, got " + $result.ExitCode)
    }
    if ($result.Output -notmatch "stdout marker" -or $result.Output -notmatch "stderr marker") {
        throw ("Expected combined output, got: " + $result.Output)
    }
}

Assert-Test "Invoke-EiaaxExternalCommand fails closed on non-zero ExitCode" {
    $python = Get-EiaaxTestPythonExecutable
    $snippet = "import sys; sys.stderr.write('ERROR real alembic failure\n'); sys.exit(3)"
    $result = Invoke-EiaaxExternalCommand -FilePath $python -ArgumentList @("-c", $snippet)
    if ($result.ExitCode -eq 0) {
        throw "Expected non-zero ExitCode for real failure"
    }
    if ($result.Output -notmatch "ERROR real alembic failure") {
        throw ("Expected stderr error text in output: " + $result.Output)
    }
}

Assert-Test "Invoke-EiaaxExternalCommand succeeds under global Stop with stderr INFO" {
    $python = Get-EiaaxTestPythonExecutable
    $snippet = "import sys; sys.stderr.write('INFO [alembic.runtime.migration] Context impl SQLiteImpl.\n')"
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Stop"
    try {
        $result = Invoke-EiaaxExternalCommand -FilePath $python -ArgumentList @("-c", $snippet)
        if ($result.ExitCode -ne 0) {
            throw ("Expected ExitCode 0 under Stop, got " + $result.ExitCode)
        }
        if ($result.Output -notmatch "Context impl SQLiteImpl") {
            throw ("Expected Alembic INFO in output under Stop: " + $result.Output)
        }
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("PS ALEMBIC TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "PS ALEMBIC TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
