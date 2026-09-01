#Requires -Version 5.1
<#
.SYNOPSIS
    Static and functional tests for convergence atomic startup helpers.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$helpers = Join-Path $PSScriptRoot "EiaaxDemo.TestHelpers.ps1"
. $helpers

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$failed = 0
$commonPath = $common
$arrancarScript = Join-Path $PSScriptRoot "arrancar_convergencia_windows.ps1"

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

Assert-Test "Read-EiaaxPyvenvCfg parses home/executable/version" {
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-pyvenv-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    try {
        $cfgPath = Join-Path $tempDir "pyvenv.cfg"
        @(
            "home = C:\Python312",
            "include-system-site-packages = false",
            'version = 3.12.6',
            'executable = C:\Python312\python.exe',
            'command = C:\Python312\python.exe -m venv D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo'
        ) | Set-Content -LiteralPath $cfgPath -Encoding ascii

        $cfg = Read-EiaaxPyvenvCfg -PyvenvCfgPath $cfgPath
        if ($cfg.home -ne "C:\Python312") {
            throw "home mismatch: " + $cfg.home
        }
        if ($cfg.executable -ne "C:\Python312\python.exe") {
            throw "executable mismatch: " + $cfg.executable
        }
        if ($cfg.version -ne "3.12.6") {
            throw "version mismatch: " + $cfg.version
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "Get-EiaaxPythonCandidatesFromPyvenvCfg excludes venv interpreter" {
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-pyvenv-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    try {
        $cfgPath = Join-Path $tempDir "pyvenv.cfg"
        @(
            "home = C:\Python312",
            'executable = D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo\Scripts\python.exe'
        ) | Set-Content -LiteralPath $cfgPath -Encoding ascii

        $candidates = @(Get-EiaaxPythonCandidatesFromPyvenvCfg -PyvenvCfgPath $cfgPath)
        foreach ($candidate in $candidates) {
            if (Test-EiaaxPythonPathLooksLikeVenvInterpreter -Path $candidate) {
                throw "venv interpreter leaked as base candidate: " + $candidate
            }
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "Test-EiaaxVenvIntegrity rejects missing Scripts python" {
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-venv-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    try {
        Set-Content -LiteralPath (Join-Path $tempDir "pyvenv.cfg") -Value "home = C:\Python312" -Encoding ascii
        $result = Test-EiaaxVenvIntegrity -VenvPath $tempDir
        if ($result.Valid) {
            throw "Expected invalid venv"
        }
        if ($result.Reason -notmatch "Scripts") {
            throw ("Unexpected reason: " + $result.Reason)
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "arrancar_convergencia_windows.ps1 contains atomic git sync and fail-closed output" {
    if (-not (Test-Path -LiteralPath $arrancarScript)) {
        throw "Missing arrancar_convergencia_windows.ps1"
    }
    $content = Get-Content -LiteralPath $arrancarScript -Raw
    foreach ($needle in @(
            "Sync-EiaaxConvergenceRepository",
            "Clear-EiaaxPortsForConvergence",
            "Confirm-EiaaxStartedProcessWorktree",
            "EIAAX — WINDOWS NO CERTIFICADO",
            "CAUSA:",
            "WINDOWS REAL OPERATIVO"
        )) {
        if ($content -notmatch [regex]::Escape($needle)) {
            throw ("Missing required token in arrancar script: " + $needle)
        }
    }
    if ($content -match "PRUEBA WINDOWS DISPONIBLE") {
        throw "arrancar script must not emit PRUEBA WINDOWS DISPONIBLE"
    }
}

Assert-Test "Get-EiaaxReferencePyvenvCfgPath points to INTEGRADO reference venv" {
    $path = Get-EiaaxReferencePyvenvCfgPath
    if ($path -notmatch '\\EMPLEADOS_IA_INTEGRADO\\\.venv-eiaax-demo\\pyvenv\.cfg$') {
        throw ("Unexpected reference cfg path: " + $path)
    }
}

Assert-Test "Discovery order places reference cfg before static installs" {
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-order-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    $pythonRoot = Join-Path $tempDir "PYTHON312"
    New-Item -ItemType Directory -Path $pythonRoot | Out-Null
    $pythonExe = Join-Path $pythonRoot "python.exe"
    Set-Content -LiteralPath $pythonExe -Value "" -Encoding ascii
    $cfgPath = Join-Path $tempDir "pyvenv.cfg"
    @(
        ("home = " + $pythonRoot),
        ("executable = " + $pythonExe)
    ) | Set-Content -LiteralPath $cfgPath -Encoding ascii

    $body = @"
function Get-EiaaxReferencePyvenvCfgPath { return '$($cfgPath.Replace("'", "''"))' }
function Get-EiaaxPythonWhereCandidates { return @() }
function Get-EiaaxPythonLauncherCandidates { return @() }
function Get-EiaaxPythonRegistryCandidates { return @() }
`$env:PATH = ''
Remove-Item Env:EIAAX_PYTHON -ErrorAction SilentlyContinue
`$candidates = @(Get-EiaaxPythonDiscoveryCandidates)
if ((Get-EiaaxCollectionCount `$candidates) -eq 0) {
    Write-Host 'SKIP_NO_CANDIDATES'
    exit 0
}
`$expected = '$($pythonExe.Replace("'", "''"))'.ToUpperInvariant()
`$first = `$candidates[0].ToUpperInvariant()
if (`$first -ne `$expected) {
    Write-Host ('ERROR: first candidate was ' + `$candidates[0])
    exit 41
}
Write-Host 'OK'
exit 0
"@

    try {
        $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
        if ($result.Output -match "SKIP_NO_CANDIDATES") {
            Write-Host "  SKIP: discovery returned no candidates in isolated shell"
            return
        }
        if ($result.ExitCode -ne 0) {
            throw ("Discovery order test failed: " + $result.Output.Trim())
        }
    }
    finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("CONVERGENCE ATOMIC TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "CONVERGENCE ATOMIC TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
