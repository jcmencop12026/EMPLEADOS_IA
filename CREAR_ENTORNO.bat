@echo off
setlocal
cd /d "%~dp0"
title EMPLEADOS_IA - Crear entorno
where py >nul 2>&1 && set PY=py -3 || set PY=python
if not exist ".venv\Scripts\python.exe" (%PY% -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
if not exist "data" mkdir data
where npm >nul 2>&1
if errorlevel 1 (
  echo [AVISO] Node.js no encontrado. Instale LTS desde https://nodejs.org para el frontend.
) else (
  cd frontend
  call npm install
  cd ..
)
echo.
echo [OK] Ejecute ARRANCAR.bat
echo Login: admin / Admin2026*
pause
