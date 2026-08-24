# CURSOR-805G — Corrección final BAT Windows

**HEAD anterior:** `fb51aa8`

## Causa exacta

CMD no puede procesar de forma segura `echo` con URLs que contienen **puntos** (`127.0.0.1`) ni `:` en ciertas posiciones. Tras el retorno exitoso de `launch_services.py`, las líneas:

- `echo [INFO] Abriendo navegador en !APP_URL!`  → IP con puntos
- `echo  Backend  - http://127.0.0.1:.../docs`   → IP con puntos

producen: **"No se esperaba . en este momento."** y exit 255.

La evidencia del usuario con `(BD + backend + frontend)` corresponde a una versión anterior; la causa de clase es la misma: **sintaxis CMD posterior al launcher**.

## Corrección

1. **BAT mínimo** — sin `EnableDelayedExpansion`, sin `echo` post-start, sin `start`, sin URLs
2. **Python** — `--open-browser` abre navegador vía `webbrowser.open()` y mensaje en stderr

## Certificación Windows

**PENDIENTE CERTIFICACIÓN WINDOWS** — el agente no dispone de CMD real en `D:\EMPLEADOS_IA`.

Verificar manualmente:

```bat
cd /d D:\EMPLEADOS_IA
INICIAR_EMPLEADOS_IA.bat
echo %ERRORLEVEL%
DETENER_EMPLEADOS_IA.bat
echo %ERRORLEVEL%
```

## Regresión Linux

46 PASSED, 0 FAILED, 0 SKIPPED. Build OK.
