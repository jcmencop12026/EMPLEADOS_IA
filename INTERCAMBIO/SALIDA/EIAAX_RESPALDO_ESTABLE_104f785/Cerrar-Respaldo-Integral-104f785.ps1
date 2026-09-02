#requires -Version 5.1
<#
.SYNOPSIS
    Respaldo integral verificado EIAAX Windows real estable 104f785.

.DESCRIPTION
    Punto de recuperación integral antes de nuevas correcciones de producto.
    - Verifica tag/commit 104f785
    - Crea bundle Git local recuperable
    - Backup SQLite consistente (sin Copy-Item sobre BD viva)
    - Prueba restauración temporal aislada
    - Materializa en D:\RESPALDOS_EIAAX\EIAAX_V1_WINDOWS_ESTABLE_104f785\
    - Genera manifiesto y README de recuperación
    - Resultado PASS/FAIL fail-closed

    NO modifica producto, BD original, scripts/windows ni tag existente.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Script:ProtectedShortSha = '104f785'
$Script:ProtectedFullSha  = '104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a'
$Script:ProtectedTag      = 'eiaax-v1-windows-real-estable-104f785'
$Script:ProtectedBranch   = 'cursor/convergencia-comercial-v1-85e4'
$Script:BaseArranqueSha   = '0014a4b01a3ccf3e849a6609c8c784873f20f497'
$Script:AlembicRevision   = '1820a1b2c3d4e'
$Script:RepoRoot          = 'D:\EMPLEADOS_IA_CONVERGENCIA'
$Script:BackupRoot        = 'D:\RESPALDOS_EIAAX\EIAAX_V1_WINDOWS_ESTABLE_104f785'
$Script:BundleFileName    = 'eiaax-v1-windows-real-estable-104f785.bundle'
$Script:DbSource          = 'D:\EMPLEADOS_IA_CONVERGENCIA\data\eiaax_integrado_demo.db'

$Script:Results = [ordered]@{
    RepoRootVerified     = $false
    TagVerified          = $false
    BranchVerified       = $false
    ScriptsWindowsIntact = $false
    BundleCreated        = $false
    BundleVerify         = $false
    BundleRestoreTest    = $false
    SqliteBackup         = $false
    SqliteIntegrity      = $false
    SqliteTableRead      = $false
    ManifestWritten      = $false
    TempCleaned          = $false
}

$Script:Artifacts = @{}

function Write-Step([string]$Message) {
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Write-Host "[$ts] $Message"
}

function Stop-Respaldo([string]$Message, [int]$ExitCode = 1) {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Red
    Write-Host ' RESULTADO FINAL: FAIL — NO AUTORIZAR CAMBIOS AL PRODUCTO' -ForegroundColor Red
    Write-Host " Motivo: $Message" -ForegroundColor Red
    Write-Host '============================================================' -ForegroundColor Red
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
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) { return (Get-Command python).Source }
    if (Get-Command py -ErrorAction SilentlyContinue) { return 'py' }
    Stop-Respaldo 'Python del proyecto no encontrado.'
}

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$Args)
    $output = & git -C $Script:RepoRoot @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        Stop-Respaldo "git $($Args -join ' ') falló: $(($output | Out-String).Trim())"
    }
    return ,$output
}

