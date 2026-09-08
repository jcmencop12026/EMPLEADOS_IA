#Requires -Version 5.1
<#
.SYNOPSIS
    Actualización controlada de la copia aislada EIAAX V1 para prueba humana.

.DESCRIPTION
    Detiene la demo, verifica copia Git limpia, hace checkout exacto al SHA certificado,
    prepara e inicia la demo aislada en D:\EIAAX_V1_PRUEBA (o ruta indicada).

    Usa la variable de entorno EIAAX_WORKTREE (no parámetros inexistentes en scripts hijos).

.PARAMETER Ruta
    Ruta de la copia aislada (worktree de prueba humana).

.PARAMETER Sha
    Commit exacto autorizado para prueba humana.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\actualizar_prueba_humana_v1.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\actualizar_prueba_humana_v1.ps1 `
        -Ruta "D:\EIAAX_V1_PRUEBA" `
        -Sha "57b89c6a04bff6452bab06e1b4e4c73a5f2647a3"
#>

param(
    [string]$Ruta = "D:\EIAAX_V1_PRUEBA",
    [string]$Sha = "57b89c6a04bff6452bab06e1b4e4c73a5f2647a3"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " EIAAX V1 - ACTUALIZACION CONTROLADA PARA PRUEBA HUMANA" -ForegroundColor Cyan
Write-Host " SHA AUTORIZADO: $Sha" -ForegroundColor Green
Write-Host "============================================================"
Write-Host ""

if (-not (Test-Path -LiteralPath $Ruta)) {
    throw "ABORTADO: no existe la ruta de prueba aislada: $Ruta"
}

Set-Location -LiteralPath $Ruta
$env:EIAAX_WORKTREE = (Resolve-Path -LiteralPath $Ruta).Path

Write-Host "=== 1. RUTA ACTUAL ===" -ForegroundColor Green
Get-Location
Write-Host "EIAAX_WORKTREE: $($env:EIAAX_WORKTREE)"

Write-Host ""
Write-Host "=== 2. VERIFICANDO REPOSITORIO GIT ===" -ForegroundColor Green

if (-not (Test-Path -LiteralPath ".git")) {
    throw "ABORTADO: $Ruta no contiene un repositorio Git."
}

$git = Get-Command git -ErrorAction SilentlyContinue

if (-not $git) {
    $GitCandidatos = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    )

    $GitExe = $GitCandidatos |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1

    if (-not $GitExe) {
        throw "ABORTADO: no se encontró Git."
    }
}
else {
    $GitExe = $git.Source
}

Write-Host "Git: $GitExe"

Write-Host ""
Write-Host "=== 3. DETENIENDO DEMO AISLADA SI ESTA ACTIVA ===" -ForegroundColor Green

$StopScript = Join-Path $Ruta "scripts\windows\detener_demo_eiaax.ps1"

