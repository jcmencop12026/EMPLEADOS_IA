# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 2 (1330 + WIRING 01–14)

**Tipo:** Integración incremental controlada
**Fecha:** 2026-08-29
**Agente:** GENERAL
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central antes** | `91cadf3889d7b5f6edd3d76f86b89cb947f94dbd` |
| **HEAD Tramo 2** | `800ae6af540b42b6165f7e82b522c2793cbe6c1b` (+ doc commit pendiente) |
| **Fuente B** | `cursor/1330-wiring-real-sobre-fase1` @ `2e160b57c0aa1b5f89ec8672615df6c6e8283a88` |
| **Método** | Cherry-pick selectivo sobre Tramo 1 — **sin merge bruto** |
| **main / V1** | NO modificados |

### Commits portados (funcionales)

| Orden | SHA central | Origen B | Contenido |
|-------|-------------|----------|-----------|
| 1 | `9a53fd1` | `1faef42` | Módulo 1330 completo (modelos, router, servicios, frontend, migración `1330a1`) |
| 2 | `7e1a0eb` | `dbac777` | Permisos PLATFORM + control_center restaurados |
| 3 | `450f627` | `7b5a786` | Migración `1330b1b2c3d4f` + enlace catálogo gobierno (WIRING-01) |
| 4 | `27b3a11` | `a56b1dd` | `integration_wiring.py` + cableado WIRING-02–14 |
| 5 | `800ae6a` | `2e160b5` | Tests wiring E2E + conftest bootstrap |

**No portados:** documentación histórica (`d4ba063`, docs en commits portados), commit vacío `18b23f4`.

---

## 1. Alembic

| Campo | Valor |
|-------|-------|
| **Head antes** | `1380a1b2c3d4e` |
| **Migraciones portadas** | `1330a1b2c3d4e` ← `1380a1b2c3d4e`; `1330b1b2c3d4f` ← `1330a1b2c3d4e` |
| **Reparent** | `1330a1` ya apuntaba a `1380a1` en rama B — **sin reparent adicional** |
| **Head después** | `1330b1b2c3d4f` |
| **Cabezas** | **1** |
| **schema_repair.HEAD_REVISION** | `1330b1b2c3d4f` |
| **SQLite roundtrip** | upgrade head → downgrade -1 → upgrade head **PASS** |

Cadena:

```
1380a1b2c3d4e → 1330a1b2c3d4e → 1330b1b2c3d4f (HEAD)
```

---

## 2. Componentes integrados

### 1330 — Integraciones reales

- Catálogo conectores (`integration_connectors`)
- Router `/api/integraciones/*`
- Permisos `integraciones.*` (6)
- Aislamiento multiempresa en lookups
- Frontend: `IntegracionesPage`, wizard, detalle
- Tests: `test_integraciones_1330.py`

### WIRING 01–14

| # | Punto | Implementación | Test focal |
|---|-------|----------------|------------|
| 01 | Catálogo/gobierno | `resolve_gov_catalog_entry` con `organization_id` | `test_wiring01`, `test_p1_01_catalog_cross_org_blocked` |
| 02 | Políticas | `preflight_governance_policy` | `test_wiring02_policy_denied_no_execution` |
| 03 | Preflight | integrado en ejecución | vía wiring02 |
| 04 | Ejecución + masking | `apply_output_masking` | `test_wiring04_masking_on_transform` |
| 05 | Auditoría acceso | `record_governance_access` | `test_wiring05_lineage_and_access` |
| 06 | Consentimiento post-ejecución | `integration_wiring` | flujo ejecución |
| 07 | Linaje | `record_governance_lineage` | `test_wiring05`, `test_idempotency_no_duplicate_lineage` |
| 08 | Resultado gobierno | acceso + audit | `test_wiring05` |
| 09 | Eventos/continuidad | `proveedor_ref_for_connector` | `test_wiring09_continuidad_proveedor_ref` |
| 10 | Continuidad/salud | `INTEGRACION_SALUD_RECUPERADA` | `test_wiring10_recovery_event` |
| 11 | Backup metadatos | metadata con `organization_id` | `test_wiring12` setup |
| 12 | Restore/privacidad | `RESTORE_BLOQUEADO_PRIVACIDAD` | `test_wiring12_restore_blocked_privacy` |
| 13 | Identidad/MFA | preflight MFA en wiring | integrado en servicio |
| 14 | Correlación cierre cadena | `correlation_id` en ejecución | `test_e2e_success_with_correlation` |

