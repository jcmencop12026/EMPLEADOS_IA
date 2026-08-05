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
echo [OK] Ejecute ARRANCAR.bat
pause
