@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "BACKEND=%ROOT%\backend"
set "VENV=%BACKEND%\.venv"
set "PY=%VENV%\Scripts\python.exe"

echo [INFO] Deteniendo servicios EMPLEADOS_IA (solo PIDs registrados)...

if not exist "%PY%" (
  echo [WARN] Python del proyecto no encontrado. Nada que detener de forma segura.
  exit /b 0
)

"%PY%" "%BACKEND%\scripts\launch_services.py" stop
if errorlevel 1 (
  echo [ERROR] Error al detener servicios registrados.
  exit /b 1
)

echo [OK] Solicitud de detencion completada.
endlocal
exit /b 0
