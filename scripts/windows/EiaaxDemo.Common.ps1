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
$script:ExpectedAlembicHead = "1820a1b2c3d4e"
$script:ConvergenceWorktreeDefault = "D:\EMPLEADOS_IA_CONVERGENCIA"
$script:ReferenceDiscoveryWorktree = "D:\EMPLEADOS_IA_INTEGRADO"
$script:ConvergenceManifestFile = "eiaax_convergence_manifest.json"
$script:EiaaxCurrentStage = "inicio"

$script:ForbiddenWorktreeNames = @(
    "EMPLEADOS_IA",
    "EMPLEADOS_IA_CERT",
    "EMPLEADOS_IA_V1_HOTFIX"
)

function Set-EiaaxStage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $script:EiaaxCurrentStage = $Name
}

function Get-EiaaxStage {
    return $script:EiaaxCurrentStage
}

function Write-EiaaxError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    # Plain stdout text avoids CLIXML serialization when stderr is redirected (PS 5.1).
    [Console]::Out.WriteLine("ERROR: $Message")
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

function Initialize-EiaaxConvergenceWorktreeFromScriptRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    if (-not (Test-Path -LiteralPath $ScriptsDir)) {
        Exit-EiaaxFailure -Message ("Scripts directory not found: " + $ScriptsDir)
    }

    $resolvedScripts = (Resolve-Path -LiteralPath $ScriptsDir).Path
    $worktree = (Resolve-Path -LiteralPath (Join-Path $resolvedScripts "..\..")).Path
    $folderName = [System.IO.Path]::GetFileName($worktree.TrimEnd('\'))

    if ($folderName -ne "EMPLEADOS_IA_CONVERGENCIA") {
        Exit-EiaaxFailure -Message (
            "EIAAX convergence scripts must live under EMPLEADOS_IA_CONVERGENCIA. Resolved: " + $worktree
        )
    }

    $env:EIAAX_WORKTREE = $worktree
    return $worktree
}

function Assert-EiaaxConvergencePathAuthority {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [string]$LogFile = $null
    )

    Assert-EiaaxNotOriginalTree -WorktreeRoot $WorktreeRoot
    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    $worktreeFull = [System.IO.Path]::GetFullPath($WorktreeRoot).TrimEnd('\')

    foreach ($entry in @{
            Backend  = $paths.Backend
            Frontend = $paths.Frontend
            Venv     = $paths.Venv
            DbFile   = $paths.DbFile
            Logs     = $paths.Logs
        }.GetEnumerator()) {
        $full = [System.IO.Path]::GetFullPath($entry.Value)
        if (-not $full.StartsWith($worktreeFull, [System.StringComparison]::OrdinalIgnoreCase)) {
            $message = "Critical path outside CONVERGENCIA worktree (" + $entry.Key + "): " + $full
            if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
                Write-EiaaxLogLine -LogFile $LogFile -Message ("ABORT: " + $message)
            }
            Exit-EiaaxFailure -Message $message
        }
    }
}

function Write-EiaaxConvergenceExecutionContext {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [string]$LogFile = $null
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    $lines = @(
        ("RUTA DE EJECUCION EIAAX: " + $WorktreeRoot),
        ("REPOSITORIO: " + $WorktreeRoot),
        ("VENV: " + $paths.Venv),
        ("BASE DEMO: " + $paths.DbFile),
        ("LOG: " + $LogFile)
    )

    foreach ($line in $lines) {
        Write-Host $line
        if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
            Write-EiaaxLogLine -LogFile $LogFile -Message $line
        }
    }
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

    if ($Value -is [System.Collections.ICollection]) {
        return $Value.Count
    }

    return @($Value).Count
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

    $result = Invoke-EiaaxExternalCommand -FilePath $FilePath -ArgumentList $ArgumentList
    if ($result.ExitCode -ne 0) {
        if (-not [string]::IsNullOrWhiteSpace($result.Output)) {
            $FailureMessage = $FailureMessage + "`n" + $result.Output
        }
        Exit-EiaaxFailure -Message $FailureMessage
    }
}

function ConvertTo-EiaaxExternalCommandOutput {
    param(
        $RawOutput
    )

    if ($null -eq $RawOutput) {
        return ""
    }

    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($RawOutput)) {
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            $lines.Add($item.ToString())
        }
        else {
            $lines.Add([string]$item)
        }
    }

    return ($lines -join "`n")
}

function Invoke-EiaaxExternalCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [AllowEmptyCollection()]
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = $null,
        [string]$LogFile = $null,
        [string]$Stage = $null,
        [string]$CommandLabel = $null
    )

    if (Test-EiaaxInteractiveInvocationRisk -FilePath $FilePath -ArgumentList $ArgumentList) {
        Exit-EiaaxFailure -Message ("Refusing interactive invocation without arguments: " + $FilePath)
    }

    $label = $CommandLabel
    if ([string]::IsNullOrWhiteSpace($label)) {
        $label = $FilePath
        if ((Get-EiaaxCollectionCount $ArgumentList) -gt 0) {
            $label += " " + ($ArgumentList -join " ")
        }
    }

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $locationPushed = $false
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = 1
    $output = ""
    try {
        if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
            Push-Location $WorkingDirectory
            $locationPushed = $true
        }

        $rawOutput = & $FilePath @ArgumentList 2>&1
        $exitCode = $LASTEXITCODE
        $output = ConvertTo-EiaaxExternalCommandOutput -RawOutput $rawOutput

        return [ordered]@{
            ExitCode = $exitCode
            Output   = $output
        }
    }
    finally {
        $stopwatch.Stop()
        if ($locationPushed) {
            Pop-Location
        }
        $ErrorActionPreference = $previousPreference

        if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
            $stagePrefix = ""
            if (-not [string]::IsNullOrWhiteSpace($Stage)) {
                $stagePrefix = "stage=" + $Stage + " | "
            }
            $logLine = $stagePrefix + $label + " | exit=" + $exitCode + " | duration_ms=" + $stopwatch.ElapsedMilliseconds
            if (-not [string]::IsNullOrWhiteSpace($output)) {
                $logLine += " | " + ($output -replace "`r?`n", " / ")
            }
            Write-EiaaxLogLine -LogFile $LogFile -Message $logLine
        }
    }
}

function Get-EiaaxGitExecutable {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $git) {
        Exit-EiaaxFailure -Message "git not found in PATH."
    }
    return $git.Source
}

function Invoke-EiaaxGitCommand {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [string[]]$ArgumentList,
        [string]$WorkingDirectory = $null,
        [string]$LogFile = $null,
        [string]$FailureMessage = $null,
        [switch]$AllowNonZeroExit
    )

    $gitExe = Get-EiaaxGitExecutable
    $commandLabel = "git " + ($ArgumentList -join " ")
    $result = Invoke-EiaaxExternalCommand `
        -FilePath $gitExe `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -LogFile $LogFile `
        -Stage (Get-EiaaxStage) `
        -CommandLabel $commandLabel

    if (-not [string]::IsNullOrWhiteSpace($result.Output)) {
        Write-Host $result.Output
    }

    if ($result.ExitCode -ne 0 -and -not $AllowNonZeroExit) {
        $message = $FailureMessage
        if ([string]::IsNullOrWhiteSpace($message)) {
            $message = $commandLabel + " failed with exit code " + $result.ExitCode
        }
        if (-not [string]::IsNullOrWhiteSpace($result.Output)) {
            $message = $message + "`n" + $result.Output
        }
        Exit-EiaaxFailure -Message $message
    }

    return $result
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

