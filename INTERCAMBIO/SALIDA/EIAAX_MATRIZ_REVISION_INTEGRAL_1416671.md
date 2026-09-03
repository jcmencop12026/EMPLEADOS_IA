# EIAAX — Matriz revisión integral (candidato post-1416671)

**Fecha:** 2026-09-03  
**Rama:** `cursor/revision-integral-completa-85e4`  
**Base:** `14166710932fa87115e700ae0b1e2aa7e110b744`  
**Alembic:** `1831a1b2c3d4e`  
**Estado:** NO autorizado para prueba humana — entrega a ChatGPT para revisión previa

---

## Resumen ejecutivo

| Métrica | Resultado |
|---|---|
| E2E Horizonte (13 pasos) | **13/13 PASS** — `data/evidence/horizonte-e2e/` |
| E2E empresarial (24 pasos) | **24/24 PASS** — `data/evidence/empresarial-e2e/report.json` |
| QA visual estricto | **11/11 PASS** — `data/evidence/cert-visual/` |
| Windows startup | **Preservado** — sin cambios en `scripts/windows/**` |
| P0 bloqueantes | **0** (pantalla blanca Horizonte, hooks, rutas rotas críticas) |
| P1 demo comercial | **2** (ver sección P1) |
| P2 mejoras | **4** (ver sección P2) |

---

## Correcciones realizadas en esta revisión (conserva 1416671)

| # | Área | Causa raíz | Corrección | Evidencia |
|---|---|---|---|---|
| 1 | KPI CC | IDs españoles en frontend vs inglés en backend | `CentroControlCockpit` usa `employees_active`, `executions_running`, etc. | E2E CC + screenshot `cert-visual/2-cc-ciclo` |
| 2 | Empleados activos null | `employees = None` hardcoded | Conteo real `AIEmployee` activos en `control_center_service` | API: `employees_active.valor=9` en demo |
| 3 | Indicadores CC empresa | Campos `valor_antes` vs API `antes` | Fallback `antes/proyectado/real` en `CentroControlEmpresaPanel` | Tablero Horizonte CC screenshot `empresarial-e2e/03-horizonte-contexto.png` |
| 4 | Tabs CC vacíos | Backend `secciones_operacionales` incompatible | Frontend fija `SECCIONES_DEFAULT` | Tabs Valor/Operación/IA renderizan contenido |
| 5 | Informes rotos | Rutas `/informes-impacto` inexistentes | Enlaces a `/resultados/informes/{id}` y hub | E2E paso 12 Informes PASS |
| 6 | Gráficos ocultos | `compact=true` ocultaba charts | Strip compacto `ValorComparacionChart` + tablero `ImpactoGrafico` | Screenshots tab Resultados/Valor |
| 7 | Ciclo no accionable | Chips estáticos | `cicloEtapaRuta()` — 15 etapas navegables | E2E CC ciclo PASS |
| 8 | Operaciones vacías | Sin filtro expediente | API `expediente` + frontend `OperationsHubPage` | 4 WorkPlans demo visibles con `?expediente=` |
| 9 | Gráficos impacto | `grafico: null` en resultados | `_build_grafico_puntos` en `get_impacto_resumen` | Barras Antes/Proy/Real en cabina |
| 10 | Instructivo | Ruta `/instructivo` ausente | Alias `/instructivo` → `GuiaRapidaPage` | E2E paso 23 PASS |
| 11 | Publicar | Texto poco visible | Panel espacio externo renombrado con copy publicación | E2E paso 15 PASS |

---

## Matriz requisitos → evidencia

Leyenda: ✅ PASS con evidencia · ⚠️ PARCIAL · ❌ PENDIENTE

### 1. Centro de Control — consola maestra

| Requisito | Existe | Funciona | Visible | Demo | Navegable | Probado | Estado |
|---|---|---|---|---|---|---|---|
| Modo todas empresas | ✅ | ✅ | ✅ | ✅ | ✅ | E2E 02 | ✅ |
| Modo empresa seleccionada | ✅ | ✅ | ✅ | Horizonte | ✅ | E2E 03 | ✅ |
| KPIs primer viewport | ✅ | ✅ | ✅ | 9 empleados, 1 ejecución | ✅ | Visual 2 | ✅ |
| Atención requerida | ✅ | ✅ | ✅ | demo | ✅ | E2E | ✅ |
| Ciclo 15 etapas | ✅ | ✅ | ✅ | ✅ | ✅ enlaces | E2E 03 | ✅ |
| Valor consolidado gráfico | ✅ | ✅ | ✅ | parcial | ✅ | Visual | ✅ |
| Tabs Resumen/Valor/Operación/IA/Impl/Salud | ✅ | ✅ | ✅ | ✅ | ✅ | Manual+E2E | ✅ |

