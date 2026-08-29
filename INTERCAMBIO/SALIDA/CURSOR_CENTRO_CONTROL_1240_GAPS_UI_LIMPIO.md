# EMPLEADOS IA — Centro de Control 1240 + Gaps UI (tramo portátil)

**Fecha:** 2026-08-29  
**Base:** `4b67183af1d527684e41cad0b02d7a997d3b2499` (`cursor/base-puente-v1-post-v1`)  
**Rama:** `cursor/centro-control-1240-gaps-ui-limpio`  
**HEAD:** `624762b8084011d81faf5785815eb7d22c294f58`

---

## Objetivo cumplido

Pieza **portátil y validada** que:

- Integra el bloque **1240** (Inteligencia Externa) en el Centro de Control existente (1230).
- Renderiza los **4 gaps UI** ya entregados por backend: `finops_extendido`, `llm`, `auditoria_reciente`, `actividad_reciente`.
- No depende de convergencia 1260–1380.
- Degradación segura si 1240 falla (sin HTTP 500 global).

---

## Commits portátiles

| # | Descripción | SHA completo |
|---|-------------|--------------|
| 1 | Integración Centro de Control 1240 (backend) | `24a0e0ee2076086684ddfba914f83f78447233c2` |
| 2 | Render 4 gaps UI + sección 1240 (frontend) | `f9155fb6a26710599d10ca8eb15dc6789e90d7b0` |
| 3 | Pruebas 1240/gaps UI | `a52db5a20c2cf241e302724b626fd879788acc93` |
| 4 | Documentación (este entregable) | `624762b8084011d81faf5785815eb7d22c294f58` |

---

## Cambios técnicos

### Backend

- `InteligenciaExternaAdapter` en `control_center_adapters.py` (bloque 1240).
- KPIs: `external_sources_active`, `external_signals_pending`, `external_risks_open`.
- `_atencion_requerida()`: `senal_externa_pendiente` (MEDIA), `riesgo_externo` (ALTA).
- `_fetch_module_adapters()` con try/except por adaptador → estado `NO DISPONIBLE`.
- Enriquecimiento `_llm_section()` y `_audit_section()` para payload ejecutivo.
- Clave `inteligencia_externa` en `GET /api/centro-control/resumen-ejecutivo`.
- `integraciones_futuras["1240"]` = Integrado.

### Frontend

- `CentroControlPage.tsx`: FinOps extendido, IA/proveedores, actividad, auditoría, inteligencia externa.
- `api.ts`: tipos extendidos para gaps y 1240.
- Un solo dashboard en `/`, textos en español, diseño compacto.

### Sin cambios de alcance prohibido

- **0 endpoints nuevos**
- **0 migraciones nuevas**
- No integración 1260–1380
- Rama D / main / V1 no modificadas

---

## Pruebas ejecutadas

### Focal

```bash
BOOTSTRAP_ADMIN_PASSWORD='Admin2026*' PYTHONPATH=backend:. pytest \
  tests/test_centro_control_1240_gaps_ui.py \
  tests/test_bloque_1230_centro_control.py \
  tests/test_bloque_1250c_centro_control_integrado.py \
  tests/test_inteligencia_externa_1240.py -q
```

**Resultado:** 52 passed

### Regresión SQLite

```bash
BOOTSTRAP_ADMIN_PASSWORD='Admin2026*' PYTHONPATH=backend:. pytest tests -q \
  -m "not postgresql and not certification_intensive and not concurrency"
```

**Resultado:** 779 passed, 2 skipped, 0 failed

### Frontend

```bash
cd frontend && npm run build
```

**Resultado:** PASS (vite build OK)

### PostgreSQL

**PENDIENTE POR ENTORNO** — `DATABASE_URL` no configurado con PostgreSQL en esta VM.

---

## Matriz de verificación

| Criterio | Resultado |
|----------|-----------|
| CENTRO CONTROL ÚNICO | SI |
| 1240 INTEGRADO | PASS |
| finops_extendido | PASS |
| llm | PASS |
| auditoria_reciente | PASS |
| actividad_reciente | PASS |
| ENDPOINT NUEVO | NO |
| MIGRACIÓN NUEVA | NO |
| DEGRADACIÓN SEGURA | PASS |
| MULTIEMPRESA | PASS |
| RBAC | PASS |
| SUPERADMIN | PASS |
| REGRESIÓN SQLite | 779 passed, 0 failed |
| POSTGRESQL | PENDIENTE POR ENTORNO |
| FRONTEND | PASS |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| RAMA D MODIFICADA | NO |
| MAIN | NO MODIFICADO |
| V1 | NO MODIFICADA |
| MERGE | NO |

**VEREDICTO:** **APTO PARA PORTAR A CONVERGENCIA**

---

## Portabilidad a convergencia

Cherry-pick recomendado (orden):

1. `24a0e0ee2076086684ddfba914f83f78447233c2`
2. `f9155fb6a26710599d10ca8eb15dc6789e90d7b0`
3. `a52db5a20c2cf241e302724b626fd879788acc93`
4. `624762b8084011d81faf5785815eb7d22c294f58`

Conflictos probables: ninguno estructural si la rama destino conserva 1230/1240/1250C y el mismo contrato de `resumen-ejecutivo`.

---

## Bloques preservados

1100, 1110, 1120, 1200, 1210, 1220, 1230, 1240, 1250 — seguridad V1, DATABASE_URL, Knowledge auth, RBAC, multiempresa, SUPERADMIN, UI español.