function Join-EiaaxPathMaybe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Base,
        [Parameter(Mandatory = $true)]
        [string]$Child
    )

    if ($Base -match '^[A-Za-z]:') {
        return Join-EiaaxWindowsPath -Base $Base -Child $Child
    }

    return Join-Path $Base $Child
}

function Join-EiaaxWindowsPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Base,
        [Parameter(Mandatory = $true)]
        [string]$Child
    )

    $trimmedBase = $Base.TrimEnd('\', '/')
    $trimmedChild = $Child.TrimStart('\', '/')
    return $trimmedBase + '\' + $trimmedChild
}

function Get-EiaaxResolvedPythonPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    if (Test-EiaaxWindowsPythonStub -Path $Path) {
        return $null
    }
    try {
        return (Resolve-Path -LiteralPath $Path).Path
    }
    catch {
        return $null
    }
}

function Read-EiaaxPyvenvCfg {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PyvenvCfgPath
    )

    $result = [ordered]@{
        home       = $null
        executable = $null
        version    = $null
        command    = $null
    }

    if (-not (Test-Path -LiteralPath $PyvenvCfgPath)) {
        return $result
    }

    foreach ($line in (Get-Content -LiteralPath $PyvenvCfgPath -ErrorAction SilentlyContinue)) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }
        if ($trimmed -match '^(home|executable|version|command)\s*=\s*(.+)$') {
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            if ($value.StartsWith('"') -and $value.EndsWith('"') -and $value.Length -ge 2) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $result[$key] = $value
        }
    }

    return $result
}

function Get-EiaaxReferenceWorktreeRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_REFERENCE_WORKTREE)) {
        return $env:EIAAX_REFERENCE_WORKTREE
    }
    return $script:ReferenceDiscoveryWorktree
}

function Get-EiaaxReferenceVenvPythonPath {
    $referenceWorktree = Get-EiaaxReferenceWorktreeRoot
    $venvDir = Join-EiaaxWindowsPath -Base $referenceWorktree -Child $script:VenvDirName
    foreach ($relative in @("Scripts\python.exe", "bin\python", "bin\python3")) {
        $candidate = if ($relative -match '^[A-Za-z]:') {
            $relative
        }
        elseif ($relative -match '\\') {
            Join-EiaaxWindowsPath -Base $venvDir -Child $relative
        }
        else {
            Join-Path $venvDir $relative
        }
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return Join-EiaaxWindowsPath -Base $venvDir -Child "Scripts\python.exe"
}

function Get-EiaaxVenvPythonPathForDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvPath
    )

    foreach ($relative in @("Scripts\python.exe", "bin\python", "bin\python3")) {
        $candidate = if ($relative -match '\\') {
            Join-EiaaxWindowsPath -Base $VenvPath -Child $relative
        }
        else {
            Join-Path $VenvPath $relative
        }
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function Get-EiaaxReferencePyvenvCfgPath {
    param(
        [string]$ReferenceWorktree = $(Get-EiaaxReferenceWorktreeRoot)
    )

    return Join-EiaaxWindowsPath -Base (Join-EiaaxWindowsPath -Base $ReferenceWorktree -Child $script:VenvDirName) -Child "pyvenv.cfg"
}

function Test-EiaaxPythonPathLooksLikeVenvInterpreter {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $normalized = $Path.ToUpperInvariant()
    return ($normalized -match '\\\.VENV[^\\]*\\SCRIPTS\\PYTHON\.EXE$') -or
        ($normalized -match '\\VENV\\SCRIPTS\\PYTHON\.EXE$')
}

function Get-EiaaxPythonCandidatesFromPyvenvCfg {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PyvenvCfgPath
    )

    $cfg = Read-EiaaxPyvenvCfg -PyvenvCfgPath $PyvenvCfgPath
    $ordered = New-Object System.Collections.Generic.List[string]
    $seen = @{}

    $addCandidate = {
        param([string]$CandidatePath)
        if ([string]::IsNullOrWhiteSpace($CandidatePath)) {
            return
        }
        if (Test-EiaaxPythonPathLooksLikeVenvInterpreter -Path $CandidatePath) {
            return
        }
        $resolved = Get-EiaaxResolvedPythonPath -Path $CandidatePath
        if ($null -eq $resolved) {
            return
        }
        $key = $resolved.ToUpperInvariant()
        if ($seen.ContainsKey($key)) {
            return
        }
        $seen[$key] = $true
        [void]$ordered.Add($resolved)
    }

    if (-not [string]::IsNullOrWhiteSpace($cfg.executable)) {
        & $addCandidate $cfg.executable
    }

    if (-not [string]::IsNullOrWhiteSpace($cfg.home)) {
        & $addCandidate (Join-EiaaxWindowsPath -Base $cfg.home -Child "python.exe")
    }

    if (-not [string]::IsNullOrWhiteSpace($cfg.command)) {
        if ($cfg.command -match '([A-Za-z]:\\[^"\s]+python\.exe)') {
            & $addCandidate $Matches[1]
        }
    }

    return [string[]]$ordered.ToArray()
}

function Invoke-EiaaxPythonSysProbe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    $result = [ordered]@{
        ExitCode        = 1
        Executable      = $null
        Prefix          = $null
        BasePrefix      = $null
        BaseExecutable  = $null
        Version         = $null
        Error           = $null
    }

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        $result.Error = "python executable missing"
        return $result
    }

    $probeScript = "import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix); print(getattr(sys, '_base_executable', sys.executable)); print(sys.version.split()[0])"
    $probe = Invoke-EiaaxExternalCommand -FilePath $PythonExe -ArgumentList @("-c", $probeScript)
    $result.ExitCode = $probe.ExitCode
    if ($probe.ExitCode -ne 0) {
        $result.Error = ($probe.Output | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($result.Error)) {
            $result.Error = "sys probe failed"
        }
        return $result
    }

    $lines = @($probe.Output -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Trim()) })
    if ($lines.Count -lt 5) {
        $result.Error = "sys probe returned incomplete output"
        return $result
    }

    $result.Executable = $lines[0].Trim()
    $result.Prefix = $lines[1].Trim()
    $result.BasePrefix = $lines[2].Trim()
    $result.BaseExecutable = $lines[3].Trim()
    $result.Version = $lines[4].Trim()
    return $result
}

function Get-EiaaxPythonBaseCandidatesFromSysProbe {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$SysProbe
    )

    $ordered = New-Object System.Collections.Generic.List[string]
    $seen = @{}

    $addCandidate = {
        param([string]$CandidatePath)
        if ([string]::IsNullOrWhiteSpace($CandidatePath)) {
            return
        }
        if (Test-EiaaxPythonPathLooksLikeVenvInterpreter -Path $CandidatePath) {
            return
        }
        $resolved = Get-EiaaxResolvedPythonPath -Path $CandidatePath
        if ($null -eq $resolved) {
            return
        }
        $key = $resolved.ToUpperInvariant()
        if ($seen.ContainsKey($key)) {
            return
        }
        $seen[$key] = $true
        [void]$ordered.Add($resolved)
    }

    & $addCandidate $SysProbe.BaseExecutable
    if (-not [string]::IsNullOrWhiteSpace($SysProbe.BasePrefix)) {
        if ($SysProbe.BasePrefix -match '^[A-Za-z]:') {
            & $addCandidate (Join-EiaaxWindowsPath -Base $SysProbe.BasePrefix -Child "python.exe")
        }
        else {
            foreach ($name in @("python", "python3")) {
                & $addCandidate (Join-Path $SysProbe.BasePrefix (Join-Path "bin" $name))
            }
        }
    }

    return [string[]]$ordered.ToArray()
}