try {
    Write-Step 'EIAAX — Respaldo integral Windows real estable 104f785'

    if (-not (Test-Path -LiteralPath $Script:RepoRoot)) {
        Stop-Respaldo "Repositorio no encontrado: $($Script:RepoRoot)"
    }
    Set-Location -LiteralPath $Script:RepoRoot
    $Script:Results.RepoRootVerified = $true

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Stop-Respaldo 'git no disponible.'
    }

    Write-Step 'Verificando rama autoritativa y tag...'
    Invoke-Git -Args @('fetch', 'origin', $Script:ProtectedBranch) | Out-Null
    Invoke-Git -Args @('fetch', '--tags', 'origin', $Script:ProtectedTag) | Out-Null

    $branchSha = (Invoke-Git -Args @('rev-parse', "origin/$($Script:ProtectedBranch)")) -join '' | ForEach-Object { $_.Trim() }
    if ($branchSha -ne $Script:ProtectedFullSha) {
        Stop-Respaldo "origin/$($Script:ProtectedBranch) = $branchSha, se esperaba $($Script:ProtectedFullSha)"
    }
    $Script:Results.BranchVerified = $true

    $tagSha = (Invoke-Git -Args @('rev-parse', "$($Script:ProtectedTag)^{commit}")) -join '' | ForEach-Object { $_.Trim() }
    if ($tagSha -ne $Script:ProtectedFullSha) {
        Stop-Respaldo "Tag $($Script:ProtectedTag) = $tagSha, se esperaba $($Script:ProtectedFullSha)"
    }
    $Script:Results.TagVerified = $true
    Write-Step "Tag y rama verificados -> $($Script:ProtectedFullSha)"

    Write-Step 'Verificando scripts/windows intactos vs base arranque 0014a4b...'
    $swDiff = (& git -C $Script:RepoRoot diff --name-only $Script:BaseArranqueSha $Script:ProtectedFullSha -- scripts/windows/ 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        Stop-Respaldo "No se pudo comparar scripts/windows con base 0014a4b."
    }
    if ($swDiff) {
        Stop-Respaldo "scripts/windows difiere respecto a 0014a4b: $swDiff"
    }
    $Script:Results.ScriptsWindowsIntact = $true
    Write-Step 'scripts/windows: sin cambios desde 0014a4b (PASS)'

    if (-not (Test-Path -LiteralPath $Script:BackupRoot)) {
        New-Item -ItemType Directory -Path $Script:BackupRoot -Force | Out-Null
    }

    $bundlePath = Join-Path $Script:BackupRoot $Script:BundleFileName
    $manifestPath = Join-Path $Script:BackupRoot 'MANIFIESTO_RESPALDO.md'
    $readmePath = Join-Path $Script:BackupRoot 'README_RECUPERACION.md'
    $sqliteReportPath = Join-Path $Script:BackupRoot 'sqlite_backup_report.json'

    Write-Step 'Creando bundle Git local...'
    if (Test-Path -LiteralPath $bundlePath) { Remove-Item -LiteralPath $bundlePath -Force }
    Invoke-Git -Args @(
        'bundle', 'create', $bundlePath,
        "refs/tags/$($Script:ProtectedTag)",
        "origin/$($Script:ProtectedBranch)"
    ) | Out-Null
    $Script:Results.BundleCreated = $true
    $Script:Artifacts.BundlePath = $bundlePath
    $Script:Artifacts.BundleSizeBytes = (Get-Item -LiteralPath $bundlePath).Length
    $Script:Artifacts.BundleSha256 = Get-FileSha256 $bundlePath

    $verifyOutput = (& git bundle verify $bundlePath 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or $verifyOutput -notmatch 'is okay') {
        Stop-Respaldo "git bundle verify falló: $verifyOutput"
    }
    $Script:Results.BundleVerify = $true

    Write-Step 'Prueba restauración temporal aislada...'
    $tempRoot = Join-Path $env:TEMP ("eiaax_restore_integral_{0}" -f $Script:ProtectedShortSha)
    if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    $tempRepo = Join-Path $tempRoot 'restored'
    & git clone $bundlePath $tempRepo 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-Respaldo 'git clone desde bundle falló.' }

    Push-Location $tempRepo
    try {
        & git checkout $Script:ProtectedTag 2>&1 | Out-Null
        $restoredSha = (git rev-parse HEAD).Trim()
        if ($restoredSha -ne $Script:ProtectedFullSha) {
            Stop-Respaldo "SHA restaurado $restoredSha != $($Script:ProtectedFullSha)"
        }
        foreach ($critical in @(
            'scripts/windows/arrancar_convergencia_windows.ps1',
            'scripts/windows/iniciar_backend_demo.ps1',
            'scripts/windows/iniciar_frontend_demo.ps1',
            'backend/app/main.py'
        )) {
            if (-not (Test-Path -LiteralPath $critical)) {
                Stop-Respaldo "Archivo crítico ausente en restauración: $critical"
            }
        }
    }
    finally { Pop-Location }

    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    $Script:Results.BundleRestoreTest = $true
    $Script:Results.TempCleaned = $true
    Write-Step "Restauración temporal: PASS ($restoredSha); residuos eliminados"

    Write-Step 'Backup SQLite consistente...'
    if (-not (Test-Path -LiteralPath $Script:DbSource)) {
        Stop-Respaldo "BD origen no encontrada: $($Script:DbSource)"
    }

    $helperScript = Join-Path $PSScriptRoot 'Backup-SqliteConsistente-104f785.py'
    if (-not (Test-Path -LiteralPath $helperScript)) {
        Stop-Respaldo "Helper SQLite no encontrado: $helperScript"
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
    $sqliteBackupPath = Join-Path $Script:BackupRoot ("eiaax_integrado_demo_104f785_{0}.db" -f $timestamp)
    $pythonExe = Resolve-PythonExecutable
    $pyArgs = @($helperScript, $Script:DbSource, $sqliteBackupPath, $sqliteReportPath)
    if ($pythonExe -eq 'py') { $pyOutput = & py -3 @pyArgs 2>&1 } else { $pyOutput = & $pythonExe @pyArgs 2>&1 }
    if ($LASTEXITCODE -ne 0) { Stop-Respaldo "Backup SQLite falló: $(($pyOutput | Out-String).Trim())" }

    $sqliteReport = Get-Content -LiteralPath $sqliteReportPath -Raw | ConvertFrom-Json
    if ($sqliteReport.integrity_check -ne 'ok') {
        Stop-Respaldo "integrity_check != ok"
    }
    if (-not $sqliteReport.table_reads_sample) {
        Stop-Respaldo 'Lectura de tablas en copia BD falló.'
    }

    $Script:Results.SqliteBackup = $true
    $Script:Results.SqliteIntegrity = $true
    $Script:Results.SqliteTableRead = $true
    $Script:Artifacts.SqliteBackupPath = $sqliteBackupPath
    $Script:Artifacts.SqliteSha256 = [string]$sqliteReport.sha256
    $Script:Artifacts.SqliteSizeBytes = [int64]$sqliteReport.size_bytes

    $utcNow = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $localNow = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')

    $manifest = @"
# MANIFIESTO — EIAAX V1 Windows Real Estable 104f785

| Campo | Valor |
|-------|-------|
| PROYECTO | EIAAX |
| TIPO | RESPALDO INTEGRAL WINDOWS REAL ESTABLE |
| SHA corto | ``$($Script:ProtectedShortSha)`` |
| SHA completo | ``$($Script:ProtectedFullSha)`` |
| Tag | ``$($Script:ProtectedTag)`` |
| Rama | ``$($Script:ProtectedBranch)`` |
| Base arranque protegida | ``$($Script:BaseArranqueSha)`` |
| Alembic head | ``$($Script:AlembicRevision)`` |
| Repositorio origen | ``$($Script:RepoRoot)`` |
| Fecha UTC | ``$utcNow`` |
| Fecha local | ``$localNow`` |

## Estado Windows real comprobado

- backend PASS · frontend PASS · ownership PASS
- Alembic PASS · runtime identity PASS
- login org_a_admin funcional
- aplicación operativa http://127.0.0.1:5180

## Bundle Git

| Campo | Valor |
|-------|-------|
| Archivo | ``$bundlePath`` |
| Tamaño (bytes) | $($Script:Artifacts.BundleSizeBytes) |
| SHA-256 | ``$($Script:Artifacts.BundleSha256)`` |
| git bundle verify | PASS |
| Restauración temporal | PASS |

## Backup SQLite

| Campo | Valor |
|-------|-------|
| Origen (solo lectura backup API) | ``$($Script:DbSource)`` |
| Copia | ``$sqliteBackupPath`` |
| Tamaño (bytes) | $($Script:Artifacts.SqliteSizeBytes) |
| SHA-256 | ``$($Script:Artifacts.SqliteSha256)`` |
| PRAGMA integrity_check | ok |
| Lectura tablas | PASS ($($sqliteReport.tables_found) tablas) |
| WAL origen | $($sqliteReport.wal_present) |
| SHM origen | $($sqliteReport.shm_present) |
| BD original modificada | NO |

## scripts/windows

Sin cambios respecto a base arranque ``0014a4b`` (verificado).

## Recuperación

Ver ``README_RECUPERACION.md`` en esta carpeta.

**RESULTADO: PASS — RESPALDO 104f785 VERIFICADO Y RECUPERABLE**
"@

    $readme = @"
# README — Recuperación EIAAX 104f785

## Código desde bundle (offline)

```powershell
git clone "$bundlePath" D:\RESTORE_EIAAX_104f785
cd D:\RESTORE_EIAAX_104f785
git checkout $($Script:ProtectedTag)
```

## Base de datos

1. Detener EIAAX de forma controlada.
2. Respaldar BD operativa actual por separado.
3. Restaurar copia: ``$(Split-Path -Leaf $sqliteBackupPath)`` sobre ``data\eiaax_integrado_demo.db``.
4. Verificar ``PRAGMA integrity_check`` y arranque.

## No incluido (regenerable)

- node_modules
- .venv / venv
- __pycache__
- dist / build

## Tag remoto

``$($Script:ProtectedTag)`` -> ``$($Script:ProtectedFullSha)``
"@

    Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8
    Set-Content -LiteralPath $readmePath -Value $readme -Encoding UTF8
    $Script:Results.ManifestWritten = $true

    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host ' RESULTADO FINAL: PASS — RESPALDO 104f785 VERIFICADO Y RECUPERABLE' -ForegroundColor Green
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host "A. SHA: $($Script:ProtectedFullSha)"
    Write-Host "B. Tag local: $($Script:ProtectedTag)"
    Write-Host "C. Tag remoto: origin/$($Script:ProtectedTag)"
    Write-Host "D. Ruta física: $Script:BackupRoot"
    Write-Host "E. Bundle bytes: $($Script:Artifacts.BundleSizeBytes)"
    Write-Host "F. SHA-256 bundle: $($Script:Artifacts.BundleSha256)"
    Write-Host 'G. git bundle verify: PASS'
    Write-Host "H. Restauración temporal: PASS ($restoredSha)"
    Write-Host "I. Copia BD: $sqliteBackupPath"
    Write-Host "J. SHA-256 BD: $($Script:Artifacts.SqliteSha256)"
    Write-Host 'K. PRAGMA integrity_check: ok'
    Write-Host "L. Lectura BD: PASS ($($sqliteReport.tables_found) tablas)"
    Write-Host "M. Manifiesto: $manifestPath"
    Write-Host 'N. Residuos temporales: eliminados'
    Write-Host 'O. Producto original: no modificado'
    Write-Host 'P. scripts/windows: intactos vs 0014a4b'
    exit 0
}
catch {
    Stop-Respaldo $_.Exception.Message
}
