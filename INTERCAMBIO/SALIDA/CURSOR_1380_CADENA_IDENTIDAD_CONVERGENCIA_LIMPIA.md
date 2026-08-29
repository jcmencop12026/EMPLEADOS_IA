# EMPLEADOS IA — Cadena identidad convergencia limpia (1300 → 1370 → 1380)

**Agente:** A (Cursor Cloud)  
**Fecha:** 2026-08-29  
**Estrategia:** Replay funcional controlado sobre base oficial post-V1 — **sin merge** de tips originales.

---

## Base y rama

| Campo | Valor |
|-------|-------|
| **BASE** | `eb229806136e29acddc0f592b5f017f5c3cb2958` (`cursor/1250-convergencia-final-post-v1`) |
| **RAMA** | `cursor/1380-identidad-convergencia-limpia` |
| **HEAD** | `8f0b3adc1380fd41fcefb109ba4438921a75d5f6` |

---

## Commits funcionales (replay limpio)

| Bloque | Commit replay | Commit original (referencia) |
|--------|---------------|------------------------------|
| **1300** MFA / seguridad avanzada | `d0ab18e21077df7fadf7e75d7dd169b753a66a12` | `09194d8f281a1506d694844dead43e5ee93849e6` |
| **1370** Identidad empresarial SSO | `dd166a353cba3a84ae179eb0a004b9f2bf8f957e` | `3c545f64fe06569ecadbfa8523d65af798d472e3` |
| **1380** Aprovisionamiento SCIM 2.0 | `e57360d675859aa97f76c76f03676692499633a1` | `a1c3319e87a4bd17279ab3b4756cca006208e932` |

> Commit adicional de integración de tests: `8f0b3adc1380fd41fcefb109ba4438921a75d5f6` (aislamiento credenciales bootstrap en `conftest`).

---

## Genealogía Alembic (una sola cabeza)

```
1250f1a2b3c4d
    ↓
1300a1b2c3d4e  (down_revision re-anclado desde 1250f)
    ↓
1370a1b2c3d4e
    ↓
1380a1b2c3d4e  (head)
```

Verificado:

- `alembic heads` → **1** cabeza: `1380a1b2c3d4e`
- `alembic history` → cadena lineal 1250f → 1300 → 1370 → 1380

---

## Preservación obligatoria (1230 / 1240 / 1250)

| Módulo | Preservado | Evidencia |
|--------|------------|-----------|
| **1230** Centro de Control | **SÍ** | `control_center` router en `main.py`; `tests/test_bloque_1230_centro_control.py` PASS |
| **1240** Inteligencia Externa | **SÍ** | `inteligencia_externa` router en `main.py`; `tests/test_inteligencia_externa_1240.py` PASS |
| **1250** Convergencia post-V1 | **SÍ** | `tests/test_convergencia_final_1250.py` PASS; merge `1250f` intacto |

**Diff vs eb22980:** 54 archivos tocados, **0 eliminaciones** (`git diff --diff-filter=D` vacío).

---

## Resolución de conflictos de alto riesgo

| Archivo | Resolución |
|---------|------------|
| `backend/app/main.py` | Conservados **todos** los routers (1230/1240/1250 + security/identidad/scim) |
| `backend/app/permissions.py` | Permisos 1240/1250 + `SECURITY_PERMISSIONS` + `IDENTITY_PERMISSIONS` |
| `backend/alembic/migration_ledger.json` | Cadena acumulativa hasta `1380a1b2c3d4e` |
| `backend/scripts/schema_repair.py` | `HEAD_REVISION = 1380a1b2c3d4e` |
| `frontend/App.tsx`, `AppShell.tsx`, `api.ts` | Rutas y APIs de identidad/SCIM sin quitar módulos previos |

---

## Resultados de verificación

```
EMPLEADOS IA — CADENA IDENTIDAD LIMPIA TERMINADA

BASE:
eb229806136e29acddc0f592b5f017f5c3cb2958

RAMA:
cursor/1380-identidad-convergencia-limpia

HEAD:
8f0b3adc1380fd41fcefb109ba4438921a75d5f6

COMMIT FUNCIONAL 1300:
d0ab18e21077df7fadf7e75d7dd169b753a66a12

COMMIT FUNCIONAL 1370:
dd166a353cba3a84ae179eb0a004b9f2bf8f957e

COMMIT FUNCIONAL 1380:
e57360d675859aa97f76c76f03676692499633a1

1300:
PASS

1370:
PASS

1380:
PASS

SUPERADMIN:
PASS

1230 PRESERVADO:
SI

1240 PRESERVADO:
SI

1250 PRESERVADO:
SI

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1380a1b2c3d4e

SQLITE ROUNDTRIP:
PASS

POSTGRESQL ROUNDTRIP:
PASS

TESTS:
126 passed, 0 failed (suite acumulativa identidad + RBAC + multiempresa + 1230/1240/1250 + migraciones)

FRONTEND:
PASS

P0:
0

P1:
0

P2:
1

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

## P2 conocido

| ID | Descripción |
|----|-------------|
| P2-1 | **SCIM rate limiting en memoria** (`_scim_rate_store` en `scim_auth_service.py`). Endurecer antes de despliegue horizontal multi-réplica (Redis/BD compartida). No bloquea convergencia ni pruebas actuales. |

---

## Pruebas ejecutadas

```bash
PYTHONPATH=backend:. pytest \
  tests/test_bloque_1300_seguridad_avanzada.py \
  tests/test_identidad_1370.py \
  tests/test_scim_1380.py \
  tests/test_migration_control.py \
  tests/test_security_rbac_v1.py \
  tests/test_multitenant_v1.py \
  tests/test_bloque_1230_centro_control.py \
  tests/test_inteligencia_externa_1240.py \
  tests/test_convergencia_final_1250.py \
  tests/test_admin_840b_v3.py::test_migration_roundtrip_upgrade_downgrade_upgrade \
  -q

cd frontend && npm run build
```

PostgreSQL roundtrip: `upgrade head → downgrade a840c4d5e6f7 → upgrade head` en BD `empleados_ia_identidad_test` (socket local).

---

## Restricciones respetadas

- NO merge/rebase de ramas originales 1300/1370/1380
- NO V1 / e8cb853 / main / PR #32 / 1330 / 1350 / 1360 / bloques comerciales
- NO `git add .`
- Ramas originales no modificadas

---

## Notificación

**EMPLEADOS IA. Cadena de identidad preparada para convergencia.**
