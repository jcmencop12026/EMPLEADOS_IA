#requires -Version 5.1
<#
.SYNOPSIS
    Launcher mínimo byte-safe para respaldo 104f785.

.DESCRIPTION
    Único punto de entrada. Usa git archive (no git show -> iex).
    NO modifica HEAD ni working tree del producto.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = 'D:\EMPLEADOS_IA_CONVERGENCIA'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProtectedFullSha = '104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a'
$ToolsRef = 'eiaax-tools-respaldo-104f785'
$ToolsPrefix = 'INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785'

function Stop-Launcher([string]$Message) {
    Write-Host "FAIL: $Message" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $RepoRoot)) { Stop-Launcher "Repo no encontrado: $RepoRoot" }
Set-Location -LiteralPath $RepoRoot

$headBefore = (git rev-parse HEAD).Trim()
if ($headBefore -ne $ProtectedFullSha) {
    Stop-Launcher "HEAD debe ser $ProtectedFullSha (actual: $headBefore)"
}

git fetch origin tag $ToolsRef 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Stop-Launcher "fetch tag $ToolsRef falló" }

$zipPath = Join-Path $env:TEMP ("eiaax_launch_{0}.zip" -f [guid]::NewGuid().ToString())
$extractRoot = Join-Path $env:TEMP ("eiaax_launch_{0}" -f [guid]::NewGuid().ToString())

try {
    git archive --format=zip -o $zipPath $ToolsRef $ToolsPrefix 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-Launcher 'git archive falló' }

    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractRoot -Force
    $toolsDir = Join-Path $extractRoot ($ToolsPrefix -replace '/', '\')
    $bootstrap = Join-Path $toolsDir 'Bootstrap-Ejecutar-Respaldo-104f785.ps1'
    if (-not (Test-Path -LiteralPath $bootstrap)) { Stop-Launcher "Bootstrap no encontrado: $bootstrap" }

    & $bootstrap -RepoRoot $RepoRoot -ToolsDirectory $toolsDir
    $code = $LASTEXITCODE
}
finally {
    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force -ErrorAction SilentlyContinue }
}

$headAfter = (git rev-parse HEAD).Trim()
if ($headAfter -ne $ProtectedFullSha) { Stop-Launcher "HEAD cambió ($headBefore -> $headAfter)" }
exit $code
