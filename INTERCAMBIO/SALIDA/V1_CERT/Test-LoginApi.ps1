#Requires -Version 5.1
<#
.SYNOPSIS
  Test login and SUPERADMIN via real API (password via secure prompt).
.DESCRIPTION
  Does not print the password. Clears password variable after use.
.PARAMETER BackendUrl
  Backend base URL (default: http://localhost:18010)
.PARAMETER Username
  Username (default: admin)
#>
param(
    [string]$BackendUrl = "http://localhost:18010",
    [string]$Username = "admin"
)

$ErrorActionPreference = "Stop"

function Clear-String([string]$Value) {
    if ($null -eq $Value) { return }
    # Best-effort memory clear in PowerShell
    $Value = $null
}

$secure = Read-Host "Password to test login" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$password = $null
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    $secure.Dispose()
}

try {
    $loginBody = @{ username = $Username; password = $password } | ConvertTo-Json -Compress
    $loginUri = ($BackendUrl.TrimEnd("/")) + "/api/auth/login"

    try {
        $login = Invoke-RestMethod -Uri $loginUri -Method POST -ContentType "application/json; charset=utf-8" -Body $loginBody
    } catch {
        Write-Host "LOGIN: FAIL ($($_.Exception.Message))" -ForegroundColor Red
        exit 1
    }

    if (-not $login.access_token) {
        Write-Host "LOGIN: FAIL (no access_token)" -ForegroundColor Red
        exit 1
    }

    $headers = @{ Authorization = "Bearer $($login.access_token)" }
    $meUri = ($BackendUrl.TrimEnd("/")) + "/api/auth/me"
    $me = Invoke-RestMethod -Uri $meUri -Headers $headers -Method GET

    $isSuper = ($me.role -eq "superadmin")
    Write-Host "LOGIN: PASS" -ForegroundColor Green
    Write-Host "USER: $($me.username)"
    Write-Host "ROLE: $($me.role)"
    Write-Host "SUPERADMIN: $(if ($isSuper) { 'YES' } else { 'NO' })"
    if ($me.permissions) {
        Write-Host "PERMISSIONS: $($me.permissions.Count)"
    }

    if (-not $isSuper) {
        Write-Host "SUPERADMIN CHECK: FAIL" -ForegroundColor Red
        exit 2
    }
    Write-Host "SUPERADMIN CHECK: PASS" -ForegroundColor Green
} finally {
    Clear-String $password
    $loginBody = $null
}
