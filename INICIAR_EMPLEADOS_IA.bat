@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM ============================================================
REM EMPLEADOS_IA — Arranque integrado (CURSOR-805)
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
set "FRONTEND_URL=http://127.0.0.1:%FRONTEND_PORT%"

echo.
echo ============================================================
echo  EMPLEADOS_IA — Iniciando servicios
echo  Raiz: %ROOT%
echo ============================================================
echo.

REM --- 1. Verificar estructura ---
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

REM --- 5. Verificar / reparar base de datos ---
if not exist "%DB%" (
  echo [INFO] Base de datos no existe. Se creara en el primer arranque.
) else (
  echo [INFO] Verificando esquema SQLite y Alembic...
  pushd "%BACKEND%"
  "%PY%" scripts\repair_legacy_database.py audit
  if errorlevel 1 (
    echo [WARN] Esquema incompleto. Ejecutando reparacion idempotente...
    "%PY%" scripts\repair_legacy_database.py repair
    if errorlevel 1 (
      echo [ERROR] Reparacion de base de datos fallida.
      popd
      exit /b 1
    )
  )
  "%PY%" -m alembic current 2>nul | findstr /C:"5b2eb2437398" >nul
  if errorlevel 1 (
    echo [WARN] Alembic no en head. Ejecutando reparacion...
    "%PY%" scripts\repair_legacy_database.py repair
    if errorlevel 1 (
      echo [ERROR] No se pudo sincronizar Alembic.
      popd
      exit /b 1
    )
  )
  popd
  echo [OK] Base de datos verificada.
)

REM --- 6. Detener instancias previas propias ---
if exist "%PIDFILE%" (
  echo [INFO] Deteniendo instancia previa...
  call "%ROOT%\DETENER_EMPLEADOS_IA.bat" >nul 2>&1
)

REM --- 7. Iniciar backend ---
echo [INFO] Iniciando backend en %BACKEND_URL% ...
start "EMPLEADOS_IA_BACKEND" /MIN cmd /c "cd /d \"%BACKEND%\" && \"%VENV%\Scripts\uvicorn.exe\" app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

REM --- 8. Iniciar frontend ---
echo [INFO] Iniciando frontend en http://127.0.0.1:%FRONTEND_PORT% ...
start "EMPLEADOS_IA_FRONTEND" /MIN cmd /c "cd /d \"%FRONTEND%\" && npm run dev -- --host 127.0.0.1 --port %FRONTEND_PORT%"

REM --- 9. Esperar servicios ---
echo [INFO] Esperando servicios...
set "TRIES=0"
:wait_backend
set /a TRIES+=1
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri '%BACKEND_URL%/health' -TimeoutSec 2).StatusCode } catch { 0 }" | findstr "200" >nul
if not errorlevel 1 goto backend_ok
if %TRIES% GEQ 30 (
  echo [ERROR] Backend no respondio en /health tras 30 intentos.
  exit /b 1
)
timeout /t 1 /nobreak >nul
goto wait_backend
:backend_ok
echo [OK] Backend activo.

set "TRIES=0"
:wait_frontend
set /a TRIES+=1
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%FRONTEND_PORT%/' -TimeoutSec 2).StatusCode } catch { 0 }" | findstr "200" >nul
if not errorlevel 1 goto frontend_ok
if %TRIES% GEQ 30 (
  echo [ERROR] Frontend no respondio tras 30 intentos.
  exit /b 1
)
timeout /t 1 /nobreak >nul
goto wait_frontend
:frontend_ok
echo [OK] Frontend activo.

REM --- 10. Abrir navegador ---
echo [INFO] Abriendo navegador...
start "" "http://127.0.0.1:%FRONTEND_PORT%/"

echo.
echo ============================================================
echo  EMPLEADOS_IA listo
echo  Frontend: http://127.0.0.1:%FRONTEND_PORT%/
echo  Backend:  %BACKEND_URL%/docs
echo  Login:    admin / Admin2026*
echo.
echo  Para detener: DETENER_EMPLEADOS_IA.bat
echo ============================================================
echo.

endlocal
exit /b 0
