@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM ============================================================
REM EMPLEADOS_IA — Arranque integrado (CURSOR-805B)
REM ============================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%" || (
  echo [ERROR] No se pudo acceder a %ROOT%
  exit /b 1
)

set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "DATA=%ROOT%\data"
set "DB=%DATA%\enterprise_ai_os.db"
set "VENV=%BACKEND%\.venv"
set "PIDFILE=%DATA%\empleados_ia.pids"
set "BACKEND_PORT=8010"
set "FRONTEND_PORT=5180"
set "BACKEND_URL=http://127.0.0.1:%BACKEND_PORT%"

echo.
echo ============================================================
echo  EMPLEADOS_IA — Iniciando servicios
echo  Raiz: %ROOT%
echo ============================================================
echo.

REM --- 1. Verificar estructura del proyecto ---
if not exist "%BACKEND%\app\main.py" (
  echo [ERROR] Backend no encontrado en %BACKEND%
  exit /b 1
)
if not exist "%FRONTEND%\package.json" (
  echo [ERROR] Frontend no encontrado en %FRONTEND%
  exit /b 1
)
if not exist "%DATA%" mkdir "%DATA%"

REM --- 2. Verificar .venv ---
if not exist "%VENV%\Scripts\python.exe" (
  echo [INFO] Creando entorno virtual en %VENV% ...
  py -3 -m venv "%VENV%" 2>nul || python -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] No se pudo crear .venv. Instale Python 3.11+.
    exit /b 1
  )
)

set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"

REM --- 3. Dependencias backend (solo si faltan) ---
"%PY%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Instalando dependencias backend...
  "%PIP%" install -q -r "%BACKEND%\requirements.txt"
  if errorlevel 1 (
    echo [ERROR] Fallo instalacion dependencias backend.
    exit /b 1
  )
)

REM --- 4. Dependencias frontend (solo si faltan) ---
if not exist "%FRONTEND%\node_modules" (
  echo [INFO] Instalando dependencias frontend...
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 (
    echo [ERROR] Fallo npm install.
    popd
    exit /b 1
  )
  popd
)

REM --- 5. Detener instancia previa propia (solo PIDs registrados) ---
if exist "%PIDFILE%" (
  echo [INFO] Deteniendo instancia previa registrada...
  "%PY%" "%BACKEND%\scripts\launch_services.py" stop
)

REM --- 6. Preparar BD: audit -^> backup -^> repair -^> audit -^> alembic ---
echo [INFO] Preparando base de datos (auditoria/reparacion si aplica)...
pushd "%BACKEND%"
"%PY%" scripts\launch_services.py prepare
if errorlevel 1 (
  echo [ERROR] Base de datos incompatible o no reparable. Arranque abortado.
  popd
  exit /b 1
)
popd

REM --- 7. Iniciar backend y esperar /health HTTP 200 ---
echo [INFO] Iniciando backend y esperando /health ...
pushd "%BACKEND%"
"%PY%" scripts\launch_services.py start --backend-port %BACKEND_PORT% --frontend-port %FRONTEND_PORT%
set START_RC=!ERRORLEVEL!
popd
if not !START_RC!==0 (
  echo [ERROR] Arranque fallido (codigo !START_RC!). No se declara exito.
  exit /b !START_RC!
)

REM --- 8. Abrir navegador ---
echo [INFO] Abriendo navegador...
start "" "http://127.0.0.1:%FRONTEND_PORT%/"

echo.
echo ============================================================
echo  EMPLEADOS_IA listo
echo  Frontend: http://127.0.0.1:%FRONTEND_PORT%/
echo  Backend:  %BACKEND_URL%/docs
echo  Credenciales: ver documentacion del proyecto
echo  Para detener: DETENER_EMPLEADOS_IA.bat
echo ============================================================
echo.

endlocal
exit /b 0
