@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo [INFO] Deteniendo servicios EMPLEADOS_IA...

REM Detener solo ventanas tituladas de este proyecto (no procesos ajenos)
taskkill /FI "WINDOWTITLE eq EMPLEADOS_IA_BACKEND*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq EMPLEADOS_IA_FRONTEND*" /F >nul 2>&1

REM Fallback: puertos conocidos del proyecto (8010 backend, 5180 frontend)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8010 .*LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5180 .*LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
)

if exist "%ROOT%\data\empleados_ia.pids" del /f /q "%ROOT%\data\empleados_ia.pids"

echo [OK] Servicios EMPLEADOS_IA detenidos.
endlocal
exit /b 0
