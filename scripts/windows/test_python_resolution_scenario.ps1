#Requires -Version 5.1
<#
.SYNOPSIS
    End-to-end scenario test: stale pyvenv.cfg + functional reference venv + empty PATH.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$helpers = Join-Path $PSScriptRoot "EiaaxDemo.TestHelpers.ps1"
. $helpers

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$failed = 0
$commonPath = $common
$prepararScript = Join-Path $PSScriptRoot "preparar_demo_eiaax.ps1"

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

function New-EiaaxScenarioWorktree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    foreach ($dir in @("backend", "frontend", "data")) {
        New-Item -ItemType Directory -Path (Join-Path $Root $dir) | Out-Null
    }
    Set-Content -LiteralPath (Join-Path $Root "backend\requirements.txt") -Value "fastapi`n" -Encoding ascii
    Set-Content -LiteralPath (Join-Path $Root "frontend\package.json") -Value '{"name":"eiaax-test"}' -Encoding ascii
}

Assert-Test "preparar_demo_eiaax.ps1 uses canonical Resolve-EiaaxPython" {
    $content = Get-Content -LiteralPath $prepararScript -Raw
    if ($content -notmatch "Resolve-EiaaxPython") {
        throw "preparar_demo_eiaax.ps1 must call Resolve-EiaaxPython"
    }
    if ($content -match "Get-EiaaxPythonDiscoveryCandidates") {
        throw "preparar_demo_eiaax.ps1 must not call discovery helpers directly"
    }
}

Assert-Test "Invoke-EiaaxPythonSysProbe returns base_prefix from real venv" {
    $systemPython = Get-Command python3 -ErrorAction SilentlyContinue
    if ($null -eq $systemPython) {
        $systemPython = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -eq $systemPython) {
        Write-Host "  SKIP: no system python available"
        return
    }

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-sysprobe-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    $venvPath = Join-Path $tempDir "probe-venv"
    try {
        Invoke-EiaaxNativeCommand -FilePath $systemPython.Source -ArgumentList @("-m", "venv", $venvPath) `
            -FailureMessage "failed to create probe venv"
        $venvPython = Join-Path $venvPath "bin/python"
        if (-not (Test-Path -LiteralPath $venvPython)) {
            $venvPython = Join-Path $venvPath "Scripts\python.exe"
        }
        $probe = Invoke-EiaaxPythonSysProbe -PythonExe $venvPython
        if ($probe.ExitCode -ne 0) {
            throw ("sys probe failed: " + $probe.Error)
        }
        if ([string]::IsNullOrWhiteSpace($probe.BasePrefix)) {
            throw "base_prefix empty"
        }
        if ([string]::IsNullOrWhiteSpace($probe.BaseExecutable)) {
            throw "base_executable empty"
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "Resolve-EiaaxPython finds base via sys probe when pyvenv.cfg paths are stale" {
    $systemPython = Get-Command python3 -ErrorAction SilentlyContinue
    if ($null -eq $systemPython) {
        $systemPython = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -eq $systemPython) {
        Write-Host "  SKIP: no system python available"
        return
    }

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-scenario-" + [Guid]::NewGuid().ToString("N"))
    $integrado = Join-Path $tempRoot "EMPLEADOS_IA_INTEGRADO"
    $convergencia = Join-Path $tempRoot "EMPLEADOS_IA_CONVERGENCIA"
    $integradoVenv = Join-Path $integrado ".venv-eiaax-demo"
    New-Item -ItemType Directory -Path $integradoVenv | Out-Null
    New-EiaaxScenarioWorktree -Root $convergencia

    try {
        Invoke-EiaaxNativeCommand -FilePath $systemPython.Source -ArgumentList @("-m", "venv", $integradoVenv) `
            -FailureMessage "failed to create reference venv"
        $cfgPath = Join-Path $integradoVenv "pyvenv.cfg"
        @(
            "home = C:\STALE\Python312",
            'executable = C:\STALE\Python312\python.exe',
            'version = 3.12.0',
            'command = C:\STALE\Python312\python.exe -m venv D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo'
        ) | Set-Content -LiteralPath $cfgPath -Encoding ascii

        $escapedIntegrado = $integrado.Replace("'", "''")
        $escapedConvergencia = $convergencia.Replace("'", "''")
        $body = @"
`$env:EIAAX_REFERENCE_WORKTREE = '$escapedIntegrado'
`$env:EIAAX_WORKTREE = '$escapedConvergencia'
`$env:PATH = ''
function Get-EiaaxPythonWhereCandidates { return @() }
function Get-EiaaxPythonLauncherCandidates { return @() }
function Get-EiaaxPythonRegistryCandidates { return @() }
`$selected = Resolve-EiaaxPython -WorktreeRoot '$escapedConvergencia'
if ([string]::IsNullOrWhiteSpace(`$selected)) {
    Write-Host 'ERROR: empty selection'
    exit 51
}
if (Test-EiaaxPythonPathLooksLikeVenvInterpreter -Path `$selected) {
    `$probe = Invoke-EiaaxPythonSysProbe -PythonExe (Join-EiaaxWindowsPath -Base '$escapedIntegrado' -Child '.venv-eiaax-demo\Scripts\python.exe')
    if (`$probe.ExitCode -ne 0) {
        Write-Host 'ERROR: cannot probe reference venv'
        exit 52
    }
    if (`$selected.ToUpperInvariant() -ne `$probe.BaseExecutable.ToUpperInvariant() -and
        `$selected.ToUpperInvariant() -ne (Join-EiaaxPathMaybe -Base `$probe.BasePrefix -Child 'python.exe').ToUpperInvariant()) {
        if (`$selected -notmatch 'venv-creator|integrado|base_prefix') {
            Write-Host ('ERROR: unexpected selection ' + `$selected)
            exit 53
        }
    }
}
Write-Host ('OK: ' + `$selected)
exit 0
"@

        $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 120
        if ($result.ExitCode -ne 0) {
            throw ("scenario resolver failed: " + $result.Output.Trim())
        }
        if ($result.Output -notmatch "PYTHON DISCOVERY") {
            throw "diagnostics block missing from resolver output"
        }
        if ($result.Output -notmatch "sys.base_prefix") {
            throw "sys.base_prefix not reported in diagnostics"
        }
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "Find-EiaaxPython is alias of Resolve-EiaaxPython" {
    $find = Get-Command Find-EiaaxPython
    $resolve = Get-Command Resolve-EiaaxPython
    if ($null -eq $find -or $null -eq $resolve) {
        throw "missing canonical resolver commands"
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("PYTHON RESOLUTION SCENARIO TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "PYTHON RESOLUTION SCENARIO TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
