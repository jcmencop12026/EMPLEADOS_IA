#Requires -Version 5.1
<#
.SYNOPSIS
  Pruebas focales de composicion de argumentos docker compose.
.DESCRIPTION
  Valida orden: docker compose [globales] <subcomando> [opciones subcomando].
  Sin ejecutar Docker real.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$CertDir = 'D:\EMPLEADOS_IA_CERT'
$ComposeFile = $CertDir + '\docker-compose.yml'

$mainScript = Join-Path $PSScriptRoot 'CERTIFICAR_V1_DOCKER_WINDOWS_E8CB853.ps1'
$source = Get-Content $mainScript -Raw
$functionBlock = [regex]::Match(
    $source,
    '(?s)function Build-ProcessArgumentString.*?function Test-PortFree'
).Value
if (-not $functionBlock) {
    throw 'No se pudo extraer funciones compose del script principal.'
}
$functionBlock = $functionBlock -replace '(?s)\r?\nfunction Test-PortFree.*', ''
Invoke-Expression $functionBlock

$failures = @()
function Assert-Compose {
    param(
        [string]$Name,
        [string[]]$ComposeArgs,
        [string[]]$ExpectedTail
    )
    try {
        $allArgs = Get-DockerComposeCommandArgs -ComposeArgs $ComposeArgs
        $globalPrefix = @('compose', '--project-directory', $CertDir, '-f', $ComposeFile)
        $expected = $globalPrefix + $ExpectedTail
        $same = ($allArgs.Count -eq $expected.Count)
        if ($same) {
            for ($i = 0; $i -lt $expected.Count; $i++) {
                if ($allArgs[$i] -ne $expected[$i]) {
                    $same = $false
                    break
                }
            }
        }
        if (-not $same) {
            throw ('esperado [' + ($expected -join '|') + '] actual [' + ($allArgs -join '|') + ']')
        }
        $joined = $allArgs -join ' '
        if ($joined -match 'compose\s+.*\s+--no-cache(\s|$)' -and $joined -notmatch '\sbuild\s+--no-cache') {
            throw 'detectado --no-cache sin subcomando build'
        }
        Write-Host "[PASS] $Name"
    }
    catch {
        Write-Host "[FAIL] $Name - $($_.Exception.Message)"
        $script:failures += $Name
    }
}

Assert-Compose 'build --no-cache' @('build', '--no-cache') @('build', '--no-cache')
Assert-Compose 'up -d' @('up', '-d') @('up', '-d')
Assert-Compose 'down' @('down') @('down')
Assert-Compose 'exec -T postgres pg_isready' @('exec', '-T', 'postgres', 'pg_isready', '-U', 'empleados_cert') @('exec', '-T', 'postgres', 'pg_isready', '-U', 'empleados_cert')
Assert-Compose 'ps' @('ps') @('ps')
Assert-Compose 'config' @('config') @('config')
Assert-Compose 'ruta Windows con espacios' @('exec', '-T', 'postgres', 'psql', '-c', 'SELECT 1') @('exec', '-T', 'postgres', 'psql', '-c', 'SELECT 1')

$script:CertDir = 'D:\EMPLEADOS_IA CERT\sub'
$script:ComposeFile = 'D:\EMPLEADOS_IA CERT\sub\docker-compose.yml'
Assert-Compose 'ruta Windows especial' @('build', '--no-cache') @('build', '--no-cache')

function Test-ComposeBinding {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ComposeArgs
    )
    return $ComposeArgs
}
$bound = Test-ComposeBinding build --no-cache
if (($bound -join '|') -ne 'build|--no-cache') {
    Write-Host "[FAIL] binding build --no-cache - [$($bound -join '|')]"
    $failures += 'binding build --no-cache'
}
else {
    Write-Host '[PASS] binding build --no-cache'
}

Write-Host ''
if ($failures.Count -gt 0) {
    Write-Host "RESULTADO: FAIL ($($failures.Count) casos)"
    exit 1
}
Write-Host 'RESULTADO: PASS (composicion docker compose)'
exit 0