function Get-EiaaxPythonCandidatesFromPyvenvCfgPaths {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Cfg
    )

    $ordered = New-Object System.Collections.Generic.List[string]
    $seen = @{}

    $addPath = {
        param([string]$CandidatePath)
        if ([string]::IsNullOrWhiteSpace($CandidatePath)) {
            return
        }
        if (Test-EiaaxPythonPathLooksLikeVenvInterpreter -Path $CandidatePath) {
            return
        }
        $key = $CandidatePath.ToUpperInvariant()
        if ($seen.ContainsKey($key)) {
            return
        }
        $seen[$key] = $true
        [void]$ordered.Add($CandidatePath)
    }

    if (-not [string]::IsNullOrWhiteSpace($Cfg.executable)) {
        & $addPath $Cfg.executable
    }
    if (-not [string]::IsNullOrWhiteSpace($Cfg.home)) {
        & $addPath (Join-EiaaxWindowsPath -Base $Cfg.home -Child "python.exe")
    }
    if (-not [string]::IsNullOrWhiteSpace($Cfg.command)) {
        if ($Cfg.command -match '([A-Za-z]:\\[^"\s]+python\.exe)') {
            & $addPath $Matches[1]
        }
    }

    return [string[]]$ordered.ToArray()
}

function Write-EiaaxPythonDiscoveryDiagnostics {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Diagnostics
    )

    Write-Host ""
    Write-Host "PYTHON DISCOVERY"
    foreach ($line in $Diagnostics.Lines) {
        Write-Host $line
    }
    Write-Host ""
}

function Add-EiaaxPythonPlanCandidate {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [System.Collections.Generic.List[hashtable]]$CandidateList,
        [Parameter(Mandatory = $true)]
        [hashtable]$SeenKeys,
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [string]$Role = "base"
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return
    }
    $resolved = Get-EiaaxResolvedPythonPath -Path $Path
    if ($null -eq $resolved) {
        return
    }
    $key = $resolved.ToUpperInvariant()
    if ($SeenKeys.ContainsKey($key)) {
        return
    }
    $SeenKeys[$key] = $true
    [void]$CandidateList.Add([ordered]@{
        Path   = $resolved
        Source = $Source
        Role   = $Role
    })
}

function Build-EiaaxPythonResolutionPlan {
    param(
        [string]$WorktreeRoot = $null
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $candidateList = New-Object System.Collections.Generic.List[hashtable]
    $seenKeys = @{}
    $referenceVenvPython = Get-EiaaxReferenceVenvPythonPath
    $referenceCfgPath = Get-EiaaxReferencePyvenvCfgPath
    $referenceCfg = Read-EiaaxPyvenvCfg -PyvenvCfgPath $referenceCfgPath
    $referenceSysProbe = $null

    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        if (Test-Path -LiteralPath $env:EIAAX_PYTHON) {
            [void]$lines.Add(("Fuente 1: EIAAX_PYTHON .......... definido (" + $env:EIAAX_PYTHON + ")"))
            Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $env:EIAAX_PYTHON -Source "EIAAX_PYTHON" -Role "base"
        }
        else {
            [void]$lines.Add("Fuente 1: EIAAX_PYTHON .......... ruta invalida")
        }
    }
    else {
        [void]$lines.Add("Fuente 1: EIAAX_PYTHON .......... no definido")
    }

    if (-not [string]::IsNullOrWhiteSpace($WorktreeRoot)) {
        $convergenceVenvPython = Get-EiaaxVenvPythonPathForDirectory -VenvPath (Join-EiaaxWindowsPath -Base $WorktreeRoot -Child $script:VenvDirName)
        if (-not [string]::IsNullOrWhiteSpace($convergenceVenvPython)) {
            [void]$lines.Add(("Fuente 2: venv convergencia ..... encontrado (" + $convergenceVenvPython + ")"))
            Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $convergenceVenvPython -Source "venv convergencia" -Role "runtime"
        }
        else {
            [void]$lines.Add("Fuente 2: venv convergencia ..... no existe")
        }
    }
    else {
        [void]$lines.Add("Fuente 2: venv convergencia ..... no evaluado")
    }

    if (Test-Path -LiteralPath $referenceVenvPython) {
        [void]$lines.Add(("Fuente 3: venv integrado ........ encontrado (" + $referenceVenvPython + ")"))
        $referenceSysProbe = Invoke-EiaaxPythonSysProbe -PythonExe $referenceVenvPython
        if ($referenceSysProbe.ExitCode -eq 0) {
            [void]$lines.Add(("sys.executable ................ " + $referenceSysProbe.Executable))
            [void]$lines.Add(("sys.base_prefix ............... " + $referenceSysProbe.BasePrefix))
            [void]$lines.Add(("sys._base_executable .......... " + $referenceSysProbe.BaseExecutable))
            [void]$lines.Add(("sys.version ................... " + $referenceSysProbe.Version))
            foreach ($probePath in @(Get-EiaaxPythonBaseCandidatesFromSysProbe -SysProbe $referenceSysProbe)) {
                Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $probePath -Source "sys.base_prefix (venv integrado)" -Role "base"
            }
        }
        else {
            [void]$lines.Add(("sys probe venv integrado ...... FAIL (" + $referenceSysProbe.Error + ")"))
        }
    }
    else {
        [void]$lines.Add("Fuente 3: venv integrado ........ no encontrado")
    }

    if (Test-Path -LiteralPath $referenceCfgPath) {
        [void]$lines.Add("pyvenv.cfg .................... leido")
        if (-not [string]::IsNullOrWhiteSpace($referenceCfg.version)) {
            [void]$lines.Add(("pyvenv.cfg version ............ " + $referenceCfg.version))
        }
        if (-not [string]::IsNullOrWhiteSpace($referenceCfg.home)) {
            $homeExists = Test-Path -LiteralPath $referenceCfg.home
            [void]$lines.Add(("pyvenv.cfg home ............... " + $referenceCfg.home + $(if (-not $homeExists) { " [no existe]" } else { "" })))
        }
        if (-not [string]::IsNullOrWhiteSpace($referenceCfg.executable)) {
            $exeExists = Test-Path -LiteralPath $referenceCfg.executable
            [void]$lines.Add(("pyvenv.cfg executable ......... " + $referenceCfg.executable + $(if (-not $exeExists) { " [no existe]" } else { "" })))
        }
        foreach ($cfgPath in @(Get-EiaaxPythonCandidatesFromPyvenvCfgPaths -Cfg $referenceCfg)) {
            if (Test-Path -LiteralPath $cfgPath) {
                Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $cfgPath -Source "pyvenv.cfg" -Role "base"
            }
        }
    }
    else {
        [void]$lines.Add(("pyvenv.cfg .................... no encontrado (" + $referenceCfgPath + ")"))
    }

    foreach ($launcherPath in @(Get-EiaaxPythonLauncherCandidates)) {
        Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $launcherPath -Source "py launcher" -Role "base"
    }

    foreach ($wherePath in @(Get-EiaaxPythonWhereCandidates)) {
        Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $wherePath -Source "where.exe" -Role "base"
    }

    foreach ($pathDir in (($env:PATH) -split ';')) {
        if ([string]::IsNullOrWhiteSpace($pathDir)) {
            continue
        }
        $trimmed = $pathDir.Trim()
        Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path (Join-EiaaxPathMaybe -Base $trimmed -Child "python.exe") -Source "PATH" -Role "base"
        Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path (Join-EiaaxPathMaybe -Base $trimmed -Child "python3.exe") -Source "PATH" -Role "base"
    }

    foreach ($commandName in @("python", "python3")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($null -ne $command -and $command.CommandType -eq "Application") {
            Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $command.Source -Source ("Get-Command " + $commandName) -Role "base"
        }
    }

    foreach ($registryPath in @(Get-EiaaxPythonRegistryCandidates)) {
        Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $registryPath -Source "registry" -Role "base"
    }

    foreach ($staticPath in @(
            "C:\Python314\python.exe",
            "C:\Python313\python.exe",
            "C:\Python312\python.exe",
            "C:\Python311\python.exe"
        )) {
        Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $staticPath -Source "standard install" -Role "base"
    }

    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        foreach ($version in @("314", "313", "312", "311")) {
            $programFilesPath = Join-Path $env:ProgramFiles ("Python" + $version + "\python.exe")
            Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path $programFilesPath -Source "Program Files" -Role "base"
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($env:LocalAppData)) {
        $userPythonRoot = Join-Path $env:LocalAppData "Programs\Python"
        if (Test-Path -LiteralPath $userPythonRoot) {
            $versionDirs = Get-ChildItem -LiteralPath $userPythonRoot -ErrorAction SilentlyContinue |
                Where-Object { $_.PSIsContainer }
            foreach ($versionDir in $versionDirs) {
                Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path (Join-Path $versionDir.FullName "python.exe") -Source "LocalAppData" -Role "base"
            }
        }
    }

    if (Test-Path -LiteralPath "C:\") {
        $pythonRoots = Get-ChildItem -Path "C:\" -ErrorAction SilentlyContinue |
            Where-Object { $_.PSIsContainer -and $_.Name -like "Python*" }
        foreach ($root in $pythonRoots) {
            Add-EiaaxPythonPlanCandidate -CandidateList $candidateList -SeenKeys $seenKeys -Path (Join-Path $root.FullName "python.exe") -Source "C:\Python*" -Role "base"
        }
    }

    $venvCreatorFallback = $null
    if ($candidateList.Count -eq 0 -and (Test-Path -LiteralPath $referenceVenvPython)) {
        $referenceProbe = Test-EiaaxPythonRuntimeCandidate -PythonExe $referenceVenvPython
        if ($referenceProbe.Executable) {
            [void]$lines.Add("Python base original ............ NO DISPONIBLE")
            [void]$lines.Add("Venv integrado ................ FUNCIONAL")
            $venvCreatorFallback = $referenceVenvPython
            [void]$candidateList.Add([ordered]@{
                Path   = $referenceVenvPython
                Source = "venv integrado (creador venv)"
                Role   = "venv-creator"
            })
        }
    }

    return [ordered]@{
        Lines               = [string[]]$lines.ToArray()
        Candidates          = @($candidateList.ToArray())
        CandidateCount      = $candidateList.Count
        ReferenceVenvPython = $referenceVenvPython
        ReferenceSysProbe   = $referenceSysProbe
        VenvCreatorFallback = $venvCreatorFallback
    }
}

