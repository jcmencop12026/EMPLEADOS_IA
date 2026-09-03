#requires -Version 5.1
<#
.SYNOPSIS
    Bootstrap byte-safe: materializa herramientas via git archive (sin checkout).

.DESCRIPTION
    Invocado desde launcher archive. NO usa git show -> texto -> WriteAllText.
    Git se ejecuta via cmd.exe para evitar NativeCommandError en PS 5.1.
    Verifica blob Git + SHA-256 del contenido exacto tras materialización.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = 'D:\EMPLEADOS_IA_CONVERGENCIA',
    [string]$ToolsDirectory = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProtectedFullSha = '104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a'
$ToolsTagName = 'eiaax-tools-respaldo-104f785'
$ToolsRef = 'refs/eiaax/bootstrap-tools-104f785'
$ToolsFetchSpec = "+refs/tags/${ToolsTagName}:${ToolsRef}"
$ToolsPrefix = 'INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785'
$ToolsStagingRoot = 'D:\RESPALDOS_EIAAX\_bootstrap_tools_104f785'

# Catálogo de confianza: blob Git (autoridad) + SHA-256 del contenido exacto
$Script:ToolCatalog = @{
    'Cerrar-Respaldo-Integral-104f785.ps1' = @{
        BlobId = '8665a7097f7747392265a1e43a601d04e591d94d'
        Sha256 = '77fdbc52a42454b1f8cf43e48ae0ef407f0b78525e98bf2d4550f35c7e3b4fe1'
    }
    'Backup-SqliteConsistente-104f785.py' = @{
        BlobId = '66e12ead386815beb6ed9b9e47084aa70c74f924'
        Sha256 = '80ea222948a823b583a8f86687fa33d1a8b22a9aeeaccc69a4303c4e0a2c4b9f'
    }
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

function Get-HeadSha {
    $head = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('rev-parse', 'HEAD')
    if ($null -eq $head) { Stop-Bootstrap 'git rev-parse HEAD falló' }
    return $head
}

function Ensure-GitObject {
    $localTag = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('rev-parse', $ToolsTagName)
    if ($null -ne $localTag) {
        Write-Step "Tag local $ToolsTagName -> $localTag (no se modifica)"
    }

    Write-Step "Fetch remoto -> $ToolsRef (sin tocar tag local)..."
    $fetchCode = Invoke-GitCmd -WorkDir $RepoRoot -GitArgs @('fetch', 'origin', $ToolsFetchSpec)
    if ($fetchCode -ne 0) {
        Stop-Bootstrap "fetch de herramientas falló (exit $fetchCode)"
    }

    $null = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('rev-parse', $ToolsRef)
    if ($LASTEXITCODE -ne 0) {
        Stop-Bootstrap "No se pudo recuperar ref de herramientas: $ToolsRef"
    }
    return $ToolsRef
}

function Get-GitBlobId([string]$Ref, [string]$GitPath) {
    $blob = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('rev-parse', "${Ref}:${GitPath}")
    if ($null -eq $blob) { Stop-Bootstrap "rev-parse blob falló: ${Ref}:${GitPath}" }
    return $blob
}

function Install-ToolsFromArchive([string]$Ref, [string]$DestinationRoot) {
    if (Test-Path -LiteralPath $DestinationRoot) {
        Remove-Item -LiteralPath $DestinationRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null

    $zipPath = Join-Path $env:TEMP ("eiaax_tools_{0}.zip" -f [guid]::NewGuid().ToString())
    $extractRoot = Join-Path $env:TEMP ("eiaax_tools_extract_{0}" -f [guid]::NewGuid().ToString())

    try {
        Write-Step 'Materializando herramientas via git archive (byte-safe)...'
        $archiveCode = Invoke-GitCmd -WorkDir $RepoRoot -GitArgs @(
            'archive', '--format=zip', '-o', $zipPath, $Ref, $ToolsPrefix
        )
        if ($archiveCode -ne 0 -or -not (Test-Path -LiteralPath $zipPath)) {
            Stop-Bootstrap "git archive falló al materializar herramientas (exit $archiveCode)."
        }

        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractRoot -Force
        $archivedDir = Join-Path $extractRoot ($ToolsPrefix -replace '/', '\')
        if (-not (Test-Path -LiteralPath $archivedDir)) {
            Stop-Bootstrap "Ruta archive inesperada: $archivedDir"
        }

        foreach ($name in $Script:ToolCatalog.Keys) {
            $src = Join-Path $archivedDir $name
            $dst = Join-Path $DestinationRoot $name
            if (-not (Test-Path -LiteralPath $src)) {
                Stop-Bootstrap "Herramienta ausente en archive: $name"
            }
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
    }
    finally {
        if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue }
        if (Test-Path -LiteralPath $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

function Test-ToolIntegrity([string]$Ref, [string]$ToolsRoot) {
    foreach ($name in $Script:ToolCatalog.Keys) {
        $meta = $Script:ToolCatalog[$name]
        $gitPath = "$ToolsPrefix/$name"
        $filePath = Join-Path $ToolsRoot $name

        if (-not (Test-Path -LiteralPath $filePath)) {
            Stop-Bootstrap "Archivo materializado ausente: $name"
        }

        $blobId = Get-GitBlobId -Ref $Ref -GitPath $gitPath
        if ($blobId -ne $meta.BlobId) {
            Stop-Bootstrap "Blob Git inesperado para ${name}: esperado $($meta.BlobId), remoto $blobId"
        }

        $hashObject = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('hash-object', $filePath)
        if ($null -eq $hashObject) { Stop-Bootstrap "git hash-object falló para $name" }
        if ($hashObject -ne $meta.BlobId) {
            Stop-Bootstrap "git hash-object no coincide para ${name}: esperado $($meta.BlobId), obtenido $hashObject (bytes alterados)"
        }

        $sha256 = Get-FileSha256 $filePath
        if ($sha256 -ne $meta.Sha256) {
            Stop-Bootstrap "SHA-256 inesperado en ${name}: esperado $($meta.Sha256), obtenido $sha256"
        }

        Write-Step "Integridad PASS: $name (blob=$blobId)"
    }
}

try {
    Write-Step 'EIAAX bootstrap byte-safe respaldo integral 104f785'

    if (-not (Test-Path -LiteralPath $RepoRoot)) {
        Stop-Bootstrap "Repositorio no encontrado: $RepoRoot"
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Stop-Bootstrap 'git no disponible en PATH.'
    }

    $headBefore = Get-HeadSha
    if ($headBefore -ne $ProtectedFullSha) {
        Stop-Bootstrap "HEAD debe ser $ProtectedFullSha (actual: $headBefore)."
    }
    Write-Step "HEAD protegido verificado: $headBefore"

    $toolsRefResolved = Ensure-GitObject
    $toolsCommit = Get-GitCmdOutput -WorkDir $RepoRoot -GitArgs @('rev-parse', "$toolsRefResolved^{commit}")
    if ($null -eq $toolsCommit) { Stop-Bootstrap 'rev-parse commit herramientas falló' }
    Write-Step "Ref herramientas: $toolsRefResolved -> $toolsCommit"

    $activeToolsRoot = $ToolsDirectory
    if ([string]::IsNullOrWhiteSpace($activeToolsRoot)) {
        Install-ToolsFromArchive -Ref $toolsRefResolved -DestinationRoot $ToolsStagingRoot
        $activeToolsRoot = $ToolsStagingRoot
    }
    else {
        Write-Step "Usando ToolsDirectory provisto: $activeToolsRoot"
    }

    Test-ToolIntegrity -Ref $toolsRefResolved -ToolsRoot $activeToolsRoot

    $mainScript = Join-Path $activeToolsRoot 'Cerrar-Respaldo-Integral-104f785.ps1'
    if (-not (Test-Path -LiteralPath $mainScript)) {
        Stop-Bootstrap "Script principal no encontrado: $mainScript"
    }

    & $mainScript -ToolsDirectory $activeToolsRoot
    $exitCode = $LASTEXITCODE

    $headAfter = Get-HeadSha
    if ($headAfter -ne $ProtectedFullSha) {
        Stop-Bootstrap "HEAD cambió durante respaldo ($headBefore -> $headAfter)."
    }
    Write-Step "HEAD sin cambios: $headAfter"

    if ($activeToolsRoot -eq $ToolsStagingRoot -and (Test-Path -LiteralPath $ToolsStagingRoot)) {
        Remove-Item -LiteralPath $ToolsStagingRoot -Recurse -Force -ErrorAction SilentlyContinue
        Write-Step 'Herramientas temporales eliminadas'
    }

    if ($exitCode -ne 0) {
        Stop-Bootstrap "Respaldo retornó código $exitCode"
    }
    exit 0
}
catch {
    Stop-Bootstrap $_.Exception.Message
}
