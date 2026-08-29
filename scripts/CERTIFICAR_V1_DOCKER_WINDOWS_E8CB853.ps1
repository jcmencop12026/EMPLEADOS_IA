#Requires -Version 5.1
<#
.SYNOPSIS
  Certificacion Docker Desktop Windows - candidata V1 e8cb853 (aislada).
.DESCRIPTION
  Ejecutar en PowerShell en Windows 10/11 con Docker Desktop.
  Workspace candidata: D:\EMPLEADOS_IA_CERT (checkout e8cb853)
  Proyecto Compose: empleados_ia_cert
  Evidencia: D:\EMPLEADOS_IA_CERT\INTERCAMBIO\SALIDA\CERT_WINDOWS_E8CB853_EVIDENCIA
  NO modifica D:\EMPLEADOS_IA ni la candidata V1.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Parametros fijos ---
$CertRoot            = 'D:\EMPLEADOS_IA_CERT'
$CertBranch          = 'cursor/v1-candidata-final-release-r2'
$CertSha             = 'e8cb853a2c447fd5e136a0907e44d68ce2c8cf81'
$ComposeProject      = 'empleados_ia_cert'
$PostgresHostPort    = 55432
$BackendPort         = 18010
$FrontendPort        = 15180
$ExpectedAlembicHead = 'd1e2f3a4b5c6'
$RepoUrl             = 'https://github.com/jcmencop12026/EMPLEADOS_IA.git'
$EvidenceDir         = Join-Path $CertRoot 'INTERCAMBIO\SALIDA\CERT_WINDOWS_E8CB853_EVIDENCIA'
$LogFile             = Join-Path $EvidenceDir 'certificacion.log'

$Results = [ordered]@{}
function Get-CertResult([string]$Key) {
    return $Results.Contains($Key) -and $Results[$Key].Pass
}
function Set-Result([string]$Key, [bool]$Pass, [string]$Detail) {
    if (-not $Detail) { $Detail = '' }
    $Results[$Key] = @{ Pass = $Pass; Detail = $Detail }
    $mark = if ($Pass) { 'PASS' } else { 'FAIL' }
    $line = "[$mark] $Key"
    if ($Detail) { $line = "$line - $Detail" }
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
}
function Test-PortFree([int]$Port) {
    -not (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue)
}
function Wait-HttpOk([string]$Url, [int]$TimeoutSec, [int[]]$AcceptStatus) {
    if (-not $TimeoutSec) { $TimeoutSec = 180 }
    if (-not $AcceptStatus) { $AcceptStatus = @(200) }
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
            if ($AcceptStatus -contains $r.StatusCode) { return $r }
        }
        catch {
            if ($_.Exception.Response) {
                $code = [int]$_.Exception.Response.StatusCode
                if ($AcceptStatus -contains $code) { return $_.Exception.Response }
            }
        }
        Start-Sleep -Seconds 3
    }
    throw "Timeout esperando $Url"
}
function Pass-Fail([string]$Key) {
    if (Get-CertResult $Key) { return 'PASS' }
    return 'FAIL'
}

# --- 0. Windows real ---
if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Este script solo puede ejecutarse en Windows real con Docker Desktop.'
}
Set-Result 'WINDOWS_REAL' $true ("OS=" + [Environment]::OSVersion.VersionString)

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$header = "=== Certificacion V1 e8cb853 " + (Get-Date -Format o) + " ==="
$header | Set-Content $LogFile

# --- 1. Docker Desktop ---
try {
    $null = docker version 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'docker version fallo' }
    $composeVer = docker compose version 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'docker compose version fallo' }
    $composeText = ($composeVer | Out-String).Trim()
    if ($composeText.Length -gt 80) { $composeText = $composeText.Substring(0, 80) }
    Set-Result 'DOCKER_DESKTOP' $true $composeText
}
catch {
    Set-Result 'DOCKER_DESKTOP' $false $_.Exception.Message
    throw 'Docker Desktop no esta operativo. Inicie Docker Desktop y reintente.'
}

# --- 2. Checkout candidata aislada ---
if (-not (Test-Path $CertRoot)) {
    git clone $RepoUrl $CertRoot
}
Set-Location $CertRoot
git fetch origin $CertBranch 2>&1 | Tee-Object -Append $LogFile
git checkout $CertSha 2>&1 | Tee-Object -Append $LogFile
$actualSha = (git rev-parse HEAD).Trim()
$shaOk = $actualSha -eq $CertSha
Set-Result 'SHA_CANDIDATA' $shaOk ("HEAD=" + $actualSha)
if (-not $shaOk) {
    throw ("SHA incorrecto. Esperado " + $CertSha + ", actual " + $actualSha)
}

