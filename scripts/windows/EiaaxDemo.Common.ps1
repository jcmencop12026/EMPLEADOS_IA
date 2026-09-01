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
$script:StateDirName = ".runtime-eiaax-demo"
$script:LogsDirName = "logs\demo"
$script:DemoDbFileName = "eiaax_integrado_demo.db"
$script:ExpectedAlembicHead = "1770a1b2c3d4e"

$script:ForbiddenWorktreeNames = @(
    "EMPLEADOS_IA",
    "EMPLEADOS_IA_CERT",
    "EMPLEADOS_IA_V1_HOTFIX"
)

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
    $logs = Join-Path $WorktreeRoot $script:LogsDirName
    $dbFile = Join-Path $data $script:DemoDbFileName

    return [ordered]@{
        WorktreeRoot = $WorktreeRoot
        Backend      = $backend
        Frontend     = $frontend
        Data         = $data
        Venv         = $venv
        State        = $state
        Logs         = $logs
        DbFile       = $dbFile
    }
}

function Ensure-EiaaxLogsDir {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    if (-not (Test-Path -LiteralPath $paths.Logs)) {
        New-Item -ItemType Directory -Path $paths.Logs | Out-Null
    }
    return $paths.Logs
}

function Write-EiaaxLogLine {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LogFile,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $line = (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " " + $Message
    Add-Content -LiteralPath $LogFile -Value $line -Encoding ascii
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
    Assert-EiaaxDemoDatabasePath -DbFilePath $paths.DbFile -WorktreeRoot $WorktreeRoot
    return ConvertTo-SqliteDatabaseUrl -DbFilePath $paths.DbFile
}

function Assert-EiaaxDemoDatabasePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DbFilePath,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $fullDb = [System.IO.Path]::GetFullPath($DbFilePath)
    $fileName = [System.IO.Path]::GetFileName($fullDb)
    if ($fileName -ne $script:DemoDbFileName) {
        Exit-EiaaxFailure -Message "Unsafe demo DB file name: $fileName"
    }

    $dataDir = [System.IO.Path]::GetDirectoryName($fullDb)
    $expectedDataDir = [System.IO.Path]::GetFullPath((Join-Path $WorktreeRoot "data"))
    if ($dataDir.ToUpperInvariant() -ne $expectedDataDir.ToUpperInvariant()) {
        Exit-EiaaxFailure -Message "Unsafe demo DB directory: $dataDir"
    }
}

function Assert-EiaaxNotOriginalTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $folderName = [System.IO.Path]::GetFileName($WorktreeRoot.TrimEnd('\'))
    if ($script:ForbiddenWorktreeNames -contains $folderName) {
        Exit-EiaaxFailure -Message "Refusing to operate on forbidden worktree: $WorktreeRoot"
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

    $output = & $PythonExe -V 2>&1
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message "Python is not executable: $PythonExe"
    }
    return ($output | Out-String).Trim()
}

function Find-EiaaxPython {
    $candidates = New-Object System.Collections.Generic.List[string]

    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        if (-not (Test-Path -LiteralPath $env:EIAAX_PYTHON)) {
            Exit-EiaaxFailure -Message "EIAAX_PYTHON path does not exist: $env:EIAAX_PYTHON"
        }
        return (Resolve-Path -LiteralPath $env:EIAAX_PYTHON).Path
    }

    $knownPaths = @(
        "C:\Python314\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($path in $knownPaths) {
        if (Test-Path -LiteralPath $path) {
            [void]$candidates.Add((Resolve-Path -LiteralPath $path).Path)
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        foreach ($version in @("3.14", "3.13", "3.12")) {
            $versioned = & py "-$version" -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($versioned)) {
                $resolved = $versioned.Trim()
                if (Test-Path -LiteralPath $resolved) {
                    [void]$candidates.Add($resolved)
                }
            }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python -and (Test-Path -LiteralPath $python.Source)) {
        [void]$candidates.Add($python.Source)
    }

    if ($candidates.Count -eq 0) {
        Exit-EiaaxFailure -Message "No Python executable found. Set EIAAX_PYTHON to a valid python.exe path."
    }

    return $candidates[0]
}

function Test-EiaaxBackendImports {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvPython
    )

    Invoke-EiaaxNativeCommand -FilePath $VenvPython -ArgumentList @(
        '-c', 'import fastapi, sqlalchemy, alembic, uvicorn, bcrypt, jose'
    ) -FailureMessage "PYTHON 3.14 INCOMPATIBLE or backend requirements incomplete. Set EIAAX_PYTHON to a supported version."
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
    Assert-EiaaxDemoDatabasePath -DbFilePath $paths.DbFile -WorktreeRoot $WorktreeRoot
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

function Write-EiaaxStateValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $file = Join-Path $StateDir ($Name + ".txt")
    Set-Content -LiteralPath $file -Value $Value -Encoding ascii
}

function Get-EiaaxStateValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $file = Join-Path $StateDir ($Name + ".txt")
    if (-not (Test-Path -LiteralPath $file)) {
        return $null
    }
    return (Get-Content -LiteralPath $file -Raw).Trim()
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

    Write-EiaaxStateValue -StateDir $StateDir -Name $Name -Value ([string]$ProcessId)
}

function Get-EiaaxPidFromFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $raw = Get-EiaaxStateValue -StateDir $StateDir -Name $Name
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return $null
    }
    if ($raw -match '^\d+$') {
        return [int]$raw
    }
    return $null
}

function Get-EiaaxListenerPid {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($null -eq $connections) {
        return $null
    }
    $first = $connections | Select-Object -First 1
    if ($null -eq $first) {
        return $null
    }
    return [int]$first.OwningProcess
}

