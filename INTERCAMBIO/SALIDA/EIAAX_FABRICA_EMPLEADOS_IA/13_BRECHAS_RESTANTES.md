# 13 — Brechas restantes e integración

## P0 (bloqueantes integración GENERAL)

| ID | Brecha | Acción GENERAL |
|----|--------|----------------|
| P0-1 | Colisión migraciones 1410/1420 con Partners, BP2, Gobierno | Reconciliar cadena Alembic |
| P0-2 | Gobierno Operacional (rama A) | Conectar `gobierno-operacional/boundary` |
| P0-3 | Capacidades externas (PIIAX) | Resolver `EmployeeBusinessCapability.code` → conector |

## P1 (mejora operativa)

| ID | Brecha | Notas |
|----|--------|-------|
| P1-1 | Wizard prefill vía `?requerimiento=` | Query param en EmployeeWizardPage |
| P1-2 | Pestaña FinOps dedicada en detalle | Datos ya en estimate-capacity |
| P1-3 | Orígenes OPORTUNIDAD/PROCESO/OPERACIONAL UI | Campos listos, falta flujo UX |
| P1-4 | diagnostic_id → findings unificado | Contrato documentado en 10 |

## P2 (evolución)

| ID | Brecha | Notas |
|----|--------|-------|
| P2-1 | Inteligencia de Resultados (D) | ANTES/PROYECTADO/REAL |
| P2-2 | Optimización automática con aprobación | Ciclo medir→ajustar preparado conceptualmente |
| P2-3 | Asignación a proceso/área formal | Metadata extensible |

## Cerrado en esta misión

- Puente Arquitecto→Fábrica con trazabilidad
- Modelo canónico evolucionado (origen, autonomía, capacidades empresariales)
- Biblioteca interna + clon borrador
- Estimación costo/capacidad (wrap FinOps)
- Validación proveedor falla controlada
- Multitenant verificado
- Frontera Gobierno Operacional sin motor paralelo
- 32 tests + frontend build OK

## Reservado para integración

- Merge a rama central (GENERAL)
- Reconciliación migraciones
- Gobierno Operacional transversal
- PIIAX / capacidades externas
- Inteligencia de Resultados completa