function Get-EiaaxPythonDiscoveryCandidates {
    param(
        [string]$WorktreeRoot = $null
    )

    $plan = Build-EiaaxPythonResolutionPlan -WorktreeRoot $WorktreeRoot
    return @($plan.Candidates | ForEach-Object { $_.Path })
}

function Resolve-EiaaxPython {
    param(
        [string]$LogFile = $null,
        [string]$WorktreeRoot = $null
    )

    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        $explicitPath = Get-EiaaxResolvedPythonPath -Path $env:EIAAX_PYTHON
        Write-EiaaxPythonDiscoveryDiagnostics -Diagnostics @{
            Lines = @(
                $(if ($null -eq $explicitPath) {
                    "Fuente 1: EIAAX_PYTHON .......... ruta invalida"
                }
                else {
                    "Fuente 1: EIAAX_PYTHON .......... definido (" + $env:EIAAX_PYTHON + ")"
                })
            )
        }
        if ($null -eq $explicitPath) {
            Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: EIAAX_PYTHON is not a valid python executable: " + $env:EIAAX_PYTHON)
        }
        $explicitProbe = Test-EiaaxPythonRuntimeCandidate -PythonExe $explicitPath
        if (-not $explicitProbe.Executable) {
            Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: EIAAX_PYTHON failed python -V: " + $env:EIAAX_PYTHON + " -> " + $explicitProbe.Error)
        }
        Write-Host ("Validacion python -V .......... PASS (" + $explicitProbe.Version + ")")
        return $explicitPath
    }

    $plan = Build-EiaaxPythonResolutionPlan -WorktreeRoot $WorktreeRoot
    Write-EiaaxPythonDiscoveryDiagnostics -Diagnostics @{ Lines = $plan.Lines }

    if ($plan.CandidateCount -eq 0) {
        $detail = "PYTHON NOT FOUND: ningun candidato ejecutable."
        if ($null -ne $plan.ReferenceSysProbe -and $plan.ReferenceSysProbe.ExitCode -eq 0) {
            $detail += " sys.base_prefix=" + $plan.ReferenceSysProbe.BasePrefix + " sys._base_executable=" + $plan.ReferenceSysProbe.BaseExecutable + "."
        }
        elseif (Test-Path -LiteralPath $plan.ReferenceVenvPython) {
            $detail += " Venv integrado existe pero no se pudo resolver Python base ni usar como creador."
        }
        Exit-EiaaxFailure -Message ($detail + " Revise el bloque PYTHON DISCOVERY arriba.")
    }

    $probeDirectory = $null
    if (-not [string]::IsNullOrWhiteSpace($WorktreeRoot)) {
        $probeDirectory = Ensure-EiaaxLogsDir -WorktreeRoot $WorktreeRoot
    }

    $failures = New-Object System.Collections.Generic.List[string]
    foreach ($entry in @($plan.Candidates)) {
        $candidate = $entry.Path
        $source = $entry.Source
        $message = "Checking Python candidate (" + $source + "): " + $candidate
        Write-Host $message
        if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
            Write-EiaaxLogLine -LogFile $LogFile -Message $message
        }

        $probe = Test-EiaaxPythonRuntimeCandidate -PythonExe $candidate
        if (-not $probe.Executable) {
            [void]$failures.Add($candidate + " -> " + $probe.Error)
            continue
        }

        if ($entry.Role -eq "venv-creator") {
            if ($null -eq $probeDirectory) {
                $probeDirectory = [System.IO.Path]::GetTempPath()
            }
            $venvProbeError = Test-EiaaxPythonVenvCapability -PythonExe $candidate -ProbeDirectory $probeDirectory
            if ($null -ne $venvProbeError) {
                [void]$failures.Add($candidate + " -> venv creator probe failed: " + $venvProbeError)
                [void]$plan.Lines.Add("Prueba python -m venv ............ FAIL (" + $venvProbeError + ")")
                continue
            }
            [void]$plan.Lines.Add("Prueba python -m venv ............ PASS (venv integrado como creador)")
        }

        Write-Host ("Validacion python -V .......... PASS (" + $probe.Version + ")")
        $selectedMessage = "Selected Python (" + $source + "): " + $candidate + " (" + $probe.Version + ")"
        Write-Host ("Python base ................... " + $candidate)
        Write-Host $selectedMessage
        if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
            Write-EiaaxLogLine -LogFile $LogFile -Message $selectedMessage
        }
        return $candidate
    }

    $detail = ($failures.ToArray() -join "; ")
    if ($null -ne $plan.VenvCreatorFallback) {
        Exit-EiaaxFailure -Message ("PYTHON BASE ORIGINAL NO DISPONIBLE. VENV ANTERIOR FUNCIONAL pero no pudo crear venv convergencia. " + $detail)
    }
    Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: candidatos detectados pero ninguno ejecuto correctamente. " + $detail)
}