### 2. Empresas / prospectos

| Requisito | Estado | Evidencia |
|---|---|---|
| Selector contexto CC | ✅ | `CentroControlPage` — sin contradicción encabezado vs selección |
| Flujo todas → empresa → cabina → regreso | ✅ | E2E 24 regreso CC |
| Horizonte `[DEMO] Clínica Demo Horizonte` | ✅ | seed `demo_comercial_service` |

### 3. Información y documentos

| Requisito | Estado | Evidencia |
|---|---|---|
| Expediente Horizonte | ✅ | E2E 04-05 |
| Información / evidencias | ✅ | `InformacionAdjuntosPanel` — E2E Documentos |
| PDF/Excel/CSV | ⚠️ | UI carga contextual; validación binaria no en E2E automatizado |
| Metadatos y persistencia | ⚠️ | Backend adjuntos; requiere prueba upload manual |

### 4. Evaluación adaptativa

| Requisito | Estado | Evidencia |
|---|---|---|
| PRELIMINAR/DIAGNÓSTICA/PROFUNDA | ✅ | Cabina Empresa + diagnóstico |
| Suficiencia / qué falta | ✅ | `sync_informacion_adaptativa` + UI porcentaje |
| No repreguntar válido | ⚠️ | Lógica backend; no E2E dedicado |

### 5. Cadena analítica

| Requisito | Estado | Evidencia |
|---|---|---|
| EVIDENCIA→ACCIÓN | ✅ | `CadenaAnaliticaPanel` — E2E 08 |
| Importación 1220 | ⚠️ | Seed diagnóstico en operaciones demo |
| Trazabilidad oportunidad | ✅ | Hallazgos → oportunidades en seed |

### 6. Oportunidades

| Requisito | Estado | Evidencia |
|---|---|---|
| Motor desde CC y profundidad | ✅ | E2E 09 |
| Campos negocio (evidencia, valor, confianza…) | ⚠️ | 3 oportunidades demo; no todas las 18 categorías sembradas |
| Sin datos inventados | ✅ | Etiqueta `[DEMO]` |

### 7. Valor / inteligencia económica (PR #162)

| Requisito | Estado | Evidencia |
|---|---|---|
| Verificado / Estimado / Potencial | ✅ | `CabinaValorPanel` + tab Valor CC |
| Separación costo/precio/valor/margen | ✅ | Copy + permisos margen |
| Precio sugerido no visible cliente | ✅ | `potential-excluded` CSS |

### 8. Indicadores y gráficos (PRIORITARIO)

| Requisito | Estado | Evidencia |
|---|---|---|
| Tablero empresarial Horizonte | ✅ | `cc-tablero-empresa` + `ImpactoGrafico` |
| Antes / Proyectado / Real | ✅ | 3 indicadores demo con medición real |
| Proyectado ≠ Real | ✅ | `tag-proyectado` + copy |
| Hub resultados | ✅ | E2E 22 `/resultados-inteligencia` |

### 9. Informes mejorados (PRIORITARIO)

| Requisito | Estado | Evidencia |
|---|---|---|
| Cabina informes expediente | ✅ | E2E 12 |
| Informe impacto generado | ✅ | seed `generate_informe_impacto` |
| Rutas correctas | ✅ | `/resultados/informes/{id}` |
| Narrativa ejecutiva completa | ⚠️ | 1 informe demo; plantillas en comunicaciones |

### 10. Vista empresa

| Requisito | Estado | Evidencia |
|---|---|---|
| Previsualización cliente | ✅ | E2E 14 |
| Publicar / visibilidad | ✅ | E2E 15 — `EspacioExternoAdminPanel` |
| DEMO→OPERACIÓN evolución | ⚠️ | Flujo demostrable; sin contrato nuevo |

### 11. Presentar / Ver como empresa / Publicar

| Acción | Estado | Evidencia |
|---|---|---|
| Presentar en reunión | ✅ | E2E 13 `/demo/presentacion/` |
| Ver como empresa | ✅ | E2E 14 |
| Publicar consulta posterior | ✅ | E2E 15 |
| Sin scoring/costos internos | ✅ | Presentación filtrada |

### 12. Modelo comercial progresivo

| Requisito | Estado | Evidencia |
|---|---|---|
| Potencial completo visible | ⚠️ | Demo page + CC valor potencial |
| Etapas implementación | ⚠️ | Tab Implementación CC |

### 13. Centro de Operaciones

| Requisito | Estado | Evidencia |
|---|---|---|
| Datos demo densos | ✅ | 4 WorkPlans sembrados |
| Filtro por expediente | ✅ | Corrección API + UI |
| Sin 6 ceros + tabla vacía (Horizonte) | ✅ | E2E 17 con contexto |

