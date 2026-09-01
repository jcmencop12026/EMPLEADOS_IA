#Requires -Version 5.1
<#
.SYNOPSIS
    Start the EIAAX demo backend (uvicorn on port 8000).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

try {
    $worktree = Get-EiaaxWorktreeRoot
    Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
    Test-EiaaxWorktree -WorktreeRoot $worktree

    if (-not (Test-EiaaxDemoDatabaseReady -WorktreeRoot $worktree)) {
        Exit-EiaaxFailure -Message "Demo database missing. Run scripts\windows\preparar_demo_eiaax.ps1 first."
    }

    $paths = Get-EiaaxPaths -WorktreeRoot $worktree
    $venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree
    $databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree
    $stateDir = Ensure-EiaaxStateDir -WorktreeRoot $worktree

    $port = $BackendPort
    $existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Exit-EiaaxFailure -Message "Port ${port} is already in use. Run scripts\windows\detener_demo_eiaax.ps1."
    }

    $launcherPath = Join-Path $stateDir "run_backend.ps1"
    $escapedDbUrl = Escape-EiaaxSingleQuoted -Value $databaseUrl
    $escapedBackend = Escape-EiaaxSingleQuoted -Value $paths.Backend
    $escapedPython = Escape-EiaaxSingleQuoted -Value $venvPython

    Write-EiaaxLauncherFile -Path $launcherPath -Lines @(
        '$ErrorActionPreference = "Stop"'
        ('$env:DATABASE_URL = ''' + $escapedDbUrl + '''')
        ('Set-Location -LiteralPath ''' + $escapedBackend + '''')
        ('& ''' + $escapedPython + ''' -m uvicorn app.main:app --host 127.0.0.1 --port ' + $port)
    )

    Write-Host "Starting backend at http://127.0.0.1:${port} ..."
    $proc = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $launcherPath) `
        -PassThru `
        -WorkingDirectory $paths.Backend `
        -WindowStyle Normal

    Write-EiaaxPidFile -StateDir $stateDir -Name "backend" -ProcessId $proc.Id
    Write-Host "Backend shell PID: $($proc.Id)"

    if (-not (Test-EiaaxHealth -Port $port -TimeoutSec 45)) {
        Exit-EiaaxFailure -Message "Backend started but /health did not respond in time."
    }

    Write-Host "Backend health OK: http://127.0.0.1:${port}/health"
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