function Find-EiaaxPython {
    param(
        [string]$LogFile = $null,
        [string]$WorktreeRoot = $null
    )

    return Resolve-EiaaxPython -LogFile $LogFile -WorktreeRoot $WorktreeRoot
}

function Get-EiaaxPythonWhereCandidates {
    if ([string]::IsNullOrWhiteSpace($env:SystemRoot)) {
        return @()
    }

    $whereExe = Join-EiaaxWindowsPath -Base $env:SystemRoot -Child "System32\where.exe"
    if (-not (Test-Path -LiteralPath $whereExe)) {
        return @()
    }

    $paths = New-Object System.Collections.Generic.List[string]
    foreach ($target in @("python.exe", "python3.exe")) {
        $result = Invoke-EiaaxExternalCommand -FilePath $whereExe -ArgumentList @($target)
        if ($result.ExitCode -ne 0) {
            continue
        }
        foreach ($line in ($result.Output -split "`r?`n")) {
            $trimmed = $line.Trim()
            if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
                [void]$paths.Add($trimmed)
            }
        }
    }
    return [string[]]$paths.ToArray()
}

function Get-EiaaxPythonLauncherCandidates {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -eq $py) {
        $py = Get-Command py -ErrorAction SilentlyContinue
    }
    if ($null -eq $py) {
        return @()
    }

    $paths = New-Object System.Collections.Generic.List[string]
    $listResult = Invoke-EiaaxExternalCommand -FilePath $py.Source -ArgumentList @("-0p")
    if ($listResult.ExitCode -eq 0) {
        foreach ($line in ($listResult.Output -split "`r?`n")) {
            if ($line -match '(C:\\[^`\r\n]+\.exe)\s*$') {
                [void]$paths.Add($Matches[1].Trim())
            }
        }
    }

    foreach ($version in @("3.12", "3.13", "3.11")) {
        $resolveResult = Invoke-EiaaxExternalCommand -FilePath $py.Source `
            -ArgumentList @("-$version", "-c", "import sys; print(sys.executable)")
        if ($resolveResult.ExitCode -eq 0) {
            foreach ($line in ($resolveResult.Output -split "`r?`n")) {
                $trimmed = $line.Trim()
                if ($trimmed -match '^[A-Za-z]:\\') {
                    [void]$paths.Add($trimmed)
                }
            }
        }
    }

    return [string[]]$paths.ToArray()
}

function Get-EiaaxPythonRegistryCandidates {
    $paths = New-Object System.Collections.Generic.List[string]
    foreach ($root in @("HKLM:\SOFTWARE\Python\PythonCore", "HKCU:\SOFTWARE\Python\PythonCore")) {
        if (-not (Test-Path -LiteralPath $root)) {
            continue
        }
        $versions = Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue
        foreach ($versionKey in $versions) {
            $installPath = (Get-ItemProperty -LiteralPath (Join-Path $versionKey.PSPath "InstallPath") -ErrorAction SilentlyContinue).'(default)'
            if (-not [string]::IsNullOrWhiteSpace($installPath)) {
                [void]$paths.Add((Join-Path $installPath "python.exe"))
            }
        }
    }
    return [string[]]$paths.ToArray()
}

function Get-EiaaxConvergenceManifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    $manifestPath = Join-Path $ScriptsDir $script:ConvergenceManifestFile
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        Exit-EiaaxFailure -Message ("Missing convergence manifest: " + $manifestPath)
    }
    return (Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json)
}

function Get-EiaaxGitBranchName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $result = Invoke-EiaaxGitCommand `
        -ArgumentList @("rev-parse", "--abbrev-ref", "HEAD") `
        -WorkingDirectory $WorktreeRoot `
        -AllowNonZeroExit
    if ($result.ExitCode -ne 0) {
        return $null
    }
    return $result.Output.Trim()
}

