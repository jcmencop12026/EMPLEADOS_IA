@echo off
title EMPLEADOS_IA - Ollama (modelos en D:\Ollama\models)
setlocal
if not exist "D:\Ollama\models" mkdir "D:\Ollama\models"
where ollama >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama no esta instalado. https://ollama.com
  pause
  exit /b 1
)
echo OLLAMA_MODELS=%OLLAMA_MODELS%
echo Iniciando ollama serve...
start "Ollama serve" /MIN ollama serve
timeout /t 5 /nobreak >nul
echo.
echo Modelos instalados:
ollama list
echo.
echo API: http://127.0.0.1:11434
echo Modelo sugerido EMPLEADOS_IA: llama3.2:3b
pause
