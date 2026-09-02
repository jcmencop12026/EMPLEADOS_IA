#Requires -Version 5.1
<#
.SYNOPSIS
    Regression tests for git sync and stderr-tolerant external command execution.
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

function Get-EiaaxTestPythonExecutable {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -eq $python) {
        throw "python not found"
    }
    return $python.Source
}

function New-EiaaxFakeGitScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Directory,
        [Parameter(Mandatory = $true)]
        [ValidateSet("success_fetch", "success_up_to_date", "success_fast_forward", "fail_pull")]
        [string]$Mode
    )

    $scriptPath = Join-Path $Directory "git"
    $lines = New-Object System.Collections.Generic.List[string]
    [void]$lines.Add("#!/usr/bin/env bash")
    [void]$lines.Add("set -e")
    [void]$lines.Add('case "$1" in')
    [void]$lines.Add('  fetch)')
    [void]$lines.Add('    echo "From https://github.com/jcmencop12026/EMPLEADOS_IA" >&2')
    [void]$lines.Add('    exit 0')
    [void]$lines.Add('    ;;')
    [void]$lines.Add('  checkout)')
    [void]$lines.Add('    echo "Switched to branch cursor/convergencia-comercial-v1-85e4"')
    [void]$lines.Add('    exit 0')
    [void]$lines.Add('    ;;')
    [void]$lines.Add('  pull)')
    switch ($Mode) {
        "success_up_to_date" {
            [void]$lines.Add('    echo "Already up to date."')
            [void]$lines.Add('    exit 0')
        }
        "success_fast_forward" {
            [void]$lines.Add('    echo "Updating abc1234..def5678"')
            [void]$lines.Add('    echo "Fast-forward"')
            [void]$lines.Add('    exit 0')
        }
        "fail_pull" {
            [void]$lines.Add('    echo "fatal: Not possible to fast-forward, aborting." >&2')
            [void]$lines.Add('    exit 1')
        }
        default {
            [void]$lines.Add('    exit 0')
        }
    }
    [void]$lines.Add('    ;;')
    [void]$lines.Add('  rev-parse)')
    [void]$lines.Add('    echo "18b9be3"')
    [void]$lines.Add('    exit 0')
    [void]$lines.Add('    ;;')
    [void]$lines.Add('esac')
    [void]$lines.Add('exit 0')
    Set-Content -LiteralPath $scriptPath -Value ($lines.ToArray()) -Encoding ascii
    & chmod +x $scriptPath
    return $scriptPath
}

