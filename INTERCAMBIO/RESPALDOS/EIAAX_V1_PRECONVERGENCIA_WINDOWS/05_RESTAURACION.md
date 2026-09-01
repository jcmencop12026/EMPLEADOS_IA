# 05 — Restauración

## Objetivo

Volver al punto operativo Windows **anterior a convergencia A+B+C+D**, exactamente en `d034566`.

## Ubicación del respaldo

### Repositorio (agente / git)

```
INTERCAMBIO/RESPALDOS/EIAAX_V1_PRECONVERGENCIA_WINDOWS/
```

### Windows (sincronizar desde repo)

```
D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_PRECONVERGENCIA_WINDOWS\
```

## Restauración Git (código)

### Opción A — Desde bundle (offline)

```bash
git clone INTERCAMBIO/RESPALDOS/EIAAX_V1_PRECONVERGENCIA_WINDOWS/eiaax-v1-preconvergencia-windows-d034566-20260901T182500Z.bundle D:\EMPLEADOS_IA_INTEGRADO_RESTAURADO
cd D:\EMPLEADOS_IA_INTEGRADO_RESTAURADO
git checkout cursor/windows-demo-arranque-85e4
# o: git checkout eiaax-v1-preconvergencia-windows-operativo
```

### Opción B — Desde remoto (online)

```bash
git fetch origin cursor/windows-demo-arranque-85e4
git checkout d034566
# o: git checkout eiaax-v1-preconvergencia-windows-operativo
```

## Restauración BD demo

1. **No** resetear ni borrar `D:\EMPLEADOS_IA_INTEGRADO\data\eiaax_integrado_demo.db` si sigue siendo el punto operativo.
2. Para restaurar desde copia de seguridad:
   - Copiar `eiaax_integrado_demo-*.db` del respaldo a `data\eiaax_integrado_demo.db` en worktree destino.
   - Incluir sidecars WAL/journal si existen.
3. Verificar checksum con `SHA256_BD_DEMO.txt` (generado por `COPIAR_BD_DEMO_DESDE_WINDOWS.ps1`).

## Reproducir entorno (sin copiar venv/node_modules)

En worktree restaurado (`D:\EMPLEADOS_IA_INTEGRADO` o clon nuevo):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\preparar_demo_eiaax.ps1
powershell -ExecutionPolicy Bypass -File scripts\windows\iniciar_demo_eiaax.ps1
```

Requisitos previos en PATH: Python 3.14, Node 24, npm 11.

## Sincronización repo → Windows D:

Copiar carpeta completa del respaldo:

```
INTERCAMBIO/RESPALDOS/EIAAX_V1_PRECONVERGENCIA_WINDOWS/
  → D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_PRECONVERGENCIA_WINDOWS\
```

Luego ejecutar `COPIAR_BD_DEMO_DESDE_WINDOWS.ps1` para registrar checksum BD.

## Qué NO hacer al restaurar

- No integrar A (`f0d02bc`), B (`2bb3caa`), C (`25c79d5`), D (`40b7c9b`)
- No sobrescribir `INTERCAMBIO/RESPALDOS/EIAAX_LOTE_3/`
- No modificar `D:\EMPLEADOS_IA` (árbol histórico)
- No recrear seed si la BD demo copiada es válida
