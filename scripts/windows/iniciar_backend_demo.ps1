#Requires -Version 5.1
<#
.SYNOPSIS
    Inicia el backend EIAAX demo (uvicorn, puerto 8000).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$worktree = Get-EiaaxWorktreeRoot
Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
Test-EiaaxWorktree -WorktreeRoot $worktree
$paths = Get-EiaaxPaths -WorktreeRoot $worktree
$venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree
$databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree
$stateDir = Ensure-EiaaxStateDir -WorktreeRoot $worktree

$port = $BackendPort
$existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($null -ne $existing) {
    throw "Puerto ${port} ya está en uso. Ejecute scripts\windows\detener_demo_eiaax.ps1"
}

$env:DATABASE_URL = $databaseUrl
$launcherPath = Join-Path $stateDir "run_backend.ps1"
@(
    "`$env:DATABASE_URL = '$databaseUrl'"
    "Set-Location -LiteralPath '$($paths.Backend)'"
    "& '$venvPython' -m uvicorn app.main:app --host 127.0.0.1 --port $port"
) | Set-Content -LiteralPath $launcherPath -Encoding UTF8

try {
    Write-Host "Iniciando backend en http://127.0.0.1:${port} ..."
    $proc = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $launcherPath) `
        -PassThru `
        -WorkingDirectory $paths.Backend `
        -WindowStyle Normal

    Write-EiaaxPidFile -StateDir $stateDir -Name "backend" -ProcessId $proc.Id
    Write-Host "Backend PID: $($proc.Id)"

    if (Test-EiaaxHealth -Port $port -TimeoutSec 45) {
        Write-Host "Health OK: http://127.0.0.1:${port}/health"
    }
    else {
        Write-Warning "Backend iniciado pero /health no respondió a tiempo. Revise la ventana del proceso."
    }
}
