#Requires -Version 5.1
<#
.SYNOPSIS
    Single atomic entry point for EIAAX convergence Windows startup.

.DESCRIPTION
    One invocation prepares and certifies the convergence candidate with fail-closed validation:
    - git fetch/checkout/pull for the convergence branch
    - repository branch/manifest
    - Python discovery (reference pyvenv.cfg, py launcher, where.exe, registry, PATH)
    - port/process isolation (stops INTEGRADO demo via official script when needed)
    - seed + Alembic 1820
    - backend/frontend owned by THIS worktree (PID/command validation)
    - runtime identity via /health

    Default worktree: D:\EMPLEADOS_IA_CONVERGENCIA

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File D:\EMPLEADOS_IA_CONVERGENCIA\scripts\windows\arrancar_convergencia_windows.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$prepareScript = Join-Path $PSScriptRoot "preparar_demo_eiaax.ps1"
$startScript = Join-Path $PSScriptRoot "iniciar_demo_eiaax.ps1"
$logFile = $null
$certificationPassed = $false
$failureCause = $null

function Write-EiaaxCertificationFailure {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Cause
    )

    Write-Host ""
    Write-Host "EIAAX — WINDOWS NO CERTIFICADO"
    Write-Host ("CAUSA: " + $Cause)
}

try {
    if ([string]::IsNullOrWhiteSpace($env:EIAAX_WORKTREE)) {
        $env:EIAAX_WORKTREE = $script:ConvergenceWorktreeDefault
    }
    Write-Host ("EIAAX_WORKTREE: " + $env:EIAAX_WORKTREE)

    $worktree = Get-EiaaxWorktreeRoot
    Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
    Test-EiaaxWorktree -WorktreeRoot $worktree

    $manifest = Get-EiaaxConvergenceManifest -ScriptsDir $PSScriptRoot
    Sync-EiaaxConvergenceRepository -WorktreeRoot $worktree -ExpectedBranch $manifest.branch

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

    $referenceCfg = Get-EiaaxReferencePyvenvCfgPath
    if (Test-Path -LiteralPath $referenceCfg) {
        $cfg = Read-EiaaxPyvenvCfg -PyvenvCfgPath $referenceCfg
        $cfgSummary = "reference pyvenv.cfg"
        if (-not [string]::IsNullOrWhiteSpace($cfg.version)) {
            $cfgSummary += " version=" + $cfg.version
        }
        if (-not [string]::IsNullOrWhiteSpace($cfg.home)) {
            $cfgSummary += " home=" + $cfg.home
        }
        Write-Host $cfgSummary
        Write-EiaaxLogLine -LogFile $logFile -Message $cfgSummary
    }
    else {
        Write-Host ("Reference pyvenv.cfg not found at " + $referenceCfg + " (discovery will use other mechanisms).")
    }

    Write-Host ""
    Write-Host "[1/7] Parser PowerShell..."
    Invoke-EiaaxPowerShellParserValidation -ScriptsDir $PSScriptRoot
    Write-Host "Parser PASS"

    Write-Host ""
    Write-Host "[2/7] Puertos y procesos previos..."
    Clear-EiaaxPortsForConvergence -WorktreeRoot $worktree -ScriptsDir $PSScriptRoot
    Write-Host "Ports PASS"

    Write-Host ""
    Write-Host "[3/7] Preparacion (Python base, venv convergencia, seed, Alembic)..."
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
    Write-Host "[4/7] Arranque backend + frontend..."
    Invoke-EiaaxPowerShellFile -FilePath $startScript
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message "Start failed. See logs\demo\"
    }
    Write-Host "Start PASS"

    Write-Host ""
    Write-Host "[5/7] Verificacion PID/comando worktree convergencia..."
    Confirm-EiaaxStartedProcessWorktree -WorktreeRoot $worktree
    Write-Host "Process ownership PASS"

    Write-Host ""
    Write-Host "[6/7] Verificacion Alembic en BD..."
    $venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree
    $databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree
    Confirm-EiaaxAlembicState -VenvPython $venvPython -BackendDir $paths.Backend -DatabaseUrl $databaseUrl
    Write-Host "Alembic PASS"

    Write-Host ""
    Write-Host "[7/7] Verificacion identidad runtime..."
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
    Write-Host ("EIAAX " + $gitSha + " — WINDOWS REAL OPERATIVO")
    Write-Host "============================================================"
    Write-Host "URL:       http://127.0.0.1:5180"
    Write-Host "Health:    http://127.0.0.1:8000/health"
    Write-Host "Usuario:   org_a_admin"
    Write-Host "Password:  DemoA2026!  (ver backend\scripts\credentials.example)"
    Write-Host "Detener:   scripts\windows\detener_demo_eiaax.ps1"
    Write-Host "Logs:      logs\demo\"
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
    $failureCause = $_.Exception.Message
    if ($null -ne $logFile) {
        Write-EiaaxLogLine -LogFile $logFile -Message ("FAILED: " + $failureCause)
    }
    Write-EiaaxError -Message $failureCause
    if (-not $certificationPassed) {
        Write-EiaaxCertificationFailure -Cause $failureCause
        Write-Host "Revise logs\demo\arrancar_convergencia.log y preparar.log"
    }
    exit 1
}
