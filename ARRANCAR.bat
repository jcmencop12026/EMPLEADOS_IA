@echo off
setlocal
cd /d "%~dp0"
title EMPLEADOS_IA - Arrancar
if not exist ".venv\Scripts\python.exe" (
  echo Ejecute CREAR_ENTORNO.bat
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Ejecute CREAR_ENTORNO.bat ^(npm install^)
  pause
  exit /b 1
)
if not exist "data" mkdir data
call .venv\Scripts\activate.bat
rem OAuth Gmail se resuelve tambien desde HKCU\\Environment en backend/app/gateway/secrets.py.
set "EIIAX_LAN_IP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$ip=(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.InterfaceAlias -notmatch 'Loopback|vEthernet|WSL|Docker' } ^| Sort-Object InterfaceMetric ^| Select-Object -First 1 -ExpandProperty IPAddress); if($ip){$ip}"`) do set "EIIAX_LAN_IP=%%I"
if defined EIIAX_LAN_IP (
  set "EIIAX_PUBLIC_URL=http://%EIIAX_LAN_IP%:5180"
) else (
  set "EIIAX_PUBLIC_URL=http://127.0.0.1:5180"
)
echo API local:   http://127.0.0.1:8010
echo Web local:   http://127.0.0.1:5180
echo Invitados:   %EIIAX_PUBLIC_URL%
echo Login: admin / Admin2026*
start "EMPLEADOS_IA API" cmd /k "cd /d %~dp0backend && call ..\.venv\Scripts\activate.bat && set EIIAX_PUBLIC_URL=%EIIAX_PUBLIC_URL%&& python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload"
timeout /t 3 /nobreak >nul
cd frontend
call npm run dev -- --host 0.0.0.0