if (Test-Path -LiteralPath $StopScript) {
    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $StopScript

    if ($LASTEXITCODE -ne 0) {
        throw "ABORTADO: detener_demo_eiaax.ps1 terminó con código $LASTEXITCODE."
    }
}
else {
    Write-Host "Script de detención no encontrado en esta revisión. Se continúa sin ejecutarlo." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 4. VERIFICANDO CAMBIOS LOCALES ===" -ForegroundColor Green

$Cambios = & $GitExe status --porcelain

if ($LASTEXITCODE -ne 0) {
    throw "ABORTADO: git status falló."
}

if ($Cambios) {
    Write-Host ""
    Write-Host "ABORTADO: existen cambios locales y NO serán sobrescritos." -ForegroundColor Red
    $Cambios | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    throw "La copia aislada no está limpia."
}

Write-Host "Copia limpia: OK" -ForegroundColor Green

Write-Host ""
Write-Host "=== 5. DESCARGANDO REFERENCIAS DE GITHUB ===" -ForegroundColor Green

& $GitExe fetch origin --prune

if ($LASTEXITCODE -ne 0) {
    throw "ABORTADO: git fetch falló."
}

Write-Host ""
Write-Host "=== 6. VERIFICANDO SHA AUTORIZADO ===" -ForegroundColor Green

& $GitExe cat-file -e "$Sha^{commit}" 2>$null

if ($LASTEXITCODE -ne 0) {
    throw "ABORTADO: el commit autorizado $Sha no está disponible (ejecute git fetch origin)."
}

Write-Host "SHA encontrado: $Sha" -ForegroundColor Green

Write-Host ""
Write-Host "=== 7. CAMBIANDO EXACTAMENTE AL SHA CERTIFICADO ===" -ForegroundColor Green

& $GitExe checkout --detach $Sha

if ($LASTEXITCODE -ne 0) {
    throw "ABORTADO: no fue posible cambiar al SHA certificado."
}

$HEAD = (& $GitExe rev-parse HEAD).Trim()

Write-Host "HEAD actual: $HEAD"

if ($HEAD -ne $Sha) {
    throw "ABORTADO: HEAD no coincide con el SHA autorizado."
}

Write-Host "HEAD EXACTO CONFIRMADO." -ForegroundColor Green

Write-Host ""
Write-Host "=== 8. VERIFICANDO LIMPIEZA DESPUES DEL CHECKOUT ===" -ForegroundColor Green

$CambiosFinales = & $GitExe status --porcelain

if ($CambiosFinales) {
    $CambiosFinales | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    throw "ABORTADO: aparecieron cambios locales después del checkout."
}

Write-Host "Repositorio limpio: OK" -ForegroundColor Green

Write-Host ""
Write-Host "=== 9. PREPARANDO DEMO EN ESTA COPIA AISLADA ===" -ForegroundColor Green

$PrepareScript = Join-Path $Ruta "scripts\windows\preparar_demo_eiaax.ps1"

if (-not (Test-Path -LiteralPath $PrepareScript)) {
    throw "ABORTADO: no existe $PrepareScript"
}

& powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File $PrepareScript

if ($LASTEXITCODE -ne 0) {
    throw "ABORTADO: preparar_demo_eiaax.ps1 terminó con código $LASTEXITCODE."
}

Write-Host ""
Write-Host "=== 10. INICIANDO DEMO AISLADA ===" -ForegroundColor Green

$StartScript = Join-Path $Ruta "scripts\windows\iniciar_demo_eiaax.ps1"

if (-not (Test-Path -LiteralPath $StartScript)) {
    throw "ABORTADO: no existe $StartScript"
}

& powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File $StartScript

if ($LASTEXITCODE -ne 0) {
    throw "ABORTADO: iniciar_demo_eiaax.ps1 terminó con código $LASTEXITCODE."
}

Write-Host ""
Write-Host "=== 11. ESPERANDO SERVICIOS ===" -ForegroundColor Green

Start-Sleep -Seconds 8

Write-Host ""
Write-Host "=== 12. VERIFICANDO BACKEND ===" -ForegroundColor Green

try {
    $Health = Invoke-WebRequest `
        -Uri "http://127.0.0.1:8000/health" `
        -UseBasicParsing `
        -TimeoutSec 10

    Write-Host "Backend HTTP: $($Health.StatusCode)" -ForegroundColor Green
}
catch {
    Write-Host "ADVERTENCIA: backend todavía no respondió correctamente." -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 13. VERIFICANDO FRONTEND ===" -ForegroundColor Green

try {
    $Frontend = Invoke-WebRequest `
        -Uri "http://127.0.0.1:5180" `
        -UseBasicParsing `
        -TimeoutSec 10

    Write-Host "Frontend HTTP: $($Frontend.StatusCode)" -ForegroundColor Green
}
catch {
    Write-Host "ADVERTENCIA: frontend todavía no respondió correctamente." -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " ACTUALIZACION FINALIZADA" -ForegroundColor Green
Write-Host "============================================================"
Write-Host "Ruta : $Ruta"
Write-Host "HEAD : $HEAD"
Write-Host "URL  : http://127.0.0.1:5180"
Write-Host "============================================================"
Write-Host ""

Start-Process "http://127.0.0.1:5180"
