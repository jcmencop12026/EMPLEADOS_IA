# 12 — Brechas restantes (P0/P1/P2)

## P0 — Entregado

- Dossier persistente por organización
- Diagnóstico adaptativo sobre BP1
- Suficiencia sin bloqueo
- Mapa progresivo, causas, alternativas, iniciativas, escenarios
- Requerimientos Empleado IA y capacidad externa (contrato)
- API `/api/transformacion/*`
- UI recorrido progresivo español
- Multitenant + RBAC probados
- Migración 1420

## P1 — Integración GENERAL

- Wire `diagnostic_id` → import findings 1220
- Adapter Centro de Control para expediente/dossier
- Knowledge retrieval en evidencias
- Validación `CAUSA_VALIDADA` workflow
- Dimensionamiento personal con métricas reales
- Selector usuarios / notificaciones

## P2 — Fuera de alcance

- PIIAX / conectores directos
- Fábrica Empleados IA completa
- BPMN / gestor proyectos
- Motor económico / Centro de Negocios
- Gobierno Operacional (rama paralela)

## Colisión migración 1410

`1410a1b2c3d4e` Partners **colisiona** con Gobierno Operacional en otra rama. GENERAL reconciliará — **no corregido aquí**.

## APIs

| Método | Ruta |
|--------|------|
| GET | `/api/transformacion/dossier` |
| POST | `/api/transformacion/necesidad` |
| GET | `/api/transformacion/expedientes/{id}/suficiencia` |
| POST | `/api/transformacion/expedientes/{id}/diagnosticar` |
| GET | `/api/transformacion/recorrido` |
| POST | `/api/transformacion/expedientes/{id}/prefill` |

## Permisos

`transformacion.view`, `transformacion.manage`, `transformacion.execute`

## Modelos nuevos

`DossierEmpresarial`, `DossierConocimientoItem`, `DossierMapaNodo`, `DossierCausa`, `TransformacionAlternativa`, `TransformacionIniciativa`, `TransformacionEscenario`, `EmpleadoIARequerimiento`, `CapacidadExternaNecesidad`
