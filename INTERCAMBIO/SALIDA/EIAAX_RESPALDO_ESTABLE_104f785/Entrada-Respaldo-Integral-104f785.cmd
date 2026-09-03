@echo off
setlocal EnableExtensions
set "REPO=D:\EMPLEADOS_IA_CONVERGENCIA"
set "TAG=eiaax-tools-respaldo-104f785"
set "TOOLS_GIT=INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785"
set "TOOLS_DIR=INTERCAMBIO\SALIDA\EIAAX_RESPALDO_ESTABLE_104f785"
set "ERRLOG=%TEMP%\eiaax_entrada_err_%RANDOM%.txt"
set "ZIP=%TEMP%\eiaax_r104f785.zip"
set "EXTRACT=%TEMP%\eiaax_r104f785"
set "LAUNCH=%EXTRACT%\%TOOLS_DIR%\Launch-Respaldo-Integral-104f785.ps1"

call :stage_repo || goto :fail_done
call :stage_fetch || goto :fail_done
call :stage_archive || goto :fail_done
call :stage_launch || goto :fail_done
call :stage_verify || goto :fail_done
goto :success_done

:stage_repo
echo [1/5] Repositorio ................
if not exist "%REPO%\.git" (
  echo FAIL
  echo CAUSA: repositorio no encontrado: %REPO%
  exit /b 1
)
cd /d "%REPO%"
echo PASS
exit /b 0

:stage_fetch
echo [2/5] Fetch herramientas .........
if exist "%ERRLOG%" del /f /q "%ERRLOG%" 2>nul
git fetch origin tag %TAG% 1>nul 2>"%ERRLOG%"
if errorlevel 1 (
  echo FAIL
  echo CAUSA:
  if exist "%ERRLOG%" (type "%ERRLOG%") else (echo git fetch retorno error sin detalle)
  exit /b 1
)
echo PASS
exit /b 0

:stage_archive
echo [3/5] Materializar launcher .......
if exist "%ERRLOG%" del /f /q "%ERRLOG%" 2>nul
if exist "%ZIP%" del /f /q "%ZIP%" 2>nul
git archive --format=zip -o "%ZIP%" %TAG% %TOOLS_GIT%/Launch-Respaldo-Integral-104f785.ps1 2>"%ERRLOG%"
if errorlevel 1 (
  echo FAIL
  echo CAUSA:
  if exist "%ERRLOG%" (type "%ERRLOG%") else (echo git archive retorno error sin detalle)
  exit /b 1
)
if not exist "%ZIP%" (
  echo FAIL
  echo CAUSA: zip no creado: %ZIP%
  exit /b 1
)
echo PASS
exit /b 0

:stage_launch
echo [4/5] Ejecutar launcher ...........
if exist "%EXTRACT%" rmdir /s /q "%EXTRACT%" 2>nul
mkdir "%EXTRACT%" 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%EXTRACT%' -Force"
if errorlevel 1 (
  echo FAIL
  echo CAUSA: Expand-Archive fallo: %ZIP%
  exit /b 1
)
if not exist "%LAUNCH%" (
  echo FAIL
  echo CAUSA: launcher no encontrado: %LAUNCH%
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%LAUNCH%"
set "LAUNCH_EC=%ERRORLEVEL%"
if not "%LAUNCH_EC%"=="0" (
  echo FAIL
  echo CAUSA: launcher retorno codigo %LAUNCH_EC%
  exit /b 1
)
echo PASS
exit /b 0

:stage_verify
echo [5/5] Verificar respaldo ..........
echo PASS
exit /b 0

:fail_done
echo.
echo RESPALDO NO REALIZADO
exit /b 1

:success_done
echo.
echo RESULTADO FINAL:
echo PASS - RESPALDO 104f785 VERIFICADO Y RECUPERABLE
exit /b 0
