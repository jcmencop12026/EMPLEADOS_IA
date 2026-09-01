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
$commonPath = $common

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
    finally {
        Restore-All-EiaaxTestEnvVars
    }
}

function Get-EiaaxPathCommandApplication {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        return $null
    }
    if ($command.CommandType -ne "Application") {
        return $null
    }
    if ([string]::IsNullOrWhiteSpace($command.Source)) {
        return $null
    }
    if (-not (Test-Path -LiteralPath $command.Source)) {
        return $null
    }
    if (Test-EiaaxWindowsPythonStub -Path $command.Source) {
        return $null
    }

    return (Resolve-Path -LiteralPath $command.Source).Path
}

Assert-Test "CASE 1 empty candidate list binding regression" {
    Clear-EiaaxTestEnvVar -Name "EIAAX_PYTHON"
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
    $target = Get-EiaaxKnownWindowsPythonExe
    if ($null -eq $target) {
        Write-Host "  SKIP: no known Windows Python install path present"
        return
    }

    Clear-EiaaxTestEnvVar -Name "EIAAX_PYTHON"
    $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
    $resolvedTarget = (Resolve-Path -LiteralPath $target).Path
    $found = $false
    foreach ($candidate in $candidates) {
        if ($candidate.ToUpperInvariant() -eq $resolvedTarget.ToUpperInvariant()) {
            $found = $true
            break
        }
    }
    if (-not $found) {
        throw ("Expected candidate missing: " + $resolvedTarget)
    }
}

Assert-Test "CASE 3 EIAAX_PYTHON valid" {
    $target = Get-EiaaxKnownWindowsPythonExe
    if ($null -eq $target) {
        Write-Host "  SKIP: no known Windows Python install path present"
        return
    }

    Set-EiaaxTestEnvVar -Name "EIAAX_PYTHON" -Value $target
    $selected = Find-EiaaxPython
    if ([string]::IsNullOrWhiteSpace($selected)) {
        throw "Find-EiaaxPython returned empty value"
    }

    $selectedResolved = (Resolve-Path -LiteralPath $selected).Path
    $targetResolved = (Resolve-Path -LiteralPath $target).Path
    if ($selectedResolved.ToUpperInvariant() -ne $targetResolved.ToUpperInvariant()) {
        throw ("Selected mismatch. expected=" + $targetResolved + " actual=" + $selectedResolved)
    }

    $probe = Invoke-EiaaxPythonVersionProbe -PythonExe $selectedResolved
    if ($probe.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($probe.Text)) {
        throw ("python -V failed: " + $probe.Text)
    }
    Write-Host ("  OK: " + $probe.Text)
}

