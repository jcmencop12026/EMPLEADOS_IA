#Requires -Version 5.1
<#
.SYNOPSIS
    Single atomic entry point for EIAAX convergence Windows startup.

.DESCRIPTION
    One invocation prepares and certifies the convergence candidate with fail-closed validation:
    - bootstrap git self-update before loading Common.ps1 (safe on stderr, exit-code authority)
    - git fetch/checkout/pull --ff-only for the convergence branch
    - repository branch/manifest
    - Python discovery (reference pyvenv.cfg, py launcher, where.exe, registry, PATH)
    - port/process isolation (stops INTEGRADO demo via official script when needed)
    - seed + Alembic 1831
    - backend/frontend owned by THIS worktree (PID/command validation)
    - runtime identity via /health

    Default worktree: D:\EMPLEADOS_IA_CONVERGENCIA

.EXAMPLE
    Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
    powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
#>

function Invoke-EiaaxBootstrapGitCommand {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [string[]]$ArgumentList,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $locationPushed = $false
    try {
        Push-Location $WorkingDirectory
        $locationPushed = $true
        $rawOutput = & git @ArgumentList 2>&1
        $exitCode = $LASTEXITCODE
        $output = ""
        if ($null -ne $rawOutput) {
            $output = (($rawOutput | ForEach-Object {
                if ($_ -is [System.Management.Automation.ErrorRecord]) {
                    $_.ToString()
                }
                else {
                    [string]$_
                }
            }) -join "`n").Trim()
        }
        return [ordered]@{
            ExitCode = $exitCode
            Output   = $output
        }
    }
    finally {
        if ($locationPushed) {
            Pop-Location
        }
        $ErrorActionPreference = $previousPreference
    }
}

function Invoke-EiaaxBootstrapRepositorySync {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    $manifestPath = Join-Path $ScriptsDir "eiaax_convergence_manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        Write-Host ("ERROR: Missing convergence manifest: " + $manifestPath)
        exit 1
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $expectedBranch = [string]$manifest.branch
    $worktree = (Resolve-Path -LiteralPath (Join-Path $ScriptsDir "..\..")).Path
    $folderName = [System.IO.Path]::GetFileName($worktree.TrimEnd('\'))

    if ($folderName -ne "EMPLEADOS_IA_CONVERGENCIA") {
        Write-Host ("ERROR: Bootstrap requires EMPLEADOS_IA_CONVERGENCIA worktree. Resolved: " + $worktree)
        exit 1
    }

    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $git) {
        Write-Host "ERROR: git not found in PATH."
        exit 1
    }

    $shaBeforeResult = Invoke-EiaaxBootstrapGitCommand `
        -ArgumentList @("rev-parse", "--short", "HEAD") `
        -WorkingDirectory $worktree
    $shaBefore = $shaBeforeResult.Output

    $steps = @(
        @{ Label = "git fetch"; Args = @("fetch", "origin", $expectedBranch) },
        @{ Label = "git checkout"; Args = @("checkout", $expectedBranch) },
        @{ Label = "git pull --ff-only"; Args = @("pull", "--ff-only", "origin", $expectedBranch) }
    )

    foreach ($step in $steps) {
        $result = Invoke-EiaaxBootstrapGitCommand -ArgumentList $step.Args -WorkingDirectory $worktree
        if ($result.ExitCode -ne 0) {
            Write-Host ("ERROR: Bootstrap " + $step.Label + " failed with exit code " + $result.ExitCode)
            if (-not [string]::IsNullOrWhiteSpace($result.Output)) {
                Write-Host $result.Output
            }
            exit 1
        }
    }

    $shaAfterResult = Invoke-EiaaxBootstrapGitCommand `
        -ArgumentList @("rev-parse", "--short", "HEAD") `
        -WorkingDirectory $worktree
    $shaAfter = $shaAfterResult.Output

    return [ordered]@{
        Worktree  = $worktree
        ShaBefore = $shaBefore
        ShaAfter  = $shaAfter
    }
}

if ([string]::IsNullOrWhiteSpace($env:EIAAX_BOOTSTRAP_REEXEC)) {
    $bootstrap = Invoke-EiaaxBootstrapRepositorySync -ScriptsDir $PSScriptRoot
    if ($bootstrap.ShaBefore -ne $bootstrap.ShaAfter) {
        Write-Host ("Bootstrap updated repository: " + $bootstrap.ShaBefore + " -> " + $bootstrap.ShaAfter)
        $env:EIAAX_BOOTSTRAP_REEXEC = "1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath
        exit $LASTEXITCODE
    }
    Remove-Item Env:EIAAX_BOOTSTRAP_REEXEC -ErrorAction SilentlyContinue
}

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
        [string]$Cause,
        [string]$LogPath = $null
    )

    Write-Host ""
    Write-Host "EIAAX — WINDOWS NO CERTIFICADO"
    Write-Host ("ETAPA: " + (Get-EiaaxStage))
    Write-Host ("CAUSA: " + $Cause)
    if (-not [string]::IsNullOrWhiteSpace($LogPath)) {
        Write-Host ("LOG: " + $LogPath)
    }
}

