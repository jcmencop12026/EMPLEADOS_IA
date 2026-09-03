#requires -Version 5.1
<#
.SYNOPSIS
    Cierre local seguro de respaldo EIAAX base Windows real operativa 0014a4b.

.DESCRIPTION
    - Verifica tag/commit protegido
    - Crea bundle Git local desde origin/tag (no copia bundle remoto)
    - Backup SQLite consistente via sqlite3.Connection.backup()
    - Verifica recuperabilidad (bundle + BD copia)
    - Genera manifiesto local
    - Resultado final PASS/FAIL (fail-closed)

    NO modifica producto, ramas, tag existente ni BD activa.
    NO usa Copy-Item sobre la BD origen.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Constantes protegidas (no modificar en ejecución) ---
$Script:ProtectedShortSha = '0014a4b'
$Script:ProtectedFullSha  = '0014a4b01a3ccf3e849a6609c8c784873f20f497'
$Script:ProtectedTag      = 'eiaax-v1-windows-real-operativo-0014a4b'
$Script:ProtectedBranch   = 'cursor/convergencia-comercial-v1-85e4'
$Script:AlembicRevision   = '1820a1b2c3d4e'
$Script:RepoRoot          = 'D:\EMPLEADOS_IA_CONVERGENCIA'
$Script:BackupRoot        = 'D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_WINDOWS_REAL_OPERATIVO_0014a4b'
$Script:BundleFileName    = 'eiaax-v1-windows-real-operativo-0014a4b.bundle'
$Script:DbSource          = 'D:\EMPLEADOS_IA_CONVERGENCIA\data\eiaax_integrado_demo.db'

$Script:Results = [ordered]@{
    RepoRootVerified        = $false
    TagVerified             = $false
    BundleCreated           = $false
    BundleVerify            = $false
    BundleRestoreTest       = $false
    SqliteBackup            = $false
    SqliteIntegrity         = $false
    ManifestWritten         = $false
}

$Script:Artifacts = @{}

function Write-Step([string]$Message) {
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Write-Host "[$ts] $Message"
}

