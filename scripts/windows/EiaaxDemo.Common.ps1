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
        [string]$WorkingDirectory = $null
    )

    if (Test-EiaaxInteractiveInvocationRisk -FilePath $FilePath -ArgumentList $ArgumentList) {
        Exit-EiaaxFailure -Message ("Refusing interactive invocation without arguments: " + $FilePath)
    }

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $locationPushed = $false
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
        if ($locationPushed) {
            Pop-Location
        }
        $ErrorActionPreference = $previousPreference
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

function Get-EiaaxReferencePyvenvCfgPath {
    param(
        [string]$ReferenceWorktree = $script:ReferenceDiscoveryWorktree
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

function Get-EiaaxPythonDiscoveryCandidates {
    $ordered = New-Object System.Collections.Generic.List[string]
    $seen = @{}

    $addCandidate = {
        param([string]$CandidatePath)
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

    # A. Explicit override.
    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        & $addCandidate $env:EIAAX_PYTHON
    }

    # B. Python base derived from the functional reference venv (discovery only).
    $referenceCfg = Get-EiaaxReferencePyvenvCfgPath
    if (Test-Path -LiteralPath $referenceCfg) {
        foreach ($referencePath in (Get-EiaaxPythonCandidatesFromPyvenvCfg -PyvenvCfgPath $referenceCfg)) {
            & $addCandidate $referencePath
        }
    }

    # C. py launcher.
    foreach ($launcherPath in (Get-EiaaxPythonLauncherCandidates)) {
        & $addCandidate $launcherPath
    }

    # D. where.exe and PATH.
    foreach ($wherePath in (Get-EiaaxPythonWhereCandidates)) {
        & $addCandidate $wherePath
    }

    foreach ($pathDir in (($env:PATH) -split ';')) {
        if ([string]::IsNullOrWhiteSpace($pathDir)) {
            continue
        }
        $trimmed = $pathDir.Trim()
        $pathCandidate = Join-EiaaxPathMaybe -Base $trimmed -Child "python.exe"
        & $addCandidate $pathCandidate
        $pathCandidate3 = Join-EiaaxPathMaybe -Base $trimmed -Child "python3.exe"
        & $addCandidate $pathCandidate3
    }

    foreach ($commandName in @("python", "python3")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($null -ne $command -and $command.CommandType -eq "Application") {
            & $addCandidate $command.Source
        }
    }

    # E. Registry.
    foreach ($registryPath in (Get-EiaaxPythonRegistryCandidates)) {
        & $addCandidate $registryPath
    }

    # F. Standard known installations.
    foreach ($staticPath in @(
            "C:\Python314\python.exe",
            "C:\Python313\python.exe",
            "C:\Python312\python.exe",
            "C:\Python311\python.exe"
        )) {
        & $addCandidate $staticPath
    }

    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        foreach ($version in @("314", "313", "312", "311")) {
            $programFilesPath = Join-Path $env:ProgramFiles ("Python" + $version + "\python.exe")
            & $addCandidate $programFilesPath
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($env:LocalAppData)) {
        $userPythonRoot = Join-Path $env:LocalAppData "Programs\Python"
        if (Test-Path -LiteralPath $userPythonRoot) {
            $versionDirs = Get-ChildItem -LiteralPath $userPythonRoot -ErrorAction SilentlyContinue |
                Where-Object { $_.PSIsContainer }
            foreach ($versionDir in $versionDirs) {
                $userPython = Join-Path $versionDir.FullName "python.exe"
                & $addCandidate $userPython
            }
        }
    }

    if (Test-Path -LiteralPath "C:\") {
        $pythonRoots = Get-ChildItem -Path "C:\" -ErrorAction SilentlyContinue |
            Where-Object { $_.PSIsContainer -and $_.Name -like "Python*" }
        foreach ($root in $pythonRoots) {
            $rootPython = Join-Path $root.FullName "python.exe"
            & $addCandidate $rootPython
        }
    }

    return [string[]]$ordered.ToArray()
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

    Push-Location $WorktreeRoot
    try {
        $branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
        return $branch.Trim()
    }
    finally {
        Pop-Location
    }
}

function Get-EiaaxGitShortSha {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

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

    $venvPython = Join-Path $VenvPath "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        $result.Reason = "Scripts\python.exe missing"
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
        Invoke-EiaaxPowerShellFile -FilePath $stopScript | Out-Null
        if ($LASTEXITCODE -ne 0) {
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
        [string]$ExpectedBranch
    )

    Push-Location $WorktreeRoot
    try {
        Write-Host ("Syncing repository: fetch/checkout/pull " + $ExpectedBranch)
        & git fetch origin $ExpectedBranch 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message ("git fetch failed for branch " + $ExpectedBranch)
        }

        & git checkout $ExpectedBranch 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message ("git checkout failed for branch " + $ExpectedBranch)
        }

        & git pull origin $ExpectedBranch 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Exit-EiaaxFailure -Message ("git pull failed for branch " + $ExpectedBranch)
        }
    }
    finally {
        Pop-Location
    }
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
        [string]$LogFile = $null,
        [string]$WorktreeRoot = $null
    )

    if (-not [string]::IsNullOrWhiteSpace($env:EIAAX_PYTHON)) {
        $explicitPath = Get-EiaaxResolvedPythonPath -Path $env:EIAAX_PYTHON
        if ($null -eq $explicitPath) {
            Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: EIAAX_PYTHON is not a valid python executable: " + $env:EIAAX_PYTHON)
        }

        $explicitProbe = Test-EiaaxPythonRuntimeCandidate -PythonExe $explicitPath
        if ($explicitProbe.Executable) {
            $selectedMessage = "Selected Python (EIAAX_PYTHON): " + $explicitPath + " (" + $explicitProbe.Version + ")"
            Write-Host $selectedMessage
            if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
                Write-EiaaxLogLine -LogFile $LogFile -Message $selectedMessage
            }
            return $explicitPath
        }

        Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: EIAAX_PYTHON failed python -V: " + $env:EIAAX_PYTHON + " -> " + $explicitProbe.Error)
    }

    if (-not [string]::IsNullOrWhiteSpace($WorktreeRoot)) {
        $venvPython = Join-Path (Join-Path $WorktreeRoot $script:VenvDirName) "Scripts\python.exe"
        $venvResolved = Get-EiaaxResolvedPythonPath -Path $venvPython
        if ($null -ne $venvResolved) {
            $venvProbe = Test-EiaaxPythonRuntimeCandidate -PythonExe $venvResolved
            if ($venvProbe.Executable) {
                $selectedMessage = "Selected Python (existing venv): " + $venvResolved + " (" + $venvProbe.Version + ")"
                Write-Host $selectedMessage
                if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
                    Write-EiaaxLogLine -LogFile $LogFile -Message $selectedMessage
                }
                return $venvResolved
            }
        }
    }

    $candidates = @(Get-EiaaxPythonDiscoveryCandidates)
    if (Get-EiaaxCollectionCount $candidates -eq 0) {
        $referenceCfg = Get-EiaaxReferencePyvenvCfgPath
        $cfgHint = ""
        if (Test-Path -LiteralPath $referenceCfg) {
            $cfg = Read-EiaaxPyvenvCfg -PyvenvCfgPath $referenceCfg
            if (-not [string]::IsNullOrWhiteSpace($cfg.version)) {
                $cfgHint = " Reference pyvenv.cfg version=" + $cfg.version + "."
            }
        }
        Exit-EiaaxFailure -Message ("PYTHON NOT FOUND: no python.exe candidates detected. Tried EIAAX_PYTHON, reference pyvenv.cfg (" + $referenceCfg + "), py launcher, where.exe, PATH, registry and standard install paths." + $cfgHint + " Set EIAAX_PYTHON to a full python.exe path if needed.")
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

function Confirm-EiaaxProductionPrerequisites {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot,
        [string]$LogFile = $null
    )

    Write-Host "Checking production prerequisites..."
    Test-EiaaxWorktree -WorktreeRoot $WorktreeRoot

    $python = Find-EiaaxPython -LogFile $LogFile -WorktreeRoot $WorktreeRoot
    if ([string]::IsNullOrWhiteSpace($python)) {
        Exit-EiaaxFailure -Message "PYTHON NOT FOUND during production prerequisite check."
    }

    $versionLine = Get-EiaaxPythonVersionLine -PythonExe $python
    Write-Host ("Production Python OK: " + $python + " (" + $versionLine + ")")

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Exit-EiaaxFailure -Message "npm not found in PATH."
    }
    Write-Host ("Production npm OK: " + $npm.Source)

    if (-not [string]::IsNullOrWhiteSpace($LogFile)) {
        Write-EiaaxLogLine -LogFile $LogFile -Message ("Production prerequisites OK. Python=" + $python)
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
    [void]$lines.Add($command + " >> " + (Get-EiaaxBatchQuotedArgument -Value $LogFile) + " 2>>&1")
    [void]$lines.Add("echo [EIAAX] EXIT_CODE=%ERRORLEVEL%>> " + (Get-EiaaxBatchQuotedArgument -Value $LogFile))

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
