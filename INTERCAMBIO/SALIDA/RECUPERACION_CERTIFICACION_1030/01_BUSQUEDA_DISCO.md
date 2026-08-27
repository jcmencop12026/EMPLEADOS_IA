# 01 — Búsqueda completa en disco

**Alcance:** `/workspace` (= `D:\EMPLEADOS_IA` en entorno Cloud Agent)
**Método:** `find`, `rg`, `glob`, inspección manual de INTERCAMBIO
**Restricción:** ningún archivo movido, borrado ni modificado (excepto creación de carpeta de recuperación)

## Términos buscados

`OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION`, `OPORTUNIDADES_1030`, `OPORTUNIDADES-PROACTIVAS-1030`, `casos_oraculo`, `OP-A`…`OP-F`, `NS-1`, `NS-2`, `PX-1`…`PX-4`, `MATRIZ_EVALUACION`, `REAUDITORIA`, `CERTIFICACION`, `oraculo`, `adversarial`, `1030`

## Rutas prioritarias

### INTERCAMBIO/ENTRADA

```
.gitkeep
MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip   (16642 bytes, 2026-08-27)
```

**Ausente:** `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip`

### INTERCAMBIO/HISTORICO

```
.gitkeep   (vacío)
```

### INTERCAMBIO/SALIDA — hallazgos 1030 (internos)

| Ruta | Tipo | Notas |
|------|------|-------|
| `oportunidades_1030/CASO_OP_*.json` (8) | Salida interna | Resultados de certificación durante desarrollo PR #24 |
| `oportunidades_1030/E2E_*.json` | Salida interna | E2E reactivo/proactivo |
| `oportunidades_1030/PRIORIZACION_GLOBAL.json` | Salida interna | |
| `oportunidades_1030/SEGUNDA_EJECUCION.json` | Salida interna | |
| `oportunidades_1030/TRAZABILIDAD.json` | Salida interna | |
| `reauditoria_externa_1030/brutos/*_ANTES_ORACULO.json` (12) | Salida interna PR25 | Generados por `run_blind_certification.py` interno |
| `reauditoria_externa_1030/run_blind_certification.py` | Script interno | No es harness del paquete externo |
| `CURSOR_OPORTUNIDADES_PROACTIVAS_1030.md` | Informe desarrollo | |
| `CURSOR_REAUDITORIA_FINAL_PR25_1020_1030.md` | Informe reauditoría | |

### Carpetas tipo BACKUP / RECUPER / CERTIFIC / etc.

Búsqueda `find -type d` con patrones `*BACKUP*`, `*RECUPER*`, `*HISTOR*`, `*CERTIFIC*`, `*AUDITOR*`, `*ENTREGA*`, `*TEMP*`:

| Directorio encontrado | Relación 1030 |
|-----------------------|---------------|
| `INTERCAMBIO/HISTORICO` | Vacío |
| `tests/certification` | Tests CI genéricos, no paquete 1030 |
| `reauditoria_externa_motor_1000` | Paquete 1000 |
| `reauditoria_orquestador_1010` | Paquete 1010 |
| `reauditoria_externa_1030` | **Interno PR25**, no paquete externo |

**No se encontraron:** `_BACKUP*`, `BACKUP*`, `RECUPER*`, `PARA_CHATGPT*`, `ENTREGA*` con contenido 1030.

## Archivos comprimidos en disco

| Archivo | SHA-256 | Contenido 1030 |
|---------|---------|----------------|
| `INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` | ver `05_HASHES_SHA256.csv` | **NO** — solo casos CASO_A…E motor 1000 |
| `*.bundle` | — | **0 archivos** |
| Otros `*.zip` | — | **0 archivos** |

Inspección interna del ZIP 1000 (`unzip -l`): carpetas `MOTOR_ANALITICO_1000_DATASET_CERTIFICACION/CASOS/CASO_*` — sin referencias OP-A, NS-1, PX-1, ni `casos_oraculo.csv`.

## Archivos NO encontrados en disco

- `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip`
- `casos_oraculo.csv`
- `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv`
- `OPORTUNIDADES_1030_REAUDITORIA.md`
- `PX_CONTROLES.json`
- Carpeta tipo `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION/` descomprimida

## Nota sobre documentos externos mencionados por el usuario

`OPORTUNIDADES_1030_REAUDITORIA.md` y `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv` fueron citados como evidencia externa nueva, pero **no están presentes** en el filesystem del entorno Cloud Agent. Podrían existir únicamente en el equipo físico `D:\EMPLEADOS_IA` del usuario fuera de este entorno; no hay forma de verificarlos desde aquí.
