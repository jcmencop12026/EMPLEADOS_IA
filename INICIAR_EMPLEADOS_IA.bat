@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%" || exit /b 1

set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "DATA=%ROOT%\data"
set "VENV=%BACKEND%\.venv"
set "PIDFILE=%DATA%\empleados_ia.pids"
set "EXITCODE=1"

if not exist "%BACKEND%\app\main.py" exit /b 1
if not exist "%FRONTEND%\package.json" exit /b 1
if not exist "%DATA%" mkdir "%DATA%"

if not exist "%VENV%\Scripts\python.exe" (
  py -3 -m venv "%VENV%" 2>nul || python -m venv "%VENV%"
  if errorlevel 1 exit /b 1
)

set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"

"%PY%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
  "%PIP%" install -q -r "%BACKEND%\requirements.txt"
  if errorlevel 1 exit /b 1
)

if not exist "%FRONTEND%\node_modules" (
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 (
    popd
    exit /b 1
  )
  popd
)

if exist "%PIDFILE%" (
  "%PY%" "%BACKEND%\scripts\launch_services.py" stop >nul 2>&1
)

pushd "%BACKEND%"
"%PY%" scripts\launch_services.py start --backend-port 8010 --frontend-port 5180 --open-browser
set "EXITCODE=%ERRORLEVEL%"
popd
exit /b %EXITCODE%
