# 02 — Búsqueda en Git

**Restricciones cumplidas:** sin cambiar ramas destructivamente, sin modificar main, sin restaurar archivos sobre rama actual.

## Estado del repositorio

| Campo | Valor |
|-------|-------|
| HEAD | `2e86ae3` |
| Rama actual | `cursor/preintegracion-1020-1030` |
| `origin/main` | `f9e0406` |
| Tags | `v0.1.0-mvp-certified` |
| Stashes | 13 (`stash@{0}`…`stash@{12}`) |

## Historial INTERCAMBIO/ENTRADA

Solo **un** ZIP alguna vez versionado en Git:

```
f0b9929 chore: paquete certificacion motor 1000
  → INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip
5622a6c CURSOR-803: certificación MVP
```

**Nunca** aparece en historial Git:
- `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip`
- `casos_oraculo.csv`
- `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv`
- `OPORTUNIDADES_1030_REAUDITORIA.md`
- `PX_CONTROLES.json`

## Pickaxe (`git log -S`)

| Cadena buscada | Commits | Observación |
|----------------|---------|-------------|
| `casos_oraculo.csv` | `4ac956f` | Solo en markdown informe PR25 |
| `PX_CONTROLES` | `4ac956f` | Solo en markdown informe PR25 |
| `MATRIZ_EVALUACION_1030` | `4ac956f` | Solo en markdown informe PR25 |
| `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION` | `4ac956f`, `2d79119`, `7ab26c6`, `9a11753` | Solo referencias textuales en informes |
| `OPORTUNIDADES_1030_REAUDITORIA` | *(ninguno)* | Nunca en historial Git |

## `git rev-list --all --objects`

Objetos Git con nombres relacionados a 1030 certificación:

- `backend/alembic/versions/1030a1b2c3d4e_oportunidades_proactivas_1030.py`
- `tests/test_oportunidades_proactivas_1030.py`
- `INTERCAMBIO/SALIDA/CURSOR_OPORTUNIDADES_PROACTIVAS_1030.md`
- Brutos `reauditoria_externa_1030/` (commits `4ac956f` en adelante)

**Sin blob** para `casos_oraculo.csv` ni ZIP 1030.

## Ramas inspeccionadas (solo lectura)

| Rama | Archivos certificación 1030 externa |
|------|-------------------------------------|
| `cursor/oportunidades-proactivas-1030` (PR #24) | **NO** — solo código + informe interno |
| `cursor/preintegracion-1020-1030` (PR #25) | **NO** — + reauditoría interna |
| `cursor/e2e-integral-1020-12b6` | **NO** |
| `origin/main` | **NO** |

## Stashes

13 stashes revisados. Solo `stash@{0}` (motor-1000 report wip) contiene `REAUDITORIA_EXTERNA_MOTOR_ANALITICO_1000.md`. **Ningún stash** contiene artefactos 1030 externos.

## Reflog (extracto relevante)

```
2e86ae3 docs(pr25): CI 4/4 confirmado
4ac956f docs(pr25): reauditoría final 1020+1030
90beef9 feat(1030): inteligencia proactiva...
f9e0406 rebase onto origin/main (PR #23 mergeado)
922c8e1 feat(1030) en rama oportunidades-proactivas-1030
```

No hay evidencia en reflog de copia o commit del ZIP 1030.

## Comparación con paquetes anteriores

| Paquete | En ENTRADA | En Git | Sustituto en SALIDA |
|---------|------------|--------|---------------------|
| Motor 1000 | **SÍ** (ZIP) | `f0b9929` | `reauditoria_externa_motor_1000/` |
| Orquestador 1010 | **NO** | **NO** | `paquete_embedded/` (especificación embebida) |
| Oportunidades 1030 | **NO** | **NO** | **NO existe `paquete_embedded` equivalente** |

## Extracción segura

No fue necesario `git show` para recuperar componentes externos 1030 porque **nunca existieron en el historial Git**.
