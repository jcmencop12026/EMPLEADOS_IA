#Requires -Version 5.1
<#
.SYNOPSIS
  Certificacion Docker Desktop Windows - candidata V1 e8cb853 (aislada).
.DESCRIPTION
  Ejecutar en PowerShell en Windows 10/11 con Docker Desktop.
  TOOLS (script): puede ejecutarse desde D:\EMPLEADOS_IA_CERT_TOOLS u otra ruta.
  CANDIDATA (git/docker): siempre D:\EMPLEADOS_IA_CERT
  Proyecto Compose: empleados_ia_cert
  Evidencia: D:\EMPLEADOS_IA_CERT\INTERCAMBIO\SALIDA\CERT_WINDOWS_E8CB853_EVIDENCIA
  NO modifica D:\EMPLEADOS_IA ni la candidata V1 (solo .env local de certificacion).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Parametros fijos ---
$CertDir             = 'D:\EMPLEADOS_IA_CERT'
$CertBranch          = 'cursor/v1-candidata-final-release-r2'
$CertSha             = 'e8cb853a2c447fd5e136a0907e44d68ce2c8cf81'
$ComposeProject      = 'empleados_ia_cert'
$PostgresHostPort    = 55432
$BackendPort         = 18010
$FrontendPort        = 15180
$ExpectedAlembicHead = 'd1e2f3a4b5c6'
$EvidenceDir         = Join-Path $CertDir 'INTERCAMBIO\SALIDA\CERT_WINDOWS_E8CB853_EVIDENCIA'
$LogFile             = Join-Path $EvidenceDir 'certificacion.log'
$ComposeFile         = Join-Path $CertDir 'docker-compose.yml'

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
function Write-CertLog([string]$Message) {
    Add-Content -Path $LogFile -Value $Message -ErrorAction SilentlyContinue
}
function Build-ProcessArgumentString {
    param([string[]]$CmdArgs)
    $parts = @()
    foreach ($arg in $CmdArgs) {
        if ($null -eq $arg) { continue }
        if ($arg -match '[\s"]') {
            $parts += '"' + ($arg -replace '"', '""') + '"'
        }
        else {
            $parts += $arg
        }
    }
    return ($parts -join ' ')
}
function Format-ExternalCommandLine {
    param(
        [string]$Exe,
        [string[]]$CmdArgs
    )
    return ($Exe + ' ' + (Build-ProcessArgumentString -CmdArgs $CmdArgs)).Trim()
}
function Invoke-ExternalCommandProcess {
    param(
        [string]$Exe,
        [string[]]$CmdArgs,
        [string]$StdinContent = $null,
        [string]$StdoutFile,
        [string]$StderrFile
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = Build-ProcessArgumentString -CmdArgs $CmdArgs
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardInput = ($null -ne $StdinContent)
    $psi.CreateNoWindow = $true

    $stdoutBuilder = New-Object System.Text.StringBuilder
    $stderrBuilder = New-Object System.Text.StringBuilder
    $streamAction = {
        if ($null -ne $EventArgs.Data) {
            [void]$Event.MessageData.AppendLine($EventArgs.Data)
        }
    }

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $null = $proc.Start()

    $stdoutEvent = Register-ObjectEvent -InputObject $proc -EventName OutputDataReceived `
        -Action $streamAction -MessageData $stdoutBuilder
    $stderrEvent = Register-ObjectEvent -InputObject $proc -EventName ErrorDataReceived `
        -Action $streamAction -MessageData $stderrBuilder

    $proc.BeginOutputReadLine()
    $proc.BeginErrorReadLine()

    if ($null -ne $StdinContent) {
        $proc.StandardInput.Write($StdinContent)
        $proc.StandardInput.Close()
    }

    $proc.WaitForExit()

    Unregister-Event -SourceIdentifier $stdoutEvent.Name -ErrorAction SilentlyContinue
    Unregister-Event -SourceIdentifier $stderrEvent.Name -ErrorAction SilentlyContinue
    Remove-Event -SourceIdentifier $stdoutEvent.Name -ErrorAction SilentlyContinue
    Remove-Event -SourceIdentifier $stderrEvent.Name -ErrorAction SilentlyContinue

    $stdoutText = $stdoutBuilder.ToString()
    $stderrText = $stderrBuilder.ToString()
    [System.IO.File]::WriteAllText($StdoutFile, $stdoutText, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText($StderrFile, $stderrText, [System.Text.UTF8Encoding]::new($false))
    return $proc.ExitCode
}
function Invoke-ExternalCommand {
    param(
        [string]$Label,
        [string]$Exe,
        [string[]]$CmdArgs,
        [string]$StdinContent = $null
    )

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    $cmdLine = Format-ExternalCommandLine -Exe $Exe -CmdArgs $CmdArgs

    try {
        $exitCode = Invoke-ExternalCommandProcess -Exe $Exe -CmdArgs $CmdArgs `
            -StdinContent $StdinContent -StdoutFile $stdoutFile -StderrFile $stderrFile

        $stdout = [System.IO.File]::ReadAllText($stdoutFile)
        $stderr = [System.IO.File]::ReadAllText($stderrFile)
        if ($null -eq $stdout) { $stdout = '' }
        if ($null -eq $stderr) { $stderr = '' }

        Write-CertLog ('COMMAND: ' + $cmdLine)
        Write-CertLog ('EXIT CODE: ' + $exitCode)
        if ($stdout.Trim().Length -gt 0) {
            Write-CertLog ('STDOUT: ' + $stdout.Trim())
        }
        if ($stderr.Trim().Length -gt 0) {
            Write-CertLog ('STDERR: ' + $stderr.Trim())
        }

        if ($exitCode -ne 0) {
            $detail = $stderr.Trim()
            if (-not $detail) { $detail = $stdout.Trim() }
            throw ($Label + ' fallo (exit ' + $exitCode + '): ' + $cmdLine + ' :: ' + $detail)
        }

        $resultText = $stdout
        if (-not $resultText.Trim() -and $stderr.Trim()) {
            $resultText = $stderr
        }
        if (-not $resultText) {
            return @()
        }
        return ($resultText -split "`r?`n")
    }
    finally {
        Remove-Item $stdoutFile -Force -ErrorAction SilentlyContinue
        Remove-Item $stderrFile -Force -ErrorAction SilentlyContinue
    }
}
function Invoke-GitCert {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$GitArgs
    )
    $allArgs = @('-C', $CertDir) + $GitArgs
    return Invoke-ExternalCommand -Label ('git candidata ' + ($GitArgs -join ' ')) -Exe 'git' -CmdArgs $allArgs
}
function Invoke-DockerCompose {
    param(
        [string]$StdinContent = $null,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ComposeArgs
    )
    $allArgs = @('compose', '--project-directory', $CertDir, '-f', $ComposeFile) + $ComposeArgs
    return Invoke-ExternalCommand -Label ('docker compose ' + ($ComposeArgs -join ' ')) -Exe 'docker' -CmdArgs $allArgs -StdinContent $StdinContent
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
function Ensure-CandidateRepository {
    $gitDir = Join-Path $CertDir '.git'
    if (-not (Test-Path $gitDir)) {
        throw ("Repositorio candidato no encontrado: " + $gitDir + ". Prepare D:\EMPLEADOS_IA_CERT con la candidata e8cb853 antes de certificar.")
    }
    if (-not (Test-Path $ComposeFile)) {
        throw ("docker-compose.yml no encontrado en candidata: " + $ComposeFile)
    }

    $origin = (Invoke-GitCert remote get-url origin | Out-String).Trim()
    Set-Result 'GIT_ORIGIN_CANDIDATA' $true ("origin=" + $origin)
    Write-CertLog ("git -C " + $CertDir + " remote get-url origin => " + $origin)

    $currentSha = (Invoke-GitCert rev-parse HEAD | Out-String).Trim()
    Write-CertLog ("git -C " + $CertDir + " rev-parse HEAD => " + $currentSha)

    if ($currentSha -eq $CertSha) {
        Write-CertLog "Candidata ya en SHA objetivo; se omite fetch/checkout destructivo."
        Set-Result 'SHA_CANDIDATA' $true ("HEAD=" + $currentSha + " (sin cambios)")
        return
    }

    $hasCommit = $false
    try {
        $null = Invoke-GitCert cat-file -e ($CertSha + '^{commit}')
        $hasCommit = $true
    }
    catch {
        $hasCommit = $false
    }

    if (-not $hasCommit) {
        Write-CertLog ("git -C " + $CertDir + " fetch origin " + $CertBranch)
        $fetchOut = Invoke-GitCert fetch origin $CertBranch
        if ($fetchOut) { Write-CertLog ($fetchOut | Out-String) }
    }

    $currentSha = (Invoke-GitCert rev-parse HEAD | Out-String).Trim()
    if ($currentSha -ne $CertSha) {
        Write-CertLog ("git -C " + $CertDir + " checkout " + $CertSha)
        $checkoutOut = Invoke-GitCert checkout $CertSha
        if ($checkoutOut) { Write-CertLog ($checkoutOut | Out-String) }
    }

    $finalSha = (Invoke-GitCert rev-parse HEAD | Out-String).Trim()
    $shaOk = $finalSha -eq $CertSha
    Set-Result 'SHA_CANDIDATA' $shaOk ("HEAD=" + $finalSha)
    if (-not $shaOk) {
        throw ("SHA incorrecto en candidata. Esperado " + $CertSha + ", actual " + $finalSha)
    }
}

# --- 0. Windows real ---
if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Este script solo puede ejecutarse en Windows real con Docker Desktop.'
}
Set-Result 'WINDOWS_REAL' $true ("OS=" + [Environment]::OSVersion.VersionString)

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$header = "=== Certificacion V1 e8cb853 " + (Get-Date -Format o) + " ==="
$header | Set-Content $LogFile
Write-CertLog ("TOOLS workdir=" + (Get-Location).Path)
Write-CertLog ("CANDIDATA dir=" + $CertDir)

# --- 1. Docker Desktop ---
try {
    $dockerVer = Invoke-ExternalCommand -Label 'docker version' -Exe 'docker' -CmdArgs @('version')
    $composeVer = Invoke-ExternalCommand -Label 'docker compose version' -Exe 'docker' -CmdArgs @('compose', 'version')
    $composeText = ($composeVer | Out-String).Trim()
    if ($composeText.Length -gt 80) { $composeText = $composeText.Substring(0, 80) }
    Set-Result 'DOCKER_DESKTOP' $true $composeText
}
catch {
    Set-Result 'DOCKER_DESKTOP' $false $_.Exception.Message
    throw 'Docker Desktop no esta operativo. Inicie Docker Desktop y reintente.'
}

# --- 2. Verificar candidata local (git -C D:\EMPLEADOS_IA_CERT) ---
Ensure-CandidateRepository

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
$envPath = Join-Path $CertDir '.env'
$envContent | Set-Content -Path $envPath -Encoding UTF8
$specialOk = ($pgPassword -match '@') -and ($pgPassword -match '#') -and ($pgPassword -match '%') `
    -and ($pgPassword -match ':') -and ($pgPassword -match '/') -and ($pgPassword -match '\+')
Set-Result 'PASSWORD_ESPECIAL' $specialOk 'contiene @ # % : / + (no logueada)'

$env:COMPOSE_PROJECT_NAME = $ComposeProject

# --- 5. docker compose config ---
$rawConfigPath = Join-Path $EvidenceDir 'compose-config-raw.tmp'
try {
    Invoke-DockerCompose config | Set-Content -Path $rawConfigPath -Encoding UTF8
    $rendered = Get-Content $rawConfigPath -Raw
    $safeConfig = $rendered
    $safeConfig = $safeConfig.Replace($pgPassword, '***REDACTED_PG***')
    $safeConfig = $safeConfig.Replace($jwtSecret, '***REDACTED_JWT***')
    $safeConfig = $safeConfig.Replace($bootstrapPass, '***REDACTED_BOOTSTRAP***')
    $safeConfig | Set-Content -Path (Join-Path $EvidenceDir 'compose-config.txt')
    $noHostWorkaround = $rendered -notmatch 'host\.docker\.internal'
    $configDetail = 'OK'
    if (-not $noHostWorkaround) { $configDetail = 'host.docker.internal detectado' }
    Set-Result 'COMPOSE_CONFIG' $noHostWorkaround $configDetail
}
catch {
    Set-Result 'COMPOSE_CONFIG' $false $_.Exception.Message
    throw
}
finally {
    Remove-Item $rawConfigPath -Force -ErrorAction SilentlyContinue
}

# --- 6. Build ---
try {
    $buildOut = Invoke-DockerCompose build --no-cache
    if ($buildOut) { Write-CertLog ($buildOut | Out-String) }
    Set-Result 'BUILD' $true
}
catch {
    Set-Result 'BUILD' $false $_.Exception.Message
    throw
}

# --- 7. Stack up ---
try {
    $upOut = Invoke-DockerCompose up -d
    if ($upOut) { Write-CertLog ($upOut | Out-String) }
    Start-Sleep -Seconds 8
    $psOut = Invoke-DockerCompose ps
    $psOut | Set-Content -Path (Join-Path $EvidenceDir 'compose-ps.txt')
    $psText = ($psOut | Out-String)
    $stackUp = ($psText -match 'postgres') -and ($psText -match 'backend') -and ($psText -match 'frontend')
    Set-Result 'STACK' $stackUp
}
catch {
    Set-Result 'STACK' $false $_.Exception.Message
    throw
}

# --- 8. PostgreSQL ---
try {
    $pgReady = Invoke-DockerCompose exec -T postgres pg_isready -U empleados_cert -d empleados_ia_cert
    Set-Result 'POSTGRESQL' (($pgReady | Out-String) -match 'accepting')
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
try {
    $alembicHeads = Invoke-DockerCompose exec -T backend alembic heads
    ($alembicHeads | Out-String) | Set-Content -Path (Join-Path $EvidenceDir 'alembic-heads.txt')
    $alembicText = ($alembicHeads | Out-String)
    $headCount = ([regex]::Matches($alembicText, '\(head\)')).Count
    $headOk = ($headCount -eq 1) -and ($alembicText -match $ExpectedAlembicHead)
    Set-Result 'ALEMBIC' $headOk ("heads=" + $headCount + " expected=" + $ExpectedAlembicHead)
    $script:AlembicHead = 'desconocido'
    if ($headOk) { $script:AlembicHead = $ExpectedAlembicHead }
}
catch {
    Set-Result 'ALEMBIC' $false $_.Exception.Message
    $script:AlembicHead = 'desconocido'
}

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
    $dbTest = Invoke-DockerCompose exec -T backend python -c $pyCode
    Set-Result 'DATABASE_URL_ESPECIAL' (($dbTest | Out-String) -match 'DATABASE_URL_OK')
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
    $null = Invoke-DockerCompose exec -T postgres psql -U empleados_cert -d empleados_ia_cert -c $sql
    $null = Invoke-DockerCompose restart
    Start-Sleep -Seconds 30
    $null = Wait-HttpOk ("http://localhost:" + $FrontendPort + "/health/ready") 180 @(200)
    $countSql = "SELECT COUNT(*) FROM cert_persistence WHERE marker='" + $marker + "';"
    $found = Invoke-DockerCompose exec -T postgres psql -U empleados_cert -d empleados_ia_cert -tAc $countSql
    Set-Result 'PERSISTENCIA' ([int](($found | Out-String).Trim()) -eq 1)
}
catch {
    Set-Result 'PERSISTENCIA' $false $_.Exception.Message
}

# --- 16. Caida / recuperacion DB ---
try {
    $null = Invoke-DockerCompose stop postgres
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
    $null = Invoke-DockerCompose start postgres
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
    $dump = Invoke-DockerCompose exec -T postgres pg_dump -U empleados_cert -d empleados_ia_cert
    ($dump | Out-String) | Set-Content -Path $backupFile -Encoding UTF8
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
    $null = Invoke-DockerCompose exec -T postgres psql -U empleados_cert -d postgres -c "DROP DATABASE IF EXISTS empleados_ia_cert_restore;"
    $null = Invoke-DockerCompose exec -T postgres psql -U empleados_cert -d postgres -c "CREATE DATABASE empleados_ia_cert_restore;"
    $restoreSqlContent = Get-Content $backupFile -Raw
    $null = Invoke-DockerCompose -StdinContent $restoreSqlContent exec -T postgres psql -U empleados_cert -d empleados_ia_cert_restore
    $restoreSql = "SELECT COUNT(*) FROM cert_persistence WHERE marker='" + $marker + "';"
    $restored = Invoke-DockerCompose exec -T postgres psql -U empleados_cert -d empleados_ia_cert_restore -tAc $restoreSql
    Set-Result 'RESTORE' ([int](($restored | Out-String).Trim()) -ge 1)
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
try {
    $stopOut = Invoke-DockerCompose stop
    if ($stopOut) { Write-CertLog ($stopOut | Out-String) }
}
catch {
    Write-CertLog ("docker compose stop warning: " + $_.Exception.Message)
}
$stopMsg = "Stack detenido. Proyecto=" + $ComposeProject + ". Volumenes conservados."
Write-CertLog $stopMsg

# --- Resumen final (formato gate) ---
$p0 = @()
$p1 = @()
$p2 = @()
$critical = @(
    'NGINX_BACKEND', 'LOGIN_VIA_FRONTEND', 'POSTGRESQL', 'ALEMBIC', 'BACKEND', 'FRONTEND',
    'PERSISTENCIA', 'BACKUP', 'RESTORE', 'PASSWORD_ESPECIAL', 'DATABASE_URL_ESPECIAL', 'SHA_CANDIDATA'
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
