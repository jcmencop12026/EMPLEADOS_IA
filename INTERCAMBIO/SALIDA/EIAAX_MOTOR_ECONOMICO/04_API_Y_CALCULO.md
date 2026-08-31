# 04 — API y cálculo

## Prefijo API

`/api/motor-economico`

| Método | Ruta | Permiso | Descripción |
|---|---|---|---|
| GET | `/vista-entidad` | `finops.view` | Resumen entidad sin economía privada |
| GET | `/indicadores` | `finops.view` | ANTES / PROYECTADO / REAL |
| POST | `/costos` | `finops.manage` | Registrar costo ESTIMADO o REAL |
| POST | `/valores` | `finops.manage` | Registrar valor con naturaleza |
| GET | `/economia-privada` | `finops.economy.private` | Leer economía operador |
| PUT | `/economia-privada` | `finops.economy.private` | Guardar economía operador |
| POST | `/precio-recomendado` | `finops.economy.recommend` | Motor precio (BORRADOR) |
| POST | `/sincronizar-finops` | `finops.manage` | Backfill desde `finops_records` |

## Costos soportados

Fuentes: consumo IA, tokens, proveedor/modelo, infraestructura, servicios externos, integraciones, implementación, horas/recursos, soporte, operación, licencias, otros.

Clases: DIRECTO, TRANSVERSAL_ATRIBUIBLE, PLATAFORMA.

## Valor

Tipos: ahorro, pérdida evitada, ingreso recuperado, productividad liberada, nuevo ingreso, oportunidad capturada, riesgo mitigado.

**POTENCIAL** se almacena y reporta por separado; `valor_realizado` = VERIFICADO + ESTIMADO únicamente.

## Precio recomendado

Factores: valor atribuible, complejidad, riesgo, urgencia, reutilización, personalización, soporte, consumo, infraestructura.

Salida: `status=BORRADOR`, `auto_published=false`.

## Planificación IA

Indicadores reutilizan MB-07: presupuesto, consumo incluido, consumo real, desviación, alertas. **No** usa solo conteo de empleados como driver — usa `simulate()` con empleados activos + transversal + plataforma.
