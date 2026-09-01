#Requires -Version 5.1
<#
.SYNOPSIS
    Prepare the EIAAX demo: venv, dependencies, SQLite seed, frontend build.
#>

param(
    [switch]$SkipFrontendBuild,
    [switch]$SkipParserValidation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$logFile = $null

try {
    if (-not $SkipParserValidation) {
        Invoke-EiaaxPowerShellParserValidation -ScriptsDir $PSScriptRoot
        $semanticsTest = Join-Path $PSScriptRoot "test_ps_semantics.ps1"
        $discoveryTest = Join-Path $PSScriptRoot "test_python_discovery.ps1"
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $semanticsTest
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message "PowerShell semantics self-test failed."
        }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $discoveryTest
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message "Python discovery self-test failed."
        }
    }

    $worktree = Get-EiaaxWorktreeRoot
    Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
    Test-EiaaxWorktree -WorktreeRoot $worktree
    $paths = Get-EiaaxPaths -WorktreeRoot $worktree
    $databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree
    $logsDir = Ensure-EiaaxLogsDir -WorktreeRoot $worktree
    $logFile = Join-Path $logsDir "preparar.log"

    Write-EiaaxLogLine -LogFile $logFile -Message "Starting EIAAX demo preparation"
    Write-Host "=== EIAAX demo preparation ==="
    Write-Host "Worktree: $worktree"
    Write-Host "DATABASE_URL: $databaseUrl"

    if (-not (Test-Path -LiteralPath $paths.Data)) {
        New-Item -ItemType Directory -Path $paths.Data | Out-Null
    }

    Assert-EiaaxDemoDatabasePath -DbFilePath $paths.DbFile -WorktreeRoot $worktree

    $basePython = Find-EiaaxPython -LogFile $logFile
    Write-Host "Base Python: $basePython"
    $pythonVersion = Get-EiaaxPythonVersionLine -PythonExe $basePython
    Write-Host "Detected: $pythonVersion"
    Write-EiaaxLogLine -LogFile $logFile -Message ("Python base: " + $pythonVersion)

    if (-not (Test-Path -LiteralPath $paths.Venv)) {
        Write-Host "Creating virtualenv at $($paths.Venv)"
        $venvProbeError = Test-EiaaxPythonVenvCapability -PythonExe $basePython -ProbeDirectory $logsDir
        if ($null -ne $venvProbeError) {
            Exit-EiaaxFailure -Message ("PYTHON " + $pythonVersion + " DETECTED BUT INCOMPATIBLE: " + $venvProbeError)
        }
        Invoke-EiaaxNativeCommand -FilePath $basePython -ArgumentList @("-m", "venv", $paths.Venv) `
            -FailureMessage ("PYTHON " + $pythonVersion + " DETECTED BUT INCOMPATIBLE: venv creation failed.")
    }

    $venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree

    Write-Host "Upgrading pip in virtualenv..."
    Invoke-EiaaxNativeCommand -FilePath $venvPython -ArgumentList @("-m", "pip", "install", "--upgrade", "pip", "wheel") `
        -FailureMessage "pip upgrade failed in virtualenv."

    Write-Host "Installing backend dependencies..."
    $requirements = Join-Path $paths.Backend "requirements.txt"
    Invoke-EiaaxNativeCommand -FilePath $venvPython -ArgumentList @("-m", "pip", "install", "-r", $requirements) `
        -FailureMessage ("PYTHON " + $pythonVersion + " DETECTED BUT INCOMPATIBLE: requirements install failed. See logs\demo\preparar.log")

    Write-Host "Verifying backend imports..."
    Test-EiaaxBackendImports -VenvPython $venvPython

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Exit-EiaaxFailure -Message "npm not found in PATH."
    }

    Push-Location $paths.Frontend
    try {
        if (Test-Path -LiteralPath "package-lock.json") {
            Write-Host "Installing frontend dependencies (npm ci)..."
            & npm ci
        }
        else {
            Write-Host "Installing frontend dependencies (npm install)..."
            & npm install
        }
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message "Frontend install failed."
        }

        if (-not $SkipFrontendBuild) {
            Write-Host "Building frontend (npm run build)..."
            & npm run build
            if ($LASTEXITCODE -ne 0) {
                Exit-EiaaxFailure -Message "Frontend build failed."
            }
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "Running demo seed (recreates demo SQLite DB only)..."
    $env:DATABASE_URL = $databaseUrl
    Push-Location $paths.Backend
    try {
        $seedScript = Join-Path $paths.Backend "scripts\seed_lote3_demo.py"
        Invoke-EiaaxNativeCommand -FilePath $venvPython -ArgumentList @($seedScript) `
            -FailureMessage "Demo seed failed."
    }
    finally {
        Pop-Location
    }

    if (-not (Test-Path -LiteralPath $paths.DbFile)) {
        Exit-EiaaxFailure -Message "Demo database file was not created."
    }

    Write-Host "Verifying Alembic state..."
    Confirm-EiaaxAlembicState -VenvPython $venvPython -BackendDir $paths.Backend -DatabaseUrl $databaseUrl

    Write-EiaaxLogLine -LogFile $logFile -Message "Preparation completed successfully"
    Write-Host ""
    Write-Host "EIAAX demo preparation completed successfully."
    Write-Host "Next step: scripts\windows\iniciar_demo_eiaax.ps1"
    Write-Host "URL: http://127.0.0.1:5180"
    Write-Host "Demo user: org_a_admin (password in backend\scripts\credentials.example)"
    exit 0
}
catch {
    if ($null -ne $logFile) {
        Write-EiaaxLogLine -LogFile $logFile -Message ("FAILED: " + $_.Exception.Message)
    }
    Write-EiaaxError -Message $_.Exception.Message
    exit 1
}