function Stop-Respaldo([string]$Message, [int]$ExitCode = 1) {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Red
    Write-Host ' RESULTADO FINAL: FAIL' -ForegroundColor Red
    Write-Host " Motivo: $Message" -ForegroundColor Red
    Write-Host '============================================================' -ForegroundColor Red
    Write-Host ''
    Write-Host 'Verificaciones:'
    foreach ($key in $Script:Results.Keys) {
        $mark = if ($Script:Results[$key]) { 'PASS' } else { 'FAIL' }
        Write-Host ("  {0,-24} {1}" -f $key, $mark)
    }
    exit $ExitCode
}

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Resolve-PythonExecutable {
    $candidates = @(
        (Join-Path $Script:RepoRoot '.venv\Scripts\python.exe'),
        (Join-Path $Script:RepoRoot 'venv\Scripts\python.exe'),
        (Join-Path $Script:RepoRoot 'backend\.venv\Scripts\python.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    $fallback = (Get-Command python -ErrorAction SilentlyContinue)
    if ($fallback) { return $fallback.Source }
    $fallback = (Get-Command py -ErrorAction SilentlyContinue)
    if ($fallback) { return 'py' }
    Stop-Respaldo 'No se encontró Python del proyecto (.venv) ni python/py en PATH.'
}

function Invoke-Git {
    param(
        [Parameter(Mandatory)][string[]]$Args,
        [switch]$AllowFailure
    )
    $output = & git -C $Script:RepoRoot @Args 2>&1
    if (-not $AllowFailure -and $LASTEXITCODE -ne 0) {
        $text = ($output | Out-String).Trim()
        Stop-Respaldo "git $($Args -join ' ') falló: $text"
    }
    return ,$output
}

try {
    Write-Step 'EIAAX — Cierre local seguro respaldo 0014a4b'
    Write-Step "Script: $PSCommandPath"

    if (-not (Test-Path -LiteralPath $Script:RepoRoot)) {
        Stop-Respaldo "Repositorio no encontrado: $($Script:RepoRoot)"
    }

    Set-Location -LiteralPath $Script:RepoRoot
    $Script:Results.RepoRootVerified = $true
    Write-Step "Directorio de trabajo: $Script:RepoRoot"

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Stop-Respaldo 'git no está disponible en PATH.'
    }

    # --- 1. Verificar tag/commit ---
    Write-Step 'Verificando tag remoto/local...'
    Invoke-Git -Args @('fetch', '--tags', 'origin', $Script:ProtectedTag) | Out-Null

    $tagCommit = (Invoke-Git -Args @('rev-parse', "$($Script:ProtectedTag)^{commit}")) -join '' | ForEach-Object { $_.Trim() }
    if ($tagCommit -ne $Script:ProtectedFullSha) {
        Stop-Respaldo "Tag $($Script:ProtectedTag) apunta a $tagCommit, se esperaba $($Script:ProtectedFullSha)."
    }
    $Script:Results.TagVerified = $true
    Write-Step "Tag verificado: $($Script:ProtectedTag) -> $tagCommit"

    $headSha = (Invoke-Git -Args @('rev-parse', 'HEAD')) -join '' | ForEach-Object { $_.Trim() }
    Write-Step "HEAD actual del repositorio: $headSha (no se modifica)"

    # --- 2. Preparar destino ---
    if (-not (Test-Path -LiteralPath $Script:BackupRoot)) {
        New-Item -ItemType Directory -Path $Script:BackupRoot -Force | Out-Null
    }
    $bundlePath = Join-Path $Script:BackupRoot $Script:BundleFileName
    $manifestPath = Join-Path $Script:BackupRoot 'MANIFIESTO_RESPALDO_LOCAL.md'
    $sqliteReportPath = Join-Path $Script:BackupRoot 'sqlite_backup_report.json'

    # --- 3. Bundle local desde tag (no copiar bundle remoto) ---
    Write-Step 'Creando bundle Git local desde origin/tag...'
    if (Test-Path -LiteralPath $bundlePath) {
        Remove-Item -LiteralPath $bundlePath -Force
    }
    Invoke-Git -Args @(
        'bundle', 'create', $bundlePath,
        "refs/tags/$($Script:ProtectedTag)",
        "origin/$($Script:ProtectedBranch)"
    ) | Out-Null
    if (-not (Test-Path -LiteralPath $bundlePath)) {
        Stop-Respaldo "No se creó el bundle en $bundlePath"
    }
    $Script:Results.BundleCreated = $true
    $Script:Artifacts.BundlePath = $bundlePath
    $Script:Artifacts.BundleSizeBytes = (Get-Item -LiteralPath $bundlePath).Length
    $Script:Artifacts.BundleSha256 = Get-FileSha256 $bundlePath
    Write-Step "Bundle creado: $bundlePath ($($Script:Artifacts.BundleSizeBytes) bytes)"

    Write-Step 'Verificando bundle (git bundle verify)...'
    $verifyOutput = (& git bundle verify $bundlePath 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or $verifyOutput -notmatch 'is okay') {
        Stop-Respaldo "git bundle verify falló: $verifyOutput"
    }
    $Script:Results.BundleVerify = $true
    Write-Step 'git bundle verify: PASS'

    # --- 4. Prueba restauración temporal ---
    Write-Step 'Prueba de restauración temporal desde bundle...'
    $tempRoot = Join-Path $env:TEMP ("eiaax_restore_test_{0}" -f $Script:ProtectedShortSha)
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    $tempRepo = Join-Path $tempRoot 'restored'
    & git clone $bundlePath $tempRepo 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Stop-Respaldo 'git clone desde bundle falló.'
    }
    Push-Location $tempRepo
    try {
        & git checkout $Script:ProtectedTag 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Stop-Respaldo "checkout tag $($Script:ProtectedTag) falló en restauración temporal."
        }
        $restoredSha = (git rev-parse HEAD).Trim()
        if ($restoredSha -ne $Script:ProtectedFullSha) {
            Stop-Respaldo "SHA restaurado $restoredSha != $($Script:ProtectedFullSha)"
        }
    }
    finally {
        Pop-Location
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
    $Script:Results.BundleRestoreTest = $true
    Write-Step "Restauración temporal: PASS ($restoredSha)"

    # --- 5. Backup SQLite consistente ---
    Write-Step 'Iniciando backup SQLite consistente (sqlite3 backup API)...'
    if (-not (Test-Path -LiteralPath $Script:DbSource)) {
        Stop-Respaldo "BD origen no encontrada: $($Script:DbSource)"
    }

    $walPath = "$Script:DbSource-wal"
    $shmPath = "$Script:DbSource-shm"
    $Script:Artifacts.WalPresent = Test-Path -LiteralPath $walPath
    $Script:Artifacts.ShmPresent = Test-Path -LiteralPath $shmPath

    $pythonExe = Resolve-PythonExecutable
    $helperScript = Join-Path $PSScriptRoot 'Backup-SqliteConsistente-0014a4b.py'
    if (-not (Test-Path -LiteralPath $helperScript)) {
        Stop-Respaldo "Helper Python no encontrado: $helperScript"
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
    $sqliteBackupName = "eiaax_integrado_demo_0014a4b_$timestamp.db"
    $sqliteBackupPath = Join-Path $Script:BackupRoot $sqliteBackupName

    $pyArgs = @(
        $helperScript,
        $Script:DbSource,
        $sqliteBackupPath,
        $sqliteReportPath
    )
    if ($pythonExe -eq 'py') {
        $pyOutput = & py -3 @pyArgs 2>&1
    }
    else {
        $pyOutput = & $pythonExe @pyArgs 2>&1
    }
    if ($LASTEXITCODE -ne 0) {
        $text = ($pyOutput | Out-String).Trim()
        Stop-Respaldo "Backup SQLite falló: $text"
    }

    $sqliteReport = Get-Content -LiteralPath $sqliteReportPath -Raw | ConvertFrom-Json
    if ($sqliteReport.integrity_check -ne 'ok') {
        Stop-Respaldo "integrity_check de la copia no es ok: $($sqliteReport.integrity_check)"
    }

    $Script:Results.SqliteBackup = $true
    $Script:Results.SqliteIntegrity = $true
    $Script:Artifacts.SqliteBackupPath = $sqliteBackupPath
    $Script:Artifacts.SqliteSizeBytes = [int64]$sqliteReport.size_bytes
    $Script:Artifacts.SqliteSha256 = [string]$sqliteReport.sha256
    Write-Step "Backup SQLite: PASS ($sqliteBackupPath)"

    # --- 6. Manifiesto local ---
    $utcNow = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $localNow = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')

    $manifest = @"
# MANIFIESTO DE RESPALDO LOCAL — EIAAX V1 Windows Real Operativo

| Campo | Valor |
|-------|-------|
| **PROYECTO** | EIAAX |
| **TIPO** | BASE WINDOWS REAL OPERATIVA — CIERRE LOCAL |
| **SHA corto** | ``$($Script:ProtectedShortSha)`` |
| **SHA completo** | ``$($Script:ProtectedFullSha)`` |
| **Tag** | ``$($Script:ProtectedTag)`` |
| **Rama histórica** | ``$($Script:ProtectedBranch)`` |
| **Alembic head/current** | ``$($Script:AlembicRevision)`` |
| **Repositorio origen** | ``$($Script:RepoRoot)`` |
| **Fecha UTC** | ``$utcNow`` |
| **Fecha local** | ``$localNow`` |
| **Script** | ``$PSCommandPath`` |

## Advertencia

**ESTA BASE ES ANTERIOR AL MACROBLOQUE FINAL DE EXPERIENCIA V1.**

## Bundle local

| Campo | Valor |
|-------|-------|
| Archivo | ``$bundlePath`` |
| Tamaño (bytes) | $($Script:Artifacts.BundleSizeBytes) |
| SHA-256 | ``$($Script:Artifacts.BundleSha256)`` |
| git bundle verify | PASS |
| Restauración temporal | PASS |
| Método | ``git bundle create`` desde tag + rama origin (NO copia bundle remoto) |

## Backup SQLite consistente

| Campo | Valor |
|-------|-------|
| Origen (NO copiado con Copy-Item) | ``$($Script:DbSource)`` |
| Copia | ``$sqliteBackupPath`` |
| Tamaño (bytes) | $($Script:Artifacts.SqliteSizeBytes) |
| SHA-256 | ``$($Script:Artifacts.SqliteSha256)`` |
| PRAGMA integrity_check | ok |
| Método | ``sqlite3.Connection.backup()`` via ``$helperScript`` |
| WAL presente en origen | $($Script:Artifacts.WalPresent) |
| SHM presente en origen | $($Script:Artifacts.ShmPresent) |
| BD activa modificada | NO |

## Método de restauración

### Código (bundle)

```powershell
git clone "$bundlePath" EIAAX_RESTORE_0014a4b
cd EIAAX_RESTORE_0014a4b
git checkout $($Script:ProtectedTag)
```

### Base de datos

Restaurar copiando ``$sqliteBackupName`` sobre la ruta operativa **solo** tras detener EIAAX y con respaldo adicional previo.

## Limitaciones

- Este manifiesto certifica ejecución local en Windows.
- La BD activa no fue modificada; solo se leyó vía backup API.
- WAL/SHM del origen se registran pero no se copian como sustituto del backup API.

## Resultado

**EIAAX — BASE 0014a4b RESPALDADA Y RECUPERABILIDAD VERIFICADA (LOCAL)**
"@

    Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8
    $Script:Results.ManifestWritten = $true
    $Script:Artifacts.ManifestPath = $manifestPath

    # --- Resumen final ---
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host ' RESULTADO FINAL: PASS' -ForegroundColor Green
    Write-Host ' EIAAX — BASE 0014a4b RESPALDADA Y RECUPERABILIDAD VERIFICADA' -ForegroundColor Green
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host ''
    Write-Host "A. SHA completo: $($Script:ProtectedFullSha)"
    Write-Host "B. Tag verificado: $($Script:ProtectedTag)"
    Write-Host 'C. Publicación origin: tag ya existente (no movido por este script)'
    Write-Host "D. Bundle: $bundlePath"
    Write-Host "E. Tamaño bundle: $($Script:Artifacts.BundleSizeBytes) bytes"
    Write-Host "F. SHA-256 bundle: $($Script:Artifacts.BundleSha256)"
    Write-Host 'G. git bundle verify: PASS'
    Write-Host "H. Restauración temporal: PASS ($restoredSha)"
    Write-Host "I. BD demo backup: $sqliteBackupPath"
    Write-Host "   integrity_check: ok | SHA-256: $($Script:Artifacts.SqliteSha256)"
    Write-Host "J. Manifiesto: $manifestPath"
    Write-Host 'K. Limitación: ejecutar en Windows real; BD activa no modificada'
    Write-Host ''
    Write-Host 'Verificaciones:'
    foreach ($key in $Script:Results.Keys) {
        Write-Host ("  {0,-24} PASS" -f $key)
    }
    exit 0
}
catch {
    Stop-Respaldo $_.Exception.Message
}
