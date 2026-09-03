#requires -Version 5.1
<#
.SYNOPSIS
    Launcher mínimo byte-safe para respaldo 104f785.

.DESCRIPTION
    Único punto de entrada. Usa git archive (no git show -> iex).
    Git se ejecuta via cmd.exe para evitar NativeCommandError en PS 5.1.
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

function Format-GitArgLine([string[]]$GitArgs) {
    $parts = @()
    foreach ($arg in $GitArgs) {
        if ($arg -match '[\s"&|<>^]') {
            $parts += '"' + ($arg -replace '"', '""') + '"'
        }
        else {
            $parts += $arg
        }
    }
    return ($parts -join ' ')
}

function Invoke-GitCmd([string]$WorkDir, [string[]]$GitArgs) {
    $gitLine = Format-GitArgLine -GitArgs $GitArgs
    if ([string]::IsNullOrWhiteSpace($WorkDir)) {
        cmd /d /c "git $gitLine"
    }
    else {
        cmd /d /c "cd /d `"$WorkDir`" && git $gitLine"
    }
    return $LASTEXITCODE
}

function Get-GitCmdOutput([string]$WorkDir, [string[]]$GitArgs) {
    $gitLine = Format-GitArgLine -GitArgs $GitArgs
    if ([string]::IsNullOrWhiteSpace($WorkDir)) {
        $out = cmd /d /c "git $gitLine 2>nul"
    }
    else {
        $out = cmd /d /c "cd /d `"$WorkDir`" && git $gitLine 2>nul"
    }
    if ($LASTEXITCODE -ne 0) { return $null }
    if ($null -eq $out) { return '' }
    return ($out | Out-String).Trim()
}

if (-not (Test-Path -LiteralPath $RepoRoot)) { Stop-Launcher "Repo no encontrado: $RepoRoot" }
Set-Location -LiteralPath $RepoRoot

$headBefore = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('rev-parse', 'HEAD')
if ($null -eq $headBefore) { Stop-Launcher 'git rev-parse HEAD falló' }
if ($headBefore -ne $ProtectedFullSha) {
    Stop-Launcher "HEAD debe ser $ProtectedFullSha (actual: $headBefore)"
}

$fetchCode = Invoke-GitCmd -WorkDir $RepoRoot -GitArgs @('fetch', 'origin', 'tag', $ToolsRef)
if ($fetchCode -ne 0) { Stop-Launcher "fetch tag $ToolsRef falló (exit $fetchCode)" }

$zipPath = Join-Path $env:TEMP ("eiaax_launch_{0}.zip" -f [guid]::NewGuid().ToString())
$extractRoot = Join-Path $env:TEMP ("eiaax_launch_{0}" -f [guid]::NewGuid().ToString())
$code = 1

try {
    $archiveCode = Invoke-GitCmd -WorkDir $RepoRoot -GitArgs @(
        'archive', '--format=zip', '-o', $zipPath, $ToolsRef, $ToolsPrefix
    )
    if ($archiveCode -ne 0) { Stop-Launcher "git archive falló (exit $archiveCode)" }

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

$headAfter = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('rev-parse', 'HEAD')
if ($null -eq $headAfter) { Stop-Launcher 'git rev-parse HEAD falló al cerrar' }
if ($headAfter -ne $ProtectedFullSha) { Stop-Launcher "HEAD cambió ($headBefore -> $headAfter)" }
exit $code
