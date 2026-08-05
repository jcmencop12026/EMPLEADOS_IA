@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Ejecute CREAR_ENTORNO.bat & pause & exit /b 1)
call .venv\Scripts\activate.bat
if not exist "data" mkdir data
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
