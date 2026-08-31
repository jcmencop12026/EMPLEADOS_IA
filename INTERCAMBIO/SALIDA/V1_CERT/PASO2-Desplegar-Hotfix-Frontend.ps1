#Requires -Version 5.1
param(
    [string]$HotfixRoot = "D:\EMPLEADOS_IA_V1_HOTFIX",
    [string]$CertDir = "D:\EMPLEADOS_IA_CERT",
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"

$ImageName = "empleados_ia_cert-frontend-hotfix:latest"
$BackendName = "empleados_ia_cert-backend-1"
$PostgresName = "empleados_ia_cert-postgres-1"
$FrontendName = "empleados_ia_cert-frontend-1"

function Find-Docker {
    $paths = @(
        "C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        "docker.exe",
        "docker"
    )
    foreach ($p in $paths) {
        if ($p -eq "docker.exe" -or $p -eq "docker") {
            $cmd = Get-Command $p -ErrorAction SilentlyContinue
            if ($cmd) { return $cmd.Source }
        } elseif (Test-Path -LiteralPath $p) {
            return $p
        }
    }
    throw "Docker not found."
}

function Test-ContainerRunning {
    param([string]$Docker, [string]$Name)
    $id = & $Docker ps --filter "name=^/${Name}$" --filter "status=running" -q
    return [bool]$id
}

function Get-FrontendPort {
    param([string]$Dir)
    $port = "5180"
    $envFile = Join-Path $Dir ".env"
    if (Test-Path -LiteralPath $envFile) {
        $line = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^\s*FRONTEND_PORT\s*=' } | Select-Object -First 1
        if ($line -match '=\s*(\d+)') { $port = $Matches[1] }
    }
    return $port
}

function Test-ImageExists {
    param([string]$Docker, [string]$Image)
    & $Docker image inspect $Image 1>$null 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Wait-Http200 {
    param([string]$Url)
    for ($i = 1; $i -le 30; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { return $r }
        } catch {
            # retry
        }
        Start-Sleep -Seconds 2
    }
    throw "HTTP not ready: $Url"
}

function Test-LoginHotfixBundle {
    param([string]$BaseUrl)
    $base = $BaseUrl.TrimEnd("/")
    $page = Invoke-WebRequest -Uri ($base + "/login") -UseBasicParsing -TimeoutSec 15
    $bundle = $page.Content
    $jsMatches = [regex]::Matches($bundle, 'src="(/assets/[^"]+\.js)"')
    foreach ($m in $jsMatches) {
        $js = Invoke-WebRequest -Uri ($base + $m.Groups[1].Value) -UseBasicParsing -TimeoutSec 15
        $bundle += $js.Content
    }
    $need = @("password-toggle", "login-forgot", "Sistema empresarial de IA", "Usuario", "Contrase", "Olvid", "Ocultar")
    foreach ($n in $need) {
        if ($bundle -notlike "*$n*") {
            throw "Hotfix marker missing: $n"
        }
    }
}

$docker = Find-Docker
$root = (Resolve-Path -LiteralPath $HotfixRoot).Path
$cert = (Resolve-Path -LiteralPath $CertDir).Path
$composeBase = Join-Path $cert "docker-compose.yml"
$composeHotfix = Join-Path $PSScriptRoot "docker-compose.frontend-hotfix.yml"

if (-not (Test-Path -LiteralPath $composeBase)) {
    throw "Missing: $composeBase"
}
if (-not (Test-Path -LiteralPath $composeHotfix)) {
    throw "Missing: $composeHotfix"
}

Write-Host "========== PASO 2: DEPLOY FRONTEND HOTFIX ==========" -ForegroundColor Cyan
Write-Host "HotfixRoot: $root"
Write-Host "CertDir:    $cert"
Write-Host "Image:      $ImageName"

Write-Host ""
Write-Host "=== Pre-flight ===" -ForegroundColor Cyan
if (-not (Test-ContainerRunning -Docker $docker -Name $BackendName)) {
    Write-Host "STOP: $BackendName is not running." -ForegroundColor Red
    exit 1
}
if (-not (Test-ContainerRunning -Docker $docker -Name $PostgresName)) {
    Write-Host "STOP: $PostgresName is not running." -ForegroundColor Red
    exit 1
}
Write-Host "Backend:  $BackendName -> running"
Write-Host "Postgres: $PostgresName -> running"

$hasImage = Test-ImageExists -Docker $docker -Image $ImageName
if ($Rebuild -or -not $hasImage) {
    Write-Host ""
    Write-Host "=== Build image ===" -ForegroundColor Cyan
    Push-Location $root
    try {
        & $docker build -t $ImageName -f frontend/Dockerfile .
        if ($LASTEXITCODE -ne 0) {
            Write-Host "STOP: docker build failed." -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
    Write-Host "BUILD: PASS" -ForegroundColor Green
} else {
    Write-Host "BUILD: SKIP (image already exists)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Deploy frontend only (docker compose) ===" -ForegroundColor Cyan
& $docker compose -f $composeBase -f $composeHotfix --project-directory $cert up -d --no-build --no-deps --force-recreate frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "STOP: docker compose up failed." -ForegroundColor Red
    exit 1
}

if (-not (Test-ContainerRunning -Docker $docker -Name $FrontendName)) {
    Write-Host "STOP: $FrontendName is not running after deploy." -ForegroundColor Red
    exit 1
}

$port = Get-FrontendPort -Dir $cert
$loginUrl = "http://localhost:${port}/login"

Write-Host ""
Write-Host "=== Verify HTTP and hotfix UI ===" -ForegroundColor Cyan
try {
    $null = Wait-Http200 -Url $loginUrl
    Write-Host "HTTP: PASS ($loginUrl)" -ForegroundColor Green
    Test-LoginHotfixBundle -BaseUrl "http://localhost:${port}"
    Write-Host "HOTFIX UI: PASS" -ForegroundColor Green
} catch {
    Write-Host "STOP: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "PASO 2: PASS" -ForegroundColor Green
Write-Host "URL: $loginUrl"
Write-Host "Backend:  $BackendName -> running (unchanged)"
Write-Host "Postgres: $PostgresName -> running (unchanged)"
Write-Host "Frontend: $FrontendName -> hotfix image deployed on port $port"
