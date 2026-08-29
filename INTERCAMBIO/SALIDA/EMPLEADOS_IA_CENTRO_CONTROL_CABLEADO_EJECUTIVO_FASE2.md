# EMPLEADOS IA — Centro de Control cableado ejecutivo Fase 2

## Identificación

| Campo | Valor |
|-------|-------|
| **Base obligatoria** | `cda96774909576e589ee1fddcbabf08aeec65540` |
| **Rama** | `cursor/centro-control-cableado-ejecutivo-fase2` |
| **HEAD** | `c05bd1c` |
| **Fix CC-DT portado** | `7bdfeee` + `3624a15` (cherry-pick de `096b7e8` + `84ab9f7`) |

## Arquitectura

El Centro de Control existente (`GET /api/centro-control/resumen-ejecutivo`) se extendió sin crear dashboard paralelo:

- **Agregador:** `backend/app/services/control_center_service.py` → `get_executive_summary()`
- **Adaptadores:** `backend/app/services/control_center_adapters.py`
- **UI:** `frontend/src/pages/CentroControlPage.tsx` (pestañas ejecutivas)

### Secciones ejecutivas (UI)

1. **Resumen** — indicadores, atención requerida, explicaciones, cadena ejecutiva
2. **Valor** — VERIFICADO / ESTIMADO / POTENCIAL separado, 1210, 1280
3. **Operación** — empleados, oportunidades, línea base, diagnóstico, señales
4. **IA y costos** — FinOps, TCO, multiproveedor 1270
5. **Implementación** — proyectos 1340, hitos en riesgo
6. **Salud** — plataforma, aprendizaje, optimización, auditoría

## Fuentes reales cableadas

| Módulo | Bloque | Adaptador | Enlace drill-down |
|--------|--------|-----------|-------------------|
| Oportunidades | 1100 | `OportunidadesAdapter` | `/oportunidades` |
| Línea base / impacto | 1200 | `ImpactoAdapter` | `/lineas-base` |
| FinOps extendido | 1110 | `FinOpsExtendidoAdapter` | `/costos-valor` |
| Valoración | 1210 | `ValorRetornoAdapter` | `/costos-valor` |
| Comercial | 1280 | `ComercialResumenAdapter` | `/comercial` |
| Diagnóstico | 1220 | `DiagnosticoAdapter` + explicaciones | `/diagnosticos` |
| Señales | 1120 | `SenalesAdapter` | `/senales` |
| Inteligencia externa | 1240 | `InteligenciaExternaAdapter` | `/inteligencia-externa` |
| Aprendizaje | 1260 | `AprendizajeAdapter` | `/aprendizaje` |
| Optimización | 1290 | `OptimizacionAdapter` | `/optimizacion` |
| Multiproveedor | 1270 | `MultiproveedorAdapter` | `/administracion/proveedores-ia` |
| TCO | 1320 | `TcoAdapter` (reutiliza `calcular_tco`) | `/tco` |
| Implementación | 1340 | `ImplementacionAdapter` | `/implementacion` |

## Semántica y valor

- **VERIFICADO** → HECHO
- **ESTIMADO** → INFERENCIA
- **POTENCIAL** → INFERENCIA (separado visualmente; no suma a valor realizado/ROI/payback)
- **Recomendaciones optimización** → RECOMENDACIÓN

Contrato expuesto en `valor_consolidado` y `semantica` del resumen ejecutivo.

## RBAC y multiempresa

- Cada adaptador valida permiso de dominio (`tco.view`, `comercial.view`, etc.)
- **Margen:** solo visible con `comercial.approve` (comercial/TCO)
- **Multiempresa:** filtro `organization_id` en todas las consultas; test obligatorio incluido
- Sin bypass superadmin nuevo

## Integraciones futuras (sin datos falsos)

`integraciones_futuras` documenta MB-07, MB-11, MB-12, Auditor, Fábrica, Conocimiento 930, Mi Trabajo, Integraciones T5 como **Pendiente**.

## Tests

| Suite | Resultado |
|-------|-----------|
| `test_centro_control_cableado_ejecutivo_fase2.py` | 9/9 PASS |
| `test_control_center_datetime_cc_dt.py` | PASS (aislado; cluster 5× PASS aislado) |
| `test_bloque_1250c_centro_control_integrado.py` | PASS |
| Frontend `npm run build` | PASS |

**Alembic:** SIN CAMBIOS

**PostgreSQL:** PENDIENTE POR ENTORNO

## Receta para General

1. Cherry-pick o merge de rama `cursor/centro-control-cableado-ejecutivo-fase2` sobre central Tramo 4
2. Verificar permisos RBAC en roles operativos
3. Tras portar MB-07/11/12: registrar adaptadores en `adapter_instances` sin romper contrato
4. No modificar `cursor/fase2-central-integracion`, `main`, `V1`

## Commits funcionales

- `17b9305` — adaptadores y servicio agregador
- `bec3a34` — UI pestañas ejecutivas
- `95f98f5` — tests focales Fase 2
- `02b5804` — fix lat_map `_llm_section`
