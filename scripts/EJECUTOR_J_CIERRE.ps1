$ErrorActionPreference = "Stop"
$ROOT = "D:\EMPLEADOS_IA"
$LOGDIR = Join-Path $ROOT "INTERCAMBIO"
$STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$OUT = Join-Path $LOGDIR ("CIERRE_EJECUTOR_J_" + $STAMP + ".txt")
$SUMMARY = Join-Path $LOGDIR ("CIERRE_EJECUTOR_J_" + $STAMP + "_RESUMEN.txt")
New-Item -ItemType Directory -Force -Path $LOGDIR | Out-Null
Set-Location $ROOT

function Write-Log([string]$text) {
    $text | Out-File -FilePath $OUT -Append -Encoding utf8
    Write-Host $text
}

function Run-Step([string]$name,[scriptblock]$cmd) {
    Write-Log ""
    Write-Log ("=== " + $name + " ===")
    $global:LASTEXITCODE = 0
    try {
        & $cmd 2>&1 | ForEach-Object {
            $_ | Out-File -FilePath $OUT -Append -Encoding utf8
            Write-Host $_
        }
        $code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
    } catch {
        $_ | Out-File -FilePath $OUT -Append -Encoding utf8
        Write-Host $_
        $code = 1
    }
    Write-Log ("EXIT=" + $code)
    return $code
}

"=== EJECUTOR-J CIERRE INTEGRAL ===" | Out-File -FilePath $OUT -Encoding utf8
(Get-Date).ToString("s") | Out-File -FilePath $OUT -Append -Encoding utf8

$results = [ordered]@{}

$results["GIT_PRE"] = Run-Step "GIT PRE" {
    git status --short
    git log -3 --oneline
}

$results["DEPENDENCIAS_BACKEND"] = Run-Step "DEPENDENCIAS BACKEND" {
    & ".\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
}

$results["REGRESION"] = Run-Step "REGRESION BACKEND+TESTS" {
    & ".\.venv\Scripts\python.exe" -m pytest backend\tests tests -q
}

$results["CONTRATO_REUNION"] = Run-Step "CONTRATO REUNION" {
    & ".\.venv\Scripts\python.exe" -m pytest backend\tests\test_demo_reunion_contract.py -q
}

Set-Location (Join-Path $ROOT "frontend")
$results["FRONTEND_BUILD"] = Run-Step "FRONTEND BUILD" {
    cmd /c "npm run build"
}
Set-Location $ROOT

$results["GIT_POST"] = Run-Step "GIT POST" {
    git status --short
}

$pass = ($results.Values | Where-Object { $_ -ne 0 }).Count -eq 0
"=== RESUMEN EJECUTOR-J ===" | Out-File -FilePath $SUMMARY -Encoding utf8
foreach ($k in $results.Keys) {
    ($k + "=" + $results[$k]) | Out-File -FilePath $SUMMARY -Append -Encoding utf8
}
("RESULTADO=" + $(if ($pass) { "PASS" } else { "FAIL" })) | Out-File -FilePath $SUMMARY -Append -Encoding utf8
("LOG=" + $OUT) | Out-File -FilePath $SUMMARY -Append -Encoding utf8

Write-Host ""
Write-Host "==============================================="
Write-Host ("EJECUTOR-J TERMINADO: " + $(if ($pass) { "PASS" } else { "FAIL" }))
Write-Host ("LOG: " + $OUT)
Write-Host ("RESUMEN: " + $SUMMARY)
Write-Host "==============================================="

if (-not $pass) { exit 1 }