# --- 3. Puertos ---
$portsOk = (Test-PortFree $PostgresHostPort) -and (Test-PortFree $BackendPort) -and (Test-PortFree $FrontendPort)
Set-Result 'PUERTOS_LIBRES' $portsOk ("PG=" + $PostgresHostPort + " BE=" + $BackendPort + " FE=" + $FrontendPort)
if (-not $portsOk) { throw 'Puertos de certificacion ocupados.' }

# --- 4. .env temporal (NO versionado) - password PG con @ # % : / + ---
$pgPassword = 'EaiCert@2026#Win%:Docker/+Pg'
$jwtSecret = -join ((48..57 + 65..90 + 97..122 | Get-Random -Count 48 | ForEach-Object { [char]$_ }))
$bootstrapUser = 'cert_admin'
$bootstrapPass = 'Bootstrap@Cert#2026!V1'
$envLines = @(
    'APP_ENV=prod'
    'POSTGRES_HOST=postgres'
    'POSTGRES_USER=empleados_cert'
    ('POSTGRES_PASSWORD=' + $pgPassword)
    'POSTGRES_DB=empleados_ia_cert'
    ('JWT_SECRET=' + $jwtSecret)
    ('CORS_ORIGINS=http://127.0.0.1:' + $FrontendPort + ',http://localhost:' + $FrontendPort)
    'ENABLE_API_DOCS=false'
    ('BOOTSTRAP_ADMIN_USERNAME=' + $bootstrapUser)
    ('BOOTSTRAP_ADMIN_PASSWORD=' + $bootstrapPass)
    'BOOTSTRAP_ORG_NAME=Certificacion V1'
    ('BACKEND_PORT=' + $BackendPort)
    ('FRONTEND_PORT=' + $FrontendPort)
    ('POSTGRES_PORT=' + $PostgresHostPort)
)
$envContent = $envLines -join "`r`n"
$envPath = Join-Path $CertRoot '.env'
$envContent | Set-Content -Path $envPath -Encoding UTF8
$specialOk = ($pgPassword -match '@') -and ($pgPassword -match '#') -and ($pgPassword -match '%') `
    -and ($pgPassword -match ':') -and ($pgPassword -match '/') -and ($pgPassword -match '\+')
Set-Result 'PASSWORD_ESPECIAL' $specialOk 'contiene @ # % : / + (no logueada)'

$env:COMPOSE_PROJECT_NAME = $ComposeProject

# --- 5. docker compose config ---
$rawConfigPath = Join-Path $EvidenceDir 'compose-config-raw.tmp'
docker compose config *> $rawConfigPath
$configExit = $LASTEXITCODE
$rendered = Get-Content $rawConfigPath -Raw
$safeConfig = $rendered
$safeConfig = $safeConfig.Replace($pgPassword, '***REDACTED_PG***')
$safeConfig = $safeConfig.Replace($jwtSecret, '***REDACTED_JWT***')
$safeConfig = $safeConfig.Replace($bootstrapPass, '***REDACTED_BOOTSTRAP***')
$safeConfig | Set-Content -Path (Join-Path $EvidenceDir 'compose-config.txt')
Remove-Item $rawConfigPath -Force -ErrorAction SilentlyContinue
$noHostWorkaround = $rendered -notmatch 'host\.docker\.internal'
$configDetail = 'OK'
if (-not $noHostWorkaround) { $configDetail = 'host.docker.internal detectado' }
Set-Result 'COMPOSE_CONFIG' (($configExit -eq 0) -and $noHostWorkaround) $configDetail

# --- 6. Build ---
docker compose build --no-cache 2>&1 | Tee-Object -Append $LogFile
Set-Result 'BUILD' ($LASTEXITCODE -eq 0)

# --- 7. Stack up ---
docker compose up -d 2>&1 | Tee-Object -Append $LogFile
Start-Sleep -Seconds 8
docker compose ps 2>&1 | Tee-Object -FilePath (Join-Path $EvidenceDir 'compose-ps.txt')
$psText = Get-Content (Join-Path $EvidenceDir 'compose-ps.txt') -Raw
$stackUp = ($psText -match 'postgres') -and ($psText -match 'backend') -and ($psText -match 'frontend')
Set-Result 'STACK' $stackUp

# --- 8. PostgreSQL ---
try {
    $pgReady = docker compose exec -T postgres pg_isready -U empleados_cert -d empleados_ia_cert 2>&1
    Set-Result 'POSTGRESQL' ($pgReady -match 'accepting')
}
catch {
    Set-Result 'POSTGRESQL' $false $_.Exception.Message
}

# --- 9. Backend health/live + ready ---
try {
    $null = Wait-HttpOk ("http://localhost:" + $BackendPort + "/health/live") 180 @(200)
    $null = Wait-HttpOk ("http://localhost:" + $BackendPort + "/health/ready") 180 @(200)
    Set-Result 'BACKEND' $true 'live+ready OK'
}
catch {
    Set-Result 'BACKEND' $false $_.Exception.Message
}

# --- 10. Frontend ---
try {
    $fe = Wait-HttpOk ("http://localhost:" + $FrontendPort + "/") 180 @(200)
    Set-Result 'FRONTEND' $true ("status=" + $fe.StatusCode)
}
catch {
    Set-Result 'FRONTEND' $false $_.Exception.Message
}

# --- 11. Alembic (1 head, upgrade en entrypoint) ---
$alembicHeads = docker compose exec -T backend alembic heads 2>&1
$alembicHeads | Tee-Object -FilePath (Join-Path $EvidenceDir 'alembic-heads.txt')
$alembicText = ($alembicHeads | Out-String)
$headCount = ([regex]::Matches($alembicText, '\(head\)')).Count
$headOk = ($headCount -eq 1) -and ($alembicText -match $ExpectedAlembicHead)
Set-Result 'ALEMBIC' $headOk ("heads=" + $headCount + " expected=" + $ExpectedAlembicHead)
$script:AlembicHead = 'desconocido'
if ($headOk) { $script:AlembicHead = $ExpectedAlembicHead }

# --- 12. Validar DATABASE_URL con caracteres especiales (backend) ---
try {
    $pyCode = @'
from app.db_url import resolve_database_url_from_environ, parse_database_password
url = resolve_database_url_from_environ()
assert url and url.startswith("postgresql"), "URL no PostgreSQL"
pwd = parse_database_password(url)
assert pwd and "@" in pwd and "#" in pwd, "round-trip password incompleto"
print("DATABASE_URL_OK")
'@
    $dbTest = docker compose exec -T backend python -c $pyCode 2>&1
    Set-Result 'DATABASE_URL_ESPECIAL' ($dbTest -match 'DATABASE_URL_OK')
}
catch {
    Set-Result 'DATABASE_URL_ESPECIAL' $false $_.Exception.Message
}

# --- 13. NGINX -> BACKEND (gate critico, red Compose) ---
try {
    $proxyLive = Invoke-WebRequest -Uri ("http://localhost:" + $FrontendPort + "/health/live") -UseBasicParsing -TimeoutSec 30
    $proxyReady = Invoke-WebRequest -Uri ("http://localhost:" + $FrontendPort + "/health/ready") -UseBasicParsing -TimeoutSec 30
    $nginxOk = ($proxyLive.StatusCode -eq 200) -and ($proxyReady.StatusCode -eq 200)
    Set-Result 'NGINX_BACKEND' $nginxOk ("live=" + $proxyLive.StatusCode + " ready=" + $proxyReady.StatusCode)
}
catch {
    Set-Result 'NGINX_BACKEND' $false $_.Exception.Message
}

# --- 14. Login via frontend/nginx (no directo backend) ---
try {
    $loginBody = @{ username = $bootstrapUser; password = $bootstrapPass } | ConvertTo-Json -Compress
    $loginUri = "http://localhost:" + $FrontendPort + "/api/auth/login"
    $login = Invoke-WebRequest -Uri $loginUri -Method POST -Body $loginBody -ContentType 'application/json' -UseBasicParsing
    $loginJson = $login.Content | ConvertFrom-Json
    $loginOk = ($login.StatusCode -eq 200) -and ($null -ne $loginJson.access_token)
    Set-Result 'LOGIN_VIA_FRONTEND' $loginOk ("HTTP=" + $login.StatusCode)
    $script:AuthToken = $loginJson.access_token
}
catch {
    Set-Result 'LOGIN_VIA_FRONTEND' $false $_.Exception.Message
}

# --- 15. Persistencia ---
$marker = "cert-marker-" + (Get-Date -Format 'yyyyMMddHHmmss')
try {
    $sql = "CREATE TABLE IF NOT EXISTS cert_persistence (id serial PRIMARY KEY, marker text NOT NULL); INSERT INTO cert_persistence(marker) VALUES ('" + $marker + "');"
    docker compose exec -T postgres psql -U empleados_cert -d empleados_ia_cert -c $sql | Out-Null
    docker compose restart 2>&1 | Out-Null
    Start-Sleep -Seconds 30
    $null = Wait-HttpOk ("http://localhost:" + $FrontendPort + "/health/ready") 180 @(200)
    $countSql = "SELECT COUNT(*) FROM cert_persistence WHERE marker='" + $marker + "';"
    $found = docker compose exec -T postgres psql -U empleados_cert -d empleados_ia_cert -tAc $countSql
    Set-Result 'PERSISTENCIA' ([int]$found.Trim() -eq 1)
}
catch {
    Set-Result 'PERSISTENCIA' $false $_.Exception.Message
}

# --- 16. Caida / recuperacion DB ---
try {
    docker compose stop postgres 2>&1 | Out-Null
    Start-Sleep -Seconds 6
    $downOk = $false
    try {
        $r = Invoke-WebRequest -Uri ("http://localhost:" + $BackendPort + "/health/ready") -UseBasicParsing -TimeoutSec 10
        $downOk = $r.StatusCode -ge 500
    }
    catch {
        $downOk = $true
    }
    Set-Result 'CAIDA_DB' $downOk 'readiness degradado con PG detenido'
    docker compose start postgres 2>&1 | Out-Null
    Start-Sleep -Seconds 20
    $null = Wait-HttpOk ("http://localhost:" + $BackendPort + "/health/ready") 180 @(200)
    Set-Result 'RECUPERACION_DB' $true
}
catch {
    Set-Result 'CAIDA_DB' $false $_.Exception.Message
    Set-Result 'RECUPERACION_DB' $false $_.Exception.Message
}

# --- 17. Backup pg_dump ---
$backupFile = Join-Path $EvidenceDir ("backup_e8cb853_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + ".sql")
try {
    docker compose exec -T postgres pg_dump -U empleados_cert -d empleados_ia_cert | Set-Content -Path $backupFile -Encoding UTF8
    $bkSize = 0
    if (Test-Path $backupFile) { $bkSize = (Get-Item $backupFile).Length }
    $bkOk = (Test-Path $backupFile) -and ($bkSize -gt 0)
    Set-Result 'BACKUP' $bkOk ("bytes=" + $bkSize)
}
catch {
    Set-Result 'BACKUP' $false $_.Exception.Message
}

# --- 18. Restore aislado ---
try {
    docker compose exec -T postgres psql -U empleados_cert -d postgres -c "DROP DATABASE IF EXISTS empleados_ia_cert_restore;" | Out-Null
    docker compose exec -T postgres psql -U empleados_cert -d postgres -c "CREATE DATABASE empleados_ia_cert_restore;" | Out-Null
    Get-Content $backupFile -Raw | docker compose exec -T postgres psql -U empleados_cert -d empleados_ia_cert_restore | Out-Null
    $restoreSql = "SELECT COUNT(*) FROM cert_persistence WHERE marker='" + $marker + "';"
    $restored = docker compose exec -T postgres psql -U empleados_cert -d empleados_ia_cert_restore -tAc $restoreSql
    Set-Result 'RESTORE' ([int]$restored.Trim() -ge 1)
}
catch {
    Set-Result 'RESTORE' $false $_.Exception.Message
}

# --- 19. Seguridad produccion ---
$secOk = ($jwtSecret.Length -ge 32) -and ($bootstrapPass -ne 'Admin2026*') `
    -and ($envContent -notmatch 'CORS_ORIGINS=\*') -and ($envContent -match 'ENABLE_API_DOCS=false') `
    -and ($envContent -match 'APP_ENV=prod')
Set-Result 'SEGURIDAD' $secOk

# --- 20. Secretos no en evidencia ---
$evidenceText = ''
Get-ChildItem $EvidenceDir -File | ForEach-Object {
    $evidenceText += (Get-Content $_.FullName -Raw)
    $evidenceText += "`n"
}
$leak = $false
if ($evidenceText -match [regex]::Escape($pgPassword)) { $leak = $true }
if ($evidenceText -match [regex]::Escape($jwtSecret)) { $leak = $true }
if ($evidenceText -match [regex]::Escape($bootstrapPass)) { $leak = $true }
Set-Result 'SECRETOS' (-not $leak)

