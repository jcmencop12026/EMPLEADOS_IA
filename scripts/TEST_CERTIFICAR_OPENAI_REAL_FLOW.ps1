#Requires -Version 5.1
<#
.SYNOPSIS
  Pruebas de flujo del certificador OpenAI sin llamadas pagadas.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$failures = @()
function Assert-Test {
    param([string]$Name, [scriptblock]$Test)
    try {
        & $Test
        Write-Host "[PASS] $Name"
    }
    catch {
        Write-Host "[FAIL] $Name - $($_.Exception.Message)"
        $script:failures += $Name
    }
}

$mainScript = Join-Path $PSScriptRoot 'CERTIFICAR_V1_OPENAI_REAL_E8CB853.ps1'
$source = Get-Content $mainScript -Raw

function Test-AllowedEvidencePath([string]$RelativePath) {
    $AllowedEvidencePathPatterns = @(
        'INTERCAMBIO/SALIDA/CERT_WINDOWS_E8CB853_EVIDENCIA/',
        'INTERCAMBIO/SALIDA/CERT_OPENAI_REAL_E8CB853_EVIDENCIA/'
    )
    $norm = ($RelativePath -replace '\\', '/').TrimStart('/')
    foreach ($prefix in $AllowedEvidencePathPatterns) {
        if ($norm.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}
function Get-OpenAiKeyPresence {
    $value = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Process')
    if (-not $value) { $value = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'User') }
    if (-not $value) { $value = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Machine') }
    if ($value -and $value.Trim().Length -gt 0) { return 'PRESENTE' }
    return 'AUSENTE'
}
function Remove-SensitiveText([string]$Text) {
    if (-not $Text) { return '' }
    $out = $Text
    $out = $out -replace '(?i)Bearer\s+[A-Za-z0-9._\-]+', 'Bearer ***REDACTED***'
    $out = $out -replace '(?i)(OPENAI_API_KEY|api[_-]?key|authorization)["\s:=]+[^\s,"]+', '$1=***REDACTED***'
    $out = $out -replace 'sk-[A-Za-z0-9]{10,}', 'sk-***REDACTED***'
    return $out
}

Assert-Test 'OPENAI_API_KEY AUSENTE sin variable' {
    $old = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Process')
    [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $null, 'Process')
    try {
        if ((Get-OpenAiKeyPresence) -ne 'AUSENTE') { throw 'debio ser AUSENTE' }
    }
    finally {
        [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $old, 'Process')
    }
}

Assert-Test 'OPENAI_API_KEY PRESENTE con variable' {
    $old = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Process')
    [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'INVALID_TEST_KEY_DO_NOT_CALL', 'Process')
    try {
        if ((Get-OpenAiKeyPresence) -ne 'PRESENTE') { throw 'debio ser PRESENTE' }
    }
    finally {
        [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $old, 'Process')
    }
}

Assert-Test 'evidencia conocida permitida' {
    if (-not (Test-AllowedEvidencePath 'INTERCAMBIO/SALIDA/CERT_WINDOWS_E8CB853_EVIDENCIA/cert.log')) {
        throw 'evidencia windows no permitida'
    }
    if (-not (Test-AllowedEvidencePath 'INTERCAMBIO\SALIDA\CERT_OPENAI_REAL_E8CB853_EVIDENCIA\resumen.txt')) {
        throw 'evidencia openai no permitida'
    }
}

Assert-Test 'cambio versionado fuera de evidencia bloqueado' {
    $norm = 'backend/app/main.py'
    if (Test-AllowedEvidencePath $norm) { throw 'main.py no debe ser evidencia' }
}

Assert-Test 'Remove-SensitiveText redacta Bearer' {
    $out = Remove-SensitiveText 'Authorization: Bearer sk-abcdefghijklmnopqrstuvwxyz'
    if ($out -match 'sk-') { throw 'secreto no redactado' }
    if ($out -notmatch 'REDACTED') { throw 'marcador redaccion ausente' }
}

Assert-Test 'TestMode documentado en script' {
    if ($source -notmatch '\[switch\]\$TestMode') { throw 'param TestMode ausente' }
    if ($source -notmatch 'llamada OpenAI real bloqueada') { throw 'bloqueo TestMode ausente' }
}

Assert-Test 'una sola llamada POST /api/llm/complete' {
    $matches = [regex]::Matches($source, "Invoke-PlatformApi[^\n]+/api/llm/complete")
    if ($matches.Count -ne 1) { throw ('llamadas POST complete=' + $matches.Count + ' esperado 1') }
}

Assert-Test 'prompt minimo OK' {
    if ($source -notmatch "Responde solamente: OK") { throw 'prompt minimo ausente' }
}

Assert-Test 'sin exposicion de fragmentos de key en script' {
    if ($source -match 'Write-Host.*OPENAI_API_KEY|Write-CertLog.*\$value') { throw 'posible exposicion de key' }
}

Write-Host ''
if ($failures.Count -gt 0) {
    Write-Host "RESULTADO: FAIL ($($failures.Count) casos)"
    exit 1
}
Write-Host 'RESULTADO: PASS (flujo OpenAI sin llamadas pagadas)'
exit 0
