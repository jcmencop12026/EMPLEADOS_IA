#Requires -Version 5.1
<#
.SYNOPSIS
    Stop only the EIAAX demo backend and frontend processes.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

try {
    $worktree = Get-EiaaxWorktreeRoot
    $paths = Get-EiaaxPaths -WorktreeRoot $worktree
    $stateDir = $paths.State

    Write-Host "=== EIAAX demo stop ==="

    if (Test-Path -LiteralPath $stateDir) {
        foreach ($name in @("backend", "frontend")) {
            $pidValue = Get-EiaaxPidFromFile -StateDir $stateDir -Name $name
            if ($null -ne $pidValue) {
                Stop-EiaaxManagedPid -ProcessId $pidValue -Label $name -WorktreeRoot $worktree -ServiceName $name | Out-Null
            }

            $wrapperName = $name + "-wrapper"
            $wrapperPidText = Get-EiaaxStateValue -StateDir $stateDir -Name $wrapperName
            if (-not [string]::IsNullOrWhiteSpace($wrapperPidText) -and $wrapperPidText -match '^\d+$') {
                $wrapperPid = [int]$wrapperPidText
                $wrapperProc = Get-Process -Id $wrapperPid -ErrorAction SilentlyContinue
                if ($null -ne $wrapperProc) {
                    Stop-Process -Id $wrapperPid -Force -ErrorAction SilentlyContinue
                }
            }

            $pidFile = Join-Path $stateDir ($name + ".txt")
            Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
            $wrapperFile = Join-Path $stateDir ($wrapperName + ".txt")
            Remove-Item -LiteralPath $wrapperFile -ErrorAction SilentlyContinue
        }
    }

    foreach ($port in @($BackendPort, $FrontendPort)) {
        $listener = Get-EiaaxListenerPid -Port $port
        if ($null -eq $listener) {
            Write-Host ("Port " + $port + ": no listener.")
            continue
        }
        $serviceName = if ($port -eq $BackendPort) { "backend" } else { "frontend" }
        if (Test-EiaaxManagedProcess -ProcessId $listener -WorktreeRoot $worktree -ServiceName $serviceName) {
            Stop-EiaaxManagedPid -ProcessId $listener -Label $serviceName -WorktreeRoot $worktree -ServiceName $serviceName | Out-Null
        }
        else {
            Write-Host ("Port " + $port + " still used by external PID " + $listener + "; left untouched.")
        }
    }

    Write-Host "EIAAX demo services stopped."
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
