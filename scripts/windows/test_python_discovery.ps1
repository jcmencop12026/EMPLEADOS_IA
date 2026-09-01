#Requires -Version 5.1
<#
.SYNOPSIS
    Self-check for Python discovery helpers (run on Windows).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

Write-Host "=== EIAAX Python discovery self-check ==="

$candidates = Get-EiaaxPythonDiscoveryCandidates
Write-Host ("Candidates discovered: " + $candidates.Count)
foreach ($candidate in $candidates) {
    $probe = Test-EiaaxPythonRuntimeCandidate -PythonExe $candidate
    $status = if ($probe.Executable) { "OK" } else { "FAIL" }
    Write-Host ("  [" + $status + "] " + $candidate + " -> " + $probe.Version + " " + $probe.Error)
}

try {
    $selected = Find-EiaaxPython
    Write-Host ("Selected runtime: " + $selected)
    exit 0
}
catch {
    Write-Host ("Selection failed: " + $_.Exception.Message)
    exit 1
}
