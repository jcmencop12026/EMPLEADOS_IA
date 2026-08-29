# CURSOR 1330 — Preparación convergencia limpia

## Resumen ejecutivo

Rama limpia del bloque **1330 Integraciones reales y conectores** reconstruida directamente sobre la base post-V1 oficial `eb229806`, incorporando únicamente el commit funcional `5271ae5` sin arrastrar genealogía 1120 (`38f7b7d`, `5eaad7e`).

---

## Clasificación de commits (verificada con Git)

| Clase | Commit | Incluido en rama limpia |
|-------|--------|-------------------------|
| **A. Funcional 1330** | `5271ae5` | **SÍ** (cherry-pick → `9fd0118`) |
| **B. Documentación 1330** | Incluida en `5271ae5` (`CURSOR_1330_INTEGRACIONES_REALES_CONECTORES.md`) | **SÍ** |
| **C. Tests 1330** | `test_integraciones_1330.py` (14 tests) en `5271ae5` | **SÍ** |
| **D. Migración 1330** | `1330a1b2c3d4e` | **SÍ** (`down_revision` → `1250f1a2b3c4d`) |
| **E. Heredado 1120** | `38f7b7d`, `5eaad7e` | **NO** |
| **F. Base vieja / ajenos** | Eliminación 1230/1240/1250, regresión 1120 | **NO** |

### Verificación `5271ae5` vs `38f7b7d`

- 24 archivos exclusivos de 1330.
- **0 líneas** de diff en `1120a1b2c3d4e_senales_reales_deteccion.py`.
- Cherry-pick seguro del commit funcional.

### Genealogía rama antigua (no usada)

| Rama | Merge-base con `eb229806` | Notas |
|------|---------------------------|-------|
| `cursor/1330-integraciones-reales-conectores` @ `5271ae54` | `4c03cbe` | Arrastra 1120 heredado |

---

## Rama limpia

| Campo | Valor |
|-------|-------|
| Rama | `cursor/1330-integraciones-convergencia-limpia` |
| HEAD | `9fd01184264d2a96e8b9347668d1eaa7b13e4bec` |
| Base | `eb229806136e29acddc0f592b5f017f5c3cb2958` |
| Commit origen funcional | `5271ae54f62113b231b20541700e102c6dca3320` |

### Diff vs `eb229806` (solo 1330)

23 archivos — backend integraciones, frontend páginas Integración, tests, ledger, integración en `main.py` / permisos / `api.ts`.

**Sin cambios** en:

- `1110a1b2c3d4e_finops_traceability_1110.py`
- `1120a1b2c3d4e_senales_reales_deteccion.py`

**Preservados** (presentes, no eliminados):

- `backend/app/routers/control_center.py` (1230)
- `backend/app/routers/inteligencia_externa.py` (1240)
- `backend/alembic/versions/1250f1a2b3c4d_merge_convergencia_final_post_v1.py` (1250)

---

## Migración Alembic

| Campo | Valor |
|-------|-------|
| Revision | `1330a1b2c3d4e` |
| down_revision | `1250f1a2b3c4d` |
| Alembic heads | 1 |
| Alembic head | `1330a1b2c3d4e` |

Tablas creadas: `integration_connectors`, `integration_executions`, `integration_webhook_events`.

---

## Funcionalidad 1330 conservada

| Capacidad | Estado |
|-----------|--------|
| Catálogo de conectores | PASS |
| API REST `/api/integraciones` | PASS |
| Tipos: API, archivos, SFTP, webhook, correo, eventos | PASS |
| Mapeo, validación, prueba de conexión | PASS |
| Salud, reintentos, circuit breaker | PASS |
| Idempotencia, SSRF/protecciones | PASS |
| Secret references | PASS |
| RBAC, multiempresa, auditoría | PASS |
| Interfaz española | PASS |
| Puente señales (`signal_ingestion_service`) | PASS |
| Preparación 1350/1360 (sin integrar) | Interfaces listas en diseño; cableado en convergencia |

---

## Validación

| Prueba | Resultado |
|--------|-----------|
| `tests/test_integraciones_1330.py` | **14 passed** |
| `tests/test_migration_control.py` + roundtrip SQLite | **PASS** |
| SQLite upgrade → downgrade → upgrade | **PASS** |
| PostgreSQL upgrade → downgrade → upgrade | **PASS** |
| Regresión `pytest tests/` | **760 passed, 0 failed, 2 skipped** |
| `test_bloque_1230_centro_control` + 1250c | **29 passed** |
| Frontend `npm run build` | **PASS** |
| `npm audit --audit-level=high` | **0 vulnerabilities** |

Errores históricos **no reproducidos**: `Constraint must have a name`, `NotImplementedError` SQLite ALTER CONSTRAINT.

---

## Auditoría P0/P1/P2

| Nivel | Cantidad |
|-------|----------|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |

---

## PR #48

**NO necesario para convergencia** en el sentido de genealogía/migraciones: la rama limpia sustituye la necesidad de mergear la rama antigua `cursor/1330-integraciones-reales-conectores` con su merge-base `4c03cbe`. PR #48 puede cerrarse tras adoptar esta rama en convergencia integral.

---

## SALIDA FINAL

```
EMPLEADOS IA — 1330 PREPARADO PARA CONVERGENCIA

BASE:
eb229806136e29acddc0f592b5f017f5c3cb2958

RAMA:
cursor/1330-integraciones-convergencia-limpia

HEAD:
9fd01184264d2a96e8b9347668d1eaa7b13e4bec

COMMIT FUNCIONAL 1330 ORIGEN:
5271ae54f62113b231b20541700e102c6dca3320

COMMITS HEREDADOS 1120 INCORPORADOS:
NO

FUNCIONALIDAD 1330:
PASS

MIGRACIÓN:
PASS

REVISION:
1330a1b2c3d4e

DOWN_REVISION:
1250f1a2b3c4d

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1330a1b2c3d4e

SQLITE ROUNDTRIP:
PASS

POSTGRESQL ROUNDTRIP:
PASS

TESTS 1330:
14 passed

REGRESIÓN:
760 passed, 0 failed, 2 skipped

FRONTEND:
PASS

1230 PRESERVADO:
SI

1240 PRESERVADO:
SI

1250 PRESERVADO:
SI

FIXES 1110/1120 PRESERVADOS:
SI

P0:
0

P1:
0

P2:
0

PR #48 NECESARIO PARA CONVERGENCIA:
NO — la rama limpia reemplaza la genealogía antigua; no depende de merge-base 4c03cbe ni commits 38f7b7d/5eaad7e

V1 MODIFICADA:
NO

MAIN MODIFICADO:
NO

MERGE:
NO

VEREDICTO:
APTO PARA CONVERGENCIA
```

---

*Generado: preparación convergencia limpia 1330 sobre base post-V1 oficial.*
