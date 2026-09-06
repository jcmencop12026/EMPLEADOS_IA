# EIAAX — Corrección consolidada post-auditoría independiente ChatGPT

**PR:** #171 — `cursor/ajuste-transversal-1-85e4`
**Repositorio:** jcmencop12026/EMPLEADOS_IA
**SHA inicial (auditado):** `2f5c6551a93cafedb1e42769e2c389de3077064d`
**SHA final (HEAD PR):** `bdbbb17` (`bdbbb17a` completo en git)
**Run CI:** `34033769309` (5/5 verde)
**Fecha entrega:** 2026-09-06

---

## Veredicto de esta entrega

Corrección de defectos residuales comprobados por auditoría independiente. **No declarado APTO PARA USUARIO** — pendiente re-auditoría ChatGPT.

**NO MERGE · NO PROMOCIÓN · NO POST-V1 · NO nuevo PR**

---

## Defectos corregidos

| Área | Problema auditado | Corrección |
|---|---|---|
| Login / logo | Fallback EX visible con logo configurado | `EnterpriseMark` sin `BrandMark`; fallback tipográfico EIAAX; seed `CERT_BRANDING_CONFIG`; endpoint `has_configured_logo` |
| Cert login | CI no sembraba logo antes de captura | Casos separados configurado/fallback en `cert_transversal_visual.mjs` |
| Ciclo CC | Compresión/corte en 1366×768 | `CycleStepper` grid 5×3 multi-fila; checks de etapas visibles y sin truncado |
| KPI Valor potencial | Texto multi-línea ilegible | `formatValorPotencialKpi` extrae `$185M` + unidad `COP / año` |
| Controles | Botones HTML nativo (Actualizar, Priorizar) | Clases `btn secondary small` en CC y Oportunidades |
| Asistente | Solapaba superficie operativa | FAB compacto elevado (`bottom: 64px`); clearance en content |
| Certificación | PASS sobre defectos visibles | Checks login, ciclo, KPI, controles V1, asistente sin solapamiento |

---

## Resultados

| Criterio | Resultado |
|---|---|
| Login logo configurado | **PASS** |
| Login fallback | **PASS** |
| Ciclo 1366 | **PASS** |
| Ciclo 1920 | **PASS** |
| KPI Valor potencial | **PASS** |
| Controles | **PASS** |
| Asistente sin solapamiento | **PASS** |
| Vista Empresa | **PASS** |
| Visual transversal | **48/48** |
| Tabs Cabina | **10/10** |
| Tabs Oportunidad | **8/8** |
| Regresión Python | **26/26** + test login-identity PostgreSQL |
| Build frontend | **PASS** |
| CI GitHub Actions | **5/5** (run `34033769309`) |
| Regresión | **PASS** |

**Artefacto CI:** `eiaax-visual-pr171-bdbbb17a` (HEAD exacto en report.json y sha-manifest)

---

## Archivos modificados en esta corrección

- `backend/app/cert_branding.py` (nuevo)
- `backend/app/routers/public_identity.py`
- `backend/scripts/seed_demo_horizonte.py`
- `frontend/src/components/identity/EnterpriseMark.tsx`
- `frontend/src/hooks/useLoginIdentity.ts`
- `frontend/src/lib/formatKpiValue.ts` (nuevo)
- `frontend/src/components/v1/CycleStepper.tsx`
- `frontend/src/components/v1/KpiStrip.tsx`
- `frontend/src/components/centroControl/CentroControlEmpresaPanel.tsx`
- `frontend/src/components/centroControl/CentroControlCockpit.tsx`
- `frontend/src/components/EiaaxContextualAssistant.tsx`
- `frontend/src/pages/CentroControlPage.tsx`
- `frontend/src/pages/OportunidadesPage.tsx`
- `frontend/src/styles/eiaax-experience-v1.css`
- `scripts/cert_transversal_visual.mjs`
- `scripts/lib/cert_branding.mjs` (nuevo)
- `tests/test_macrointegral_v1_correcciones.py`

---

## Preservado (auditoría previa)

ContextBar, Centro Oportunidades inteligencia, Cabina siguiente acción, Valoración formulario propio, sin `window.prompt`, Vista Empresa, scoping empresa/expediente, Publicable cliente, aislamiento A/B, DEMO/REAL, evidencia sin JSON crudo, 10 tabs Cabina, 8 tabs Oportunidad, backend PostgreSQL, CI existente.

---

## Pendientes reales

Ninguno identificado en esta iteración. Re-auditoría independiente ChatGPT requerida antes de prueba humana.