function Test-EiaaxPortAvailable {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listener = Get-EiaaxListenerPid -Port $Port
    return ($null -eq $listener)
}

function Assert-EiaaxPortAvailable {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $listener = Get-EiaaxListenerPid -Port $Port
    if ($null -ne $listener) {
        Exit-EiaaxFailure -Message ("Port " + $Port + " is already in use by PID " + $listener + " (" + $Label + "). Stop the conflicting process manually or choose another environment.")
    }
}

function Get-EiaaxProcessCommandLine {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    try {
        $process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $ProcessId) -ErrorAction Stop
        return $process.CommandLine
    }
    catch {
        return $null
    }
}

function Test-EiaaxManagedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string]$ServiceName
    )

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        return $false
    }

    $commandLine = Get-EiaaxProcessCommandLine -ProcessId $ProcessId
    if ([string]::IsNullOrWhiteSpace($commandLine)) {
        return $false
    }

    $normalizedWorktree = $WorktreeRoot.ToUpperInvariant()
    $normalizedCommand = $commandLine.ToUpperInvariant()

    if (-not $normalizedCommand.Contains($normalizedWorktree)) {
        return $false
    }

    if ($ServiceName -eq "backend") {
        return $normalizedCommand.Contains("UVICORN") -and $normalizedCommand.Contains("APP.MAIN:APP")
    }

    if ($ServiceName -eq "frontend") {
        return $normalizedCommand.Contains("VITE") -or $normalizedCommand.Contains("NPM.CMD") -or $normalizedCommand.Contains("NODE.EXE")
    }

    return $false
}

function Start-EiaaxManagedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$LogFile,
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$WrapperName,
        [hashtable]$Environment = @{}
    )

    $wrapperBat = Join-Path $StateDir ($WrapperName + ".bat")
    $lines = New-Object System.Collections.Generic.List[string]
    [void]$lines.Add("@echo off")
    foreach ($key in $Environment.Keys) {
        [void]$lines.Add("set " + $key + "=" + $Environment[$key])
    }
    [void]$lines.Add("cd /d """ + $WorkingDirectory + """")

    $commandParts = New-Object System.Collections.Generic.List[string]
    [void]$commandParts.Add('"' + $FilePath + '"')
    foreach ($arg in $ArgumentList) {
        [void]$commandParts.Add($arg)
    }
    $command = ($commandParts -join ' ')
    [void]$lines.Add($command + ' >> "' + $LogFile + '" 2>>&1')

    [System.IO.File]::WriteAllLines($wrapperBat, $lines.ToArray())

    return Start-Process -FilePath $wrapperBat -WorkingDirectory $WorkingDirectory -PassThru -WindowStyle Hidden
}

function Wait-EiaaxListenerPid {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [int]$TimeoutSec = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $listener = Get-EiaaxListenerPid -Port $Port
        if ($null -ne $listener) {
            return $listener
        }
        Start-Sleep -Seconds 1
    }
    return $null
}

function Stop-EiaaxManagedPid {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId,
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string]$ServiceName
    )

    if (-not (Test-EiaaxManagedProcess -ProcessId $ProcessId -WorktreeRoot $WorktreeRoot -ServiceName $ServiceName)) {
        Write-Host ("Skipping PID " + $ProcessId + " for " + $Label + "; not managed by EIAAX demo.")
        return $false
    }

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        return $false
    }

    Write-Host ("Stopping " + $Label + " (PID " + $ProcessId + ")")
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    return $true
}

function Test-EiaaxHealth {
    param(
        [int]$Port = $script:BackendPort,
        [int]$TimeoutSec = 45
    )

    $uri = "http://127.0.0.1:" + $Port + "/health"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200 -and $response.Content -match '"status"\s*:\s*"up"') {
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

    $uri = "http://127.0.0.1:" + $Port + "/"
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

function Test-EiaaxFrontendProxyHealth {
    param(
        [int]$Port = $script:FrontendPort,
        [int]$TimeoutSec = 45
    )

    $uri = "http://127.0.0.1:" + $Port + "/health"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200 -and $response.Content -match '"status"\s*:\s*"up"') {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Confirm-EiaaxAlembicState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvPython,
        [Parameter(Mandatory = $true)]
        [string]$BackendDir,
        [Parameter(Mandatory = $true)]
        [string]$DatabaseUrl
    )

    $env:DATABASE_URL = $DatabaseUrl
    Push-Location $BackendDir
    try {
        $headsOutput = & $VenvPython -m alembic heads 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message "alembic heads failed."
        }
        if ($headsOutput -notmatch $script:ExpectedAlembicHead) {
            Exit-EiaaxFailure -Message ("Expected alembic head " + $script:ExpectedAlembicHead + " not found.")
        }
        if (($headsOutput -split "`n").Where({ $_ -match '\(head\)' }).Count -gt 1) {
            Exit-EiaaxFailure -Message "Multiple alembic heads detected."
        }

        $currentOutput = & $VenvPython -m alembic current 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message "alembic current failed."
        }
        if ($currentOutput -notmatch $script:ExpectedAlembicHead) {
            Exit-EiaaxFailure -Message ("Database is not at alembic head " + $script:ExpectedAlembicHead + ".")
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-EiaaxPowerShellParserValidation {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    $validator = Join-Path $ScriptsDir "validate_ps_parse.ps1"
    if (-not (Test-Path -LiteralPath $validator)) {
        Exit-EiaaxFailure -Message "Missing validate_ps_parse.ps1"
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $validator
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message "PowerShell parser validation failed."
    }
}
