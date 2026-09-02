#requires -Version 5.1
<#
.SYNOPSIS
    Bootstrap autocontenido: materializa herramientas de respaldo desde Git sin checkout.

.NOTES
    Diseñado para ejecutarse via:
    iex ((git show eiaax-tools-respaldo-104f785:INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/Bootstrap-Ejecutar-Respaldo-104f785.ps1) -join [char]10)

    NO modifica working tree del candidato protegido 104f785.
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
$ToolsStagingRoot = 'D:\RESPALDOS_EIAAX\_bootstrap_tools_104f785'

$ExpectedHashes = @{
    'Cerrar-Respaldo-Integral-104f785.ps1' = '77fdbc52a42454b1f8cf43e48ae0ef407f0b78525e98bf2d4550f35c7e3b4fe1'
    'Backup-SqliteConsistente-104f785.py' = '80ea222948a823b583a8f86687fa33d1a8b22a9aeeaccc69a4303c4e0a2c4b9f'
}

function Write-Step([string]$Message) {
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Write-Host "[$ts] [bootstrap] $Message"
}

function Stop-Bootstrap([string]$Message) {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Red
    Write-Host ' RESULTADO FINAL: FAIL — NO AUTORIZAR CAMBIOS AL PRODUCTO' -ForegroundColor Red
    Write-Host " Motivo: $Message" -ForegroundColor Red
    Write-Host '============================================================' -ForegroundColor Red
    exit 1
}

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-HeadSha {
    return (git -C $RepoRoot rev-parse HEAD).Trim()
}

function Ensure-GitObject([string]$Ref) {
    $null = git -C $RepoRoot rev-parse $Ref 2>$null
    if ($LASTEXITCODE -eq 0) { return $Ref }

    Write-Step "Objeto Git $Ref no local; fetch desde origin..."
    git -C $RepoRoot fetch origin tag $ToolsRef --no-tags 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        git -C $RepoRoot fetch origin $ToolsRef --depth=1 2>&1 | Out-Null
    }
    $null = git -C $RepoRoot rev-parse $Ref 2>$null
    if ($LASTEXITCODE -ne 0) {
        Stop-Bootstrap "No se pudo recuperar ref de herramientas: $Ref"
    }
    return $Ref
}

function Write-GitBlobToFile([string]$Ref, [string]$GitPath, [string]$DestFile) {
    $parent = Split-Path -Parent $DestFile
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $content = git -C $RepoRoot show "${Ref}:${GitPath}" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Stop-Bootstrap "git show falló para ${Ref}:${GitPath}: $content"
    }
    $text = if ($content -is [array]) { $content -join "`n" } else { [string]$content }
    if ($GitPath.EndsWith('.py')) {
        [System.IO.File]::WriteAllText($DestFile, $text + "`n", [System.Text.UTF8Encoding]::new($false))
    }
    else {
        [System.IO.File]::WriteAllText($DestFile, $text, [System.Text.UTF8Encoding]::new($true))
    }
    if (-not (Test-Path -LiteralPath $DestFile)) {
        Stop-Bootstrap "No se escribió archivo materializado: $DestFile"
    }
}

try {
    Write-Step 'EIAAX bootstrap respaldo integral 104f785'

    if (-not (Test-Path -LiteralPath $RepoRoot)) {
        Stop-Bootstrap "Repositorio no encontrado: $RepoRoot"
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Stop-Bootstrap 'git no disponible en PATH.'
    }

    $headBefore = Get-HeadSha
    if ($headBefore -ne $ProtectedFullSha) {
        Stop-Bootstrap "HEAD debe ser $ProtectedFullSha (actual: $headBefore). No ejecutar fuera del candidato protegido."
    }
    Write-Step "HEAD protegido verificado: $headBefore"

    $toolsRefResolved = Ensure-GitObject -Ref $ToolsRef
    Write-Step "Ref herramientas resuelto: $toolsRefResolved -> $((git -C $RepoRoot rev-parse "$toolsRefResolved^{commit}").Trim())"

    if (Test-Path -LiteralPath $ToolsStagingRoot) {
        Remove-Item -LiteralPath $ToolsStagingRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $ToolsStagingRoot -Force | Out-Null

    foreach ($name in $ExpectedHashes.Keys) {
        $gitPath = "$ToolsPrefix/$name"
        $dest = Join-Path $ToolsStagingRoot $name
        Write-Step "Materializando $name desde Git (sin checkout)..."
        Write-GitBlobToFile -Ref $toolsRefResolved -GitPath $gitPath -DestFile $dest
        $hash = Get-FileSha256 $dest
        if ($hash -ne $ExpectedHashes[$name]) {
            Stop-Bootstrap "Hash inesperado en $name`: esperado $($ExpectedHashes[$name]), obtenido $hash"
        }
    }
    Write-Step 'Herramientas materializadas y verificadas (SHA-256 PASS)'

    $mainScript = Join-Path $ToolsStagingRoot 'Cerrar-Respaldo-Integral-104f785.ps1'
    & $mainScript -ToolsDirectory $ToolsStagingRoot
    $exitCode = $LASTEXITCODE

    $headAfter = Get-HeadSha
    if ($headAfter -ne $ProtectedFullSha) {
        Stop-Bootstrap "HEAD cambió durante el respaldo ($headBefore -> $headAfter). Abortado."
    }
    Write-Step "HEAD sin cambios tras respaldo: $headAfter"

    Remove-Item -LiteralPath $ToolsStagingRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Step 'Herramientas temporales eliminadas'

    if ($exitCode -ne 0) {
        Stop-Bootstrap "El script de respaldo retornó código $exitCode"
    }
    exit 0
}
catch {
    Stop-Bootstrap $_.Exception.Message
}
