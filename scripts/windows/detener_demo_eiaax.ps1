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

    $managedPids = New-Object System.Collections.Generic.List[int]

    if (Test-Path -LiteralPath $stateDir) {
        foreach ($name in @("backend", "frontend")) {
            $pidValue = Get-EiaaxPidFromFile -StateDir $stateDir -Name $name
            if ($null -ne $pidValue) {
                [void]$managedPids.Add($pidValue)
                Stop-EiaaxManagedPid -ProcessId $pidValue -Label $name -WorktreeRoot $worktree | Out-Null
                $pidFile = Join-Path $stateDir ($name + ".pid")
                Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
            }
        }
    }

    foreach ($port in @($BackendPort, $FrontendPort)) {
        $stopped = Stop-EiaaxListenerOnPort -Port $port -WorktreeRoot $worktree -AllowedPidList $managedPids.ToArray()
        if ($stopped.Count -eq 0) {
            Write-Host "Port ${port}: no managed listener found."
        }
    }

    Write-Host "EIAAX demo services stopped."
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
