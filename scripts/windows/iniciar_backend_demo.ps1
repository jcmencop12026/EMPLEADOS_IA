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
    $logsDir = Ensure-EiaaxLogsDir -WorktreeRoot $worktree
    $venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree
    $databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree
    $stateDir = Ensure-EiaaxStateDir -WorktreeRoot $worktree

    $port = $BackendPort
    Assert-EiaaxPortAvailable -Port $port -Label "backend"

    $logFile = Join-Path $logsDir "backend.log"
    if (Test-Path -LiteralPath $logFile) {
        Remove-Item -LiteralPath $logFile -Force
    }

    Write-Host "Starting backend at http://127.0.0.1:${port} ..."
    $proc = Start-EiaaxManagedProcess `
        -FilePath $venvPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", [string]$port) `
        -WorkingDirectory $paths.Backend `
        -LogFile $logFile `
        -StateDir $stateDir `
        -WrapperName "run_backend" `
        -Environment @{ DATABASE_URL = $databaseUrl }

    $listenerPid = Wait-EiaaxListenerPid -Port $port -TimeoutSec 45
    if ($null -eq $listenerPid) {
        Exit-EiaaxFailure -Message "Backend process did not open port 8000 in time. See logs\demo\backend.log"
    }

    if (-not (Test-EiaaxManagedProcess -ProcessId $listenerPid -WorktreeRoot $worktree -ServiceName "backend")) {
        Exit-EiaaxFailure -Message ("Port 8000 is owned by unexpected PID " + $listenerPid + ". Aborting.")
    }

    Write-EiaaxPidFile -StateDir $stateDir -Name "backend" -ProcessId $listenerPid
    Write-EiaaxStateValue -StateDir $stateDir -Name "backend-wrapper" -Value ([string]$proc.Id)

    if (-not (Test-EiaaxHealth -Port $port -TimeoutSec 45)) {
        Exit-EiaaxFailure -Message "Backend /health did not respond in time. See logs\demo\backend.log"
    }

    Write-Host "Backend health OK: http://127.0.0.1:${port}/health"
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
