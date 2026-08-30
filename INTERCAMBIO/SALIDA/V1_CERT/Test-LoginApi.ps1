#Requires -Version 5.1
<#
.SYNOPSIS
  Prueba login vía API sin imprimir contraseña (solicita prompt seguro).
#>
param(
    [string]$BackendUrl = "http://localhost:18010",
    [string]$Username = "admin"
)

$ErrorActionPreference = "Stop"
$secure = Read-Host "Contraseña para probar login" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$body = @{ username = $Username; password = $password } | ConvertTo-Json
try {
    $login = Invoke-RestMethod -Uri "$BackendUrl/api/auth/login" -Method POST -ContentType "application/json" -Body $body
} catch {
    Write-Host "LOGIN: FAIL ($($_.Exception.Message))" -ForegroundColor Red
    exit 1
}

if (-not $login.access_token) {
    Write-Host "LOGIN: FAIL (sin token)" -ForegroundColor Red
    exit 1
}

$headers = @{ Authorization = "Bearer $($login.access_token)" }
$me = Invoke-RestMethod -Uri "$BackendUrl/api/auth/me" -Headers $headers -Method GET

Write-Host "LOGIN: PASS" -ForegroundColor Green
Write-Host "USUARIO: $($me.username)"
Write-Host "ROL: $($me.role)"
Write-Host "SUPERADMIN: $(if ($me.role -eq 'superadmin') { 'SI' } else { 'NO' })"
Write-Host "PERMISOS: $($me.permissions.Count) asignados"
