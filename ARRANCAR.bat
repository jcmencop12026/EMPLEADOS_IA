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
echo API:  http://127.0.0.1:8010
echo Web:  http://127.0.0.1:5180
echo Login: admin / Admin2026*
start "EMPLEADOS_IA API" cmd /k "cd /d %~dp0backend && call ..\.venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload"
timeout /t 3 /nobreak >nul
cd frontend
call npm run dev