Assert-Test "CASE 4 EIAAX_PYTHON missing path" {
    $body = @"
`$env:EIAAX_PYTHON = 'Z:\EIAAX\no-such-python.exe'
Find-EiaaxPython | Out-Null
exit 0
"@

    $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
    if ($result.ExitCode -eq 0) {
        throw "Expected non-zero exit for missing EIAAX_PYTHON path"
    }
    if ($result.Output -notmatch "PYTHON NOT FOUND") {
        throw ("Unexpected output: " + $result.Output.Trim())
    }
}

Assert-Test "CASE 5 python in PATH" {
    $pathPython = Get-EiaaxPathCommandApplication -Name "python"
    if ($null -eq $pathPython) {
        Write-Host "  SKIP: no non-stub python application in PATH"
        return
    }

    $escapedPath = $pathPython.Replace("'", "''")
    $body = @"
Remove-Item Env:EIAAX_PYTHON -ErrorAction SilentlyContinue
`$candidates = @(Get-EiaaxPythonDiscoveryCandidates)
`$found = `$false
foreach (`$candidate in `$candidates) {
    if (`$candidate.ToUpperInvariant() -eq '$($pathPython.ToUpperInvariant())') {
        `$found = `$true
        break
    }
}
if (-not `$found) {
    Write-Host ('ERROR: PATH python not discovered: $escapedPath')
    exit 21
}
Write-Host 'OK: PATH python discovered'
exit 0
"@

    $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
    if ($result.ExitCode -ne 0) {
        throw ("PATH discovery failed. ExitCode=" + $result.ExitCode + " Output=" + $result.Output.Trim())
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

    $escapedStub = $stub.Replace("'", "''")
    $body = @"
`$env:EIAAX_PYTHON = '$escapedStub'
`$candidates = @(Get-EiaaxPythonDiscoveryCandidates)
foreach (`$candidate in `$candidates) {
    if (`$candidate.ToUpperInvariant() -eq '$($stub.ToUpperInvariant())') {
        Write-Host 'ERROR: WindowsApps stub was not excluded from candidates'
        exit 31
    }
}
Write-Host 'OK: WindowsApps stub excluded'
exit 0
"@

    $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
    if ($result.ExitCode -ne 0) {
        throw ("WindowsApps exclusion failed. Output=" + $result.Output.Trim())
    }
}

Assert-Test "CASE 7 no candidates handled cleanly" {
    $body = @"
`$env:EIAAX_PYTHON = 'Z:\EIAAX\no-such-python.exe'
`$env:PATH = ''
function Get-EiaaxPythonWhereCandidates { return @() }
function Get-EiaaxPythonLauncherCandidates { return @() }
function Get-EiaaxPythonRegistryCandidates { return @() }
function Get-EiaaxReferencePyvenvCfgPath { return 'Z:\EIAAX\no-reference-pyvenv.cfg' }
`$candidates = @(Get-EiaaxPythonDiscoveryCandidates)
if ((Get-EiaaxCollectionCount `$candidates) -gt 0) {
    Write-Host 'SKIP_HAS_CANDIDATES'
    exit 0
}
Remove-Item Env:EIAAX_PYTHON -ErrorAction SilentlyContinue
Find-EiaaxPython | Out-Null
exit 0
"@

    $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
    if ($result.Output -match "SKIP_HAS_CANDIDATES") {
        Write-Host "  SKIP: machine still exposes python candidates in restricted PATH"
        return
    }
    if ($result.ExitCode -eq 0) {
        throw "Expected failure when no candidates are available"
    }
    if ($result.Output -notmatch "PYTHON NOT FOUND") {
        throw ("Unexpected output: " + $result.Output.Trim())
    }
}

Assert-Test "CASE 8 pyvenv.cfg base candidate derivation" {
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-pyvenv-" + [Guid]::NewGuid().ToString("N"))
    $pythonRoot = Join-Path $tempDir "Python312"
    New-Item -ItemType Directory -Path $pythonRoot | Out-Null
    $pythonExe = Join-Path $pythonRoot "python.exe"
    Set-Content -LiteralPath $pythonExe -Value "" -Encoding ascii

    try {
        $cfgPath = Join-Path $tempDir "pyvenv.cfg"
        @(
            ("home = " + $pythonRoot),
            ("executable = " + $pythonExe),
            'version = 3.12.6'
        ) | Set-Content -LiteralPath $cfgPath -Encoding ascii

        $candidates = @(Get-EiaaxPythonCandidatesFromPyvenvCfg -PyvenvCfgPath $cfgPath)
        if ((Get-EiaaxCollectionCount $candidates) -lt 1) {
            throw "Expected at least one candidate from pyvenv.cfg"
        }
        $expected = (Resolve-Path -LiteralPath $pythonExe).Path
        if ($candidates[0].ToUpperInvariant() -ne $expected.ToUpperInvariant()) {
            throw ("Unexpected first candidate: " + $candidates[0])
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "CASE 9 WindowsApps alias rejected as executable candidate" {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        Write-Host "  SKIP: LOCALAPPDATA not set"
        return
    }

    $stub = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python.exe"
    if (-not (Test-Path -LiteralPath $stub)) {
        Write-Host "  SKIP: WindowsApps python stub not present"
        return
    }

    $probe = Test-EiaaxPythonRuntimeCandidate -PythonExe $stub
    if ($probe.Executable) {
        throw "WindowsApps stub must not pass runtime candidate probe"
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("PYTHON DISCOVERY TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "PYTHON DISCOVERY TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
Write-Host ""
Write-Host "============================================================"
Write-Host "EIAAX -- AUTOTEST DESARROLLO PYTHON COMPLETADO"
Write-Host "============================================================"
try {
    Add-Type -AssemblyName System.Speech -ErrorAction Stop
    $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $speaker.Speak("EIAAX autotest Windows Python corregido y revisado integralmente")
}
catch {
    # Voice notification is optional.
}
exit 0