### 14. Empleados IA 2.0 (PR #163)

| Requisito | Estado | Evidencia |
|---|---|---|
| Directorio / ficha | ✅ | E2E 18 |
| UI español | ✅ | Visual 23 |
| Adapter señales CC | POST-V1 | No P1 V1 |

### 15-16. Automatizaciones / ejecuciones / aprobaciones

| Requisito | Estado | Evidencia |
|---|---|---|
| Navegación | ✅ | E2E 19-21 |
| Sin botones muertos | ✅ | Enlaces funcionales |

### 17. Tablas

| Requisito | Estado | Evidencia |
|---|---|---|
| Estándar EiaaxTable | ⚠️ | KnowledgePage + varias; no auditadas todas |
| Control columnas compacto | ⚠️ | Parcial según módulo |

### 18. Menú y navegación

| Requisito | Estado | Evidencia |
|---|---|---|
| Sin truncado "..." | ✅ | 1416671 preservado |
| Scroll / persistencia | ✅ | Visual audit |
| Sin duplicados visibles | ⚠️ | Inventario no exhaustivo automatizado |

### 19. Logos / identidad

| Requisito | Estado | Evidencia |
|---|---|---|
| Login / header | ✅ | Visual audit 1 PASS |
| Upload logos grandes | ⚠️ | P1 — límite frontend 180KB vs backend 200KB |

### 20. Asistente EIAAX

| Requisito | Estado | Evidencia |
|---|---|---|
| Panel contextual | ✅ | `EiaaxAskPanel` en cabina |
| Preguntas demo | ⚠️ | Modo demo; no E2E LLM |

### 21. Instructivo (10 partes)

| Requisito | Estado | Evidencia |
|---|---|---|
| 10 partes navegables | ✅ | `INSTRUCTIVO_PARTES` — E2E 23 |
| Rutas `/ayuda/guia` y `/instructivo` | ✅ | Alias añadido |

### 22. Inventario opciones visibles

| Clasificación | Conteo estimado |
|---|---|
| FUNCIONAL | Mayoría rutas E2E |
| DEMO | Horizonte, presentación demo |
| POST-V1 | Integraciones T5, bridge 1260 |
| ROTA visible | **0** en recorrido E2E |
| DUPLICADA innecesaria | **0** críticas |

### 23. E2E empresarial completo

| Paso | Estado |
|---|---|
| LOGIN → CC → HORIZONTE → … → REGRESO CC | **24/24 PASS** |

### 24. QA visual 1440×900

| Check | Estado |
|---|---|
| Overflow / clipping / above-fold | **11/11 PASS** |

### 25. Protección Windows

| Check | Estado |
|---|---|
| `scripts/windows/**` sin cambios lógica | ✅ |
| `integration_sha` | Actualizar solo metadato al merge |

---

## P0 / P1 / P2 reales (post-revisión)

### P0 — Bloqueantes operación
**Ninguno** en recorrido demo certificado.

### P1 — Afectan demostración comercial
1. **Upload logos grandes:** `EnterpriseLogoField` MAX_BYTES 180_000 vs backend 200KB — puede rechazar logos reales motivadores de la corrección.
2. **Valor verificado/estimado en CC global:** KPIs `verified_value`/`estimated_value` pueden mostrar pendiente sin seed IE específico Horizonte.

### P2 — Mejoras V1.1
1. Inventario automático exhaustivo de todas las tablas del producto.
2. Categorías completas motor oportunidades (18 tipos) con demo etiquetada.
3. E2E upload documentos PDF/Excel/CSV con verificación binaria.
4. Bridge aprendizaje 1260 / adapter señales CC (POST-V1 acordado).

---

## Archivos de evidencia

```
data/evidence/horizonte-e2e/          — 13 screenshots E2E Horizonte
data/evidence/empresarial-e2e/        — 24 screenshots + report.json
data/evidence/cert-visual/            — 11 screenshots QA visual
```

## Scripts de certificación

```bash
node scripts/cert_horizonte_e2e.mjs
node scripts/cert_empresarial_completo.mjs
node scripts/cert_visual_audit.mjs
```

## Credenciales demo (Windows certificadas)

- Usuario: `org_a_admin` / `DemoA2026!`
- BD: `data/eiaax_integrado_demo.db`
- Horizonte: `[DEMO] Clínica Demo Horizonte — EVA-2026-0002`

---

**Decisión:** Candidato técnicamente más sólido que 1416671 aislado; **permanece NO AUTORIZADO** para prueba humana hasta revisión ChatGPT de esta matriz y cierre P1.