function Get-EiaaxGitShortSha {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $result = Invoke-EiaaxGitCommand `
        -ArgumentList @("rev-parse", "--short", "HEAD") `
        -WorkingDirectory $WorktreeRoot `
        -AllowNonZeroExit
    if ($result.ExitCode -ne 0) {
        return $null
    }
    return $result.Output.Trim()
}

function Confirm-EiaaxConvergenceRepository {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    $manifest = Get-EiaaxConvergenceManifest -ScriptsDir $ScriptsDir
    $branch = Get-EiaaxGitBranchName -WorktreeRoot $WorktreeRoot
    $sha = Get-EiaaxGitShortSha -WorktreeRoot $WorktreeRoot

    if ([string]::IsNullOrWhiteSpace($branch)) {
        Exit-EiaaxFailure -Message "Cannot resolve git branch for convergence validation."
    }
    if ($branch -ne $manifest.branch) {
        Exit-EiaaxFailure -Message ("Wrong git branch. Expected " + $manifest.branch + " but found " + $branch + ".")
    }

    if ([string]::IsNullOrWhiteSpace($sha)) {
        Exit-EiaaxFailure -Message "Cannot resolve git SHA for convergence validation."
    }

    Write-Host ("Repository OK: branch=" + $branch + " sha=" + $sha)
    return [ordered]@{
        Manifest = $manifest
        Branch   = $branch
        Sha      = $sha
    }
}

function Test-EiaaxVenvIntegrity {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvPath
    )

    $result = [ordered]@{
        Valid  = $false
        Reason = $null
    }

    if (-not (Test-Path -LiteralPath $VenvPath)) {
        $result.Reason = "venv directory missing"
        return $result
    }

    $venvPython = Get-EiaaxVenvPythonPathForDirectory -VenvPath $VenvPath
    if ([string]::IsNullOrWhiteSpace($venvPython)) {
        $result.Reason = "venv python missing (Scripts\python.exe or bin/python)"
        return $result
    }

    $pyvenvCfg = Join-Path $VenvPath "pyvenv.cfg"
    if (-not (Test-Path -LiteralPath $pyvenvCfg)) {
        $result.Reason = "pyvenv.cfg missing"
        return $result
    }

    $probe = Test-EiaaxPythonRuntimeCandidate -PythonExe $venvPython
    if (-not $probe.Executable) {
        $result.Reason = "venv python not executable: " + $probe.Error
        return $result
    }

    $result.Valid = $true
    return $result
}

function Remove-EiaaxDamagedVenv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvPath,
        [Parameter(Mandatory = $true)]
        [string]$Reason,
        [string]$LogFile = $null
    )

    $message = "Removing damaged venv at " + $VenvPath + " (" + $Reason + ")"
    Write-Host $message
    if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
        Write-EiaaxLogLine -LogFile $LogFile -Message $message
    }
    Remove-Item -LiteralPath $VenvPath -Recurse -Force -ErrorAction Stop
}

function Invoke-EiaaxDemoStopForWorktree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    if (-not (Test-Path -LiteralPath $WorktreeRoot)) {
        return
    }

    $stopScript = Join-Path $ScriptsDir "detener_demo_eiaax.ps1"
    if (-not (Test-Path -LiteralPath $stopScript)) {
        return
    }

    $previousWorktree = $env:EIAAX_WORKTREE
    try {
        $env:EIAAX_WORKTREE = $WorktreeRoot
        Write-Host ("Stopping EIAAX demo for worktree: " + $WorktreeRoot)
        $stopExitCode = Invoke-EiaaxScriptInProcess -FilePath $stopScript
        if ($stopExitCode -ne 0) {
            Exit-EiaaxFailure -Message ("Failed to stop EIAAX demo for worktree: " + $WorktreeRoot)
        }
    }
    finally {
        if ($null -eq $previousWorktree) {
            Remove-Item Env:EIAAX_WORKTREE -ErrorAction SilentlyContinue
        }
        else {
            $env:EIAAX_WORKTREE = $previousWorktree
        }
    }
}

function Sync-EiaaxConvergenceRepository {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedBranch,
        [string]$LogFile = $null
    )

    Write-Host ("Syncing repository: fetch/checkout/pull --ff-only " + $ExpectedBranch)

    Invoke-EiaaxGitCommand `
        -ArgumentList @("fetch", "origin", $ExpectedBranch) `
        -WorkingDirectory $WorktreeRoot `
        -LogFile $LogFile `
        -FailureMessage ("git fetch failed for branch " + $ExpectedBranch)

    Invoke-EiaaxGitCommand `
        -ArgumentList @("checkout", $ExpectedBranch) `
        -WorkingDirectory $WorktreeRoot `
        -LogFile $LogFile `
        -FailureMessage ("git checkout failed for branch " + $ExpectedBranch)

    Invoke-EiaaxGitCommand `
        -ArgumentList @("pull", "--ff-only", "origin", $ExpectedBranch) `
        -WorkingDirectory $WorktreeRoot `
        -LogFile $LogFile `
        -FailureMessage ("git pull --ff-only failed for branch " + $ExpectedBranch)
}

function Get-EiaaxPortOccupantInfo {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $listener = Get-EiaaxListenerPid -Port $Port
    if ($null -eq $listener) {
        return $null
    }

    $serviceName = if ($Port -eq $script:BackendPort) { "backend" } else { "frontend" }
    $commandLine = Get-EiaaxProcessCommandLine -ProcessId $listener
    $managed = Test-EiaaxManagedProcess -ProcessId $listener -WorktreeRoot $WorktreeRoot -ServiceName $serviceName
    $sameWorktree = $false
    if (-not [string]::IsNullOrWhiteSpace($commandLine)) {
        $sameWorktree = $commandLine.ToUpperInvariant().Contains($WorktreeRoot.ToUpperInvariant())
    }

    return [ordered]@{
        Port         = $Port
        ProcessId    = $listener
        CommandLine  = $commandLine
        Managed      = $managed
        SameWorktree = $sameWorktree
        ServiceName  = $serviceName
    }
}

function Clear-EiaaxPortsForConvergence {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    $referenceWorktree = $script:ReferenceDiscoveryWorktree
    $foreign = New-Object System.Collections.Generic.List[string]
    $stopWorktrees = New-Object System.Collections.Generic.List[string]
    $seenStop = @{}

    $queueStop = {
        param([string]$TargetWorktree)
        if ([string]::IsNullOrWhiteSpace($TargetWorktree)) {
            return
        }
        if (-not (Test-Path -LiteralPath $TargetWorktree)) {
            return
        }
        $key = $TargetWorktree.ToUpperInvariant()
        if ($seenStop.ContainsKey($key)) {
            return
        }
        $seenStop[$key] = $true
        [void]$stopWorktrees.Add($TargetWorktree)
    }

    foreach ($port in @($script:BackendPort, $script:FrontendPort)) {
        $info = Get-EiaaxPortOccupantInfo -Port $port -WorktreeRoot $WorktreeRoot
        if ($null -eq $info) {
            Write-Host ("Port " + $port + ": libre.")
            continue
        }

        Write-Host ("Port " + $port + " ocupado por PID " + $info.ProcessId)
        if (-not [string]::IsNullOrWhiteSpace($info.CommandLine)) {
            Write-Host ("  CMD: " + $info.CommandLine)
        }

        if (-not $info.Managed) {
            [void]$foreign.Add("Port " + $port + " used by non-EIAAX process PID " + $info.ProcessId + ".")
            continue
        }

        $normalizedCommand = $info.CommandLine.ToUpperInvariant()
        $convergenceKey = $WorktreeRoot.ToUpperInvariant()
        $referenceKey = $referenceWorktree.ToUpperInvariant()

        if ($normalizedCommand.Contains($convergenceKey)) {
            Write-Host ("  -> proceso EIAAX del worktree convergencia; se detendra.")
            & $queueStop $WorktreeRoot
            continue
        }

        if ($normalizedCommand.Contains($referenceKey)) {
            Write-Host ("  -> proceso EIAAX del entorno INTEGRADO; se detendra via script oficial.")
            & $queueStop $referenceWorktree
            continue
        }

        [void]$foreign.Add("Port " + $port + " used by EIAAX from unsupported worktree (PID " + $info.ProcessId + ").")
    }

    if ($foreign.Count -gt 0) {
        Exit-EiaaxFailure -Message ("Cannot start convergence candidate safely: " + ($foreign -join " "))
    }

    foreach ($target in $stopWorktrees) {
        Invoke-EiaaxDemoStopForWorktree -WorktreeRoot $target -ScriptsDir $ScriptsDir
    }

    foreach ($port in @($script:BackendPort, $script:FrontendPort)) {
        $remaining = Get-EiaaxListenerPid -Port $port
        if ($null -ne $remaining) {
            Exit-EiaaxFailure -Message ("Port " + $port + " still in use by PID " + $remaining + " after stop.")
        }
    }
}

function Confirm-EiaaxStartedProcessWorktree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [int]$BackendPort = $script:BackendPort,
        [int]$FrontendPort = $script:FrontendPort
    )

    foreach ($pair in @(
            @{ Port = $BackendPort; Service = "backend" },
            @{ Port = $FrontendPort; Service = "frontend" }
        )) {
        $listener = Get-EiaaxListenerPid -Port $pair.Port
        if ($null -eq $listener) {
            Exit-EiaaxFailure -Message ($pair.Service + " port " + $pair.Port + " has no listener after start.")
        }

        if (-not (Test-EiaaxManagedProcess -ProcessId $listener -WorktreeRoot $WorktreeRoot -ServiceName $pair.Service)) {
            $commandLine = Get-EiaaxProcessCommandLine -ProcessId $listener
            Exit-EiaaxFailure -Message ($pair.Service + " PID " + $listener + " is not owned by worktree " + $WorktreeRoot + ". CMD=" + $commandLine)
        }

        $commandLine = Get-EiaaxProcessCommandLine -ProcessId $listener
        Write-Host ($pair.Service + " ownership PASS (PID " + $listener + ")")
        if (-not [string]::IsNullOrWhiteSpace($commandLine)) {
            Write-Host ("  CMD: " + $commandLine)
        }
    }

    return $true
}

function Write-EiaaxRuntimeIdentityState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$GitSha,
        [Parameter(Mandatory = $true)]
        [string]$DemoProfile,
        [Parameter(Mandatory = $true)]
        [string]$RuntimeMarker
    )

    Write-EiaaxStateValue -StateDir $StateDir -Name "runtime_git_sha" -Value $GitSha
    Write-EiaaxStateValue -StateDir $StateDir -Name "runtime_demo_profile" -Value $DemoProfile
    Write-EiaaxStateValue -StateDir $StateDir -Name "runtime_marker" -Value $RuntimeMarker
}

function Get-EiaaxBackendRuntimeEnvironment {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DatabaseUrl,
        [Parameter(Mandatory = $true)]
        [string]$StateDir
    )

    $envMap = @{ DATABASE_URL = $DatabaseUrl }
    foreach ($pair in @(
            @{ Name = "runtime_git_sha"; Env = "EIAAX_GIT_SHA" },
            @{ Name = "runtime_demo_profile"; Env = "EIAAX_DEMO_PROFILE" },
            @{ Name = "runtime_marker"; Env = "EIAAX_RUNTIME_MARKER" }
        )) {
        $value = Get-EiaaxStateValue -StateDir $StateDir -Name $pair.Name
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            $envMap[$pair.Env] = $value
        }
    }
    return $envMap
}

function Invoke-EiaaxHealthJson {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [string]$Path = "/health"
    )

    $uri = "http://127.0.0.1:" + $Port + $Path
    try {
        $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 10
        return [ordered]@{
            StatusCode = [int]$response.StatusCode
            Body       = $response.Content
        }
    }
    catch {
        return [ordered]@{
            StatusCode = 0
            Body       = $_.Exception.Message
        }
    }
}

function Confirm-EiaaxRuntimeIdentity {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ExpectedGitSha,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedAlembicHead,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedDemoProfile,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedRuntimeMarker,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedDemoDbName,
        [int]$BackendPort = $script:BackendPort,
        [int]$FrontendPort = $script:FrontendPort
    )

    $backend = Invoke-EiaaxHealthJson -Port $BackendPort -Path "/health"
    if ($backend.StatusCode -ne 200) {
        Exit-EiaaxFailure -Message ("Backend /health failed. Status=" + $backend.StatusCode + " Body=" + $backend.Body)
    }

    $health = $backend.Body | ConvertFrom-Json
    if ($health.status -ne "up") {
        Exit-EiaaxFailure -Message ("Backend health status is not up: " + $health.status)
    }
    if (-not $health.runtime) {
        Exit-EiaaxFailure -Message "Backend /health missing runtime identity block."
    }

    $runtime = $health.runtime
    if ($runtime.git_sha -ne $ExpectedGitSha) {
        Exit-EiaaxFailure -Message ("Runtime git_sha mismatch. Expected " + $ExpectedGitSha + " got " + $runtime.git_sha)
    }
    if ($runtime.demo_profile -ne $ExpectedDemoProfile) {
        Exit-EiaaxFailure -Message ("Runtime demo_profile mismatch. Expected " + $ExpectedDemoProfile + " got " + $runtime.demo_profile)
    }
    if ($runtime.runtime_marker -ne $ExpectedRuntimeMarker) {
        Exit-EiaaxFailure -Message ("Runtime marker mismatch. Expected " + $ExpectedRuntimeMarker + " got " + $runtime.runtime_marker)
    }
    if ($runtime.alembic_current -ne $ExpectedAlembicHead) {
        Exit-EiaaxFailure -Message ("Alembic current mismatch. Expected " + $ExpectedAlembicHead + " got " + $runtime.alembic_current)
    }
    if ($runtime.demo_db_name -ne $ExpectedDemoDbName) {
        Exit-EiaaxFailure -Message ("Demo DB name mismatch. Expected " + $ExpectedDemoDbName + " got " + $runtime.demo_db_name)
    }

    $proxy = Invoke-EiaaxHealthJson -Port $FrontendPort -Path "/health"
    if ($proxy.StatusCode -ne 200) {
        Exit-EiaaxFailure -Message ("Frontend proxy /health failed. Status=" + $proxy.StatusCode)
    }
    $proxyHealth = $proxy.Body | ConvertFrom-Json
    if (-not $proxyHealth.runtime) {
        Exit-EiaaxFailure -Message "Frontend proxy /health missing runtime identity."
    }
    if ($proxyHealth.runtime.git_sha -ne $ExpectedGitSha) {
        Exit-EiaaxFailure -Message "Frontend proxy points to a different backend instance."
    }

    $frontend = Invoke-EiaaxHealthJson -Port $FrontendPort -Path "/"
    if ($frontend.StatusCode -ne 200) {
        Exit-EiaaxFailure -Message ("Frontend root failed. Status=" + $frontend.StatusCode)
    }

    Write-Host "Runtime identity PASS (backend + frontend proxy)."
    return $true
}

function Invoke-EiaaxPythonVersionProbe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    $result = Invoke-EiaaxExternalCommand -FilePath $PythonExe -ArgumentList @("-V")
    return [ordered]@{
        ExitCode = $result.ExitCode
        Text     = $result.Output.Trim()
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
    try {
        $result = Invoke-EiaaxExternalCommand -FilePath $PythonExe -ArgumentList @("-m", "venv", $probeVenv)
        if ($result.ExitCode -ne 0) {
            return "venv probe failed for " + $PythonExe
        }

        $probePython = Get-EiaaxVenvPythonPathForDirectory -VenvPath $probeVenv
        if ([string]::IsNullOrWhiteSpace($probePython)) {
            return "venv probe created no python interpreter"
        }

        return $null
    }
    finally {
        if (Test-Path -LiteralPath $probeVenv) {
            Remove-Item -LiteralPath $probeVenv -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Confirm-EiaaxProductionPrerequisites {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [string]$LogFile = $null,
        [string]$ResolvedPython = $null,
        [switch]$SkipPythonCheck
    )

    Write-Host "Checking production prerequisites..."
    Test-EiaaxWorktree -WorktreeRoot $WorktreeRoot

    if (-not $SkipPythonCheck) {
        $python = if (-not [string]::IsNullOrWhiteSpace($ResolvedPython)) {
            $ResolvedPython
        }
        else {
            Resolve-EiaaxPython -LogFile $LogFile -WorktreeRoot $WorktreeRoot
        }
        if ([string]::IsNullOrWhiteSpace($python)) {
            Exit-EiaaxFailure -Message "PYTHON NOT FOUND during production prerequisite check."
        }

        $versionLine = Get-EiaaxPythonVersionLine -PythonExe $python
        Write-Host ("Production Python OK: " + $python + " (" + $versionLine + ")")
    }

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Exit-EiaaxFailure -Message "npm not found in PATH."
    }
    Write-Host ("Production npm OK: " + $npm.Source)

    if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
        $pythonNote = if ($SkipPythonCheck) { "skipped" } else { $python }
        Write-EiaaxLogLine -LogFile $LogFile -Message ("Production prerequisites OK. Python=" + $pythonNote)
    }
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
    $venvPython = Get-EiaaxVenvPythonPathForDirectory -VenvPath $paths.Venv
    if ([string]::IsNullOrWhiteSpace($venvPython)) {
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

function Resolve-EiaaxNpmCmdExecutable {
    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -ne $npmCmd) {
        return $npmCmd.Source
    }

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -ne $npm) {
        $source = $npm.Source
        if ($source -match '\.cmd$') {
            return $source
        }

        $parent = Split-Path -Parent $source
        $siblingCmd = Join-Path $parent "npm.cmd"
        if (Test-Path -LiteralPath $siblingCmd) {
            return $siblingCmd
        }
    }

    Exit-EiaaxFailure -Message "npm.cmd not found in PATH. Install Node.js and ensure npm.cmd is available."
}

function Get-EiaaxBatchQuotedArgument {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $escaped = $Value -replace '"', '""'
    return '"' + $escaped + '"'
}

function Get-EiaaxLogTail {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LogFile,
        [int]$MaxLines = 30
    )

    if (-not (Test-Path -LiteralPath $LogFile)) {
        return "(log file not found: " + $LogFile + ")"
    }

    $lines = @(Get-Content -LiteralPath $LogFile -ErrorAction SilentlyContinue)
    if ($lines.Count -eq 0) {
        return "(log file empty)"
    }

    $start = [Math]::Max(0, $lines.Count - $MaxLines)
    return ($lines[$start..($lines.Count - 1)] -join "`n")
}

