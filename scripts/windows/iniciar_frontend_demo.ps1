#Requires -Version 5.1
<#
.SYNOPSIS
    Inicia el frontend EIAAX demo (Vite dev, puerto 5180).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$worktree = Get-EiaaxWorktreeRoot
Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
Test-EiaaxWorktree -WorktreeRoot $worktree
$paths = Get-EiaaxPaths -WorktreeRoot $worktree
$stateDir = Ensure-EiaaxStateDir -WorktreeRoot $worktree

$port = $FrontendPort
$existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($null -ne $existing) {
    throw "Puerto ${port} ya está en uso. Ejecute scripts\windows\detener_demo_eiaax.ps1"
}

if (-not (Test-Path -LiteralPath (Join-Path $paths.Frontend "node_modules"))) {
    throw "node_modules no instalado. Ejecute scripts\windows\preparar_demo_eiaax.ps1"
}

$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($null -eq $npm) {
    throw "npm no encontrado en PATH."
}

$launcherPath = Join-Path $stateDir "run_frontend.ps1"
@(
    "Set-Location -LiteralPath '$($paths.Frontend)'"
    "& npm run dev"
) | Set-Content -LiteralPath $launcherPath -Encoding UTF8

Push-Location $paths.Frontend
try {
    Write-Host "Iniciando frontend en http://127.0.0.1:${port} ..."
    $proc = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $launcherPath) `
        -PassThru `
        -WorkingDirectory $paths.Frontend `
        -WindowStyle Normal

    Write-EiaaxPidFile -StateDir $stateDir -Name "frontend" -ProcessId $proc.Id
    Write-Host "Frontend PID: $($proc.Id)"
    Write-Host "Abrir: http://127.0.0.1:${port}"
}
finally {
    Pop-Location
}
