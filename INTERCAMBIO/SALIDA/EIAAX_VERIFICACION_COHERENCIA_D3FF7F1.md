# EIAAX — Verificación final de coherencia (candidato d3ff7f1+)

**Fecha:** 2026-09-03
**Rama PR #169:** `cursor/revision-integral-completa-85e4`
**Candidato aislado:** sí — **NO** es rama autoritativa Windows
**NO merge** · **NO promoción** · **NO comando al usuario**

---

## 1. Estado autoritativo

| Campo | Valor |
|---|---|
| **Base exacta** | `14166710932fa87115e700ae0b1e2aa7e110b744` (`cursor/convergencia-comercial-v1-85e4`) |
| **Candidato HEAD** | _ver HEAD final sección C en `EIAAX_CIERRE_CERTIFICACION_CI_PR169.md`_ |
| **producto / integration_sha** | _alineado al HEAD final en manifest_ |
| **PR** | [#169](https://github.com/jcmencop12026/EMPLEADOS_IA/pull/169) |
| **Conflictos con base** | **0** (`git merge-tree` sin changed-in-both) |
| **Migraciones nuevas** | **0** — Alembic head sin cambio: `1831a1b2c3d4e` |
| **scripts/windows** | Solo `eiaax_convergence_manifest.json` → `integration_sha` (sin tocar lógica startup) |

### Commits del PR (4 + coherencia)

```
e569548 fix(v1): revisión integral CC, gráficos, informes y E2E empresarial
7b44f20 chore(windows): integration_sha e569548 post-revisión integral
4b77c49 fix(v1): cierre brechas P1 logos, valor Horizonte, docs E2E e informes
d3ff7f1 chore(windows): integration_sha 4b77c49 post-cierre brechas
<coherencia> fix(v1): semántica demo económica, asistente clasificado, informes 4v
```

### Diff vs `cursor/convergencia-comercial-v1-85e4`

27 archivos · +1859 / −152 líneas (sin `scripts/windows/**` salvo manifest metadata).

---

## 2. Demo económica — terminología corregida

### Problema detectado

Semilla usaba `RealValueNature.VERIFICADO` junto a banner DEMO → riesgo de interpretar ficticio como verificado real.

### Corrección

- Nuevo `backend/app/demo_economico_semantica.py`
- Semilla Horizonte: **ningún** valor demo con naturaleza `VERIFICADO`
- 28,5M → **SIMULACIÓN DE RESULTADO VERIFICADO** (`ESTIMADO` + etiqueta explícita)
- 62M → **ESTIMADO** (simulado)
- 185M → **POTENCIAL** (simulado)
- UI (`CabinaValorPanel`, `CabinaInformesPanel`, CC empresa): banner `DEMO — DATOS SIMULADOS`
- API `/impacto` → `resumen.es_demo`, `simulacion_verificado`, `verificado: null`

### Prueba

`test_horizonte_economico_semantica_demo_sin_verificado_real` — **PASS**

---

## 3. Asistente EIAAX — clasificación REAL vs DEMO

| Modo | Cuándo | Proveedor | LLM real |
|---|---|---|---|
| **demo_controlado** | Expediente `[DEMO]` / Horizonte | `plantillas_demo_horizonte` (`_demo_ask_response`) | No |
| **local_heuristica** | Intenciones A/B/D–H sin LLM | `evaluacion_intent_service` | No |
| **llm_real** | Intención C + proveedor configurado | `route_task` | Sí |

### A. Simulación demo (Horizonte)

`_demo_ask_response()` — plantillas con prefijo `[DEMO]`, contexto real del expediente (hallazgos, pendientes, oportunidades DB).

### B. Asistente real

`ask_eiaax()` → `classify_intent` + `route_task` cuando hay LLM; respuestas locales heurísticas sin demo.

### C. Contexto consumido

`contexto_expediente`: código, entidad, estado, confianza, información pendiente; hallazgos/oportunidades desde DB.

### D. Pendiente (no bloqueante V1)

- Asistente LLM en producción sin expediente demo (depende proveedor org)
- Bridge PIIAX ampliado
- **No se declara "asistente contextual cerrado"** — se declara **demo_controlado certificado + real clasificado**

### Fuga cross-org

`test_vista_entidad` org B → 403/404 — **PASS**
Asistente demo atado a `organization_id` del expediente.

Respuesta incluye `modo_respuesta`, `proveedor`, `llm_real`.

---

## 4. Informes — cuatro experiencias reales

Motor único: `fetchEvaluacionImpacto` + datos expediente. Sin motores duplicados.

| Vista | Destinatario | Muestra | Omite |
|---|---|---|---|
| **Ejecutiva** | Dirección | KPIs, narrativa qué/por qué/significa, alertas, valor simulado, recomendación | Costos internos, margen, prompts |
| **Operativa** | Jefes proceso | Tabla indicadores + desviación + alerta por fila | Economía privada, scoring |
| **Resultados/Valor** | Finanzas | Tarjetas simulación verificado / estimado / potencial + narrativa | Verificado real en demo |
| **Publicable cliente** | Empresa | Hallazgos, indicadores autorizados, valor publicable simulado, acciones vista empresa/presentar | Todo lo interno |

**Evidencia visual:** `data/evidence/coherencia-verificacion/02-informe-1..4-*.png`

---

## 5. Indicadores / gráficos — interpretación

`get_impacto_resumen` ahora incluye `interpretacion`:

- qué_ocurrió → por_qué → qué_significa → requiere_atención → oportunidad → valor → recomendación → acciones

**CC Horizonte:** `CentroControlEmpresaPanel` — strip interpretación + tablero `ImpactoGrafico`
**Evidencia:** `data/evidence/coherencia-verificacion/01-cc-horizonte-tablero.png`

---

## 6. Overflow /operaciones — resuelto

| Aspecto | Resultado |
|---|---|
| Tipo | Scroll horizontal **intencional** (tabla extensa 13 columnas) |
| Corrección | `ops-table-panel` + columna Acciones **sticky** derecha |
| Usabilidad | `actionsVisible: true`, scroll 1158→1240px |
| Cert | `/operaciones` ya no marca defecto overflow |

**Evidencia:** `data/evidence/coherencia-verificacion/04-operaciones-tabla.png`

---

## 7. Logos

| Check | Estado |
|---|---|
| Entrada >1MB | 1.398.344 B → 121.870 B optimizado |
| Persistencia API | PASS (`cert_logo_upload.mjs`) |
| Proporción | Resize max 512px lado, aspecto preservado (`logoUpload.ts`) |
| Preview | `EnterpriseLogoField` |
| Configuración | `/admin/configuracion` — screenshot `05-config-logo.png` |
| Login / presentación / Vista Empresa | Heredan `enterprise_logo_url` org (sin cambio lógica) |
| Reinicio | Persistido en DB org config |

---

## 8. Documentos

| Check | Estado |
|---|---|
| PDF + CSV upload/list/download | PASS |
| Persistencia post-reinicio real | `test_documentos_persisten_tras_reinicio_real` PASS (uvicorn stop/start) |
| Metadatos | organization_id vía sesión; expediente + item_id en ruta |
| Excel adicional | No exigido — CSV cubre tabular V1 |

---

## 9. Vista Empresa — seguridad sin anular valor

| Aspecto | Comportamiento |
|---|---|
| Filtra | notas_internas, margen, precio_sugerido, prompts, scoring, economia_privada |
| **Incluye** | `valor_publicable` (estimado/proyectado/potencial/simulación con banner DEMO) |
| **Incluye** | hallazgos `visible_entidad`, indicadores autorizados, oportunidades publicables |
| Cross-org | 403/404 |

**Evidencia:** `data/evidence/coherencia-verificacion/03-vista-empresa.png`

---

## 10. Inventario 19 superficies V1

| # | Opción | Estado | Ruta |
|---|---|---|---|
| 1 | Centro de Control | FUNCIONAL | `/` |
| 2 | Empresas | FUNCIONAL | `/empresas` |
| 3 | Evaluaciones | FUNCIONAL | `/evaluaciones` |
| 4 | Operaciones | FUNCIONAL | `/operaciones` |
| 5 | Empleados IA | FUNCIONAL | `/directorio` |
| 6 | Oportunidades | FUNCIONAL | `/oportunidades` |
| 7 | Resultados | FUNCIONAL | `/resultados-inteligencia` |
| 8 | Comunicaciones | FUNCIONAL | `/comunicaciones` |
| 9 | **Automatizaciones** | **DEMO** | `/automatizaciones` |
| 10 | Ejecuciones | FUNCIONAL | `/ejecuciones` |
| 11 | Aprobaciones | FUNCIONAL | `/aprobaciones` |
| 12 | Instructivo | FUNCIONAL | `/ayuda/guia` |
| 13 | **Demo comercial** | **DEMO** | `/demo` |
| 14 | Cabina Empresa | FUNCIONAL | `/evaluaciones/{id}#empresa` |
| 15 | Cabina Diagnóstico | FUNCIONAL | `#diagnóstico` |
| 16 | Cabina Valor | FUNCIONAL | `#valor` |
| 17 | Cabina Resultados | FUNCIONAL | `#resultados` |
| 18 | Cabina Informes | FUNCIONAL | `#informes` |
| 19 | Cabina Operaciones | FUNCIONAL | `#operaciones` |

**DEMO visual:** badge/copy demo en `/automatizaciones` y `/demo`; expedientes `[DEMO]` con banner amarillo en valor/informes/CC.

**ROTA=0 · DUPLICADA=0 · POST-V1 confusa visible=0**

---

## 11. P0 / P1 / P2 recalculados

| Nivel | Count | Detalle |
|---|---|---|
| **P0** | **0** | Sin roturas E2E, hooks, rutas críticas |
| **P1 material V1** | **0** | Tras corrección semántica demo + clasificación asistente + informes 4v + overflow ops |
| **P2** | 3 | Inventario tablas histórico fuera V1; 18 categorías oportunidades; bridge aprendizaje 1260 |

---

## 12. Pruebas ejecutadas

```
pytest tests/test_db_startup_805e.py              → 4/4 PASS (HEAD final)
pytest tests/test_cierre_brechas_horizonte.py     → 8/8 PASS (HEAD final)
pytest -m "certification and not certification_intensive" → PASS (HEAD final)
cert_horizonte_e2e.mjs                            → 13/13 (HEAD final)
cert_empresarial_completo.mjs                     → 24/24 (HEAD final)
cert_visual_audit.mjs                             → 11/11 (HEAD final)
cert_logo_upload.mjs                              → PASS (HEAD final)
cert_opciones_e2e.mjs                             → ROTA=0 (HEAD final)
cert_coherencia_verificacion.mjs                  → PASS (HEAD final)
frontend npm run build                            → PASS (HEAD final)
```

---

## Screenshots clave

| Archivo | Contenido |
|---|---|
| `coherencia-verificacion/01-cc-horizonte-tablero.png` | Tablero + interpretación |
| `coherencia-verificacion/02-informe-1-ejecutiva.png` | Informe ejecutiva |
| `coherencia-verificacion/02-informe-2-operativa.png` | Informe operativa |
| `coherencia-verificacion/02-informe-3-resultados-/-valor.png` | Informe valor |
| `coherencia-verificacion/02-informe-4-publicable-cliente.png` | Informe cliente |
| `coherencia-verificacion/03-vista-empresa.png` | Vista empresa |
| `coherencia-verificacion/04-operaciones-tabla.png` | Operaciones scroll+sticky |
| `coherencia-verificacion/05-config-logo.png` | Config logo |

---

*Entrega exclusiva ChatGPT — decisión de promoción pendiente.*
