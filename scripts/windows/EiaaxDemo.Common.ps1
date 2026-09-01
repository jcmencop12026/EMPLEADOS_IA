#Requires -Version 5.1
<#
.SYNOPSIS
    Shared helpers for the EIAAX Windows SQLite demo.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:DefaultWorktree = "D:\EMPLEADOS_IA_INTEGRADO"
$script:BackendPort = 8000
$script:FrontendPort = 5180
$script:VenvDirName = ".venv-eiaax-demo"
$script:StateDirName = ".eiaax-demo"
$script:DemoDbFileName = "eiaax_integrado_demo.db"

function Write-EiaaxError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Exit-EiaaxFailure {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    Write-EiaaxError -Message $Message
    exit 1
}

function Get-EiaaxWorktreeRoot {
    $root = $env:EIAAX_WORKTREE
    if ([string]::IsNullOrWhiteSpace($root)) {
        $root = $script:DefaultWorktree
    }
    if (-not (Test-Path -LiteralPath $root)) {
        Exit-EiaaxFailure -Message "Worktree not found: $root"
    }
    return (Resolve-Path -LiteralPath $root).Path
}

function Get-EiaaxPaths {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $backend = Join-Path $WorktreeRoot "backend"
    $frontend = Join-Path $WorktreeRoot "frontend"
    $data = Join-Path $WorktreeRoot "data"
    $venv = Join-Path $WorktreeRoot $script:VenvDirName
    $state = Join-Path $WorktreeRoot $script:StateDirName
    $dbFile = Join-Path $data $script:DemoDbFileName

    return [ordered]@{
        WorktreeRoot = $WorktreeRoot
        Backend      = $backend
        Frontend     = $frontend
        Data         = $data
        Venv         = $venv
        State        = $state
        DbFile       = $dbFile
    }
}

function ConvertTo-SqliteDatabaseUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DbFilePath
    )

    $fullPath = [System.IO.Path]::GetFullPath($DbFilePath)
    $posix = $fullPath -replace '\\', '/'
    return "sqlite:///$posix"
}

function Get-EiaaxDatabaseUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    Assert-EiaaxDemoDatabasePath -DbFilePath $paths.DbFile
    return ConvertTo-SqliteDatabaseUrl -DbFilePath $paths.DbFile
}

function Assert-EiaaxDemoDatabasePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DbFilePath
    )

    $fullDb = [System.IO.Path]::GetFullPath($DbFilePath)
    $fileName = [System.IO.Path]::GetFileName($fullDb)
    if ($fileName -ne $script:DemoDbFileName) {
        Exit-EiaaxFailure -Message "Unsafe demo DB file name: $fileName"
    }

    $dataDir = [System.IO.Path]::GetDirectoryName($fullDb)
    $dataDirName = [System.IO.Path]::GetFileName($dataDir)
    if ($dataDirName -ne "data") {
        Exit-EiaaxFailure -Message "Unsafe demo DB directory: $dataDir"
    }

    $worktree = [System.IO.Path]::GetDirectoryName($dataDir)
    $worktreeName = [System.IO.Path]::GetFileName($worktree)
    if ($worktreeName -eq "EMPLEADOS_IA") {
        Exit-EiaaxFailure -Message "Refusing demo DB under D:\EMPLEADOS_IA. Use D:\EMPLEADOS_IA_INTEGRADO."
    }
}

function Test-EiaaxWorktree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    foreach ($required in @($paths.Backend, $paths.Frontend)) {
        if (-not (Test-Path -LiteralPath $required)) {
            Exit-EiaaxFailure -Message "Required path not found: $required"
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $paths.Backend "requirements.txt"))) {
        Exit-EiaaxFailure -Message "Missing backend\requirements.txt"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $paths.Frontend "package.json"))) {
        Exit-EiaaxFailure -Message "Missing frontend\package.json"
    }
}

function Assert-EiaaxNotOriginalTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $normalized = ($WorktreeRoot.TrimEnd('\') + '\').ToUpperInvariant()
    if ($normalized -eq "D:\EMPLEADOS_IA\") {
        Exit-EiaaxFailure -Message "Refusing to operate on D:\EMPLEADOS_IA. Use D:\EMPLEADOS_IA_INTEGRADO or EIAAX_WORKTREE."
    }
}

function Invoke-EiaaxNativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,
        [string]$FailureMessage = "Command failed."
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message $FailureMessage
    }
}

function Get-EiaaxPythonVersionLine {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    $output = & $PythonExe -c 'import sys; print(sys.version)' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message "Python is not executable: $PythonExe"
    }
    return ($output | Out-String).Trim()
}

