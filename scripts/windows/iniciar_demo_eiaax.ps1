#Requires -Version 5.1
<#
.SYNOPSIS
    Start backend and frontend for the EIAAX demo.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$backendScript = Join-Path $PSScriptRoot "iniciar_backend_demo.ps1"
$frontendScript = Join-Path $PSScriptRoot "iniciar_frontend_demo.ps1"
$stopScript = Join-Path $PSScriptRoot "detener_demo_eiaax.ps1"

try {
    $worktree = Get-EiaaxWorktreeRoot
    if (-not (Test-EiaaxDemoDatabaseReady -WorktreeRoot $worktree)) {
        Exit-EiaaxFailure -Message "Demo not prepared. Run scripts\windows\preparar_demo_eiaax.ps1 first."
    }

    $backendExitCode = Invoke-EiaaxPowerShellFile -FilePath $backendScript
    if ($backendExitCode -ne 0) {
        exit $backendExitCode
    }

    Start-Sleep -Seconds 2

    $frontendExitCode = Invoke-EiaaxPowerShellFile -FilePath $frontendScript
    if ($frontendExitCode -ne 0) {
        Invoke-EiaaxPowerShellFile -FilePath $stopScript | Out-Null
        exit $frontendExitCode
    }

    if (-not (Test-EiaaxFrontendProxyHealth -Port $FrontendPort -TimeoutSec 30)) {
        Invoke-EiaaxPowerShellFile -FilePath $stopScript | Out-Null
        Exit-EiaaxFailure -Message "Frontend proxy to backend failed on /health."
    }

    Write-Host ""
    Write-Host "EIAAX demo is running."
    Write-Host "URL: http://127.0.0.1:5180"
    Write-Host "Demo user: org_a_admin (password in backend\scripts\credentials.example)"
    Write-Host "Stop: scripts\windows\detener_demo_eiaax.ps1"
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