function New-EiaaxStartupFailureMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Summary,
        [Parameter(Mandatory = $true)]
        [string]$LogFile,
        [int]$WrapperPid = 0
    )

    $parts = New-Object System.Collections.Generic.List[string]
    [void]$parts.Add($Summary)
    if ($WrapperPid -gt 0) {
        $wrapperProc = Get-Process -Id $WrapperPid -ErrorAction SilentlyContinue
        if ($null -eq $wrapperProc) {
            [void]$parts.Add("Wrapper process PID " + $WrapperPid + " has exited.")
        }
        else {
            [void]$parts.Add("Wrapper process PID " + $WrapperPid + " is still running.")
        }
    }
    [void]$parts.Add("Recent log output:")
    [void]$parts.Add((Get-EiaaxLogTail -LogFile $LogFile))
    return ($parts -join "`n")
}

function Test-EiaaxReuseRunningService {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [Parameter(Mandatory = $true)]
        [string]$ServiceName,
        [Parameter(Mandatory = $true)]
        [scriptblock]$ReadyTest,
        [Parameter(Mandatory = $true)]
        [string]$ReadyLabel
    )

    $listener = Get-EiaaxListenerPid -Port $Port
    if ($null -eq $listener) {
        return $false
    }

    if (-not (Test-EiaaxManagedProcess -ProcessId $listener -WorktreeRoot $WorktreeRoot -ServiceName $ServiceName)) {
        Exit-EiaaxFailure -Message ("Port " + $Port + " is already in use by PID " + $listener + " (not an EIAAX " + $ServiceName + "). Stop it manually before retrying.")
    }

    if (-not (& $ReadyTest)) {
        Exit-EiaaxFailure -Message ("Port " + $Port + " is used by EIAAX " + $ServiceName + " PID " + $listener + " but " + $ReadyLabel + " check failed.")
    }

    Write-Host ($ServiceName + " already running at http://127.0.0.1:" + $Port + " (PID " + $listener + "); reusing.")
    return $true
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

