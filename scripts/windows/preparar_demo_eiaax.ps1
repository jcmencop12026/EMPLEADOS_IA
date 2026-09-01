#Requires -Version 5.1
<#
.SYNOPSIS
    Prepara la demo EIAAX (venv Python, dependencias, SQLite, seed, frontend build).
#>

param(
    [switch]$SkipFrontendBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$worktree = Get-EiaaxWorktreeRoot
Assert-EiaaxNotOriginalTree -WorktreeRoot $worktree
Test-EiaaxWorktree -WorktreeRoot $worktree
$paths = Get-EiaaxPaths -WorktreeRoot $worktree
$databaseUrl = Get-EiaaxDatabaseUrl -WorktreeRoot $worktree

Write-Host "=== EIAAX demo — preparación ==="
Write-Host "Worktree: ${worktree}"
Write-Host "DATABASE_URL: ${databaseUrl}"

if (-not (Test-Path -LiteralPath $paths.Data)) {
    New-Item -ItemType Directory -Path $paths.Data | Out-Null
}

$basePython = Find-EiaaxPython
Write-Host "Python base: ${basePython}"
& $basePython -c "import sys; print('Python', sys.version)"
if ($LASTEXITCODE -ne 0) {
    throw "Python base no ejecutable: ${basePython}"
}

if (-not (Test-Path -LiteralPath $paths.Venv)) {
    Write-Host "Creando entorno virtual en $($paths.Venv)"
    & $basePython -m venv $paths.Venv
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo crear el entorno virtual. Pruebe otra versión de Python (3.12/3.13) con EIAAX_PYTHON."
    }
}

$venvPython = Get-EiaaxVenvPython -WorktreeRoot $worktree
Write-Host "Actualizando pip en el entorno virtual..."
& $venvPython -m pip install --upgrade pip wheel
if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade falló en el entorno virtual."
}

Write-Host "Instalando dependencias backend..."
& $venvPython -m pip install -r (Join-Path $paths.Backend "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Instalación backend falló. Si usa Python 3.14, pruebe EIAAX_PYTHON apuntando a 3.12 o 3.13."
}

$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($null -eq $npm) {
    throw "npm no encontrado en PATH."
}

Push-Location $paths.Frontend
try {
    if (Test-Path -LiteralPath "package-lock.json") {
        Write-Host "Instalando dependencias frontend (npm ci)..."
        npm ci
    }
    else {
        Write-Host "Instalando dependencias frontend (npm install)..."
        npm install
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Instalación frontend falló."
    }

    if (-not $SkipFrontendBuild) {
        Write-Host "Compilando frontend (npm run build)..."
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Build frontend falló."
        }
    }
}
finally {
    Pop-Location
}

Write-Host "Ejecutando seed demo (recrea la BD SQLite demo)..."
$env:DATABASE_URL = $databaseUrl
Push-Location $paths.Backend
try {
    & $venvPython "scripts\seed_lote3_demo.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Seed demo falló."
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Preparación completada."
Write-Host "Siguiente paso: scripts\windows\iniciar_demo_eiaax.ps1"
Write-Host "URL prevista: http://127.0.0.1:5180"
Write-Host "Usuarios demo: org_a_admin / DemoA2026!  (ver backend\scripts\credentials.example)"