Assert-Test "A. Invoke-EiaaxExternalCommand exit 0 + stderr text under Stop" {
    $python = Get-EiaaxTestPythonExecutable
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Stop"
    try {
        $result = Invoke-EiaaxExternalCommand -FilePath $python -ArgumentList @(
            "-c", "import sys; sys.stderr.write('stderr informational line\n')"
        )
        if ($result.ExitCode -ne 0) {
            throw ("Expected exit 0, got " + $result.ExitCode)
        }
        if ($result.Output -notmatch "stderr informational line") {
            throw ("Expected stderr in output: " + $result.Output)
        }
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
}

Assert-Test "B. Invoke-EiaaxExternalCommand exit 0 + From https://... under Stop" {
    $python = Get-EiaaxTestPythonExecutable
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Stop"
    try {
        $result = Invoke-EiaaxExternalCommand -FilePath $python -ArgumentList @(
            "-c", "import sys; sys.stderr.write('From https://github.com/jcmencop12026/EMPLEADOS_IA\n')"
        )
        if ($result.ExitCode -ne 0) {
            throw ("Expected exit 0, got " + $result.ExitCode)
        }
        if ($result.Output -notmatch "From https://github.com/jcmencop12026/EMPLEADOS_IA") {
            throw ("Expected From line in output: " + $result.Output)
        }
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
}

Assert-Test "C. Invoke-EiaaxExternalCommand exit 1 + stderr is FAIL" {
    $python = Get-EiaaxTestPythonExecutable
    $result = Invoke-EiaaxExternalCommand -FilePath $python -ArgumentList @(
        "-c", "import sys; sys.stderr.write('fatal: simulated git error\n'); sys.exit(1)"
    )
    if ($result.ExitCode -eq 0) {
        throw "Expected non-zero exit code"
    }
    if ($result.Output -notmatch "fatal: simulated git error") {
        throw ("Expected error text in output: " + $result.Output)
    }
}

Assert-Test "D. Invoke-EiaaxGitCommand fetch tolerates From stderr (already up to date path)" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-git-" + [Guid]::NewGuid().ToString("N"))
    $fakeBin = Join-Path $tempRoot "bin"
    $repo = Join-Path $tempRoot "repo"
    New-Item -ItemType Directory -Path $fakeBin | Out-Null
    New-Item -ItemType Directory -Path $repo | Out-Null
    New-EiaaxFakeGitScript -Directory $fakeBin -Mode "success_up_to_date" | Out-Null

  $body = @"
`$env:PATH = '$($fakeBin.Replace("'", "''")):' + `$env:PATH
function Get-EiaaxGitExecutable { return (Join-Path '$($fakeBin.Replace("'", "''"))' 'git') }
`$ErrorActionPreference = 'Stop'
`$result = Invoke-EiaaxGitCommand -ArgumentList @('fetch', 'origin', 'cursor/convergencia-comercial-v1-85e4') -WorkingDirectory '$($repo.Replace("'", "''"))'
if (`$result.ExitCode -ne 0) { Write-Host 'ERROR exit'; exit 41 }
if (`$result.Output -notmatch 'From https://github.com/jcmencop12026/EMPLEADOS_IA') { Write-Host 'ERROR missing From'; exit 42 }
Write-Host 'OK'
exit 0
"@

    try {
        $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
        if ($result.ExitCode -ne 0) {
            throw ("fake git fetch failed: " + $result.Output.Trim())
        }
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "E. Sync-EiaaxConvergenceRepository PASS on fast-forward stderr/stdout" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-git-" + [Guid]::NewGuid().ToString("N"))
    $fakeBin = Join-Path $tempRoot "bin"
    $repo = Join-Path $tempRoot "repo"
    New-Item -ItemType Directory -Path $fakeBin | Out-Null
    New-Item -ItemType Directory -Path $repo | Out-Null
    New-EiaaxFakeGitScript -Directory $fakeBin -Mode "success_fast_forward" | Out-Null

    $body = @"
`$env:PATH = '$($fakeBin.Replace("'", "''")):' + `$env:PATH
function Get-EiaaxGitExecutable { return (Join-Path '$($fakeBin.Replace("'", "''"))' 'git') }
`$ErrorActionPreference = 'Stop'
Sync-EiaaxConvergenceRepository -WorktreeRoot '$($repo.Replace("'", "''"))' -ExpectedBranch 'cursor/convergencia-comercial-v1-85e4'
Write-Host 'OK'
exit 0
"@

    try {
        $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
        if ($result.ExitCode -ne 0) {
            throw ("sync fast-forward failed: " + $result.Output.Trim())
        }
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "F. Sync-EiaaxConvergenceRepository FAIL on non-fast-forward" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-git-" + [Guid]::NewGuid().ToString("N"))
    $fakeBin = Join-Path $tempRoot "bin"
    $repo = Join-Path $tempRoot "repo"
    New-Item -ItemType Directory -Path $fakeBin | Out-Null
    New-Item -ItemType Directory -Path $repo | Out-Null
    New-EiaaxFakeGitScript -Directory $fakeBin -Mode "fail_pull" | Out-Null

    $body = @"
`$env:PATH = '$($fakeBin.Replace("'", "''")):' + `$env:PATH
function Get-EiaaxGitExecutable { return (Join-Path '$($fakeBin.Replace("'", "''"))' 'git') }
`$ErrorActionPreference = 'Stop'
Sync-EiaaxConvergenceRepository -WorktreeRoot '$($repo.Replace("'", "''"))' -ExpectedBranch 'cursor/convergencia-comercial-v1-85e4'
Write-Host 'ERROR should have exited'
exit 51
"@

    try {
        $result = Invoke-EiaaxProductionShellTest -CommonPath $commonPath -Body $body -TimeoutSec 30
        if ($result.ExitCode -eq 0) {
            throw "Expected sync to fail on non-fast-forward"
        }
        if ($result.Output -notmatch "pull --ff-only failed|Not possible to fast-forward") {
            throw ("unexpected failure output: " + $result.Output.Trim())
        }
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "arrancar script documents ETAPA and LOG on failure" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "arrancar_convergencia_windows.ps1") -Raw
    if ($content -notmatch "ETAPA:") {
        throw "arrancar_convergencia_windows.ps1 must print ETAPA on failure"
    }
    if ($content -notmatch "LOG:") {
        throw "arrancar_convergencia_windows.ps1 must print LOG on failure"
    }
    if ($content -notmatch "pull --ff-only") {
        throw "arrancar must use git pull --ff-only via Sync-EiaaxConvergenceRepository"
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("GIT SYNC TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "GIT SYNC TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
