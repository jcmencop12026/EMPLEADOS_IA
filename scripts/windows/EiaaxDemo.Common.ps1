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

function ConvertTo-EiaaxArray {
    param(
        [Parameter(ValueFromPipeline = $true)]
        $InputObject
    )

    return @($InputObject)
}

function Get-EiaaxCollectionCount {
    param(
        $Value
    )

    if ($null -eq $Value) {
        return 0
    }

    return @( $Value ).Count
}

function Get-EiaaxAlembicHeadRevisions {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Output
    )

    $revisions = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($Output -split "`r?`n")) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }
        if ($trimmed -match '^([0-9a-f]+)\s+\(head\)') {
            [void]$revisions.Add($Matches[1])
        }
    }

    return ,@($revisions.ToArray())
}

function Get-EiaaxAlembicCurrentRevisions {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Output
    )

    $revisions = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($Output -split "`r?`n")) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }
        if ($trimmed -match '^([0-9a-f]+)\b') {
            [void]$revisions.Add($Matches[1])
        }
    }

    return ,@($revisions.ToArray())
}

function Test-EiaaxInteractiveInvocationRisk {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [AllowEmptyCollection()]
        [string[]]$ArgumentList = @()
    )

    $executableName = [System.IO.Path]::GetFileName($FilePath).ToLowerInvariant()
    $interactiveExecutables = @(
        "python.exe",
        "python",
        "python3.exe",
        "python3",
        "pythonw.exe",
        "node.exe",
        "node"
    )

    if ($interactiveExecutables -contains $executableName -and (Get-EiaaxCollectionCount $ArgumentList) -eq 0) {
        return $true
    }

    return $false
}

function Invoke-EiaaxNativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [AllowEmptyCollection()]
        [string[]]$ArgumentList = @(),
        [string]$FailureMessage = "Command failed."
    )

    if (Test-EiaaxInteractiveInvocationRisk -FilePath $FilePath -ArgumentList $ArgumentList) {
        Exit-EiaaxFailure -Message ("Refusing interactive invocation without arguments: " + $FilePath)
    }

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message $FailureMessage
    }
}

function Test-EiaaxWindowsPythonStub {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $normalized = $Path.ToUpperInvariant()
    if ($normalized -match '\\MICROSOFT\\WINDOWSAPPS\\') {
        return $true
    }
    if ($normalized -match '\\WINDOWSAPPS\\PYTHON') {
        return $true
    }
    return $false
}

function Get-EiaaxPythonDiscoveryCandidates {
    $result = New-Object System.Collections.Generic.List[string]
    $seen = @{}

    $tryAdd = {
        param([string]$CandidatePath)
        if ([string]::IsNullOrWhiteSpace($CandidatePath)) {
            return
        }
        try {
            $fullPath = [System.IO.Path]::GetFullPath($CandidatePath)
        }
        catch {
            return
        }
        if (-not (Test-Path -LiteralPath $fullPath)) {
            return
        }
        if (Test-EiaaxWindowsPythonStub -Path $fullPath) {
            return
        }
        $key = $fullPath.ToUpperInvariant()
        if ($seen.ContainsKey($key)) {
            return
        }
        $seen[$key] = $true
        [void]$result.Add($fullPath)
    }

    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        & $tryAdd $env:EIAAX_PYTHON
    }

    foreach ($staticPath in @(
            "C:\Python314\python.exe",
            "C:\Python313\python.exe",
            "C:\Python312\python.exe"
        )) {
        & $tryAdd $staticPath
    }

    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        foreach ($version in @("314", "313", "312")) {
            $programFilesPath = Join-Path $env:ProgramFiles ("Python" + $version + "\python.exe")
            & $tryAdd $programFilesPath
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($env:LocalAppData)) {
        $userPythonRoot = Join-Path $env:LocalAppData "Programs\Python"
        if (Test-Path -LiteralPath $userPythonRoot) {
            $versionDirs = Get-ChildItem -LiteralPath $userPythonRoot -ErrorAction SilentlyContinue |
                Where-Object { $_.PSIsContainer }
            foreach ($versionDir in $versionDirs) {
                $userPython = Join-Path $versionDir.FullName "python.exe"
                & $tryAdd $userPython
            }
        }
    }

    if (Test-Path -LiteralPath "C:\") {
        $pythonRoots = Get-ChildItem -Path "C:\" -ErrorAction SilentlyContinue |
            Where-Object { $_.PSIsContainer -and $_.Name -like "Python*" }
        foreach ($root in $pythonRoots) {
            $rootPython = Join-Path $root.FullName "python.exe"
            & $tryAdd $rootPython
        }
    }

    foreach ($commandName in @("python", "python3")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($null -ne $command -and $command.CommandType -eq "Application") {
            & $tryAdd $command.Source
        }
    }

    return ,@($result.ToArray())
}

function Invoke-EiaaxPythonVersionProbe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $PythonExe -V 2>&1
        $exitCode = $LASTEXITCODE
        $text = ($output | Out-String).Trim()
        return [ordered]@{
            ExitCode = $exitCode
            Text     = $text
        }
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
}

function Test-EiaaxPythonRuntimeCandidate {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    $result = [ordered]@{
        Path       = $PythonExe
        Executable = $false
        Version    = $null
        Error      = $null
    }

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        $result.Error = "path does not exist"
        return $result
    }

    $probe = Invoke-EiaaxPythonVersionProbe -PythonExe $PythonExe
    if ($probe.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($probe.Text)) {
        $result.Error = "python -V failed"
        if (-not [string]::IsNullOrWhiteSpace($probe.Text)) {
            $result.Error = $result.Error + ": " + $probe.Text
        }
        return $result
    }

    $result.Executable = $true
    $result.Version = $probe.Text
    return $result
}

