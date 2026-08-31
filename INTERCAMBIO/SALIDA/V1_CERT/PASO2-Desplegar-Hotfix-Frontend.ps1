#Requires -Version 5.1
<#
.SYNOPSIS
  PASO 2: Build and deploy frontend hotfix (api.ts fix + login UI).
.DESCRIPTION
  Does NOT modify D:\EMPLEADOS_IA_CERT Git HEAD, PostgreSQL, admin credentials, or backend data.
  Recreates ONLY empleados_ia_cert-frontend-1.
.PARAMETER HotfixRoot
  Hotfix worktree (default: D:\EMPLEADOS_IA_V1_HOTFIX)
.PARAMETER CertDir
  CERT docker compose directory (default: D:\EMPLEADOS_IA_CERT)
.PARAMETER Rebuild
  Force docker build even if empleados_ia_cert-frontend-hotfix:latest already exists.
.PARAMETER FrontendImage
  Image tag to deploy (default: empleados_ia_cert-frontend-hotfix:latest)
#>
param(
    [string]$HotfixRoot = "",
    [string]$CertDir = "D:\EMPLEADOS_IA_CERT",
    [switch]$Rebuild,
    [string]$FrontendImage = "empleados_ia_cert-frontend-hotfix:latest"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_V1CertCommon.ps1"

$docker = Get-V1CertDockerExe
$root = Resolve-V1CertHotfixRoot -HotfixRoot $HotfixRoot
$backendContainer = "empleados_ia_cert-backend-1"
$postgresContainer = "empleados_ia_cert-postgres-1"
$frontendContainer = "empleados_ia_cert-frontend-1"

if (-not (Test-Path -LiteralPath $CertDir)) {
    throw "CertDir not found: $CertDir"
}

$composeFile = Join-Path $CertDir "docker-compose.yml"
if (-not (Test-Path -LiteralPath $composeFile)) {
    throw "docker-compose.yml not found in $CertDir"
}

Write-Host "========== PASO 2: DEPLOY FRONTEND HOTFIX ==========" -ForegroundColor Cyan
Write-Host "HotfixRoot: $root"
Write-Host "CertDir:    $CertDir"
Write-Host "Image:      $FrontendImage"

Write-Host ""
Write-Host "=== Pre-flight (read-only) ===" -ForegroundColor Cyan
Assert-V1CertContainerRunning -Docker $docker -ContainerName $backendContainer
Assert-V1CertContainerRunning -Docker $docker -ContainerName $postgresContainer

$backendHealth = Get-V1CertContainerHealthLabel -Docker $docker -ContainerName $backendContainer
$postgresHealth = Get-V1CertContainerHealthLabel -Docker $docker -ContainerName $postgresContainer
Write-Host "Backend:  $backendContainer -> $backendHealth"
Write-Host "Postgres: $postgresContainer -> $postgresHealth"

if ($backendHealth -notmatch 'healthy|RUNNING') {
    Write-Host "STOP: backend is not healthy." -ForegroundColor Red
    exit 1
}
if ($postgresHealth -notmatch 'healthy|RUNNING') {
    Write-Host "STOP: postgres is not healthy." -ForegroundColor Red
    exit 1
}

$imageExists = Test-V1CertDockerImageExists -Docker $docker -ImageRef $FrontendImage
if ($Rebuild -or -not $imageExists) {
    if ($imageExists -and $Rebuild) {
        Write-Host "Rebuild requested (-Rebuild)." -ForegroundColor Yellow
    } else {
        Write-Host "Image not found; building frontend hotfix..." -ForegroundColor Yellow
    }
    Push-Location $root
    try {
        & $docker build -t $FrontendImage -f frontend/Dockerfile .
        if ($LASTEXITCODE -ne 0) {
            Write-Host "STOP: docker build failed." -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
    Write-Host "BUILD: PASS" -ForegroundColor Green
} else {
    Write-Host "BUILD: SKIP (reusing existing image $FrontendImage)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Network detection (JSON inspect) ===" -ForegroundColor Cyan
$network = Get-V1CertContainerNetwork -Docker $docker -ReferenceContainer $backendContainer
Write-Host "Docker network: $network"

$frontendPort = Get-V1CertFrontendPort -CertDir $CertDir
Write-Host "Frontend port: $frontendPort"

Write-Host ""
Write-Host "=== Recreate frontend container only ===" -ForegroundColor Cyan
& $docker compose -f $composeFile --project-directory $CertDir stop frontend 2>$null | Out-Null
& $docker rm -f $frontendContainer 2>$null | Out-Null

& $docker run -d --name $frontendContainer `
    --network $network `
    -p "${frontendPort}:80" `
    --restart unless-stopped `
    $FrontendImage

if ($LASTEXITCODE -ne 0) {
    Write-Host "STOP: frontend container failed to start." -ForegroundColor Red
    exit 1
}

Assert-V1CertContainerRunning -Docker $docker -ContainerName $frontendContainer
$frontendHealth = Get-V1CertContainerHealthLabel -Docker $docker -ContainerName $frontendContainer
Write-Host "Frontend container: $frontendContainer -> $frontendHealth"

$loginUrl = "http://localhost:${frontendPort}/login"
Write-Host ""
Write-Host "=== HTTP verification ===" -ForegroundColor Cyan
Write-Host "Waiting for $loginUrl ..."
try {
    $null = Wait-V1CertHttpReady -Url $loginUrl
    Write-Host "HTTP: PASS ($loginUrl)" -ForegroundColor Green
} catch {
    Write-Host "STOP: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Hotfix content verification ===" -ForegroundColor Cyan
try {
    $null = Test-V1CertLoginHotfixContent -BaseUrl "http://localhost:${frontendPort}"
    Write-Host "HOTFIX UI: PASS (password toggle, forgot link, Spanish login)" -ForegroundColor Green
} catch {
    Write-Host "STOP: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "PASO 2: PASS" -ForegroundColor Green
Write-Host "URL: $loginUrl"
Write-Host "Backend:  $backendContainer -> $backendHealth"
Write-Host "Postgres: $postgresContainer -> $postgresHealth"
Write-Host "Frontend: $frontendContainer -> RUNNING on port $frontendPort"
Write-Host "Expected UI: Usuario, Contrasena, eye toggle, forgot password, Spanish 401 message."