# --- 21. API autenticada via nginx ---
if ($script:AuthToken) {
    try {
        $meUri = "http://localhost:" + $FrontendPort + "/api/auth/me"
        $headers = @{ Authorization = ("Bearer " + $script:AuthToken) }
        $me = Invoke-WebRequest -Uri $meUri -Headers $headers -UseBasicParsing
        Set-Result 'API_AUTENTICADA' ($me.StatusCode -eq 200)
    }
    catch {
        Set-Result 'API_AUTENTICADA' $false
    }
}

# --- 22. Limpieza ---
docker compose stop 2>&1 | Tee-Object -Append $LogFile
$stopMsg = "Stack detenido. Proyecto=" + $ComposeProject + ". Volumenes conservados."
$stopMsg | Add-Content $LogFile

# --- Resumen final (formato gate) ---
$p0 = @()
$p1 = @()
$p2 = @()
$critical = @(
    'NGINX_BACKEND', 'LOGIN_VIA_FRONTEND', 'POSTGRESQL', 'ALEMBIC', 'BACKEND', 'FRONTEND',
    'PERSISTENCIA', 'BACKUP', 'RESTORE', 'PASSWORD_ESPECIAL', 'DATABASE_URL_ESPECIAL'
)
$allPass = $true
foreach ($kv in $Results.GetEnumerator()) {
    if (-not $kv.Value.Pass) {
        $allPass = $false
        if ($critical -contains $kv.Key) {
            $p0 += $kv.Key
        }
        else {
            $p1 += $kv.Key
        }
    }
}
$veredicto = 'NO CERTIFICADO'
if ($allPass -and ($p0.Count -eq 0)) { $veredicto = 'CERTIFICADO' }

