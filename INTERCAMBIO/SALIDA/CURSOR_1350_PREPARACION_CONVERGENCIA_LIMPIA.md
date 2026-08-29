# CURSOR 1350 — Preparación convergencia limpia

## Resumen ejecutivo

Rama limpia de Gobierno de Datos (1350) reconstruida directamente sobre la base post-V1 oficial `eb229806`, incorporando únicamente la funcionalidad propia del bloque 1350 sin duplicar fixes heredados 1110/1120 ni genealogía de `6352836` / `ceedde5`.

---

## Genealogía y clasificación de commits

### Base oficial

| Campo | Valor |
|-------|-------|
| Rama | `cursor/1250-convergencia-final-post-v1` |
| SHA | `eb229806136e29acddc0f592b5f017f5c3cb2958` |
| Alembic head base | `1250f1a2b3c4d` |

### Rama 1350 original (genealogía antigua — no usada como base)

| Rama | HEAD | Notas |
|------|------|-------|
| `cursor/1350-gobierno-datos-privacidad` | `3216b7d` | Base `6352836` (1250a) |
| `cursor/1350a-recert-migrations` | `ceedde5` | Incluye fixes 1110/1120 redundantes |

### Clasificación de commits 1350

| Clase | Commits / contenido | Incluido en rama limpia |
|-------|---------------------|-------------------------|
| **A. Funcionalidad 1350** | `a17cb6c` — models, schemas, service, masking, adapters, router, UI, integración main/permissions | **SÍ** (cherry-pick → `3d5bf04`) |
| **B. Documentación 1350** | `b27aea5`, `3216b7d` — actualizaciones de entregable GOBIERNO_DATOS | **NO** (solo doc funcional incluida en cherry-pick) |
| **C. Tests 1350** | `test_governance_1350.py` (28 tests) en `a17cb6c` | **SÍ** |
| **D. Migración 1350** | `1350a1b2c3d4e_data_governance_1350.py` | **SÍ** (`down_revision` corregido a `1250f1a2b3c4d`) |
| **E. Fixes heredados 1110/1120** | Solo en `ceedde5` / ya en `eb229806` | **NO** |
| **F. Cambios ajenos / base antigua** | Eliminación 1240/control_center/inteligencia_externa del diff vs eb229806 | **NO** |

### Commits funcionales 1350 identificados

1. `a17cb6c` — `feat(1350): gobierno de datos, privacidad, retención y control de acceso`
2. Rama limpia: `3d5bf04` — mismo mensaje, cherry-pick con fusión de integración sobre base oficial

---

## Rama limpia

| Campo | Valor |
|-------|-------|
| Rama | `cursor/1350-gobierno-datos-convergencia-limpia` |
| HEAD | `3d5bf04dd9f42b941c5c113c3e0b81221a9adb8d` |
| Base | `eb229806136e29acddc0f592b5f017f5c3cb2958` |
| Commits sobre base | 1 |

### Archivos modificados respecto a `eb229806` (solo 1350 + integración)

- `backend/alembic/versions/1350a1b2c3d4e_data_governance_1350.py` (nuevo)
- `backend/alembic/migration_ledger.json`
- `backend/app/governance_models.py` (nuevo)
- `backend/app/routers/governance.py` (nuevo)
- `backend/app/schemas_governance.py` (nuevo)
- `backend/app/services/governance_*.py` (nuevo)
- `backend/app/main.py` — añade governance sin quitar inteligencia_externa/control_center
- `backend/app/permissions.py` — DATOS_PERMISSIONS + permisos existentes
- `backend/scripts/schema_repair.py` — HEAD `1350a1b2c3d4e`
- `frontend/src/pages/GobernanzaDatosPage.tsx` (nuevo)
- `frontend/src/App.tsx`, `AppShell.tsx`, `api.ts`, `auth/permissions.ts`
- `tests/test_governance_1350.py` (nuevo)
- `tests/conftest.py`
- `INTERCAMBIO/SALIDA/CURSOR_1350_GOBIERNO_DATOS_PRIVACIDAD.md` (nuevo)