function Find-EiaaxPython {
    $candidates = New-Object System.Collections.Generic.List[string]
    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        [void]$candidates.Add($env:EIAAX_PYTHON)
    }
    foreach ($path in @(
            "C:\Python314\python.exe",
            "C:\Python313\python.exe",
            "C:\Python312\python.exe"
        )) {
        [void]$candidates.Add($path)
    }

    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        foreach ($version in @("3.14", "3.13", "3.12")) {
            $versioned = & py "-$version" -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($versioned)) {
                return $versioned.Trim()
            }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        return $python.Source
    }

    Exit-EiaaxFailure -Message "No compatible Python found. Install Python 3.12+ or set EIAAX_PYTHON."
}

function Get-EiaaxVenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    $venvPython = Join-Path $paths.Venv "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Exit-EiaaxFailure -Message "Virtualenv missing. Run scripts\windows\preparar_demo_eiaax.ps1 first."
    }
    return $venvPython
}

function Test-EiaaxDemoDatabaseReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    Assert-EiaaxDemoDatabasePath -DbFilePath $paths.DbFile
    return (Test-Path -LiteralPath $paths.DbFile)
}

function Ensure-EiaaxStateDir {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    if (-not (Test-Path -LiteralPath $paths.State)) {
        New-Item -ItemType Directory -Path $paths.State | Out-Null
    }
    return $paths.State
}

function Write-EiaaxLauncherFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string[]]$Lines
    )

    $content = ($Lines -join [Environment]::NewLine) + [Environment]::NewLine
    $utf8Bom = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($Path, $content, $utf8Bom)
}

function Write-EiaaxPidFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    $file = Join-Path $StateDir ($Name + ".pid")
    Set-Content -LiteralPath $file -Value $ProcessId -Encoding ascii
}

function Get-EiaaxPidFromFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $file = Join-Path $StateDir ($Name + ".pid")
    if (-not (Test-Path -LiteralPath $file)) {
        return $null
    }
    $raw = (Get-Content -LiteralPath $file -Raw).Trim()
    if ($raw -match '^\d+$') {
        return [int]$raw
    }
    return $null
}

function Test-EiaaxManagedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        return $false
    }

    try {
        $commandLine = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $ProcessId)).CommandLine
    }
    catch {
        return $true
    }

    if ([string]::IsNullOrWhiteSpace($commandLine)) {
        return $true
    }

    $normalizedWorktree = $WorktreeRoot.ToUpperInvariant()
    $normalizedCommand = $commandLine.ToUpperInvariant()
    return (
        $normalizedCommand.Contains($normalizedWorktree) -or
        $normalizedCommand.Contains("UVICORN APP.MAIN:APP") -or
        $normalizedCommand.Contains("RUN_FRONTEND.PS1") -or
        $normalizedCommand.Contains("RUN_BACKEND.PS1") -or
        $normalizedCommand.Contains("VITE")
    )
}

function Stop-EiaaxManagedPid {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId,
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    if (-not (Test-EiaaxManagedProcess -ProcessId $ProcessId -WorktreeRoot $WorktreeRoot)) {
        Write-Host "Skipping PID ${ProcessId} for ${Label}; not managed by EIAAX demo."
        return $false
    }

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        return $false
    }

    Write-Host "Stopping ${Label} (PID ${ProcessId})"
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    return $true
}

function Stop-EiaaxListenerOnPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string[]]$AllowedPidList
    )

    $stopped = @()
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $procId = [int]$conn.OwningProcess
        if ($procId -le 0) {
            continue
        }
        if ($AllowedPidList -notcontains $procId) {
            if (-not (Test-EiaaxManagedProcess -ProcessId $procId -WorktreeRoot $WorktreeRoot)) {
                Write-Host "Port ${Port} is used by PID ${procId}; leaving it untouched."
                continue
            }
        }
        Write-Host "Stopping PID ${procId} listening on port ${Port}"
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        $stopped += $procId
    }
    return $stopped
}

function Test-EiaaxHealth {
    param(
        [int]$Port = $script:BackendPort,
        [int]$TimeoutSec = 45
    )

    $uri = "http://127.0.0.1:${Port}/health"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Test-EiaaxFrontendReady {
    param(
        [int]$Port = $script:FrontendPort,
        [int]$TimeoutSec = 45
    )

    $uri = "http://127.0.0.1:${Port}/"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Escape-EiaaxSingleQuoted {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )
    return $Value.Replace("'", "''")
}
