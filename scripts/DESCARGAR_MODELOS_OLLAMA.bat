@echo off
title EMPLEADOS_IA - Descargar modelo Ollama en D:
setlocal
if not exist "D:\Ollama\models" mkdir "D:\Ollama\models"
where ollama >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Instale Ollama desde https://ollama.com
  pause
  exit /b 1
)
echo OLLAMA_MODELS=%OLLAMA_MODELS%
start "Ollama serve" /MIN ollama serve
timeout /t 5 /nobreak >nul
echo Descargando llama3.2:3b (si ya existe, Ollama lo omitira)...
ollama pull llama3.2:3b
ollama list
pause
