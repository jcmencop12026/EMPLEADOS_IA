# EIAAX — Macrobloque Transversal 1: Normalización visual V1

**Fecha:** 2026-09-05
**Ruta:** `D:\EMPLEADOS_IA_CONVERGENCIA`
**Rama:** `cursor/ajuste-transversal-1-85e4`
**SHA inicial (backup):** `3e6d2c3d825983280e640f70849e76e78abcbb6b`
**SHA referencia ChatGPT:** `72978e4d1b3753a53064e8a2e29b72f974294bfc`
**SHA final:** *(completar tras push)*
**NO merge · NO promoción · NO POST-V1 · NO cambios Windows arranque**

---

## 1. Punto de retorno (backup)

| Mecanismo | Referencia |
|---|---|
| Tag | `backup/eiaax-antes-ajuste-transversal-1-20260905` |
| Rama | `backup/eiaax-antes-ajuste-transversal-1-20260905` |
| Documentación | `INTERCAMBIO/RESPALDOS/EIAAX_TRANSVERSAL_1/BACKUP_PUNTO_RETORNO_20260905.md` |

**Restauración:** `git checkout backup/eiaax-antes-ajuste-transversal-1-20260905`

Verificado: tag y rama apuntan a `3e6d2c3`.

---

## 2. Sistema transversal creado

**Archivo:** `frontend/src/styles/eiaax-transversal-v1.css`

**Activación:** clase `eiaax-v1-transversal` en `AppShell` + import en `main.tsx`

| Subsistema | Alcance |
|---|---|
| Ancho útil | `ops-page`, `eval-console`, `trabajo-page` sin max-width estrecho |
| Densidad vertical | paddings/gaps compactos en paneles, headers, KPI |
| Pestañas | `.tab-bar` + `.tab-nav` unificados (activo, hover, focus) |
| Botones | primario/secundario/terciario/peligro/deshabilitado |
| Formularios | `.compact-form` y `.form-grid` en grid responsivo |
| Tablas | filas compactas, hover, alineación numérica |
| KPI | `.executive-kpi`, `.cc-kpi-item`, dashboard cards compactos |
| Cadenas | `.chain-list`, `.wizard-step`, `.cc-ciclo-chip` como etapas |
| Sidebar | espaciado mínimo |
| Asistente | clearance inferior, rail compacto |
| Overflow | badge notificaciones (preexistente 10px) corregido |

---

## 3. Archivos modificados

- `frontend/src/styles/eiaax-transversal-v1.css` *(nuevo)*
- `frontend/src/main.tsx`
- `frontend/src/AppShell.tsx`
- `scripts/cert_transversal_visual.mjs` *(nuevo)*
- `INTERCAMBIO/RESPALDOS/EIAAX_TRANSVERSAL_1/BACKUP_PUNTO_RETORNO_20260905.md` *(nuevo)*

**Sin cambios:** lógica backend, endpoints, modelos, scripts Windows, datos DEMO.

---

## 4. Pantallas verificadas visualmente

1366×768 y 1920×1080 — `cert_transversal_visual.mjs` (**26/26 PASS**):

CC global, Empresas, Evaluaciones, Oportunidades, Cabina (Empresa/Diagnóstico/Valor/Informes/Vista Empresa), Oportunidad (Resumen/Seguimiento/Valoración), Operaciones.

---

## 5. Pruebas ejecutadas

| Prueba | Resultado |
|---|---|
| `npm run build` | **PASS** |
| `test_integracion_funcional_final_v1.py` | **11/11 PASS** |
| `test_db_startup_805e.py` | **PASS** |
| `test_cierre_brechas_horizonte.py` | **14/15 PASS** (1 skip condicional demo DB) |
| `cert_integracion_pr170.mjs` | **2/2 PASS** |
| `cert_horizonte_e2e.mjs` | **13/13 PASS** |
| `cert_transversal_visual.mjs` | **26/26 PASS** |

---

## 6. Autoauditoría

| Defecto encontrado | Corrección |
|---|---|
| Badge notificación desbordaba 10px (preexistente) | `notification-badge { right: 0 }` en sistema transversal |
| Vitest no instalado en frontend | Preexistente — no bloqueante |
| `test_documentos_persisten_tras_reinicio_real` | Preexistente — requiere BD demo específica |

---

## 7. Confirmaciones

- **NO MERGE**
- **NO PROMOCIÓN**
- **NO CAMBIOS POST-V1**
- **NO CAMBIOS EN ARRANQUE WINDOWS**

Detenido — esperar auditoría independiente ChatGPT.
