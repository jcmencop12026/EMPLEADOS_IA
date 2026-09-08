# EIAAX — Macrobloque Integral de Corrección V1
## Informe único de entrega — PR #171

**Repositorio:** jcmencop12026/EMPLEADOS_IA
**Rama:** `cursor/ajuste-transversal-1-85e4`
**PR:** #171 — feat(ui): Macrobloque Transversal 1 — normalización visual V1
**Revisión humana base:** `7c1314554ee59f9b7e5cd6961108f2faccd49fbf`
**SHA inicial real (HEAD pre-macrointegral):** `f684e096e83610f1f8bc26dc095e716de6e09762`
**SHA final:** `13d6c8b` (commit macrobloque integral)

**Confirmación:** NO MERGE · NO PROMOCIÓN · NO POST-V1

---

## 1. Comparativa SHA inicial vs revisión humana

| Commit | Contenido |
|--------|-----------|
| `7c13145` | Corrección PR171: cert visual 44/44, tabs folder, selectores seguros |
| `f684e09` | Solo docs CI 4/4 PASS — **sin cambios funcionales adicionales** |

El macrobloque integral parte de `f684e09` sin revertir mejoras posteriores a `7c13145`.

---

## 2. Archivos modificados / añadidos

### Frontend
- `frontend/src/lib/oportunidadLabels.ts` — etiquetas empresariales (estados, pertinencia, trazas, prioridad/confianza)
- `frontend/src/lib/oportunidadLabels.test.ts` — tests unitarios labels
- `frontend/src/components/StructuredEvidenceView.tsx` — evidencia estructurada (no JSON crudo)
- `frontend/src/components/oportunidad/ValuationFormsPanel.tsx` — valoración sin `window.prompt`
- `frontend/src/pages/OportunidadDetailPage.tsx` — evidencia, trazabilidad, valoración integrada
- `frontend/src/pages/OportunidadesPage.tsx` — tabla con lenguaje empresarial
- `frontend/src/pages/LoginPage.tsx` — `BrandMark level="corporativo"`
- `frontend/src/components/centroControl/CentroControlEmpresaPanel.tsx` — KPI valor potencial DEMO, acciones deduplicadas
- `frontend/src/components/centroControl/CentroControlCockpit.tsx` — ciclo empresarial con estados visuales
- `frontend/src/lib/cicloOperativo.ts` — `cicloChipState`, mapeo etapa por estado expediente
- `frontend/src/components/evaluacion/EmpresaOperacionPanel.tsx` — scoping expediente/org, estados en español
- `frontend/src/components/evaluacion/CabinaValorPanel.tsx` — sin terminología FinOps visible
- `frontend/src/components/espacioExterno/EspacioExternoAdminPanel.tsx` — no recrear entidad si existe
- `frontend/src/styles/eiaax-transversal-v1.css` — equilibrio legibilidad post compactación
- `frontend/src/pages/CentroControlPage.tsx`, `EvaluacionConsolePage.tsx` — KPI información requerida

### Tests y certificación
- `tests/test_macrointegral_v1_correcciones.py` — regresiones + aislamiento oportunidades
- `scripts/cert_vista_empresa_flow.mjs` — E2E Vista Empresa contexto
- `scripts/cert_macrointegral_v1.mjs` — orquestador
- `scripts/cert_transversal_visual.mjs` — evidencia tab actualizado
- `.github/workflows/qa.yml` — job certificación visual + artefactos + pytest focal

### Evidencia
- `data/evidence/transversal-visual/report.json` — 44/44 PASS
- `data/evidence/vista-empresa-flow/report.json` — PASS
- `data/evidence/README.md`

---

## 3. Matriz hallazgo → corrección → prueba → evidencia

