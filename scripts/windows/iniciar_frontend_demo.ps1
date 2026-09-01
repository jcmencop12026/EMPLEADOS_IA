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
    $stateDir = Ensure-EiaaxStateDir -WorktreeRoot $worktree

    $port = $FrontendPort
    $existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Exit-EiaaxFailure -Message "Port ${port} is already in use. Run scripts\windows\detener_demo_eiaax.ps1."
    }

    $nodeModules = Join-Path $paths.Frontend "node_modules"
    if (-not (Test-Path -LiteralPath $nodeModules)) {
        Exit-EiaaxFailure -Message "node_modules missing. Run scripts\windows\preparar_demo_eiaax.ps1 first."
    }

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Exit-EiaaxFailure -Message "npm not found in PATH."
    }

    $launcherPath = Join-Path $stateDir "run_frontend.ps1"
    $escapedFrontend = Escape-EiaaxSingleQuoted -Value $paths.Frontend

    Write-EiaaxLauncherFile -Path $launcherPath -Lines @(
        '$ErrorActionPreference = "Stop"'
        ('Set-Location -LiteralPath ''' + $escapedFrontend + '''')
        '& npm run dev'
    )

    Write-Host "Starting frontend at http://127.0.0.1:${port} ..."
    $proc = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $launcherPath) `
        -PassThru `
        -WorkingDirectory $paths.Frontend `
        -WindowStyle Normal

    Write-EiaaxPidFile -StateDir $stateDir -Name "frontend" -ProcessId $proc.Id
    Write-Host "Frontend shell PID: $($proc.Id)"

    if (-not (Test-EiaaxFrontendReady -Port $port -TimeoutSec 45)) {
        Exit-EiaaxFailure -Message "Frontend started but did not respond in time."
    }

    Write-Host "Frontend ready: http://127.0.0.1:${port}"
    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
