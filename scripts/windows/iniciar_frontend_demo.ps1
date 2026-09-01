#Requires -Version 5.1
<#
.SYNOPSIS
    Start the EIAAX demo frontend (Vite dev server on port 5180).
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
    $stateDir = Ensure-EiaaxStateDir -WorktreeRoot $worktree

    $port = $FrontendPort
    Assert-EiaaxPortAvailable -Port $port -Label "frontend"

    $nodeModules = Join-Path $paths.Frontend "node_modules"
    if (-not (Test-Path -LiteralPath $nodeModules)) {
        Exit-EiaaxFailure -Message "node_modules missing. Run scripts\windows\preparar_demo_eiaax.ps1 first."
    }

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Exit-EiaaxFailure -Message "npm not found in PATH."
    }

    $npmCmd = $npm.Source
    $logFile = Join-Path $logsDir "frontend.log"
    if (Test-Path -LiteralPath $logFile) {
        Remove-Item -LiteralPath $logFile -Force
    }

    Write-Host "Starting frontend at http://127.0.0.1:${port} ..."
    $proc = Start-EiaaxManagedProcess `
        -FilePath $npmCmd `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory $paths.Frontend `
        -LogFile $logFile `
        -StateDir $stateDir `
        -WrapperName "run_frontend" `
        -Environment @{}

    $listenerPid = Wait-EiaaxListenerPid -Port $port -TimeoutSec 45
    if ($null -eq $listenerPid) {
        Exit-EiaaxFailure -Message "Frontend process did not open port 5180 in time. See logs\demo\frontend.log"
    }

    if (-not (Test-EiaaxManagedProcess -ProcessId $listenerPid -WorktreeRoot $worktree -ServiceName "frontend")) {
        Exit-EiaaxFailure -Message ("Port 5180 is owned by unexpected PID " + $listenerPid + ". Aborting.")
    }

    Write-EiaaxPidFile -StateDir $stateDir -Name "frontend" -ProcessId $listenerPid
    Write-EiaaxStateValue -StateDir $stateDir -Name "frontend-wrapper" -Value ([string]$proc.Id)

    if (-not (Test-EiaaxFrontendReady -Port $port -TimeoutSec 45)) {
        Exit-EiaaxFailure -Message "Frontend did not respond in time. See logs\demo\frontend.log"
    }

    Write-Host "Frontend ready: http://127.0.0.1:${port}"
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
