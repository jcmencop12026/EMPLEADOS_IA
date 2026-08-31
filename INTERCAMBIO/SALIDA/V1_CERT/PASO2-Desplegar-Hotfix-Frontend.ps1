#Requires -Version 5.1
<#
.SYNOPSIS
  PASO 2: Build and deploy frontend hotfix (api.ts fix + login UI).
  Does NOT modify D:\EMPLEADOS_IA_CERT database or backend SHA e8cb853 data.
.PARAMETER HotfixRoot
  Hotfix worktree with frontend fixes (default: D:\EMPLEADOS_IA_V1_HOTFIX)
.PARAMETER CertDir
  CERT docker compose directory (default: D:\EMPLEADOS_IA_CERT)
#>
param(
    [string]$HotfixRoot = "",
    [string]$CertDir = "D:\EMPLEADOS_IA_CERT"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_V1CertCommon.ps1"

$docker = Get-V1CertDockerExe
$root = Resolve-V1CertHotfixRoot -HotfixRoot $HotfixRoot

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
Write-Host "Building frontend image from hotfix source..."

Push-Location $root
try {
    & $docker build -t empleados_ia_cert-frontend-hotfix -f frontend/Dockerfile .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "STOP: docker build failed." -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

$network = Get-V1CertContainerNetwork -Docker $docker -ReferenceContainer "empleados_ia_cert-backend-1"
Write-Host "Docker network: $network"

Write-Host "Recreating frontend container with hotfix image..."
& $docker compose -f $composeFile --project-directory $CertDir stop frontend 2>$null | Out-Null
& $docker rm -f empleados_ia_cert-frontend-1 2>$null | Out-Null

$frontendPort = "5180"
$envPath = Join-Path $CertDir ".env"
if (Test-Path -LiteralPath $envPath) {
    $portLine = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^\s*FRONTEND_PORT\s*=' } | Select-Object -First 1
    if ($portLine -match '=\s*(\d+)') {
        $frontendPort = $Matches[1]
    }
}

& $docker run -d --name empleados_ia_cert-frontend-1 `
    --network $network `
    -p "${frontendPort}:80" `
    --restart unless-stopped `
    empleados_ia_cert-frontend-hotfix

if ($LASTEXITCODE -ne 0) {
    Write-Host "STOP: frontend container failed to start." -ForegroundColor Red
    Write-Host "Fallback: docker compose -f $composeFile --project-directory $CertDir up -d frontend" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "PASO 2: PASS (frontend container started)" -ForegroundColor Green
Write-Host "Open: http://localhost:${frontendPort}/login"
Write-Host "Expected: password eye toggle, forgot password link, correct error messages on bad login."
Write-Host "If network error: verify backend container empleados_ia_cert-backend-1 is on network $network."
