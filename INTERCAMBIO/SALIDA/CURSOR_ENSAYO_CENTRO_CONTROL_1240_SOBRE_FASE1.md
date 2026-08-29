# EMPLEADOS IA — Ensayo Centro de Control 1240 + Gaps UI sobre Fase 1

**Fecha:** 2026-08-29  
**Tipo:** Ensayo en rama aislada (sin modificar convergencia central)

---

## Fase 1 — punto de partida

| Campo | Valor |
|-------|-------|
| Rama base | `cursor/convergencia-final-post-v1-integracion` |
| **FASE1_HEAD_REAL** | `041209f4acabd595b5249c979a7e61031f598048` |
| Alembic HEAD | `1380a1b2c3d4e` |
| Alembic HEADS | 1 |

---

## Rama de ensayo

| Campo | Valor |
|-------|-------|
| Rama | `cursor/ensayo-centro-control-sobre-fase1` |
| **HEAD** | `689498cd8dfa23f5ff23270982086983704ccff1` |

---

## Commits portados (cherry-pick limpio)

| Pieza | SHA fuente | SHA resultante en ensayo |
|-------|------------|--------------------------|
| Backend 1240 | `24a0e0ee2076086684ddfba914f83f78447233c2` | `1028187cb0f70a536ea7ba80b31dc74ae93a7ce4` |
| Frontend gaps UI | `f9155fb6a26710599d10ca8eb15dc6789e90d7b0` | `aaf8881c95cda41b289ffca9e737b68ce9918c79` |
| Pruebas | `a52db5a20c2cf241e302724b626fd879788acc93` | `ec44052c4ef5b02e0a4b2ae9f1b539c95a05ade9` |

**Documentación fuente** (`2aaae46…`) no portada como funcionalidad — solo este entregable.

---

## Conflictos reales

**Total: 0**

Los tres cherry-picks aplicaron sin conflicto manual.

| Archivo vigilado | Conflicto | Resolución | Riesgo | Prueba |
|------------------|-----------|------------|--------|--------|
| `control_center_adapters.py` | No | — | — | `test_centro_control_1240_gaps_ui.py` |
| `control_center_service.py` | No | — | — | `test_bloque_1230_*`, `test_bloque_1250c_*` |
| `main.py` | No | — | — | Regresión 882 passed |
| `permissions.py` | No | — | — | RBAC focal |
| `api.ts` | Auto-merge limpio | — | — | `npm run build` PASS |
| `CentroControlPage.tsx` | No | — | — | Build + focal |
| `App.tsx` | No | — | — | Ruta `/` única |
| `AppShell.tsx` | No | — | — | Menú intacto |
| `auth/permissions.ts` | No | — | — | Identidad focal |
| `conftest.py` | No | — | — | Regresión |

---

## Validación funcional

### Centro de Control 1230 + 1240 + gaps UI

- Un solo dashboard en `/` (`App.tsx` → `CentroControlPage`)
- `InteligenciaExternaAdapter`: filtro por empresa, RBAC, degradación segura
- Gaps UI consumen payload real: `finops_extendido`, `llm`, `auditoria_reciente`, `actividad_reciente`
- Sin endpoints nuevos ni migraciones

### Bloques Fase 1 preservados (presencia no rompe CC)

| Bloque | Prueba focal | Resultado |
|--------|--------------|-----------|
| 1300 Seguridad avanzada | `test_bloque_1300_seguridad_avanzada.py` | PASS |
| 1350 Gobierno datos | `test_governance_1350.py` | PASS |
| 1360 Continuidad | `test_continuidad_1360.py` | PASS |
| 1370 Identidad empresarial | `test_identidad_1370.py` | PASS |
| 1380 SCIM | `test_scim_1380.py` | PASS |

**Nota:** 1350/1360/1300/1370/1380 no se cablearon como adaptadores del Centro de Control (alcance correcto del ensayo).

### Seguridad / multiempresa / RBAC