**Sin cambios** en `1110a1b2c3d4e_finops_traceability_1110.py` ni `1120a1b2c3d4e_senales_reales_deteccion.py`.

---

## Migración Alembic

| Campo | Valor |
|-------|-------|
| Revision ID | `1350a1b2c3d4e` |
| down_revision | `1250f1a2b3c4d` |
| Alembic heads | 1 |
| Alembic head | `1350a1b2c3d4e` |

---

## Validación roundtrip

| Prueba | Resultado |
|--------|-----------|
| SQLite upgrade → downgrade → upgrade | **PASS** |
| PostgreSQL upgrade → downgrade → upgrade | **PASS** |

Errores históricos **no reproducidos**:

- `Constraint must have a name`
- `NotImplementedError` SQLite ALTER CONSTRAINT

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| `tests/test_governance_1350.py` | **28 passed** |
| Regresión `pytest tests/` | **774 passed, 0 failed, 2 skipped** |
| `test_migration_roundtrip_upgrade_downgrade_upgrade` | **PASS** |
| Frontend `npm run build` | **PASS** |
| `npm audit --audit-level=high` | **0 vulnerabilities** |

Entorno de pruebas: `env -u BOOTSTRAP_ADMIN_USERNAME -u BOOTSTRAP_ADMIN_PASSWORD` con SQLite temporal o PostgreSQL `127.0.0.1:55433`.

---

## Control funcional 1350

| Capacidad | Estado |
|-----------|--------|
| Clasificación de datos | PASS |
| Catálogo | PASS |
| Linaje | PASS |
| Políticas salida IA/proveedores | PASS |
| Minimización | PASS |
| Enmascaramiento | PASS |
| Seudonimización | PASS |
| Anonimización | PASS |
| Retención | PASS |
| Legal hold | PASS |
| Solicitudes de datos | PASS |
| Exportación | PASS |
| Producción/pruebas/sintéticos | PASS |
| Jerarquía de políticas | PASS |
| Riesgo determinista | PASS |
| Acciones correctivas | PASS |
| Auditoría | PASS |
| RBAC | PASS |
| Multiempresa | PASS |
| Interfaz española | PASS |
| Dashboard/API | PASS |
| Interfaces preparadas 1270/1330 (sin integrar) | PASS |

---

## Auditoría P0/P1/P2

| Nivel | Cantidad |
|-------|----------|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |

---

## Dependencias excluidas

| Elemento | Estado |
|----------|--------|
| Fixes 1110/1120 duplicados | **NO** |
| PR #52 (`ceedde5`) necesario | **NO** — fixes ya en base oficial |
| Base `6352836` / 1250a | **NO** |
| Módulos 1260–1340, 1360–1380 | **NO integrados** |
| V1 / e8cb853 / PR #32 | **NO** |
| main modificado | **NO** |
| merge | **NO** |

---

## SALIDA FINAL

```
EMPLEADOS IA — 1350 PREPARADO PARA CONVERGENCIA

BASE:
eb229806136e29acddc0f592b5f017f5c3cb2958

RAMA:
cursor/1350-gobierno-datos-convergencia-limpia

HEAD:
3d5bf04dd9f42b941c5c113c3e0b81221a9adb8d

COMMITS FUNCIONALES 1350 IDENTIFICADOS:
a17cb6c (origen), 3d5bf04 (rama limpia)

FIXES 1110/1120 DUPLICADOS:
NO

FUNCIONALIDAD 1350:
PASS

MIGRACIÓN 1350:
PASS

DOWN_REVISION:
1250f1a2b3c4d

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1350a1b2c3d4e

SQLITE ROUNDTRIP:
PASS

POSTGRESQL ROUNDTRIP:
PASS

TESTS 1350:
28 passed

REGRESIÓN:
774 passed, 0 failed, 2 skipped

FRONTEND:
PASS

P0:
0

P1:
0

P2:
0

PR #52 NECESARIO:
NO — la base oficial eb229806 ya contiene los fixes 1110/1120; esta rama no los duplica ni depende de ceedde5

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

*Generado: preparación convergencia limpia 1350 sobre base post-V1 oficial.*