try {
    Set-EiaaxStage -Name "inicio"
    $worktree = Initialize-EiaaxConvergenceWorktreeFromScriptRoot -ScriptsDir $PSScriptRoot
    Test-EiaaxWorktree -WorktreeRoot $worktree

    $logsDir = Ensure-EiaaxLogsDir -WorktreeRoot $worktree
    $logFile = Join-Path $logsDir "arrancar_convergencia.log"
    Write-EiaaxLogLine -LogFile $logFile -Message "=== Convergence startup begin ==="

    Assert-EiaaxConvergencePathAuthority -WorktreeRoot $worktree -LogFile $logFile
    Write-EiaaxConvergenceExecutionContext -WorktreeRoot $worktree -LogFile $logFile

    $manifest = Get-EiaaxConvergenceManifest -ScriptsDir $PSScriptRoot
    $initialBranch = Get-EiaaxGitBranchName -WorktreeRoot $worktree
    $initialSha = Get-EiaaxGitShortSha -WorktreeRoot $worktree
    Write-Host ("Rama inicial: " + $initialBranch)
    Write-Host ("Codigo activo SHA (pre-sync): " + $initialSha)
    Write-EiaaxLogLine -LogFile $logFile -Message ("Pre-sync branch=" + $initialBranch + " sha=" + $initialSha)

    Set-EiaaxStage -Name "sincronizacion_git"
    Sync-EiaaxConvergenceRepository -WorktreeRoot $worktree -ExpectedBranch $manifest.branch -LogFile $logFile

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "EIAAX CONVERGENCIA - CERTIFICACION ARRANQUE WINDOWS"
    Write-Host "============================================================"

    Set-EiaaxStage -Name "validacion_repositorio"
    $repo = Confirm-EiaaxConvergenceRepository -WorktreeRoot $worktree -ScriptsDir $PSScriptRoot
    $manifest = $repo.Manifest
    $gitSha = $repo.Sha
    Write-Host ("Codigo activo SHA: " + $gitSha)
    Write-EiaaxLogLine -LogFile $logFile -Message ("Active code SHA: " + $gitSha)

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

    Set-EiaaxStage -Name "parser_powershell"
    Write-Host ""
    Write-Host "[1/7] Parser PowerShell..."
    $bomUpdates = @(Ensure-EiaaxWindowsScriptsUtf8Bom -ScriptsDir $PSScriptRoot)
    if ($bomUpdates.Count -gt 0) {
        Write-Host ("Normalized UTF-8 BOM for: " + ($bomUpdates -join ", "))
        Write-EiaaxLogLine -LogFile $logFile -Message ("UTF-8 BOM normalized: " + ($bomUpdates -join ", "))
    }
    Invoke-EiaaxPowerShellParserValidation -ScriptsDir $PSScriptRoot
    Write-Host "Parser PASS"

    Set-EiaaxStage -Name "puertos_procesos"
    Write-Host ""
    Write-Host "[2/7] Puertos y procesos previos..."
    Clear-EiaaxPortsForConvergence -WorktreeRoot $worktree -ScriptsDir $PSScriptRoot
    Write-Host "Ports PASS"

    Set-EiaaxStage -Name "preparacion_python_venv"
    Write-Host ""
    Write-Host "[3/7] Preparacion (Python base, venv convergencia, seed, Alembic)..."
    $prepareExitCode = Invoke-EiaaxPowerShellFile -FilePath $prepareScript -TimeoutSec 7200
    if ($prepareExitCode -eq 124) {
        Exit-EiaaxFailure -Message "Preparation timed out after 7200 seconds."
    }
    if ($prepareExitCode -ne 0) {
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

    Set-EiaaxStage -Name "arranque_backend_frontend"
    Write-Host ""
    Write-Host "[4/7] Arranque backend + frontend..."
    $startExitCode = Invoke-EiaaxScriptInProcess -FilePath $startScript
    if ($startExitCode -ne 0) {
        Exit-EiaaxFailure -Message "Start failed. See logs\demo\"
    }
    Write-Host "Start PASS"

    Set-EiaaxStage -Name "verificacion_pid_worktree"
    Write-Host ""
    Write-Host "[5/7] Verificacion PID/comando worktree convergencia..."
    Confirm-EiaaxStartedProcessWorktree -WorktreeRoot $worktree
    Write-Host "Process ownership PASS"

    Set-EiaaxStage -Name "verificacion_alembic"
    Write-Host ""
    Write-Host "[6/7] Verificacion Alembic en BD..."
    $venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree
    $databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree
    Confirm-EiaaxAlembicState -VenvPython $venvPython -BackendDir $paths.Backend -DatabaseUrl $databaseUrl
    Write-Host "Alembic PASS"

    Set-EiaaxStage -Name "verificacion_runtime_identity"
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
        Write-EiaaxLogLine -LogFile $logFile -Message ("FAILED [" + (Get-EiaaxStage) + "]: " + $failureCause)
    }
    Write-EiaaxError -Message $failureCause
    if (-not $certificationPassed) {
        Write-EiaaxCertificationFailure -Cause $failureCause -LogPath $logFile
        if ($null -ne $logFile) {
            Write-Host ("Revise " + $logFile + " y preparar.log")
        }
        else {
            Write-Host "Revise logs\demo\arrancar_convergencia.log y preparar.log"
        }
    }
    exit 1
}
