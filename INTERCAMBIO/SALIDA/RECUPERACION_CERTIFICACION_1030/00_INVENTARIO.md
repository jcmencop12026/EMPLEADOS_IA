# 00 — Inventario general recuperación forense certificación 1030

**Fecha:** 2026-08-27
**Git root:** `/workspace` (`D:\EMPLEADOS_IA`)
**Rama activa (sin cambios):** `cursor/preintegracion-1020-1030` @ `2e86ae3`
**Alcance:** solo recuperación y diagnóstico — sin certificar, sin reconstruir, sin modificar código

## Resumen ejecutivo

| Elemento buscado | Encontrado | Ubicación |
|------------------|------------|-----------|
| `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip` | **NO** | — |
| `casos_oraculo.csv` | **NO** | Solo mencionado en informes markdown |
| `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv` | **NO** | Solo mencionado en informes markdown |
| `OPORTUNIDADES_1030_REAUDITORIA.md` | **NO** | No en disco ni en Git |
| `PX_CONTROLES.json` | **NO** | Solo mencionado en informes markdown |
| Casos OP-A…OP-F (paquete externo) | **NO** | Existen salidas internas derivadas |
| Casos NS-1/NS-2 (paquete externo) | **NO** | Existen salidas internas derivadas |
| Casos PX-1…PX-4 (paquete externo) | **NO** | Existen salidas internas derivadas |
| Harness/script certificación externo 1030 | **NO** | Existe harness interno distinto |
| Evidencias internas desarrollo 1030 | **SÍ** | `INTERCAMBIO/SALIDA/oportunidades_1030/` |
| Certificación ciega interna PR25 | **SÍ** | `INTERCAMBIO/SALIDA/reauditoria_externa_1030/` |
| Referencia estructural 1010 | **SÍ** | `paquete_embedded/` (sustituto, no ZIP original) |
| Referencia confirmada 1000 | **SÍ** | `INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` |

## Carpetas INTERCAMBIO inspeccionadas

| Ruta | Contenido relevante 1030 |
|------|--------------------------|
| `INTERCAMBIO/ENTRADA/` | Solo ZIP motor 1000; **sin ZIP 1030** |
| `INTERCAMBIO/HISTORICO/` | Vacío (solo `.gitkeep`) |
| `INTERCAMBIO/SALIDA/` | Evidencias internas y reauditoría interna 1030 |

## Artefactos copiados a recuperación

Ver `RECUPERADOS/` y `05_HASHES_SHA256.csv` (56 archivos hasheados).

## Conclusión preliminar

**Escenario D** — No existe evidencia de que el paquete externo original 1030 haya estado en este repositorio/entorno.

Existen artefactos **internos derivados** (no equivalentes al paquete adversarial externo).
