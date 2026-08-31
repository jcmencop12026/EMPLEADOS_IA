# 01 — Alcance implementado — Bloque Producto 2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Base certificada BP1:** `7e9abba11f4c4f216142c6c70d662229ffc585bb`  
**Rama:** `cursor/producto-bloque-2-piiax-prep-85e4`

## Objetivo cumplido

Preparar EIAAX para interactuar con PIIAX mediante **capacidades** (no conectores), con trazabilidad empresarial, aprobación humana, impacto evolucionado y UX de consola mejorada — **sin construir PIIAX**.

## Componentes entregados

| # | Requisito | Estado |
|---|-----------|--------|
| 1 | Modelo de capacidades externas (catálogo) | ✅ |
| 2 | Acciones desde expediente/hallazgo → solicitud → estado → resultado | ✅ |
| 3 | Trazabilidad `correlation_id` punta a punta (empresarial) | ✅ |
| 4 | Aprobación humana LECTURA/ANÁLISIS/PROPUESTA/EJECUCIÓN | ✅ |
| 5 | Estado controlado si PIIAX no conectado | ✅ |
| 6 | Panel «Preguntar a EIAAX» con intención A–F | ✅ |
| 7 | Impacto ANTES/PROYECTADO/REAL con gráficos dinámicos | ✅ |
| 8 | Vista Entidad legible (no JSON crudo) | ✅ |
| 9 | Etiquetas español en códigos técnicos | ✅ |
| 10 | RBAC + multitenant en acciones e indicadores | ✅ |
| 11 | Pruebas propias BP2 + compatibilidad BP1 | ✅ |

## Fuera de alcance (respetado)

PIIAX real, conectores, endpoints hardcodeados, Partners, propuesta comercial, Centro Oportunidades, FinOps, CC, Fábrica, Bloque 3.

## Cómo ver el resultado

1. Backend + frontend en ejecución.
2. **Análisis y control → Evaluaciones EIAAX** → abrir expediente.
3. Barra de estado PIIAX (disponible / no conectado).
4. Pestaña **Análisis** → en un hallazgo, solicitar capacidad externa.
5. Aprobar si tipo PROPUESTA/EJECUCIÓN → estado `PIIAX_NO_DISPONIBLE` o `SOLICITADA`.
6. Pestaña **Impacto** → indicadores y gráfico ANTES/PROYECTADO/REAL.
7. **Vista Entidad** → presentación estructurada.
8. Panel **Preguntar a EIAAX** → intención clasificada A–F.
