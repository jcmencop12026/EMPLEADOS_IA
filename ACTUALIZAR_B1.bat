@echo off
cd /d "%~dp0"
title EMPLEADOS_IA - Actualizar B1
echo git pull origin main...
git pull origin main
if errorlevel 1 pause & exit /b 1
echo.
echo Si existe frontend\package.json ejecute:
echo   CREAR_ENTORNO.bat
echo   ARRANCAR.bat
echo.
curl -s http://127.0.0.1:8010/health 2>nul
echo.
pause
