#Requires -Version 5.1
<#
.SYNOPSIS
    Functional self-tests for Python discovery helpers (non-interactive only).
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

Assert-Test "CASE 1 empty candidate list binding regression" {
    $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
    if ($null -eq $candidates) {
        throw "Get-EiaaxPythonDiscoveryCandidates returned null"
    }
    $typeName = $candidates.GetType().FullName
    if ($typeName -ne "System.Object[]" -and $typeName -notlike "*Object[]") {
        throw ("Unexpected return type: " + $typeName)
    }
}

Assert-Test "CASE 2 explicit C:\Python314\python.exe when present" {
    $target = "C:\Python314\python.exe"
    if (Test-Path -LiteralPath $target) {
        $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
        if ($candidates -notcontains (Resolve-Path -LiteralPath $target).Path) {
            throw ("Expected candidate missing: " + $target)
        }
    }
    else {
        Write-Host "  SKIP: C:\Python314\python.exe not present on this machine"
    }
}

Assert-Test "CASE 3 EIAAX_PYTHON valid" {
    $python = (Get-Command python -ErrorAction SilentlyContinue)
    if ($null -eq $python) {
        Write-Host "  SKIP: python not in PATH"
        return
    }
    $previous = $env:EIAAX_PYTHON
    try {
        $env:EIAAX_PYTHON = $python.Source
        $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
        if ((Get-EiaaxCollectionCount $candidates) -lt 1) {
            throw "Expected at least one candidate with EIAAX_PYTHON set"
        }
        $selected = Find-EiaaxPython
        if ([string]::IsNullOrWhiteSpace($selected)) {
            throw "Find-EiaaxPython returned empty value"
        }
    }
    finally {
        $env:EIAAX_PYTHON = $previous
    }
}

Assert-Test "CASE 4 EIAAX_PYTHON missing path" {
    $commonPath = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
    $scriptText = @"
`$ErrorActionPreference = 'Stop'
. '$commonPath'
`$env:EIAAX_PYTHON = 'Z:\EIAAX\no-such-python.exe'
Find-EiaaxPython | Out-Null
"@
    Push-Location $PSScriptRoot
    try {
        $result = Invoke-EiaaxTestShellCommand -Script $scriptText -TimeoutSec 30
    }
    finally {
        Pop-Location
    }
    if ($result.ExitCode -eq 0) {
        throw "Expected non-zero exit for missing EIAAX_PYTHON path"
    }
    if ($result.Output -notmatch "PYTHON NOT FOUND") {
        throw ("Unexpected output: " + $result.Output)
    }
}

Assert-Test "CASE 5 python in PATH" {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        Write-Host "  SKIP: python not in PATH"
        return
    }
    $previous = $env:EIAAX_PYTHON
    try {
        Remove-Item Env:EIAAX_PYTHON -ErrorAction SilentlyContinue
        $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
        $found = $false
        foreach ($candidate in $candidates) {
            if ($candidate.ToUpperInvariant() -eq $python.Source.ToUpperInvariant()) {
                $found = $true
                break
            }
        }
        if (-not $found) {
            throw ("PATH python not discovered: " + $python.Source)
        }
    }
    finally {
        $env:EIAAX_PYTHON = $previous
    }
}

Assert-Test "CASE 6 WindowsApps alias ignored" {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        Write-Host "  SKIP: LOCALAPPDATA not set"
        return
    }
    $stub = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python.exe"
    if (-not (Test-Path -LiteralPath $stub)) {
        Write-Host "  SKIP: WindowsApps python stub not present"
        return
    }
    if (-not (Test-EiaaxWindowsPythonStub -Path $stub)) {
        throw "WindowsApps stub was not classified as stub"
    }
}

Assert-Test "CASE 7 no candidates handled cleanly" {
    $commonPath = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
    $scriptText = @"
`$ErrorActionPreference = 'Stop'
. '$commonPath'
`$env:EIAAX_PYTHON = 'Z:\EIAAX\no-such-python.exe'
`$env:PATH = 'C:\Windows\System32'
`$candidates = @(Get-EiaaxPythonDiscoveryCandidates)
if (`$candidates.Count -gt 0) { Write-Host 'SKIP_HAS_CANDIDATES'; exit 0 }
Find-EiaaxPython | Out-Null
"@
    Push-Location $PSScriptRoot
    try {
        $result = Invoke-EiaaxTestShellCommand -Script $scriptText -TimeoutSec 30
    }
    finally {
        Pop-Location
    }
    if ($result.Output -match "SKIP_HAS_CANDIDATES") {
        Write-Host "  SKIP: machine still exposes python candidates in restricted PATH"
        return
    }
    if ($result.ExitCode -eq 0) {
        throw "Expected failure when no candidates are available"
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("PYTHON DISCOVERY TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "PYTHON DISCOVERY TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
