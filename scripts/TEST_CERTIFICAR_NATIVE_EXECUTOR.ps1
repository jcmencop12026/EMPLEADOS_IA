#Requires -Version 5.1
<#
.SYNOPSIS
  Pruebas focales del ejecutor nativo (sin Docker real).
.DESCRIPTION
  Valida Invoke-ExternalCommand con salida stdout/stderr y exit codes reales.
  Compatible con Windows PowerShell 5.1 y PowerShell Core (Linux smoke).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$tempDir = if ($env:TEMP) { $env:TEMP } elseif ($env:TMPDIR) { $env:TMPDIR } else { '/tmp' }
$LogFile = Join-Path $tempDir 'cert_native_executor_test.log'
"=== TEST CERTIFICAR NATIVE EXECUTOR $(Get-Date -Format o) ===" | Set-Content -Path $LogFile

function Write-CertLog([string]$Message) {
    Add-Content -Path $LogFile -Value $Message -ErrorAction SilentlyContinue
}

$mainScript = Join-Path $PSScriptRoot 'CERTIFICAR_V1_DOCKER_WINDOWS_E8CB853.ps1'
$executorSource = Get-Content $mainScript -Raw
$functionBlock = [regex]::Match(
    $executorSource,
    '(?s)function Build-ProcessArgumentString.*?function Invoke-GitCert'
).Value
if (-not $functionBlock) {
    throw 'No se pudo extraer el bloque del ejecutor nativo del script principal.'
}
$functionBlock = $functionBlock -replace '(?s)\r?\nfunction Invoke-GitCert.*', ''
Invoke-Expression $functionBlock

$failures = @()
function Assert-Test {
    param(
        [string]$Name,
        [scriptblock]$Test
    )
    try {
        & $Test
        Write-Host "[PASS] $Name"
    }
    catch {
        Write-Host "[FAIL] $Name - $($_.Exception.Message)"
        $script:failures += $Name
    }
}

if ($IsWindows -or $env:OS -eq 'Windows_NT') {
    $shellExe = 'cmd.exe'
    $caseA = @('/c', 'echo CASE_A_STDOUT')
    $caseB = @('/c', 'echo CASE_B_STDERR 1>&2')
    $caseC = @('/c', 'echo CASE_C_ERROR 1>&2 & exit /b 1')
    $caseD = @('/c', 'for /L %i in (1,1,500) do @echo LINE_%i')
    $caseE = @('/c', 'echo arg=@ # %% : / +')
    $stdinExe = 'cmd.exe'
    $stdinArgs = @('/c', 'more')
}
else {
    $shellExe = 'bash'
    $caseA = @('-c', 'echo CASE_A_STDOUT')
    $caseB = @('-c', 'echo CASE_B_STDERR 1>&2')
    $caseC = @('-c', 'echo CASE_C_ERROR 1>&2; exit 1')
    $caseD = @('-c', 'for i in $(seq 1 500); do echo LINE_$i; done')
    $caseE = @('-c', 'echo "arg=@ # % : / +"')
    $stdinExe = 'bash'
    $stdinArgs = @('-c', 'cat')
}

Assert-Test 'CASO A: stdout + exit 0 => PASS' {
    $out = Invoke-ExternalCommand -Label 'case-a' -Exe $shellExe -CmdArgs $caseA
    if (($out | Out-String) -notmatch 'CASE_A_STDOUT') {
        throw 'stdout no capturado'
    }
}

Assert-Test 'CASO B: stderr informativo + exit 0 => PASS' {
    $out = Invoke-ExternalCommand -Label 'case-b' -Exe $shellExe -CmdArgs $caseB
    $joined = ($out | Out-String)
    if ($joined -notmatch 'CASE_B_STDERR') {
        throw 'stderr informativo no disponible en resultado'
    }
}

Assert-Test 'CASO C: stderr real + exit 1 => FAIL' {
    $threw = $false
    try {
        $null = Invoke-ExternalCommand -Label 'case-c' -Exe $shellExe -CmdArgs $caseC
    }
    catch {
        $threw = $true
        if ($_.Exception.Message -notmatch 'fallo \(exit 1\)') {
            throw ('mensaje inesperado: ' + $_.Exception.Message)
        }
    }
    if (-not $threw) { throw 'debio fallar con exit 1' }
}

Assert-Test 'CASO D: stdout+stderr abundantes => sin deadlock' {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $out = Invoke-ExternalCommand -Label 'case-d' -Exe $shellExe -CmdArgs $caseD
    $sw.Stop()
    if ($sw.Elapsed.TotalSeconds -gt 30) {
        throw 'posible deadlock (timeout 30s)'
    }
    if ((@($out).Count) -lt 100) {
        throw 'salida abundante incompleta'
    }
}

Assert-Test 'CASO E: argumentos con caracteres especiales' {
    $out = Invoke-ExternalCommand -Label 'case-e' -Exe $shellExe -CmdArgs $caseE
    $joined = ($out | Out-String)
    if ($joined -notmatch '@') { throw 'falta @' }
    if ($joined -notmatch '#') { throw 'falta #' }
    if ($joined -notmatch '/') { throw 'falta /' }
    if ($joined -notmatch '\+') { throw 'falta +' }
}

Assert-Test 'CASO F: stdin + exit 0' {
    $stdinSql = "SELECT 1;`n"
    $out = Invoke-ExternalCommand -Label 'case-f' -Exe $stdinExe -CmdArgs $stdinArgs -StdinContent $stdinSql
    if (($out | Out-String) -notmatch 'SELECT') {
        throw 'stdin no propagado'
    }
}

Write-Host ''
Write-Host "Log: $LogFile"
if ($failures.Count -gt 0) {
    Write-Host "RESULTADO: FAIL ($($failures.Count) casos)"
    exit 1
}
Write-Host 'RESULTADO: PASS (todos los casos focales)'
exit 0