function Build-EiaaxManagedProcessWrapperContent {
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
        [string]$WrapperName,
        [hashtable]$Environment = @{}
    )

    $lines = New-Object System.Collections.Generic.List[string]
    [void]$lines.Add("@echo off")
    foreach ($key in $Environment.Keys) {
        [void]$lines.Add("set " + $key + "=" + $Environment[$key])
    }
    [void]$lines.Add("cd /d " + (Get-EiaaxBatchQuotedArgument -Value $WorkingDirectory))

    $commandParts = New-Object System.Collections.Generic.List[string]
    $executableLower = $FilePath.ToLowerInvariant()
    if ($executableLower.EndsWith(".cmd") -or $executableLower.EndsWith(".bat")) {
        [void]$commandParts.Add("call")
    }
    [void]$commandParts.Add((Get-EiaaxBatchQuotedArgument -Value $FilePath))
    foreach ($arg in $ArgumentList) {
        [void]$commandParts.Add((Get-EiaaxBatchQuotedArgument -Value ([string]$arg)))
    }
    $command = ($commandParts -join " ")
    $redirect = " >> " + (Get-EiaaxBatchQuotedArgument -Value $LogFile) + " 2>>&1"
    [void]$lines.Add($command + $redirect)
    [void]$lines.Add("echo [EIAAX] EXIT_CODE=%ERRORLEVEL%>> " + (Get-EiaaxBatchQuotedArgument -Value $LogFile))
    return ,$lines.ToArray()
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
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -LogFile $LogFile `
        -WrapperName $WrapperName `
        -Environment $Environment

    [System.IO.File]::WriteAllLines($wrapperBat, $lines)

    $launcher = Start-Process -FilePath $wrapperBat -WorkingDirectory $WorkingDirectory -PassThru -WindowStyle Hidden
    if ($null -eq $launcher) {
        Exit-EiaaxFailure -Message ("Failed to launch managed process wrapper: " + $WrapperName)
    }
    return $launcher
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
    $headsResult = Invoke-EiaaxExternalCommand -FilePath $VenvPython `
        -ArgumentList @("-m", "alembic", "heads") `
        -WorkingDirectory $BackendDir
    if ($headsResult.ExitCode -ne 0) {
        Exit-EiaaxFailure -Message ("alembic heads failed. ExitCode=" + $headsResult.ExitCode + " Output=" + $headsResult.Output.Trim())
    }

    $headsOutput = $headsResult.Output
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

    $currentResult = Invoke-EiaaxExternalCommand -FilePath $VenvPython `
        -ArgumentList @("-m", "alembic", "current") `
        -WorkingDirectory $BackendDir
    if ($currentResult.ExitCode -ne 0) {
        Exit-EiaaxFailure -Message ("alembic current failed. ExitCode=" + $currentResult.ExitCode + " Output=" + $currentResult.Output.Trim())
    }

    $currentOutput = $currentResult.Output
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

function Test-EiaaxScriptUtf8Bom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    return ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
}

function Get-EiaaxParserValidationFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    return @(Get-ChildItem -LiteralPath $ScriptsDir -Filter "*.ps1" |
        Where-Object { $_.Name -ne "validate_ps_parse.ps1" } |
        Sort-Object Name)
}

function Ensure-EiaaxWindowsScriptsUtf8Bom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptsDir
    )

    $updated = New-Object System.Collections.Generic.List[string]
    foreach ($file in (Get-EiaaxParserValidationFiles -ScriptsDir $ScriptsDir)) {
        if (Test-EiaaxScriptUtf8Bom -Path $file.FullName) {
            continue
        }
        $text = [System.IO.File]::ReadAllText($file.FullName, [System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::WriteAllText($file.FullName, $text, [System.Text.UTF8Encoding]::new($true))
        [void]$updated.Add($file.Name)
    }
    return @($updated)
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
        [string[]]$ArgumentList = @(),
        [int]$TimeoutSec = 0
    )

    $shell = Get-EiaaxWindowsPowerShellExecutable
    $argumentList = @("-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $FilePath) + $ArgumentList
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $process = Start-Process `
            -FilePath $shell `
            -ArgumentList $argumentList `
            -PassThru `
            -NoNewWindow `
            -RedirectStandardOutput $stdoutFile `
            -RedirectStandardError $stderrFile
        if ($null -eq $process) {
            Exit-EiaaxFailure -Message ("Failed to start PowerShell process for: " + $FilePath)
        }

        $waitMs = if ($TimeoutSec -gt 0) { $TimeoutSec * 1000 } else { [int]::MaxValue }
        $completed = $process.WaitForExit($waitMs)
        if (-not $completed) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            return 124
        }

        if (Test-Path -LiteralPath $stdoutFile) {
            $stdout = Get-Content -LiteralPath $stdoutFile -Raw -ErrorAction SilentlyContinue
            if (-not [string]::IsNullOrWhiteSpace($stdout)) {
                Write-Host $stdout.TrimEnd()
            }
        }
        if (Test-Path -LiteralPath $stderrFile) {
            $stderr = Get-Content -LiteralPath $stderrFile -Raw -ErrorAction SilentlyContinue
            if (-not [string]::IsNullOrWhiteSpace($stderr)) {
                Write-Host $stderr.TrimEnd()
            }
        }

        return [int]$process.ExitCode
    }
    finally {
        Remove-Item -LiteralPath $stdoutFile -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $stderrFile -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-EiaaxScriptInProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    & $FilePath @ArgumentList
    return [int]$LASTEXITCODE
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

    $shell = Get-EiaaxWindowsPowerShellExecutable
    Write-Host ("Parser shell: " + $shell)
    $parseExitCode = Invoke-EiaaxPowerShellFile -FilePath $validator
    if ($parseExitCode -ne 0) {
        Exit-EiaaxFailure -Message ("PowerShell parser validation failed (exit " + $parseExitCode + "). See FAILED FILES above.")
    }
}
