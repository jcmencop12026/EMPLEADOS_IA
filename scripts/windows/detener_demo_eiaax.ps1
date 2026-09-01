#Requires -Version 5.1
<#
.SYNOPSIS
    Detiene backend y frontend de la demo EIAAX de forma limpia.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$worktree = Get-EiaaxWorktreeRoot
$paths = Get-EiaaxPaths -WorktreeRoot $worktree
$stateDir = $paths.State

Write-Host "=== EIAAX demo — detención ==="

if (Test-Path -LiteralPath $stateDir) {
    foreach ($name in @("backend", "frontend")) {
        $pidValue = Get-EiaaxPidFromFile -StateDir $stateDir -Name $name
        if ($null -ne $pidValue) {
            Stop-EiaaxPidIfRunning -ProcessId $pidValue -Label $name | Out-Null
            Remove-Item -LiteralPath (Join-Path $stateDir "${name}.pid") -ErrorAction SilentlyContinue
        }
    }
}

foreach ($port in @($BackendPort, $FrontendPort)) {
    $stopped = Stop-ListenerOnPort -Port $port
    if ($stopped.Count -eq 0) {
        Write-Host "Puerto ${port}: sin procesos en escucha."
    }
}

Write-Host "Servicios demo detenidos."
