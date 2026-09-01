#Requires -Version 5.1
<#
.SYNOPSIS
    Single certified entry point for EIAAX convergence Windows startup.

.DESCRIPTION
    Prepares and starts the convergence candidate with fail-closed validation:
    - repository branch/manifest
    - Python discovery (where.exe, py launcher, registry, PATH)
    - port/process isolation
    - seed + Alembic 1820
    - backend/frontend owned by THIS worktree
    - runtime identity via /health

    Default worktree: D:\EMPLEADOS_IA_CONVERGENCIA
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$prepareScript = Join-Path $PSScriptRoot "preparar_demo_eiaax.ps1"
$startScript = Join-Path $PSScriptRoot "iniciar_demo_eiaax.ps1"
$logFile = $null
$certificationPassed = $false

try {
    if ([string]::IsNullOrWhiteSpace($env:EIAAX_WORKTREE)) {
        $env:EIAAX_WORKTREE = $script:ConvergenceWorktreeDefault
    }
    Write-Host ("EIAAX_WORKTREE: " + $env:EIAAX_WORKTREE)

    $worktree = Get-EiaaxWorktreeRoot
    Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
    Test-EiaaxWorktree -WorktreeRoot $worktree

    $logsDir = Ensure-EiaaxLogsDir -WorktreeRoot $worktree
    $logFile = Join-Path $logsDir "arrancar_convergencia.log"
    Write-EiaaxLogLine -LogFile $logFile -Message "=== Convergence startup begin ==="

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "EIAAX CONVERGENCIA - CERTIFICACION ARRANQUE WINDOWS"
    Write-Host "============================================================"

    $repo = Confirm-EiaaxConvergenceRepository -WorktreeRoot $worktree -ScriptsDir $PSScriptRoot
    $manifest = $repo.Manifest
    $gitSha = $repo.Sha

    if ($manifest.alembic_head -ne $script:ExpectedAlembicHead) {
        Exit-EiaaxFailure -Message ("Manifest alembic_head mismatch with Common.ps1 (" + $manifest.alembic_head + " vs " + $script:ExpectedAlembicHead + ").")
    }

    Write-Host ""
    Write-Host "[1/6] Parser PowerShell..."
    Invoke-EiaaxPowerShellParserValidation -ScriptsDir $PSScriptRoot
    Write-Host "Parser PASS"

    Write-Host ""
    Write-Host "[2/6] Puertos y procesos previos..."
    Clear-EiaaxPortsForConvergence -WorktreeRoot $worktree -ScriptsDir $PSScriptRoot
    Write-Host "Ports PASS"

    Write-Host ""
    Write-Host "[3/6] Preparacion (Python, venv, seed, Alembic)..."
    Invoke-EiaaxPowerShellFile -FilePath $prepareScript
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message "Preparation failed. Aborting before start to avoid false positives."
    }
    Write-Host "Preparation PASS"

    $paths = Get-EiaaxPaths -WorktreeRoot $worktree
    $stateDir = Ensure-EiaaxStateDir -WorktreeRoot $worktree
    Write-EiaaxRuntimeIdentityState `
        -StateDir $stateDir `
        -GitSha $gitSha `
        -DemoProfile $manifest.profile `
        -RuntimeMarker $manifest.runtime_marker
    Write-EiaaxStateValue -StateDir $stateDir -Name "certification_started_at" -Value ((Get-Date).ToString("o"))

    Write-Host ""
    Write-Host "[4/6] Arranque backend + frontend..."
    Invoke-EiaaxPowerShellFile -FilePath $startScript
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message "Start failed. See logs\\demo\\"
    }
    Write-Host "Start PASS"

    Write-Host ""
    Write-Host "[5/6] Verificacion Alembic en BD..."
    $venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree
    $databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree
    Confirm-EiaaxAlembicState -VenvPython $venvPython -BackendDir $paths.Backend -DatabaseUrl $databaseUrl
    Write-Host "Alembic PASS"

    Write-Host ""
    Write-Host "[6/6] Verificacion identidad runtime..."
    Confirm-EiaaxRuntimeIdentity `
        -ExpectedGitSha $gitSha `
        -ExpectedAlembicHead $manifest.alembic_head `
        -ExpectedDemoProfile $manifest.profile `
        -ExpectedRuntimeMarker $manifest.runtime_marker `
        -ExpectedDemoDbName $manifest.demo_db_name

    $certificationPassed = $true
    Write-EiaaxStateValue -StateDir $stateDir -Name "certification_passed" -Value "true"
    Write-EiaaxStateValue -StateDir $stateDir -Name "certification_completed_at" -Value ((Get-Date).ToString("o"))
    Write-EiaaxLogLine -LogFile $logFile -Message "=== Convergence startup PASS ==="

    Write-Host ""
    Write-Host "============================================================"
    Write-Host ("EIAAX " + $gitSha + " - WINDOWS REAL OPERATIVO")
    Write-Host "============================================================"
    Write-Host "URL:       http://127.0.0.1:5180"
    Write-Host "Health:    http://127.0.0.1:8000/health"
    Write-Host "Usuario:   org_a_admin"
    Write-Host "Password:  DemoA2026!  (ver backend\\scripts\\credentials.example)"
    Write-Host "Detener:   scripts\\windows\\detener_demo_eiaax.ps1"
    Write-Host "Logs:      logs\\demo\\"
    Write-Host ("BD:        " + $paths.DbFile)
    Write-Host ""

    try {
        Add-Type -AssemblyName System.Speech -ErrorAction Stop
        $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
        $speaker.Speak("EIAAX convergencia Windows real operativo")
    }
    catch {
        # Voice optional.
    }

    exit 0
}
catch {
    if ($null -ne $logFile) {
        Write-EiaaxLogLine -LogFile $logFile -Message ("FAILED: " + $_.Exception.Message)
    }
    Write-EiaaxError -Message $_.Exception.Message
    Write-Host ""
    if (-not $certificationPassed) {
        Write-Host "CERTIFICACION ABORTADA - NO declarar candidato operativo."
        Write-Host "Revise logs\\demo\\arrancar_convergencia.log y preparar.log"
    }
    exit 1
}
