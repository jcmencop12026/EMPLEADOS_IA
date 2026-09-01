#Requires -Version 5.1
<#
.SYNOPSIS
    Funciones compartidas para la demo EIAAX en Windows (SQLite local).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:DefaultWorktree = "D:\EMPLEADOS_IA_INTEGRADO"
$script:BackendPort = 8000
$script:FrontendPort = 5180
$script:VenvDirName = ".venv-eiaax-demo"
$script:StateDirName = ".eiaax-demo"

function Get-EiaaxWorktreeRoot {
    $root = $env:EIAAX_WORKTREE
    if ([string]::IsNullOrWhiteSpace($root)) {
        $root = $script:DefaultWorktree
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
    $dbFile = Join-Path $data "eiaax_integrado_demo.db"

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

    $posix = ($DbFilePath -replace '\\', '/')
    return "sqlite:///$posix"
}

function Get-EiaaxDatabaseUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    return ConvertTo-SqliteDatabaseUrl -DbFilePath $paths.DbFile
}

function Test-EiaaxWorktree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    foreach ($required in @($paths.Backend, $paths.Frontend)) {
        if (-not (Test-Path -LiteralPath $required)) {
            throw "No se encontró la ruta requerida: ${required}"
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $paths.Backend "requirements.txt"))) {
        throw "Falta backend\requirements.txt en ${WorktreeRoot}"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $paths.Frontend "package.json"))) {
        throw "Falta frontend\package.json en ${WorktreeRoot}"
    }
}

function Find-EiaaxPython {
    param(
        [string[]]$Candidates = @(
            $env:EIAAX_PYTHON,
            "C:\Python314\python.exe",
            "C:\Python313\python.exe",
            "C:\Python312\python.exe"
        )
    )

    foreach ($candidate in $Candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    foreach ($version in @("3.14", "3.13", "3.12")) {
        $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
        if ($null -ne $pyLauncher) {
            $versioned = & py "-${version}" -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($versioned)) {
                return $versioned.Trim()
            }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        return $python.Source
    }

    throw "No se encontró Python compatible. Instale Python 3.12+ o defina EIAAX_PYTHON."
}

function Get-EiaaxVenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $paths = Get-EiaaxPaths -WorktreeRoot $WorktreeRoot
    $venvPython = Join-Path $paths.Venv "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Entorno virtual no preparado. Ejecute primero scripts\windows\preparar_demo_eiaax.ps1"
    }
    return $venvPython
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

function Write-EiaaxPidFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    $file = Join-Path $StateDir "${Name}.pid"
    Set-Content -LiteralPath $file -Value $ProcessId -Encoding ascii
}

function Get-EiaaxPidFromFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateDir,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $file = Join-Path $StateDir "${Name}.pid"
    if (-not (Test-Path -LiteralPath $file)) {
        return $null
    }
    $raw = (Get-Content -LiteralPath $file -Raw).Trim()
    if ($raw -match '^\d+$') {
        return [int]$raw
    }
    return $null
}

function Stop-ListenerOnPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $stopped = @()
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $procId = [int]$conn.OwningProcess
        if ($procId -le 0) {
            continue
        }
        Write-Host "Deteniendo proceso ${procId} escuchando en puerto ${Port}"
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        $stopped += $procId
    }
    return $stopped
}

function Stop-EiaaxPidIfRunning {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        return $false
    }
    Write-Host "Deteniendo ${Label} (PID ${ProcessId})"
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    return $true
}

function Test-EiaaxHealth {
    param(
        [int]$Port = $script:BackendPort,
        [int]$TimeoutSec = 30
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

function Assert-EiaaxNotOriginalTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorktreeRoot
    )

    $normalized = ($WorktreeRoot.TrimEnd('\') + '\').ToUpperInvariant()
    if ($normalized -eq "D:\EMPLEADOS_IA\") {
        throw "Refusing to operate on D:\EMPLEADOS_IA. Use D:\EMPLEADOS_IA_INTEGRADO or set EIAAX_WORKTREE."
    }
}
