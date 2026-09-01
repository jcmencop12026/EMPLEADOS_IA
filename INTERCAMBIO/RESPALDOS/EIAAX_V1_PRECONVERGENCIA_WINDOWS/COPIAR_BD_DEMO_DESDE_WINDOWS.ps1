#Requires -Version 5.1
<#
.SYNOPSIS
    Copia la BD demo SQLite desde el worktree Windows al respaldo, sin modificar el original.
.DESCRIPTION
    Ejecutar en el equipo Windows donde corrio la prueba visual exitosa.
    Origen esperado: D:\EMPLEADOS_IA_INTEGRADO\data\eiaax_integrado_demo.db
#>

param(
    [string]$WorktreeRoot = "D:\EMPLEADOS_IA_INTEGRADO",
    [string]$BackupDir = "D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_PRECONVERGENCIA_WINDOWS"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourceDb = Join-Path $WorktreeRoot "data\eiaax_integrado_demo.db"
$journal = $sourceDb + "-journal"
$wal = $sourceDb + "-wal"
$shm = $sourceDb + "-shm"

if (-not (Test-Path -LiteralPath $sourceDb)) {
    Write-Error ("BD demo no encontrada: " + $sourceDb)
}

if (-not (Test-Path -LiteralPath $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$destBase = Join-Path $BackupDir ("eiaax_integrado_demo-" + $timestamp)
$destDb = $destBase + ".db"

Write-Host "Copiando BD demo sin modificar original..."
Copy-Item -LiteralPath $sourceDb -Destination $destDb -Force

foreach ($sidecar in @($journal, $wal, $shm)) {
    if (Test-Path -LiteralPath $sidecar) {
        $sidecarName = Split-Path -Leaf $sidecar
        Copy-Item -LiteralPath $sidecar -Destination ($destBase + "-" + $sidecarName.Substring($sidecarName.IndexOf("-"))) -Force
        Write-Host ("Sidecar copiado: " + $sidecarName)
    }
}

$hash = (Get-FileHash -LiteralPath $destDb -Algorithm SHA256).Hash.ToLowerInvariant()
$hashFile = Join-Path $BackupDir "SHA256_BD_DEMO.txt"
@(
    "timestamp_utc=" + $timestamp
    "source=" + $sourceDb
    "copy=" + $destDb
    "sha256=" + $hash
    "type=DEMO_SQLITE"
    "nota=NO es PostgreSQL productivo"
) | Set-Content -LiteralPath $hashFile -Encoding ASCII

Write-Host ""
Write-Host "BD demo respaldada:"
Write-Host ("  Archivo: " + $destDb)
Write-Host ("  SHA256:  " + $hash)
Write-Host ("  Manifiesto hash: " + $hashFile)
exit 0