| # | Hallazgo | Corrección | Prueba | Evidencia |
|---|----------|------------|--------|-----------|
| 1 | UI excesivamente compacta | Sección equilibrio legibilidad en CSS transversal | cert_transversal_visual 44/44 | screenshots 1366/1920 |
| 2 | Login isotipo "EX" | BrandMark corporativo oficial | test_login_usa_brand_corporativo | captura login en suite visual |
| 3 | CC ciclo sin estados | Chips done/current/next/pending por estado expediente | visual CC empresa | report.json |
| 4 | CC empresa KPI DEMO comprimido | Valor + banner DEMO separado | visual CC empresa | screenshot 02 |
| 5 | Acciones duplicadas CC empresa | Solo "Abrir cabina" en panel empresa | inspección UI | CC empresa panel |
| 6 | Operación sin scoping | Filtro expediente + nota org-wide | test_operacion_panel_scoping | cabina operación visual |
| 7 | Estados FAILED/COMPLETED crudos | labels EXECUTION_STATUS español | EmpresaOperacionPanel | cabina operación |
| 8 | FinOps en valor cabina | Texto "valor económico" sin FinOps | CabinaValorPanel | cabina valor visual |
| 9 | Crear entidad en empresa existente | Mensaje contextual si entidad vinculada | cert_vista_empresa_flow | report.json PASS |
| 10 | JSON crudo en evidencia oportunidad | StructuredEvidenceView | cert opp evidencia tab | screenshot oportunidad |
| 11 | Trazas SENAL_CREADA etc. | labelTraceEtapa + formatTraceDetalle | test_oportunidad_labels | trazabilidad tab |
| 12 | Valoración con window.prompt | ValuationFormsPanel modal integrado | test_oportunidad_detail_sin_window_prompt | valoración tab func |
| 13 | Tabla oportunidades densa/códigos | Prioridad/confianza/pertinencia humanizados | OportunidadesPage | visual oportunidades |
| 14 | Vista Empresa pierde contexto | E2E reload + CC expediente param | cert_vista_empresa_flow | 01-vista-empresa-tab.png |
| 15 | Aislamiento multi-org | test_aislamiento_oportunidades | pytest PASS | CI backend |
| 16 | Información KPI ambiguo | "Información requerida completada" | EvaluacionConsolePage | cabina empresa visual |

---

## 4. Pruebas ejecutadas (SHA pre-push `f684e09` + cambios locales)

| Prueba | Resultado |
|--------|-----------|
| `npm run build` | PASS |
| `pytest tests/test_macrointegral_v1_correcciones.py` | 6/6 PASS |
| `pytest tests/test_integracion_funcional_final_v1.py` | 11/11 PASS |
| `cert_transversal_visual.mjs` | Visual 44/44, tabs 18/18 PASS |
| `cert_vista_empresa_flow.mjs` | PASS |

---

## 5. E2E flujo cubierto

LOGIN → CC global → CC empresa (Horizonte) → Cabina 10 tabs → Centro oportunidades → Oportunidad 8 tabs → Vista Empresa reload → regreso CC con `?expediente=`.

---

## 6. Aislamiento

- `test_aislamiento_oportunidades_entre_organizaciones` — org A ∩ org B = ∅
- Patrón existente `test_aislamiento_organizacion_espacio_externo` preservado

---

## 7. Evidencia visual accesible

- Local: `data/evidence/` (reportes JSON + capturas PNG)
- CI: artefacto `eiaax-visual-pr171-<SHA>` en GitHub Actions job **Certificación visual PR171**

---

## 8. Pendientes reales (no bloqueantes para auditoría)

1. **Cabina Diagnóstico / Solución IA / Consumo / Informes** — mejoras narrativas parciales; requieren datos backend más ricos para validación humana completa.
2. **Backend filtro "Publicable cliente"** — filtro existente en CabinaInformesPanel; auditoría de permisos backend recomendada en ciclo posterior.
3. **window.prompt en otros módulos** (EmployeeDetail, Comunicaciones, etc.) — fuera del alcance §24 valoración oportunidad; no tocados.
4. **CI visual job** — requiere validación en GitHub tras push (nuevo job en qa.yml).

---

## 9. Declaración

Este informe **no declara APTO**. Se detiene para auditoría independiente ChatGPT sobre el SHA final.

**NO MERGE · NO PROMOCIÓN · NO POST-V1**
