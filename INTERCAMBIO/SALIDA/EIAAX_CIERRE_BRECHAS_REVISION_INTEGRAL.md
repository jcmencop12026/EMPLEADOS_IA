# EIAAX — Cierre brechas revisión integral (entrega ChatGPT)

**Fecha:** 2026-09-03  
**Rama:** `cursor/revision-integral-completa-85e4`  
**PR:** #169  
**Base:** `cursor/convergencia-comercial-v1-85e4`  
**SHA:** *(actualizar tras commit — ver `git rev-parse --short HEAD`)*  
**Estado:** Cierre P1 material V1 ejecutado — pendiente decisión ChatGPT (no comando al usuario)

---

## Resumen cierre

| Métrica | Resultado |
|---|---|
| P0 material | **0** |
| P1 material V1 | **0** (logos + valor Horizonte cerrados) |
| `test_cierre_brechas_horizonte.py` | **6/6 PASS** |
| E2E Horizonte | **13/13 PASS** — `data/evidence/horizonte-e2e/` |
| E2E empresarial | **24/24 PASS** — `data/evidence/empresarial-e2e/report.json` |
| QA visual 1440×900 | **11/11 PASS** — `data/evidence/cert-visual/` |
| Logo >1 MB | **PASS** — `data/evidence/logo-upload/` |
| Inventario opciones E2E | **ROTA=0** — `data/evidence/opciones-e2e/inventario.json` |
| Windows startup | **Preservado** — solo `integration_sha` en manifest si aplica |

---

## 1. P1 Logos — CERRADO

| Aspecto | Implementación |
|---|---|
| Entrada cliente | `logoUpload.ts`: hasta **2,5 MB** PNG/JPEG/WebP |
| Optimización | Redimensiona (máx. 512px lado), comprime ~400 KB, proporción preservada |
| Preview | `EnterpriseLogoField.tsx` — preview antes de guardar |
| Backend | `schemas_admin.py`: `max_length=700_000` (data URL optimizado) |
| Persistencia | PUT `/api/admin/config` + reinicio — verificado en cert |

**Evidencia logo >1 MB:**

```json
{
  "originalBytes": 1398344,
  "outputBytes": 121870,
  "optimized": true,
  "saveOk": true,
  "persisted": true
}
```

Script: `scripts/cert_logo_upload.mjs`  
Screenshot: `data/evidence/logo-upload/` (generado por cert)

---

## 2. P1 Valor Horizonte — CERRADO

Semilla idempotente: `backend/app/services/demo_economico_horizonte.py`  
Marcador: `DEMO_HORIZONTE_ECON_V1`  
Etiqueta: **DEMO — DATOS SIMULADOS** / **ESTIMADO / PROYECTADO**

| Naturaleza | Monto (COP) | Nota |
|---|---|---|
| VERIFICADO | 28.500.000 | Piloto Q1 — medición validada |
| ESTIMADO | 62.000.000 | Proyección anual reprocesos |
| POTENCIAL | 185.000.000 | Escenario automatización completa |

- `exp.valor_potencial` = `DEMO — $185M COP/año (ESTIMADO)`
- CC `valor_consolidado.potencial` visible en `/api/centro-control/resumen-ejecutivo`
- Oportunidades demo con variedad: AHORRO/eficiencia, RECUPERACION/ingresos, RIESGO/calidad
- `register_finops=False` en seed para evitar commits anidados

Wired en `demo_comercial_service.py` (nuevo seed y expediente existente).

---

## 3. Documentos E2E — CERRADO

**Bug corregido:** `list_adjuntos_by_informacion_item` usaba `created_at` inexistente en `EvaluacionEntregaExterna` → `solicitado_at`.

**Bug corregido:** cada upload a un ítem creaba entrega nueva; el listado solo mostraba la última. Ahora:
- Reutiliza entrega abierta del mismo ítem
- Lista adjuntos actuales de todas las entregas del ítem

**Prueba automatizada:** `test_upload_pdf_y_csv_horizonte` — PDF + CSV subidos, listados, descarga binaria `%PDF`.

Formatos soportados (backend `knowledge_storage.py`): `.pdf`, `.csv`, `.xlsx`, `.txt`, `.json`, `.docx` (máx. 20 MB).

---

## 4. Tablas recorrido V1 — AUDITADO

Script `scripts/cert_opciones_e2e.mjs` — inventario + auditoría tablas en:
- Rutas globales E2E (13 opciones)
- Cabina Horizonte: Empresa, Diagnóstico, Valor, Resultados, Informes, Operaciones

**ROTA en tablas cabina Horizonte: 0**

Nota menor (P2): `/operaciones` reporta `tabla 1 overflow horizontal` en viewport 1440×900 — no marca ROTA; scroll contenido presente.

---

## 5. Informes — 4 experiencias conceptuales — CERRADO

`CabinaInformesPanel.tsx` — pestañas navegables con datos Horizonte:

| Vista | Contenido |
|---|---|
| **Ejecutiva** | Síntesis, KPIs, alertas, valor, recomendación |
| **Operativa** | Proceso, indicadores, desviaciones |
| **Resultados / Valor** | Antes → Proyectado → Real (etiquetado DEMO) |
| **Publicable cliente** | Solo contenido autorizado |

Patrón narrativo: qué ocurrió → por qué → qué significa → atención → oportunidad → valor → recomendación EIAAX.

E2E empresarial paso 12 Informes: **PASS**.

---

## 6. Vista Empresa — seguridad — CERRADO

`test_vista_entidad_no_expone_datos_internos`:
- No expone: `notas_internas`, `margen`, `precio_sugerido`, `costo_interno`, `prompt`, `scoring`, `economia_privada`
- `valor_potencial` = null en vista entidad
- Org B → 403/404 al consultar expediente Horizonte de Org A

---

## 7. Asistente contextual — CERRADO

`evaluacion_service.py` — `_demo_ask_response()` para expedientes `[DEMO]` / Horizonte.

Preguntas probadas: qué falta, hallazgos, oportunidad, valor, decisión, vista empresa (+ más en test).

`test_ask_eiaax_demo_horizonte_contexto`: **PASS** — respuestas coherentes con contexto Horizonte, sin fuga cross-org.

---

## 8. Oportunidades demo — CERRADO

`test_oportunidades_demo_variedad`: ≥3 oportunidades, ≥2 tipos (AHORRO, RECUPERACION, RIESGO).

18 categorías completas: **P2** (no bloqueante V1).

---

## 9. Inventario opciones visibles E2E V1

Archivo: `data/evidence/opciones-e2e/inventario.json`

| Estado | Cantidad | Ejemplos |
|---|---|---|
| FUNCIONAL | 17 | CC, Empresas, Evaluaciones, cabina Horizonte (6 tabs) |
| DEMO | 2 | Automatizaciones, Demo comercial |
| ROTA | **0** | — |
| DUPLICADA confusa | **0** | — |
| POST-V1 visible confusa | **0** | — |

---

## 10. Pruebas ejecutadas

```bash
DATABASE_URL=sqlite:////workspace/data/eiaax_integrado_demo.db \
  PYTHONPATH=backend:. pytest tests/test_cierre_brechas_horizonte.py -q
# 6 passed

node scripts/cert_horizonte_e2e.mjs          # 13/13
node scripts/cert_empresarial_completo.mjs   # 24/24
node scripts/cert_visual_audit.mjs           # 11/11
node scripts/cert_logo_upload.mjs            # originalBytes>1MB OK
node scripts/cert_opciones_e2e.mjs         # ROTA=0
```

`pageerror` material en certs: **0**  
`console.error` material en certs: **0** (warnings de red no bloqueantes)

---

## P0 / P1 / P2 finales

### P0 — 0

Sin pantallas blancas, hooks rotos, rutas críticas caídas en recorrido V1.

### P1 material V1 — 0

| Antes | Cierre |
|---|---|
| Logos 180/200 KB incoherentes | Upload >1 MB + optimización + backend 700K |
| CC sin valor económico Horizonte | Seed idempotente + etiquetas DEMO |

### P2 aceptables (documentados)

1. Inventario histórico tablas fuera recorrido V1
2. Ampliar oportunidades demo a 18 categorías
3. Overflow horizontal menor en tabla `/operaciones` (1440×900)
4. Bridge aprendizaje 1260
5. Refinamientos no bloqueantes

---

## Archivos tocados (cierre brechas)

| Archivo | Cambio |
|---|---|
| `backend/app/schemas_admin.py` | Logo max_length 700K |
| `backend/app/services/demo_economico_horizonte.py` | **NUEVO** — seed económico |
| `backend/app/services/demo_comercial_service.py` | Llama `ensure_horizonte_economico` |
| `backend/app/services/evaluacion_service.py` | Asistente demo + contexto entidad |
| `backend/app/services/evidencia_entrega_service.py` | Adjuntos multi-archivo + solicitado_at |
| `frontend/.../CabinaInformesPanel.tsx` | 4 vistas informe |
| `frontend/.../EvaluacionConsolePage.tsx` | Props demo/entidad |
| `tests/test_cierre_brechas_horizonte.py` | **NUEVO** — 6 tests |
| `scripts/cert_logo_upload.mjs` | **NUEVO** |
| `scripts/cert_opciones_e2e.mjs` | **NUEVO** + audit cabina |

**Preservado:** `scripts/windows/**` (lógica startup sin cambios).

---

## Screenshots clave

| Evidencia | Ruta |
|---|---|
| Horizonte E2E | `data/evidence/horizonte-e2e/*.png` |
| Empresarial 24 pasos | `data/evidence/empresarial-e2e/*.png` |
| Visual QA | `data/evidence/cert-visual/*.png` |
| Logo upload | `data/evidence/logo-upload/` |
| Inventario | `data/evidence/opciones-e2e/inventario.json` |

---

*Entrega exclusiva para revisión ChatGPT. No emitir comando al usuario hasta autorización.*