- SUPERADMIN: contexto org cruzado — PASS (`test_cc_superadmin_org_context`)
- RBAC sin `inteligencia_externa.view`: restringido — PASS
- Cross-tenant A ≠ B — PASS
- Degradación 1240 (`NO DISPONIBLE` sin tumbar agregador) — PASS

---

## Pruebas ejecutadas

### Focal

```bash
BOOTSTRAP_ADMIN_PASSWORD='Admin2026*' PYTHONPATH=backend:. pytest \
  tests/test_centro_control_1240_gaps_ui.py \
  tests/test_bloque_1230_centro_control.py \
  tests/test_bloque_1250c_centro_control_integrado.py \
  tests/test_inteligencia_externa_1240.py \
  tests/test_bloque_1300_seguridad_avanzada.py \
  tests/test_identidad_1370.py \
  tests/test_scim_1380.py \
  tests/test_continuidad_1360.py \
  tests/test_governance_1350.py -q
```

**155 passed, 0 failed**

### Regresión SQLite acumulativa

```bash
BOOTSTRAP_ADMIN_PASSWORD='Admin2026*' PYTHONPATH=backend:. pytest tests -q \
  -m "not postgresql and not certification_intensive and not concurrency"
```

**882 passed, 2 skipped, 0 failed, 0 errors**

### Frontend

```bash
cd frontend && npm run build
```

**PASS**

### PostgreSQL

**PENDIENTE POR ENTORNO** — sin `DATABASE_URL` PostgreSQL en esta VM.

### Alembic post-ensayo

- HEAD: `1380a1b2c3d4e`
- HEADS: **1** (sin migración nueva)

---

## Matriz de verificación

| Criterio | Resultado |
|----------|-----------|
| CENTRO CONTROL ÚNICO | SI |
| 1240 | PASS |
| finops_extendido | PASS |
| llm | PASS |
| auditoria_reciente | PASS |
| actividad_reciente | PASS |
| 1360 PRESERVADO | PASS |
| 1350 PRESERVADO | PASS |
| 1300 PRESERVADO | PASS |
| 1370 PRESERVADO | PASS |
| 1380 PRESERVADO | PASS |
| MULTIEMPRESA | PASS |
| RBAC | PASS |
| SUPERADMIN | PASS |
| DEGRADACIÓN | PASS |
| ALEMBIC HEADS | 1 |
| ALEMBIC HEAD | 1380a1b2c3d4e |
| REGRESIÓN | 882 passed, 0 failed |
| POSTGRESQL | PENDIENTE POR ENTORNO |
| FRONTEND | PASS |
| CONFLICTOS REALES | 0 |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| RAMA CENTRAL MODIFICADA | NO |
| MAIN | NO MODIFICADO |
| V1 | NO MODIFICADA |
| MERGE | NO |

**VEREDICTO:** **CANDIDATA TÉCNICA LISTA PARA FASE 2**

---

## SHAs para integración posterior (Fase 2 oficial)

Cuando se autorice el cableado final sobre la rama central de convergencia:

| Pieza | SHA en ensayo |
|-------|---------------|
| BACKEND | `1028187cb0f70a536ea7ba80b31dc74ae93a7ce4` |
| FRONTEND | `aaf8881c95cda41b289ffca9e737b68ce9918c79` |
| PRUEBAS | `ec44052c4ef5b02e0a4b2ae9f1b539c95a05ade9` |

Alternativa equivalente: cherry-pick directo de los SHAs fuente validados en rama limpia (`24a0e0e`, `f9155fb`, `a52db5a`) si Fase 2 parte del mismo `FASE1_HEAD_REAL`.

---

## Restricciones respetadas

- Rama central `cursor/convergencia-final-post-v1-integracion` **no modificada**
- Sin merge, sin tag, sin migraciones nuevas
- Sin wiring de las otras 13 integraciones CC (1270, 1260, etc.)
- Sin segundo dashboard