**Eventos nuevos certificados:** `INTEGRACION_SALUD_RECUPERADA`, `RESTORE_BLOQUEADO_PRIVACIDAD` — sin otros añadidos.

### Preservado (Fase 1 + Tramo 1)

1350, 1360, 1300, 1370, 1380, 1220 fix, Centro Control, 1240, P1-ID-01 — **sin regresión**.

### NO incorporado (Tramo 2)

- P1-ID-02 semántica HECHO/INFERENCIA (agente A)
- Vistas/comercial final (agente C)
- P1-ID-03 línea base (agente D)
- 1260/1270/1280/1290 chain
- **Cableado 1330 → Centro de Control** (pendiente tramo posterior)

`control_center_service.py` **no** referencia integraciones/wiring — CC preservado.

---

## 3. Validación diferencial

| Métrica | Antes (Tramo 1) | Después (Tramo 2) | Δ |
|---------|-----------------|-------------------|---|
| passed | 902 | **927** | +25 (tests nuevos 1330+wiring) |
| skipped | 4 | **4** | 0 |
| failed | 0 | **0** | 0 |
| errors | 0 | **0** | 0 |

**FALLOS NUEVOS INTRODUCIDOS: 0**
**ERRORES NUEVOS INTRODUCIDOS: 0**

Rama B cloud reportaba 151 failed + 40 errors — **resueltos en integración central** (causa: ensayo sobre base sin Tramo 1; cherry-pick sobre `91cadf3` elimina conflictos).

### Focales ejecutados

| Suite | Resultado |
|-------|-----------|
| `test_integraciones_1330` | PASS |
| `test_wiring_1330_fase1` (14 puntos) | **14/14 PASS** |
| 1350, 1360, 1300, 1370, 1380 | PASS |
| CC 1240 + P1-ID-01 + 1230 | PASS |
| 1220 (15 tests) | PASS |
| RBAC + multitenant + SUPERADMIN + V1 | PASS |
| Frontend `npm run build` | PASS |
| PostgreSQL | **PENDIENTE POR ENTORNO** |

### Idempotencia / multiempresa / privacidad

| Control | Resultado |
|---------|-----------|
| Multiempresa catálogo cross-org | PASS (`test_p1_01_catalog_cross_org_blocked`) |
| Multiempresa conector cross-org | PASS (`test_cross_org_connector_404`) |
| RESTORE_BLOQUEADO_PRIVACIDAD | PASS (`test_wiring12_restore_blocked_privacy`) |
| Idempotencia ejecución/linaje | PASS (`test_idempotency_no_duplicate_lineage`) |
| correlation_id | PASS (`test_e2e_success_with_correlation`) |

| Severidad | Conteo |
|-----------|--------|
| P0 | **0** |
| P1 | **0** |
| P2 | **0** |

---

## 4. Arranque para revisión visual

Sin cambios respecto Tramo 1. URLs:

- Login: http://127.0.0.1:5180/login
- Centro de Control: http://127.0.0.1:5180/ (sin cableado 1330 aún)
- **Integraciones (nuevo):** http://127.0.0.1:5180/integraciones

Usuario bootstrap dev: `admin` (contraseña según README proyecto — solo entorno local).

---

## SALIDA FINAL

```
EMPLEADOS IA — FASE 2 CENTRAL TRAMO 2 TERMINADO

BASE CENTRAL ANTES:
91cadf3889d7b5f6edd3d76f86b89cb947f94dbd

RAMA:
cursor/fase2-central-integracion

HEAD NUEVO:
800ae6af540b42b6165f7e82b522c2793cbe6c1b

1330:
PASS

WIRING 01–14:
14/14 PASS

1350:
PASS

1360:
PASS

1300:
PASS

1370:
PASS

1380:
PASS

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1330b1b2c3d4f

SQLITE:
PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

REGRESIÓN ANTES:
902 passed, 4 skipped, 0 failed

REGRESIÓN DESPUÉS:
927 passed, 4 skipped, 0 failed

FALLOS NUEVOS INTRODUCIDOS:
0

ERRORES NUEVOS INTRODUCIDOS:
0

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

PRIVACIDAD RESTORE:
PASS

IDEMPOTENCIA:
PASS

CORRELATION_ID:
PASS

CENTRO CONTROL PRESERVADO:
PASS

FRONTEND BUILD:
PASS

P0:
0

P1:
0

P2:
0

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE MAIN:
NO

VEREDICTO:
TRAMO 2 APTO
```

---

*Siguiente tramo: integrar piezas certificadas de A/C/D cuando estén listas, manteniendo rama ejecutable.*