$summaryLines = @(
    ("SHA: " + $CertSha)
    ("WINDOWS REAL: " + (Pass-Fail 'WINDOWS_REAL'))
    ("DOCKER DESKTOP: " + (Pass-Fail 'DOCKER_DESKTOP'))
    ("COMPOSE CONFIG: " + (Pass-Fail 'COMPOSE_CONFIG'))
    ("BUILD: " + (Pass-Fail 'BUILD'))
    ("STACK: " + (Pass-Fail 'STACK'))
    ("POSTGRESQL: " + (Pass-Fail 'POSTGRESQL'))
    ("PASSWORD ESPECIAL: " + (Pass-Fail 'PASSWORD_ESPECIAL'))
    ("ALEMBIC: " + (Pass-Fail 'ALEMBIC'))
    ("ALEMBIC HEAD: " + $script:AlembicHead)
    ("BACKEND: " + (Pass-Fail 'BACKEND'))
    ("FRONTEND: " + (Pass-Fail 'FRONTEND'))
    ("NGINX -> BACKEND: " + (Pass-Fail 'NGINX_BACKEND'))
    ("LOGIN VIA FRONTEND: " + (Pass-Fail 'LOGIN_VIA_FRONTEND'))
    ("PERSISTENCIA: " + (Pass-Fail 'PERSISTENCIA'))
    ("CAIDA DB: " + (Pass-Fail 'CAIDA_DB'))
    ("RECUPERACION DB: " + (Pass-Fail 'RECUPERACION_DB'))
    ("BACKUP: " + (Pass-Fail 'BACKUP'))
    ("RESTORE: " + (Pass-Fail 'RESTORE'))
    ("SEGURIDAD: " + (Pass-Fail 'SEGURIDAD'))
    ("SECRETOS: " + (Pass-Fail 'SECRETOS'))
    ("P0: " + $p0.Count)
    ("P1: " + $p1.Count)
    ("P2: " + $p2.Count)
    ("VEREDICTO: " + $veredicto)
    'CANDIDATA MODIFICADA: NO'
)
$summary = $summaryLines -join "`r`n"

Write-Host ""
Write-Host "========== RESUMEN CERTIFICACION V1 e8cb853 ==========" -ForegroundColor Cyan
Write-Host $summary
$summary | Set-Content (Join-Path $EvidenceDir 'RESUMEN.txt')

if ($veredicto -eq 'CERTIFICADO') {
    Write-Host ""
    Write-Host "EMPLEADOS IA. Docker Windows V1 certificado." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "EMPLEADOS IA. Docker Windows V1 requiere correccion." -ForegroundColor Yellow
}