function Test-EiaaxPythonVenvCapability {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe,
        [Parameter(Mandatory = $true)]
        [string]$ProbeDirectory
    )

    if (-not (Test-Path -LiteralPath $ProbeDirectory)) {
        New-Item -ItemType Directory -Path $ProbeDirectory | Out-Null
    }

    $probeVenv = Join-Path $ProbeDirectory ("probe-venv-" + [Guid]::NewGuid().ToString("N"))
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $PythonExe -m venv $probeVenv 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            return "venv probe failed for " + $PythonExe
        }

        $probePython = Join-Path $probeVenv "Scripts\python.exe"
        if (-not (Test-Path -LiteralPath $probePython)) {
            return "venv probe created no Scripts\python.exe"
        }

        return $null
    }
    finally {
        $ErrorActionPreference = $previousPreference
        if (Test-Path -LiteralPath $probeVenv) {
            Remove-Item -LiteralPath $probeVenv -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Find-EiaaxPython {
    param(
        [string]$LogFile = $null
    )

    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        if (-not (Test-Path -LiteralPath $env:EIAAX_PYTHON)) {
            Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: EIAAX_PYTHON does not exist: " + $env:EIAAX_PYTHON)
        }
    }

    $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
    if (Get-EiaaxCollectionCount $candidates -eq 0) {
        $detail = ""
        if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
            $detail = " EIAAX_PYTHON=" + $env:EIAAX_PYTHON
        }
        Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: no python.exe candidates detected on this machine." + $detail)
    }

    $failures = @()
    foreach ($candidate in $candidates) {
        $message = "Checking Python candidate: " + $candidate
        Write-Host $message
        if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
            Write-EiaaxLogLine -LogFile $LogFile -Message $message
        }

        $probe = Test-EiaaxPythonRuntimeCandidate -PythonExe $candidate
        if (-not $probe.Executable) {
            $failures += ($candidate + " -> " + $probe.Error)
            continue
        }

        $selectedMessage = "Selected Python: " + $candidate + " (" + $probe.Version + ")"
        Write-Host $selectedMessage
        if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
            Write-EiaaxLogLine -LogFile $LogFile -Message $selectedMessage
        }
        return $candidate
    }

    $detail = ($failures -join "; ")
    Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: candidates were detected but none executed successfully. " + $detail)
}

function Get-EiaaxPythonVersionLine {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    $probe = Invoke-EiaaxPythonVersionProbe -PythonExe $PythonExe
    if ($probe.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($probe.Text)) {
        Exit-EiaaxFailure -Message ("Python is not executable: " + $PythonExe)
    }
    return $probe.Text
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
            Exit-EiaaxFailure -Message ("alembic heads failed. ExitCode=" + $LASTEXITCODE + " Output=" + $headsOutput.Trim())
        }

        $headRevisions = Get-EiaaxAlembicHeadRevisions -Output $headsOutput
        $headCount = Get-EiaaxCollectionCount $headRevisions
        if ($headCount -eq 0) {
            Exit-EiaaxFailure -Message ("alembic heads returned no head revisions. Output=" + $headsOutput.Trim())
        }
        if ($headCount -gt 1) {
            Exit-EiaaxFailure -Message ("Multiple alembic heads detected (" + $headCount + "). Output=" + $headsOutput.Trim())
        }

        $headRevision = $headRevisions[0]
        if ($headRevision -ne $script:ExpectedAlembicHead) {
            Exit-EiaaxFailure -Message ("Expected alembic head " + $script:ExpectedAlembicHead + " but found " + $headRevision + ".")
        }

        $currentOutput = & $VenvPython -m alembic current 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message ("alembic current failed. ExitCode=" + $LASTEXITCODE + " Output=" + $currentOutput.Trim())
        }

        $currentRevisions = Get-EiaaxAlembicCurrentRevisions -Output $currentOutput
        $currentCount = Get-EiaaxCollectionCount $currentRevisions
        if ($currentCount -eq 0) {
            Exit-EiaaxFailure -Message ("alembic current returned no revision. Output=" + $currentOutput.Trim())
        }

        $currentRevision = $currentRevisions[$currentCount - 1]
        if ($currentRevision -ne $script:ExpectedAlembicHead) {
            Exit-EiaaxFailure -Message ("Database is not at alembic head " + $script:ExpectedAlembicHead + "; current=" + $currentRevision + ".")
        }

        Write-Host ("Alembic heads OK: " + $headRevision + " (single head)")
        Write-Host ("Alembic current OK: " + $currentRevision)
    }
    finally {
        Pop-Location
    }
}

function Get-EiaaxWindowsPowerShellExecutable {
    if (-not [string]::IsNullOrWhiteSpace($env:WINDIR)) {
        $windowsPowerShell = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"
        if (Test-Path -LiteralPath $windowsPowerShell) {
            return $windowsPowerShell
        }
    }

    $powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($null -ne $powershell) {
        return $powershell.Source
    }

    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($null -ne $pwsh) {
        return $pwsh.Source
    }

    Exit-EiaaxFailure -Message "PowerShell executable not found."
}

function Invoke-EiaaxPowerShellFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    $shell = Get-EiaaxWindowsPowerShellExecutable
    & $shell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $FilePath @ArgumentList
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

    Invoke-EiaaxPowerShellFile -FilePath $validator
    if ($LASTEXITCODE -ne 0) {
        Exit-EiaaxFailure -Message "PowerShell parser validation failed."
    }
}
