@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%" || exit /b 1

set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "DATA=%ROOT%\data"
set "VENV=%BACKEND%\.venv"
set "PIDFILE=%DATA%\empleados_ia.pids"
set "BACKEND_PORT=8010"
set "FRONTEND_PORT=5180"
set "START_RC=1"

if not exist "%BACKEND%\app\main.py" (
  echo [ERROR] Backend no encontrado
  exit /b 1
)
if not exist "%FRONTEND%\package.json" (
  echo [ERROR] Frontend no encontrado
  exit /b 1
)
if not exist "%DATA%" mkdir "%DATA%"

if not exist "%VENV%\Scripts\python.exe" (
  echo [INFO] Creando entorno virtual...
  py -3 -m venv "%VENV%" 2>nul || python -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual
    exit /b 1
  )
)

set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"

"%PY%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Instalando dependencias backend...
  "%PIP%" install -q -r "%BACKEND%\requirements.txt"
  if errorlevel 1 (
    echo [ERROR] Fallo instalacion dependencias backend
    exit /b 1
  )
)

if not exist "%FRONTEND%\node_modules" (
  echo [INFO] Instalando dependencias frontend...
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 (
    echo [ERROR] Fallo npm install
    popd
    exit /b 1
  )
  popd
)

if exist "%PIDFILE%" (
  echo [INFO] Deteniendo instancia previa registrada...
  "%PY%" "%BACKEND%\scripts\launch_services.py" stop
)

echo [INFO] Iniciando servicios...
pushd "%BACKEND%"
"%PY%" scripts\launch_services.py start --backend-port %BACKEND_PORT% --frontend-port %FRONTEND_PORT%
set "START_RC=!ERRORLEVEL!"
popd

if not "!START_RC!"=="0" (
  echo [ERROR] EMPLEADOS_IA no pudo iniciarse. Codigo !START_RC!
  exit /b !START_RC!
)

echo [INFO] EMPLEADOS_IA iniciado correctamente
set "APP_URL=http://127.0.0.1:%FRONTEND_PORT%/"
echo [INFO] Abriendo navegador en !APP_URL!
start "" "!APP_URL!"

echo.
echo ============================================================
echo  EMPLEADOS_IA listo
echo  Frontend - !APP_URL!
echo  Backend  - http://127.0.0.1:%BACKEND_PORT%/docs
echo  Para detener - DETENER_EMPLEADOS_IA.bat
echo ============================================================
echo.

endlocal & exit /b 0
