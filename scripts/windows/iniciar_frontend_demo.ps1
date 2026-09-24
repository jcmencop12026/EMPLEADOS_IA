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
    if (Test-EiaaxReuseRunningService -Port $port -WorktreeRoot $worktree -ServiceName "frontend" `
            -ReadyTest { Test-EiaaxFrontendReady -Port $port -TimeoutSec 5 } -ReadyLabel "HTTP") {
        $listenerPid = Get-EiaaxListenerPid -Port $port
        Write-EiaaxPidFile -StateDir $stateDir -Name "frontend" -ProcessId $listenerPid
        Write-Host "Frontend ready: http://127.0.0.1:${port}"
        exit 0
    }

    Assert-EiaaxPortAvailable -Port $port -Label "frontend"

    $nodeModules = Join-Path $paths.Frontend "node_modules"
    if (-not (Test-Path -LiteralPath $nodeModules)) {
        Exit-EiaaxFailure -Message "node_modules missing. Run scripts\windows\preparar_demo_eiaax.ps1 first."
    }

    $npmCmd = Resolve-EiaaxNpmCmdExecutable
    if ($npmCmd -match '\.ps1$') {
        Exit-EiaaxFailure -Message ("Refusing npm.ps1 launcher for service start: " + $npmCmd + ". npm.cmd is required.")
    }
    Write-Host ("Using npm executable: " + $npmCmd)
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
    Write-Host ("[frontend] Servicio lanzado (wrapper PID " + $proc.Id + ")")

    Write-Host "[frontend] Esperando puerto $port ..."
    $listenerPid = Wait-EiaaxListenerPid -Port $port -TimeoutSec 60
    if ($null -eq $listenerPid) {
        $failure = New-EiaaxStartupFailureMessage `
            -Summary "Frontend process did not open port 5180 in time." `
            -LogFile $logFile `
            -WrapperPid $proc.Id
        Exit-EiaaxFailure -Message $failure
    }

    if (-not (Test-EiaaxManagedProcess -ProcessId $listenerPid -WorktreeRoot $worktree -ServiceName "frontend")) {
        Exit-EiaaxFailure -Message ("Port 5180 is owned by unexpected PID " + $listenerPid + ". Aborting.")
    }

    Write-EiaaxPidFile -StateDir $stateDir -Name "frontend" -ProcessId $listenerPid
    Write-EiaaxStateValue -StateDir $stateDir -Name "frontend-wrapper" -Value ([string]$proc.Id)

    if (-not (Test-EiaaxFrontendReady -Port $port -TimeoutSec 60)) {
        $failure = New-EiaaxStartupFailureMessage `
            -Summary "Frontend did not respond over HTTP in time." `
            -LogFile $logFile `
            -WrapperPid $proc.Id
        Exit-EiaaxFailure -Message $failure
    }

    Write-Host ("Frontend ready: http://127.0.0.1:${port} (listener PID " + $listenerPid + ")")
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
