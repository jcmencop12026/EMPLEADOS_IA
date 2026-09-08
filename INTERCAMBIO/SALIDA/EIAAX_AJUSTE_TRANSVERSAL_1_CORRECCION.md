# EIAAX — Corrección auditoría ChatGPT PR #171 (Transversal 1)

**Fecha:** 2026-09-05
**Rama:** `cursor/ajuste-transversal-1-85e4`
**SHA inicial corrección:** `9792f52b42ee95bb7ad4981ad25963f7712d3cad`
**SHA final:** `7c1314554ee59f9b7e5cd6961108f2faccd49fbf`
**CI:** **4/4 PASS** (Backend, Frontend, Validación Git, Windows)
**Backup intacto:** `backup/eiaax-antes-ajuste-transversal-1-20260905` → `3e6d2c3`
**NO merge · NO promoción · NO POST-V1 · NO backend · NO Windows**

---

## Hallazgos corregidos

| # | Hallazgo | Corrección |
|---|---|---|
| 1 | Cert visual solo 13 rutas | Script ampliado a **22 vistas × 2 resoluciones = 44** |
| 2 | `hasActiveTab` no fallaba | Validación obligatoria: 1 activa, label correcto, diff visual computed styles |
| 3 | Pestañas tipo botón | CSS folder: unidas al contenido, activa inequívoca |
| 4 | Cobertura visual incompleta | 44 screenshots + métricas scroll/ancho/asistente |
| 5 | Densidad/scroll | `scrollRatio` registrado en report.json (no FAIL por scroll válido) |
| 6 | Selectores peligrosos | Eliminado `.panel > button:not(.btn)`; solo `compact-form > button[type=submit]` |
| 7 | Tabs funcionales | 10 Cabina + 8 Oportunidad: clic, URL, contenido, reload |

---

## Resultados

### Automático

| Suite | Resultado |
|---|---|
| Visual 1366×768 | **22/22 PASS** |
| Visual 1920×1080 | **22/22 PASS** |
| **Total visual** | **44/44 PASS** |
| Tabs Cabina (funcional) | **10/10 PASS** |
| Tabs Oportunidad (funcional) | **8/8 PASS** |
| `npm run build` | **PASS** |
| `test_integracion_funcional_final_v1.py` | **11/11 PASS** |
| `cert_horizonte_e2e.mjs` | **13/13 PASS** |
| `cert_integracion_pr170.mjs` | **2/2 PASS** |

### Revisión visual (screenshots)

44 capturas en `data/evidence/transversal-visual/` revisadas en autoauditoría:
- Pestañas estilo carpeta con activa diferenciada
- Sin scroll horizontal global
- Ancho útil ~100% del área de contenido
- Asistente no tapa controles primarios

---

## Archivos modificados

- `scripts/cert_transversal_visual.mjs` — 44 vistas + tabs funcionales + active tab strict
- `frontend/src/styles/eiaax-transversal-v1.css` — pestañas folder + selectores seguros

---

## Confirmaciones

- Backup **intacto** (`3e6d2c3`)
- **NO MERGE**
- **NO PROMOCIÓN**
- **NO POST-V1**
- **NO BACKEND**
- **NO STARTUP WINDOWS**

Detenido — esperar auditoría ChatGPT.
