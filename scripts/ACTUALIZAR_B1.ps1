# EMPLEADOS_IA — traer B1 desde GitHub (ejecutar en D:\EMPLEADOS_IA)
Set-Location $PSScriptRoot\..
Write-Host "git pull origin main..."
git pull origin main
if ($LASTEXITCODE -ne 0) { pause; exit 1 }
$health = Invoke-RestMethod -Uri "http://127.0.0.1:8010/health" -ErrorAction SilentlyContinue
if ($health.phase -eq "B1") {
  Write-Host "[OK] B1 detectado en API"
} else {
  Write-Host "[AVISO] /health no muestra B1. Si pull no trajo cambios, use Cursor local en esta carpeta."
}
Write-Host "Luego: .\CREAR_ENTORNO.bat  y  .\ARRANCAR.bat"
pause
