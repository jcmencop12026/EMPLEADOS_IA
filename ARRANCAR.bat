@echo off
setlocal EnableExtensions EnableDelayedExpansion
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
if not exist "runtime" mkdir runtime
call .venv\Scripts\activate.bat

rem ============================================================
rem EIIAX: acceso local + acceso remoto temporal para invitados.
rem Quick Tunnel es para demo/pruebas; no requiere dominio.
rem ============================================================
set "EIIAX_PUBLIC_URL="
set "EIIAX_TUNNEL_LOG=%~dp0runtime\cloudflared-quick.log"
set "EIIAX_CLOUDFLARED="

where cloudflared.exe >nul 2>&1
if not errorlevel 1 set "EIIAX_CLOUDFLARED=cloudflared.exe"
if not defined EIIAX_CLOUDFLARED if exist "%~dp0cloudflared.exe" set "EIIAX_CLOUDFLARED=%~dp0cloudflared.exe"
if not defined EIIAX_CLOUDFLARED if exist "%ProgramFiles%\cloudflared\cloudflared.exe" set "EIIAX_CLOUDFLARED=%ProgramFiles%\cloudflared\cloudflared.exe"

echo API local:   http://127.0.0.1:8010
echo Web local:   http://127.0.0.1:5180
echo Login: admin / Admin2026*

rem Arrancar primero API y Web. El backend lee EIIAX_PUBLIC_URL tambien
rem desde runtime\eiaax_public_url.txt para permitir que el tunel nazca despues.
start "EMPLEADOS_IA API" cmd /k "cd /d %~dp0backend && call ..\.venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload"
timeout /t 3 /nobreak >nul
start "EMPLEADOS_IA WEB" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 127.0.0.1"
timeout /t 3 /nobreak >nul

if not defined EIIAX_CLOUDFLARED (
  echo.
  echo [EIIAX] cloudflared no esta instalado.
  echo [EIIAX] La aplicacion local queda disponible, pero no se generara enlace remoto.
  echo [EIIAX] Instale cloudflared y vuelva a ejecutar ARRANCAR.bat.
  goto :LOCAL
)

del /q "%EIIAX_TUNNEL_LOG%" >nul 2>&1
del /q "%~dp0runtime\eiaax_public_url.txt" >nul 2>&1
start "EIIAX TUNEL HTTPS" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\MONITOR_TUNEL_EIIAX.ps1" -Cloudflared "%EIIAX_CLOUDFLARED%" -Root "%~dp0"

echo.
echo [EIIAX] Creando acceso HTTPS temporal para el Gerente...
for /l %%N in (1,1,30) do (
  for /f "usebackq delims=" %%U in (`powershell -NoProfile -Command "$p='%EIIAX_TUNNEL_LOG%'; if(Test-Path $p){$m=Select-String -Path $p -Pattern 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' -AllMatches | Select-Object -Last 1; if($m){$m.Matches.Value | Select-Object -Last 1}}"`) do set "EIIAX_PUBLIC_URL=%%U"
  if defined EIIAX_PUBLIC_URL goto :TUNNEL_OK
  timeout /t 1 /nobreak >nul
)

echo [EIIAX] No se obtuvo URL publica del tunel.
echo [EIIAX] Revise: %EIIAX_TUNNEL_LOG%
goto :LOCAL

:TUNNEL_OK
> "%~dp0runtime\eiaax_public_url.txt" echo !EIIAX_PUBLIC_URL!
echo.
echo ============================================================
echo EIIAX REMOTO LISTO
echo Invitados: !EIIAX_PUBLIC_URL!
echo Canal supervisado: si Cloudflare lo interrumpe, EIIAX intentara renovarlo.
echo La cabina actualizara el enlace vigente; si cambia, reenvie la invitacion.
echo ============================================================

:LOCAL
echo.
echo EIIAX local: http://127.0.0.1:5180
echo Puede cerrar esta ventana; API, Web y Tunel tienen sus propias ventanas.
pause
