$ErrorActionPreference = "Continue"
$ROOT = "D:\EMPLEADOS_IA"
$OUT = Join-Path $ROOT "INTERCAMBIO\CIERRE_EJECUTOR_J.txt"
Set-Location $ROOT
"=== EJECUTOR-J CIERRE INTEGRAL ===" | Out-File $OUT
Get-Date | Out-File $OUT -Append
function Run($name,[scriptblock]$cmd) {
  "" | Tee-Object -FilePath $OUT -Append
  "=== $name ===" | Tee-Object -FilePath $OUT -Append
  & $cmd 2>&1 | Tee-Object -FilePath $OUT -Append
  "EXIT=$LASTEXITCODE" | Tee-Object -FilePath $OUT -Append
}
Run "GIT PRE" { git status --short; git log -3 --oneline }
Run "DEPENDENCIAS BACKEND" { & ".\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt }
Run "REGRESION BACKEND+TESTS" { & ".\.venv\Scripts\python.exe" -m pytest backend\tests tests -q }
Run "CONTRATO REUNION" { & ".\.venv\Scripts\python.exe" -m pytest backend\tests\test_demo_reunion_contract.py -q }
Set-Location (Join-Path $ROOT "frontend")
Run "FRONTEND BUILD" { cmd /c "npm run build" }
Set-Location $ROOT
Run "GIT POST" { git status --short }
"" | Out-File $OUT -Append
"=== FIN EJECUTOR-J ===" | Out-File $OUT -Append
Get-Date | Out-File $OUT -Append
Write-Host "EJECUTOR-J TERMINADO -> $OUT"