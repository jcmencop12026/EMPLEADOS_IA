#Requires -Version 5.1
<#
.SYNOPSIS
    Single entry point: prepare and start EIAAX converged candidate on Windows.

.DESCRIPTION
    Uses the certified Windows demo stack (preparar + iniciar) for branch
    cursor/convergencia-comercial-v1-85e4 (SHA 482ff6f, Alembic 1820).

    Default worktree: D:\EMPLEADOS_IA_CONVERGENCIA (does NOT touch D:\EMPLEADOS_IA).
    Override with env EIAAX_WORKTREE before running.

    Rollback to pre-convergence Windows candidate (d034566):
    keep D:\EMPLEADOS_IA_INTEGRADO on tag eiaax-v1-preconvergencia-windows-operativo.

.PARAMETER PrepareOnly
    Run preparation only (venv, deps, seed, alembic verify).

.PARAMETER StartOnly
    Start backend+frontend only (requires prior preparation).

.PARAMETER SkipPrepare
    Skip preparation and start directly (same as StartOnly).
#>

param(
    [switch]$PrepareOnly,
    [switch]$StartOnly,
    [switch]$SkipPrepare
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$prepareScript = Join-Path $PSScriptRoot "preparar_demo_eiaax.ps1"
$startScript = Join-Path $PSScriptRoot "iniciar_demo_eiaax.ps1"
$stopScript = Join-Path $PSScriptRoot "detener_demo_eiaax.ps1"

function Get-EiaaxGitShortSha {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $git) {
        return $null
    }

    Push-Location $WorktreeRoot
    try {
        $sha = (& git rev-parse --short HEAD 2>$null)
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
        return $sha.Trim()
    }
    finally {
        Pop-Location
    }
}

function Confirm-EiaaxConvergenceCandidate {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $sha = Get-EiaaxGitShortSha -WorktreeRoot $WorktreeRoot
    if ([string]::IsNullOrWhiteSpace($sha)) {
        Write-Host "WARNING: git SHA not verified (not a git worktree or git missing)."
        return
    }

    if ($sha -ne $script:ExpectedConvergenceSha) {
        Write-Host ("WARNING: worktree SHA is " + $sha + "; expected convergence " + $script:ExpectedConvergenceSha + ".")
        Write-Host "Continue only if this is intentional."
    }
    else {
        Write-Host ("Convergence candidate SHA OK: " + $sha)
    }
}

try {
    if ([string]::IsNullOrWhiteSpace($env:EIAAX_WORKTREE)) {
        $env:EIAAX_WORKTREE = $script:ConvergenceWorktreeDefault
        Write-Host ("EIAAX_WORKTREE set to: " + $env:EIAAX_WORKTREE)
    }
    else {
        Write-Host ("EIAAX_WORKTREE (existing): " + $env:EIAAX_WORKTREE)
    }

    $worktree = Get-EiaaxWorktreeRoot
    Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
    Test-EiaaxWorktree -WorktreeRoot $worktree
    Confirm-EiaaxConvergenceCandidate -WorktreeRoot $worktree

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "EIAAX CONVERGENCIA COMERCIAL V1 - ARRANQUE WINDOWS"
    Write-Host "============================================================"
    Write-Host ("Worktree: " + $worktree)
    Write-Host ("Alembic head esperado: " + $script:ExpectedAlembicHead)
    Write-Host ("URL final: http://127.0.0.1:" + $FrontendPort)
    Write-Host ("Rollback d034566: D:\EMPLEADOS_IA_INTEGRADO (tag preconvergencia)")
    Write-Host ""

    $doPrepare = (-not $StartOnly) -and (-not $SkipPrepare)
    $doStart = (-not $PrepareOnly)

    if ($doPrepare) {
        Write-Host "PASO 1/2: Preparacion (venv, seed, alembic)..."
        Invoke-EiaaxPowerShellFile -FilePath $prepareScript
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    if ($doStart) {
        Write-Host "PASO 2/2: Arranque backend + frontend..."
        Invoke-EiaaxPowerShellFile -FilePath $startScript
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "EIAAX 482ff6f - LISTO PARA PRUEBA WINDOWS"
    Write-Host "============================================================"
    Write-Host "URL:      http://127.0.0.1:5180"
    Write-Host "Health:   http://127.0.0.1:8000/health"
    Write-Host "Usuario:  org_a_admin"
    Write-Host "Password: ver backend\scripts\credentials.example"
    Write-Host "Detener:  scripts\windows\detener_demo_eiaax.ps1"
    Write-Host "Logs:     logs\demo\"
    Write-Host ""
    Write-Host "Rutas convergencia (recorrido humano):"
    Write-Host "  /centro-estrategico   Centro Estrategico"
    Write-Host "  /demo                 Demo comercial"
    Write-Host "  /evaluaciones         Expedientes"
    Write-Host "  /centro-control       Centro operacional MB-08"
    Write-Host "  /mi-espacio           Portal externo (usuario prospecto)"
    Write-Host ""
    Write-Host "Documentacion: INTERCAMBIO\SALIDA\EIAAX_CONVERGENCIA_COMERCIAL_V1_WINDOWS\"
    Write-Host ""

    try {
        Add-Type -AssemblyName System.Speech -ErrorAction Stop
        $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
        $speaker.Speak("EIAAX convergencia listo para prueba Windows")
    }
    catch {
        # Voice optional.
    }

    exit 0
}
catch {
    Write-EiaaxError -Message $_.Exception.Message
    Write-Host ""
    Write-Host "Arranque abortado. Revise logs\demo\ y la guia en INTERCAMBIO\SALIDA\EIAAX_CONVERGENCIA_COMERCIAL_V1_WINDOWS\"
    exit 1
}
