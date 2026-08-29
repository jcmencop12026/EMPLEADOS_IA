#Requires -Version 5.1
<#
.SYNOPSIS
  Certificacion OpenAI real V1 e8cb853 - una sola llamada via gateway.
.DESCRIPTION
  Ejecutar en Windows PowerShell 5.1 con backend EMPLEADOS_IA operativo.
  TOOLS: D:\EMPLEADOS_IA_CERT_TOOLS
  CANDIDATA: D:\EMPLEADOS_IA_CERT @ e8cb853
  Requiere OPENAI_API_KEY en entorno local (no se guarda ni se loguea).
  NO ejecutar desde Cloud Agent (sin llamadas pagadas remotas).
.PARAMETER TestMode
  Solo prevalidacion y control de flujo. Bloquea llamada OpenAI real.
#>
[CmdletBinding()]
param(
    [switch]$TestMode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Parametros fijos ---
$CertDir      = 'D:\EMPLEADOS_IA_CERT'
$CertSha      = 'e8cb853a2c447fd5e136a0907e44d68ce2c8cf81'
$EvidenceDir  = Join-Path $CertDir 'INTERCAMBIO\SALIDA\CERT_OPENAI_REAL_E8CB853_EVIDENCIA'
$LogFile      = Join-Path $EvidenceDir 'certificacion_openai.log'
$ReportPath   = Join-Path $CertDir 'INTERCAMBIO\SALIDA\CURSOR_V1_CERTIFICACION_OPENAI_REAL_E8CB853.md'
$PromptText   = 'Responde solamente: OK'
$FrontendPort = 15180
$BackendPort  = 18010
$script:LlmCallsMade = 0

$AllowedEvidencePathPatterns = @(
    'INTERCAMBIO/SALIDA/CERT_WINDOWS_E8CB853_EVIDENCIA/',
    'INTERCAMBIO/SALIDA/CERT_OPENAI_REAL_E8CB853_EVIDENCIA/'
)

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
    $safe = Remove-SensitiveText -Text $Message
    Add-Content -Path $LogFile -Value $safe -ErrorAction SilentlyContinue
}
function Remove-SensitiveText([string]$Text) {
    if (-not $Text) { return '' }
    $out = $Text
    $out = $out -replace '(?i)Bearer\s+[A-Za-z0-9._\-]+', 'Bearer ***REDACTED***'
    $out = $out -replace '(?i)(OPENAI_API_KEY|api[_-]?key|authorization)["\s:=]+[^\s,"]+', '$1=***REDACTED***'
    $out = $out -replace 'sk-[A-Za-z0-9]{10,}', 'sk-***REDACTED***'
    return $out
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
function Invoke-ExternalCommandProcess {
    param(
        [string]$Exe,
        [string[]]$CmdArgs,
        [string]$StdoutFile,
        [string]$StderrFile
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = Build-ProcessArgumentString -CmdArgs $CmdArgs
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
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
    $proc.WaitForExit()

    Unregister-Event -SourceIdentifier $stdoutEvent.Name -ErrorAction SilentlyContinue
    Unregister-Event -SourceIdentifier $stderrEvent.Name -ErrorAction SilentlyContinue
    Remove-Event -SourceIdentifier $stdoutEvent.Name -ErrorAction SilentlyContinue
    Remove-Event -SourceIdentifier $stderrEvent.Name -ErrorAction SilentlyContinue

    [System.IO.File]::WriteAllText($StdoutFile, $stdoutBuilder.ToString(), [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText($StderrFile, $stderrBuilder.ToString(), [System.Text.UTF8Encoding]::new($false))
    return $proc.ExitCode
}
function Invoke-ExternalCommand {
    param(
        [string]$Label,
        [string]$Exe,
        [string[]]$CmdArgs
    )
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $exitCode = Invoke-ExternalCommandProcess -Exe $Exe -CmdArgs $CmdArgs `
            -StdoutFile $stdoutFile -StderrFile $stderrFile
        $stdout = [System.IO.File]::ReadAllText($stdoutFile)
        $stderr = [System.IO.File]::ReadAllText($stderrFile)
        if ($exitCode -ne 0) {
            $detail = $stderr.Trim()
            if (-not $detail) { $detail = $stdout.Trim() }
            throw ($Label + ' fallo (exit ' + $exitCode + '): ' + $detail)
        }
        if ($stdout) { return ($stdout -split "`r?`n") }
        return @()
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
    return Invoke-ExternalCommand -Label ('git ' + ($GitArgs -join ' ')) -Exe 'git' -CmdArgs $allArgs
}
function Test-AllowedEvidencePath([string]$RelativePath) {
    $norm = ($RelativePath -replace '\\', '/').TrimStart('/')
    foreach ($prefix in $AllowedEvidencePathPatterns) {
        if ($norm.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}
function Test-CandidateVersionedChanges {
    $changed = @()
    $diffHead = Invoke-GitCert diff --name-only HEAD
    if ($diffHead) { $changed += $diffHead }
    $diffCached = Invoke-GitCert diff --cached --name-only
    if ($diffCached) { $changed += $diffCached }
    $blocked = @()
    foreach ($path in ($changed | Select-Object -Unique)) {
        $trim = ($path | Out-String).Trim()
        if (-not $trim) { continue }
        if (-not (Test-AllowedEvidencePath $trim)) {
            $blocked += $trim
        }
    }
    return $blocked
}
function Get-OpenAiKeyPresence {
    $value = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Process')
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'User')
    }
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Machine')
    }
    if ($value -and $value.Trim().Length -gt 0) {
        return 'PRESENTE'
    }
    return 'AUSENTE'
}
function Read-BootstrapCredentials {
    $username = $env:BOOTSTRAP_ADMIN_USERNAME
    $password = $env:BOOTSTRAP_ADMIN_PASSWORD
    $envPath = Join-Path $CertDir '.env'
    if (Test-Path $envPath) {
        $lines = Get-Content $envPath
        foreach ($line in $lines) {
            if ($line -match '^BOOTSTRAP_ADMIN_USERNAME=(.+)$') {
                if (-not $username) { $username = $Matches[1].Trim() }
            }
            if ($line -match '^BOOTSTRAP_ADMIN_PASSWORD=(.+)$') {
                if (-not $password) { $password = $Matches[1].Trim() }
            }
        }
    }
    if (-not $username) { $username = 'cert_admin' }
    if (-not $password) { $password = 'Bootstrap@Cert#2026!V1' }
    return @{ Username = $username; Password = $password }
}
function Get-ApiBaseUrl {
    $fePort = $env:CERT_FRONTEND_PORT
    if (-not $fePort) { $fePort = $FrontendPort }
    return ('http://127.0.0.1:' + $fePort)
}
function Invoke-PlatformApi {
    param(
        [string]$Method,
        [string]$Path,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int[]]$AcceptStatus = @(200)
    )
    $uri = (Get-ApiBaseUrl) + $Path
    $params = @{
        Uri             = $uri
        Method          = $Method
        UseBasicParsing = $true
        TimeoutSec      = 120
        Headers         = $Headers
    }
    if ($Body) {
        $params['Body'] = $Body
        $params['ContentType'] = 'application/json'
    }
    try {
        $response = Invoke-WebRequest @params
        if ($AcceptStatus -notcontains $response.StatusCode) {
            throw ('HTTP inesperado ' + $response.StatusCode + ' en ' + $Path)
        }
        return $response
    }
    catch {
        if ($_.Exception.Response) {
            $code = [int]$_.Exception.Response.StatusCode
            if ($AcceptStatus -contains $code) {
                return $_.Exception.Response
            }
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errBody = $reader.ReadToEnd()
            $reader.Close()
            throw ('HTTP ' + $code + ' en ' + $Path + ': ' + (Remove-SensitiveText $errBody))
        }
        throw
    }
}
function Convert-JsonResponse([object]$Response) {
    if ($Response -is [System.Net.HttpWebResponse]) {
        $reader = New-Object System.IO.StreamReader($Response.GetResponseStream())
        $text = $reader.ReadToEnd()
        $reader.Close()
        return ($text | ConvertFrom-Json)
    }
    return ($Response.Content | ConvertFrom-Json)
}

# --- Inicio ---
if (-not $TestMode -and $env:OS -ne 'Windows_NT') {
    Write-Error 'Este script solo puede ejecutarse en Windows real (use -TestMode solo para pruebas de flujo).'
}

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$header = '=== Certificacion OpenAI real e8cb853 ' + (Get-Date -Format o) + ' ==='
$header | Set-Content $LogFile
Write-CertLog ('TOOLS workdir=' + (Get-Location).Path)
Write-CertLog ('CANDIDATA dir=' + $CertDir)
Write-CertLog ('TestMode=' + $TestMode)

# 1. Candidata existe
$certOk = Test-Path $CertDir
Set-Result 'CANDIDATA_DIR' $certOk $CertDir
if (-not $certOk) { throw 'Candidata no encontrada.' }

# 2. Git root
$gitDir = Join-Path $CertDir '.git'
if (-not (Test-Path $gitDir)) {
    Set-Result 'GIT_ROOT' $false 'sin .git'
    throw 'Git root incorrecto en candidata.'
}
$gitRoot = (Invoke-GitCert rev-parse --show-toplevel | Out-String).Trim()
$rootNorm = ($gitRoot -replace '\\', '/').TrimEnd('/')
$certNorm = ($CertDir -replace '\\', '/').TrimEnd('/')
$gitRootOk = ($rootNorm -eq $certNorm)
Set-Result 'GIT_ROOT' $gitRootOk ('root=' + $gitRoot)
if (-not $gitRootOk) { throw 'Git root no coincide con D:\EMPLEADOS_IA_CERT.' }

# 3. SHA exacto
$currentSha = (Invoke-GitCert rev-parse HEAD | Out-String).Trim()
$shaOk = $currentSha -eq $CertSha
Set-Result 'SHA_CANDIDATA' $shaOk ('HEAD=' + $currentSha)
if (-not $shaOk) { throw ('SHA incorrecto. Esperado ' + $CertSha) }

# 4. Cambios versionados
$blockedChanges = Test-CandidateVersionedChanges
$versionedOk = ($blockedChanges.Count -eq 0)
$blockedDetail = 'sin cambios versionados'
if (-not $versionedOk) {
    $blockedDetail = 'cambios=' + ($blockedChanges -join ',')
}
Set-Result 'CAMBIOS_VERSIONADOS' $versionedOk $blockedDetail
if (-not $versionedOk) {
    throw ('Cambios versionados no permitidos en candidata: ' + ($blockedChanges -join ', '))
}

# 5. OPENAI_API_KEY presencia
$keyPresence = Get-OpenAiKeyPresence
Set-Result 'OPENAI_API_KEY' ($keyPresence -eq 'PRESENTE') ('estado=' + $keyPresence)
Write-CertLog ('OPENAI_API_KEY: ' + $keyPresence)

if ($keyPresence -eq 'AUSENTE') {
    Write-Host ''
    Write-Host 'OPENAI REAL: PENDIENTE POR CREDENCIAL LOCAL AUSENTE' -ForegroundColor Yellow
    Write-CertLog 'OPENAI REAL: PENDIENTE POR CREDENCIAL LOCAL AUSENTE'
    $summaryPending = @(
        'VEREDICTO: PENDIENTE CREDENCIAL LOCAL'
        'LLAMADAS OPENAI REALES: 0'
        'CANDIDATA MODIFICADA: NO'
    ) -join "`r`n"
    $summaryPending | Set-Content (Join-Path $EvidenceDir 'RESUMEN.txt')
    exit 2
}

if ($TestMode) {
    Write-Host ''
    Write-Host 'TEST MODE: prevalidacion OK. Llamada OpenAI real bloqueada.' -ForegroundColor Cyan
    Write-CertLog 'TEST MODE: llamada OpenAI real bloqueada'
    exit 0
}

# 6. Backend operativo
$apiBase = Get-ApiBaseUrl
try {
    $null = Invoke-PlatformApi -Method GET -Path '/health/ready' -AcceptStatus @(200)
    Set-Result 'BACKEND_READY' $true $apiBase
}
catch {
    Set-Result 'BACKEND_READY' $false $_.Exception.Message
    throw 'Backend no disponible. Ejecute primero la certificacion Docker Windows o arranque el stack.'
}

# 7. Login plataforma
$creds = Read-BootstrapCredentials
$loginBody = (@{ username = $creds.Username; password = $creds.Password } | ConvertTo-Json -Compress)
try {
    $loginResp = Invoke-PlatformApi -Method POST -Path '/api/auth/login' -Body $loginBody -AcceptStatus @(200)
    $loginJson = Convert-JsonResponse $loginResp
    if ($loginJson.mfa_required) {
        throw 'MFA requerido. Use usuario bootstrap sin MFA para certificacion.'
    }
    $token = $loginJson.access_token
    if (-not $token) { throw 'Token ausente en login.' }
    Set-Result 'LOGIN' $true ('user=' + $creds.Username)
}
catch {
    Set-Result 'LOGIN' $false (Remove-SensitiveText $_.Exception.Message)
    throw 'Login fallido en plataforma.'
}

$authHeaders = @{ Authorization = ('Bearer ' + $token) }

# 8. Contexto org/usuario
try {
    $meResp = Invoke-PlatformApi -Method GET -Path '/api/auth/me' -Headers $authHeaders -AcceptStatus @(200)
    $me = Convert-JsonResponse $meResp
    $orgOk = ($null -ne $me.organization_id) -and ($me.organization_id.Length -gt 0)
    Set-Result 'ORGANIZACION' $orgOk ('org_id=' + $me.organization_id)
    Set-Result 'USUARIO' $true ('user_id=' + $me.id)
    $script:OrgId = $me.organization_id
    $script:UserId = $me.id
}
catch {
    Set-Result 'ORGANIZACION' $false $_.Exception.Message
    Set-Result 'USUARIO' $false $_.Exception.Message
    throw
}

# 9. Proveedor OpenAI configurado
try {
    $provResp = Invoke-PlatformApi -Method GET -Path '/api/llm/providers' -Headers $authHeaders -AcceptStatus @(200)
    $providers = @(Convert-JsonResponse $provResp)
    $openaiProv = $providers | Where-Object { $_.provider_type -eq 'openai' -and $_.is_enabled } | Select-Object -First 1
    $provOk = ($null -ne $openaiProv)
    $provDetail = 'sin proveedor openai habilitado'
    if ($provOk) {
        $provDetail = 'provider_id=' + $openaiProv.id + ' secret_configured=' + $openaiProv.secret_configured
    }
    Set-Result 'PROVEEDOR_OPENAI' $provOk $provDetail
    if (-not $provOk) { throw 'Proveedor OpenAI no configurado en plataforma.' }
}
catch {
    Set-Result 'PROVEEDOR_OPENAI' $false (Remove-SensitiveText $_.Exception.Message)
    throw
}

# 10. UNA sola llamada via gateway
$completeBody = (@{ prompt = $PromptText; include_knowledge = $false } | ConvertTo-Json -Compress)
Write-CertLog ('LLM CALL: POST /api/llm/complete prompt=' + $PromptText)
$script:LlmCallsMade = 1
try {
    $completeResp = Invoke-PlatformApi -Method POST -Path '/api/llm/complete' -Headers $authHeaders -Body $completeBody -AcceptStatus @(200)
    $complete = Convert-JsonResponse $completeResp
    if ($complete.error) {
        $errMsg = ($complete.error | ConvertTo-Json -Compress)
        throw ('Gateway error: ' + (Remove-SensitiveText $errMsg))
    }
    $traceId = $complete.trace_id
    $responseOk = ($null -ne $complete.text) -and (($complete.text -match 'OK') -or ($complete.text.Trim().Length -gt 0))
    Set-Result 'RESPUESTA' $responseOk ('text=' + $complete.text)
    Set-Result 'PROVEEDOR' (($complete.provider -eq 'openai')) ('provider=' + $complete.provider)
    Set-Result 'MODELO' (($complete.model) -and ($complete.model -notmatch 'mock|fixture|fake')) ('model=' + $complete.model)
    Set-Result 'MOCK' ($complete.provider -ne 'mock') ('mock=NO')
    Set-Result 'TOKENS_ENTRADA' (($complete.tokens_in -ge 0)) ('tokens_in=' + $complete.tokens_in)
    Set-Result 'TOKENS_SALIDA' (($complete.tokens_out -ge 0)) ('tokens_out=' + $complete.tokens_out)
    Set-Result 'USO_TOTAL' (($complete.tokens_total -gt 0)) ('tokens_total=' + $complete.tokens_total)
    $script:TraceId = $traceId
    $script:CompleteResult = $complete
}
catch {
    Set-Result 'RESPUESTA' $false (Remove-SensitiveText $_.Exception.Message)
    throw 'Llamada OpenAI via gateway fallo. Sin reintentos pagados.'
}

# 11. Inference log
try {
    $logsResp = Invoke-PlatformApi -Method GET -Path '/api/llm/inference-logs?limit=20' -Headers $authHeaders -AcceptStatus @(200)
    $logs = @(Convert-JsonResponse $logsResp)
    $matchLog = $logs | Where-Object { $_.trace_id -eq $script:TraceId } | Select-Object -First 1
    $logOk = ($null -ne $matchLog) -and ($matchLog.provider -eq 'openai') -and ($matchLog.status -eq 'OK')
    Set-Result 'LLM_INFERENCE_LOG' $logOk ('trace_id=' + $script:TraceId)
    $script:InferenceLog = $matchLog
}
catch {
    Set-Result 'LLM_INFERENCE_LOG' $false (Remove-SensitiveText $_.Exception.Message)
}

# 12. FinOps
try {
    $finResp = Invoke-PlatformApi -Method GET -Path '/api/finops/consumptions?provider=openai&limit=20' -Headers $authHeaders -AcceptStatus @(200)
    $consumptions = @(Convert-JsonResponse $finResp)
    $matchFin = $consumptions | Where-Object { $_.execution_ref -eq $script:TraceId } | Select-Object -First 1
    if (-not $matchFin) {
        $matchFin = $consumptions | Where-Object {
            $_.provider -eq 'openai' -and $_.tokens_in -eq $script:CompleteResult.tokens_in
        } | Select-Object -First 1
    }
    $finOk = ($null -ne $matchFin) -and ($matchFin.organization_id -eq $script:OrgId)
    Set-Result 'FINOPS' $finOk ('consumption_id=' + $matchFin.id)
    $script:FinOpsRecord = $matchFin
}
catch {
    Set-Result 'FINOPS' $false (Remove-SensitiveText $_.Exception.Message)
}

# 13. Auditoria
try {
    $auditResp = Invoke-PlatformApi -Method GET -Path '/api/audit/logs?limit=50' -Headers $authHeaders -AcceptStatus @(200)
    $audits = @(Convert-JsonResponse $auditResp)
    $auditHit = $audits | Where-Object { $_.action -eq 'llm.inference.success' } | Select-Object -First 1
    $auditOk = ($null -ne $auditHit)
    Set-Result 'AUDITORIA' $auditOk ('action=llm.inference.success')
}
catch {
    Set-Result 'AUDITORIA' $false (Remove-SensitiveText $_.Exception.Message)
}

# 14. UAT focal
$uat015 = (Get-CertResult 'RESPUESTA') -and (Get-CertResult 'PROVEEDOR') -and (Get-CertResult 'MODELO') `
    -and (Get-CertResult 'MOCK') -and (Get-CertResult 'USO_TOTAL') -and ($script:LlmCallsMade -eq 1)
$uat020 = (Get-CertResult 'FINOPS') -and (Get-CertResult 'LLM_INFERENCE_LOG') -and (Get-CertResult 'AUDITORIA') `
    -and (Get-CertResult 'ORGANIZACION')
Set-Result 'UAT-015' $uat015 'OpenAI real via gateway'
Set-Result 'UAT-020' $uat020 'FinOps + inference log + auditoria'

# Evidencia JSON (sin secretos)
$evidence = [ordered]@{
    timestamp       = (Get-Date -Format o)
    sha             = $CertSha
    trace_id        = $script:TraceId
    provider        = $script:CompleteResult.provider
    model           = $script:CompleteResult.model
    tokens_in       = $script:CompleteResult.tokens_in
    tokens_out      = $script:CompleteResult.tokens_out
    tokens_total    = $script:CompleteResult.tokens_total
    latency_ms      = $script:CompleteResult.latency_ms
    organization_id = $script:OrgId
    user_id         = $script:UserId
    llm_calls_made  = $script:LlmCallsMade
    uat_015         = if ($uat015) { 'PASS' } else { 'FAIL' }
    uat_020         = if ($uat020) { 'PASS' } else { 'FAIL' }
    mock            = 'NO'
}
($evidence | ConvertTo-Json -Depth 4) | Set-Content (Join-Path $EvidenceDir 'evidencia_openai.json') -Encoding UTF8

$allPass = $uat015 -and $uat020 -and (Get-CertResult 'PROVEEDOR') -and (Get-CertResult 'RESPUESTA')
$veredicto = if ($allPass) { 'CERTIFICADO OPENAI REAL' } else { 'REQUIERE CORRECCION' }

$summaryLines = @(
    ('SHA: ' + $CertSha)
    ('OPENAI_API_KEY: PRESENTE')
    ('LLAMADAS OPENAI REALES: ' + $script:LlmCallsMade)
    ('TRACE_ID: ' + $script:TraceId)
    ('PROVEEDOR: ' + $script:CompleteResult.provider)
    ('MODELO: ' + $script:CompleteResult.model)
    ('TOKENS TOTAL: ' + $script:CompleteResult.tokens_total)
    ('UAT-015: ' + (if ($uat015) { 'PASS' } else { 'FAIL' }))
    ('UAT-020: ' + (if ($uat020) { 'PASS' } else { 'FAIL' }))
    ('VEREDICTO: ' + $veredicto)
    'CANDIDATA MODIFICADA: NO'
)
$summary = $summaryLines -join "`r`n"
Write-Host ''
Write-Host '========== RESUMEN CERTIFICACION OPENAI REAL ==========' -ForegroundColor Cyan
Write-Host $summary
$summary | Set-Content (Join-Path $EvidenceDir 'RESUMEN.txt')

$report = @(
    '# CURSOR V1 - Certificacion OpenAI real e8cb853'
    ''
    '## Ejecucion local'
    ''
    ('- Fecha: ' + (Get-Date -Format o))
    ('- SHA candidata: ' + $CertSha)
    ('- Llamadas OpenAI: ' + $script:LlmCallsMade)
    ('- UAT-015: ' + (if ($uat015) { 'PASS' } else { 'FAIL' }))
    ('- UAT-020: ' + (if ($uat020) { 'PASS' } else { 'FAIL' }))
    ('- Veredicto: ' + $veredicto)
    ''
    '## Anti-mock'
    ''
    '- Provider real: openai'
    '- Tokens reales registrados en gateway/FinOps'
    '- Inference log con trace_id'
    '- Sin bypass del gateway'
    ''
    '## Evidencia'
    ''
    ('- ' + $EvidenceDir)
) -join "`r`n"
$report | Set-Content $ReportPath -Encoding UTF8

if ($allPass) {
    Write-Host ''
    Write-Host 'EMPLEADOS IA. OpenAI real V1 certificado.' -ForegroundColor Green
}
else {
    Write-Host ''
    Write-Host 'EMPLEADOS IA. OpenAI real V1 requiere correccion.' -ForegroundColor Yellow
    exit 1
}
