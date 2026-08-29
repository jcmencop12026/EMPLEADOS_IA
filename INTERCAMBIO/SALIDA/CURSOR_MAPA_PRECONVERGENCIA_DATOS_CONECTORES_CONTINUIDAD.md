# CURSOR — Mapa preconvergencia: Datos + Conectores + Continuidad

## Resumen ejecutivo

Análisis **solo lectura** para incorporar **1330**, **1350 limpio** y **1360** a la futura convergencia integral sobre la base post-V1 oficial. **No se ha modificado código**, **no merge**, **no cherry-pick**.

**Hallazgo crítico:** la rama **1330 actual** no desciende de `eb229806`; requiere la misma estrategia de **rama limpia** que ya aplicó 1350. **1350 limpio** y **1360** descienden correctamente de la base oficial.

---

## SHA verificados en origin

| Referencia | Rama | SHA | Estado |
|------------|------|-----|--------|
| Base post-V1 | `cursor/1250-convergencia-final-post-v1` | `eb229806136e29acddc0f592b5f017f5c3cb2958` | OK |
| 1330 | `cursor/1330-integraciones-reales-conectores` | `5271ae54f62113b231b20541700e102c6dca3320` | OK |
| 1350 limpio | `cursor/1350-gobierno-datos-convergencia-limpia` | `78493e60a604f492f9ff9e31a9723700f06e67ef` | OK |
| 1360 | `cursor/1360-continuidad-resiliencia` | `3edc6370488edf3441268b40fde6954f93767ff9` | OK |

---

## 1. Genealogía Git real vs `eb229806`

### Merge-base y commits exclusivos

| Rama | Merge-base con `eb229806` | Commits `eb229806..HEAD` | Genealogía |
|------|---------------------------|---------------------------|------------|
| **1350 limpio** | `eb229806` | 2 | **Limpia** — directa desde base oficial |
| **1360** | `eb229806` | 1 | **Limpia** — directa desde base oficial |
| **1330** | `4c03cbe` (V1 traceability R2) | 3 | **Antigua** — no incluye convergencia 1200–1250 |

### Commits exclusivos por bloque (vs `eb229806`)

#### 1330 — clasificación

| Commit | Clase | Descripción |
|--------|-------|-------------|
| `5271ae5` | **A. Funcional 1330** | Integraciones reales y conectores |
| `38f7b7d` | **E. Heredado 1120** | Señales reales, ingesta (no es 1330) |
| `5eaad7e` | **B. Documentación 1120** | Entregable 1120 |

**Commit funcional 1330 aislado:** solo `5271ae5` (24 archivos vs padre `38f7b7d`).

#### 1350 limpio

| Commit | Clase | Descripción |
|--------|-------|-------------|
| `3d5bf04` | **A. Funcional 1350** | Gobierno de datos completo |
| `78493e6` | **B. Documentación** | Entregable convergencia limpia |

**Fuente técnica obligatoria:** rama limpia @ `78493e60`. **No** usar `1250a`, `6352836`, `ceedde5`, PR #52.

#### 1360

| Commit | Clase | Descripción |
|--------|-------|-------------|
| `3edc637` | **A. Funcional 1360** | Continuidad, resiliencia y recuperación |

### Lo que 1330 **no tiene** respecto a `eb229806`

La rama 1330 carece del bloque convergencia post-V1 (migraciones y módulos):

- `1200`, `1210`, `1220`, `1240`, `1250a`, `1250b`, `1250f`
- Centro de Control (1230), inteligencia externa (1240), línea base, valoración, diagnósticos
- Fix certificado migración `1110` en rama oficial (1330 tiene versión distinta de `1120`)

**Integrar 1330 sin limpieza reintroduciría regresión en `1120a1b2c3d4e`** (elimina `FK_PROACTIVE_SIGNALS_SOURCE` y `batch_alter_table` con nombre de FK que `eb229806` ya corrige).

---

## 2. Archivos compartidos y conflictos

### Archivos tocados vs `eb229806`

| Rama | Archivos en diff |
|------|------------------|
| 1330 | 96 |
| 1350 limpio | 20 |
| 1360 | 18 |

### Intersección (todos los módulos)

Archivos de **integración** compartidos (conflicto mecánico al fusionar):

- `backend/alembic/migration_ledger.json`
- `backend/app/main.py`
- `backend/app/permissions.py`
- `backend/scripts/schema_repair.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/AppShell.tsx`
- `frontend/src/auth/permissions.ts`
- `tests/conftest.py`

### Simulación de conflictos (`git merge-tree`)

| Pareja | Archivos con marcadores `<<<<<<<` |
|--------|-----------------------------------|
| **1350 + 1360** | **6** |
| **1350 + 1330** | **12** |
| **1360 + 1330** | **12** |
| **eb229806 + 1330** | **12** |

#### 1350 + 1360 — conflictos reales (6)

1. `backend/alembic/migration_ledger.json`
2. `backend/app/main.py`
3. `backend/app/permissions.py`
4. `backend/scripts/schema_repair.py`
5. `frontend/src/api.ts`
6. `tests/conftest.py`

Resolución prevista (no aplicada): fusionar routers/modelos de ambos; `HEAD_REVISION` y `baseline_head` → cabeza convergida; permisos `DATOS_*` + `CONTINUIDAD_*` + `INCIDENTES_*` + `BACKUPS_*`.

#### 1330 + cualquier rama oficial — conflictos reales (12)

Los 6 anteriores más:

7. `frontend/src/App.tsx`
8. `frontend/src/AppShell.tsx`
9. `frontend/src/auth/permissions.ts`
10. `backend/alembic/versions/1120a1b2c3d4e_senales_reales_deteccion.py` (**regresión 1120**)
11. `tests/test_migration_control.py`
12. `INTERCAMBIO/SALIDA/CURSOR_1120_SENALES_REALES_DETECCION_PROACTIVA.md`

### Archivos exclusivos (sin conflicto entre módulos)

| Módulo | Archivos clave exclusivos |
|--------|---------------------------|
| **1330** | `integration_*`, `routers/integraciones.py`, `schemas_integration.py`, `integration_service.py`, `integration_executors.py`, páginas `Integracion*`, `test_integraciones_1330.py`, migración `1330a1b2c3d4e` |
| **1350** | `governance_*`, `routers/governance.py`, `GobernanzaDatosPage.tsx`, `test_governance_1350.py`, migración `1350a1b2c3d4e` |
| **1360** | `continuidad_*`, `routers/continuidad.py`, `ContinuidadPage.tsx`, `test_continuidad_1360.py`, migración `1360a1b2c3d4e` |

---

## 3. Modelos y tablas

### Sin tablas compartidas entre módulos

| Módulo | Prefijo tablas | Cantidad |
|--------|----------------|----------|
| 1330 | `integration_*` | 3 |
| 1350 | `gov_*` | 17 |
| 1360 | `cont_*` | 20 |

No hay colisiones de nombre de tabla ni FK cruzadas **hoy** (integración runtime pendiente de convergencia).

### Riesgos FK / nombres (Alembic)

- **1330:** `down_revision = 1120a1b2c3d4e` crea rama paralela a `1220/1240/1250*` — **riesgo alto** si no se reparenta.
- **1350 y 1360:** ambos `down_revision = 1250f1a2b3c4d` — ramas gemelas; requiere **merge revision** o reparent de uno sobre el otro.
- **1120 en 1330:** conflicto de contenido con fix oficial — **no aceptar** versión 1330 de ese archivo.

---

## 4. Routers / API

| Módulo | Prefijo API | Endpoints principales |
|--------|-------------|----------------------|
| 1330 | `/api/integraciones` | catálogo, conectores CRUD, probar, ejecutar, salud, webhook |
| 1350 | `/api/gobierno-datos` | dashboard, catálogo, clasificaciones, retención, accesos, solicitudes, hallazgos |
| 1360 | `/api/continuidad` | tablero, servicios, backups, incidentes, SLO, planes, alertas |

Sin colisión de rutas. Integración en `main.py` es el punto de fusión.

---

## 5. RBAC / permisos

| Módulo | Conjunto de permisos |
|--------|----------------------|
| 1330 | `integraciones.view`, `create`, `configure`, `test`, `execute`, `manage_secrets` |
| 1350 | `datos.view`, `classify`, `manage_policy`, `export`, `audit`, `requests`, `retention` |
| 1360 | `continuidad.view`, `manage`, `activate`, `test`; `incidentes.*`; `backups.*` |

Fusión en `permissions.py` y `ROLE_PERMISSIONS_FALLBACK` — conflicto real al combinar 1350+1360; añadir `INTEGRATION_*` al integrar 1330.

---

## 6. Auditoría / observabilidad

| Módulo | Mecanismo |
|--------|-----------|
| 1330 | `write_audit` en conector (crear, editar, probar, ejecutar); health/circuit breaker en modelo |
| 1350 | `gov_access_logs`, hallazgos, exportaciones, auditoría en servicio |
| 1360 | `cont_auditoria`, tablero, alertas, post-incidentes |

**Compartido:** tabla global `audit` vía `write_audit`. Sin conflicto de esquema; coordinación de acciones de auditoría en runtime al cablear integraciones.

---

## 7. Frontend

### Rutas

| Módulo | Rutas |
|--------|-------|
| 1330 | `/integraciones`, `/integraciones/nueva`, `/integraciones/:connectorId` |
| 1350 | `/gobernanza-datos` |
| 1360 | `/continuidad` |

### Menú / sidebar

- 1330: entrada `/integraciones`
- 1350: entrada `/gobernanza-datos`
- 1360: entrada `/continuidad`

Rutas ortogonales; conflicto probable solo al fusionar `App.tsx` / `AppShell.tsx` (añadir las tres entradas).

### Permisos de vistas (`auth/permissions.ts`)

- `/integraciones` → `integraciones.view`
- `/gobernanza-datos` → `datos.view`
- `/continuidad` → `continuidad.view`

---

## 8. Interfaz 1330 ↔ 1350

### Estado actual

- **1350 preparado:** `GovernanceConnectorAdapter.get_resource_policy()` y `ConnectorPolicyView` en `governance_adapters.py`.
- **1330 no cableado:** `integration_service.py` no invoca governance; tiene catálogo propio y circuit breaker interno.

### Convergencia prevista (no implementada)

| Aspecto | 1350 provee | 1330 consumiría |
|---------|-------------|-----------------|
| Clasificación | `gov_classification_levels`, catálogo | Política por recurso/conector |
| Salida a externos | `gov_provider_policies`, minimización | Antes de ejecutar conector |
| Retención | `gov_retention_policies` | Ciclo de vida de ejecuciones/webhooks |
| Auditoría | `gov_access_logs`, exportaciones | Registrar ejecuciones sensibles |
| Enmascaramiento | `governance_masking` | Payload salida/entrada |

**Orden lógico:** integrar **1350 antes de 1330** para cablear adaptadores en `integration_service`.

---

## 9. Interfaz 1330 ↔ 1360

### Estado actual

- **1330:** `get_health()`, circuit breaker (`circuit_open_until`, `consecutive_failures`), endpoint `/conectores/{id}/salud`.
- **1360 preparado:** `integracion_1330_prep.reportar_salud` → `/api/continuidad/servicios/{id}/estado`; `reportar_salud` en servicio.

### Convergencia prevista

| Aspecto | 1330 | 1360 |
|---------|------|------|
| Health | Salud por conector | Servicios críticos, SLO, disponibilidad |
| Fallos | Circuit breaker local | Incidentes, modo degradado, fallback |
| Contingencia | — | Planes, activaciones, runbooks |
| Recuperación | Reintentos en ejecución | Restore pruebas, post-incidentes |

Cableado bidireccional pendiente; sin conflicto de esquema.

---

## 10. Interfaz 1350 ↔ 1360

### Estado actual

- **1350:** retención, legal hold, exportación, disposición de datos.
- **1360:** `cont_backup_politicas`, ejecuciones, verificaciones, restores.

### Convergencia prevista

| Aspecto | 1350 | 1360 |
|---------|------|------|
| Retención | `gov_retention_policies` | Políticas backup alineadas a disposición |
| Legal hold | `gov_legal_holds` | Bloquear purge/restore según hold |
| Recuperación | Solicitudes de datos | `cont_restore_pruebas`, verificaciones |
| Protección | Clasificación, enmascaramiento | Datos en backups según sensibilidad |

Sin FK cruzadas hoy; integración de negocio en fase de convergencia.

---

## 11. Alembic — mapa exacto

### Revisiones

| Revision | Rama origen | `down_revision` actual | Head en rama |
|----------|-------------|------------------------|--------------|
| `1330a1b2c3d4e` | 1330 (antigua) | `1120a1b2c3d4e` | Sí (`1330` branch) |
| `1350a1b2c3d4e` | 1350 limpio | `1250f1a2b3c4d` | Sí |
| `1360a1b2c3d4e` | 1360 | `1250f1a2b3c4d` | Sí |

### Cabecera oficial base (`eb229806`)

- **1 head:** `1250f1a2b3c4d`

### Cabezas resultantes al incorporar sin merge revision

| Escenario | Heads | Revisiones head |
|-----------|-------|-----------------|
| +1350 limpio | 1 | `1350a1b2c3d4e` |
| +1360 | 1 | `1360a1b2c3d4e` |
| +1350 +1360 (sin merge) | **2** | `1350a1b2c3d4e`, `1360a1b2c3d4e` |
| +1330 rama actual (sin limpieza) | **2+** | `1330a1b2c3d4e` + head oficial divergente |
| + los tres sin limpieza | **3** | `1330a1b2c3d4e`, `1350a1b2c3d4e`, `1360a1b2c3d4e` |

### Merge revision necesaria

**SÍ** — al menos:

1. **Merge 1350 + 1360** (hijos de `1250f1a2b3c4d`) → 1 head intermedio.
2. **Reparent o merge de 1330** tras preparar rama limpia (`down_revision` → head convergido, no `1120`).

**NO crear** merge revision en este análisis.

### Orden Alembic más seguro (propuesta)

**Opción A — lineal (recomendada tras ramas limpias):**

```
1250f1a2b3c4d → 1350a1b2c3d4e → 1360a1b2c3d4e → 1330a1b2c3d4e
```

(reparent `1360` y `1330` en convergencia; no aplicado ahora)

**Opción B — merge revision:**

```
1250f → 1350 ─┐
1250f → 1360 ─┴→ MERGE_X → 1330 (reparentado)
```

### Riesgos migración

| Riesgo | Severidad | Mitigación prevista |
|--------|-----------|---------------------|
| Rama 1330 desde `1120` | Alta | Rama limpia cherry-pick `5271ae5` sobre `eb229806` |
| Regresión `1120` | Alta | Conservar archivo de `eb229806` |
| Heads gemelas 1350/1360 | Media | Merge revision o reparent |
| Tablas `integration_*` vs `gov_*` vs `cont_*` | Baja | Sin colisión de nombres |

---

## 12. Estrategia de integración propuesta

### Clasificación de conflictos

| Tipo | Cantidad | Detalle |
|------|----------|---------|
| **CONFLICTO REAL** | **12** | Archivos con conflictos verificados al fusionar con rama 1330 actual; **6** al fusionar solo 1350+1360 |
| **CONFLICTO PROBABLE** | **3** | `App.tsx`, `AppShell.tsx`, `auth/permissions.ts` — ortogonales en rutas; conflicto al añadir 1330 o si fusión no manual |
| **SIN CONFLICTO** | **47+** | Archivos exclusivos de cada módulo (backend/frontend/tests) |
| **MERGE ALEMBIC NECESARIO** | **SÍ** | 1350∩1360 obligatorio; 1330 tras limpieza |

### Orden recomendado de integración

1. **Preparar 1330 limpio** desde `eb229806` (cherry-pick solo `5271ae5`; `down_revision → 1250f1a2b3c4d`; sin commits 1120).
2. **Integrar 1350 limpio** (rama ya lista @ `78493e60`).
3. **Integrar 1360** — resolver 6 conflictos mecánicos de integración.
4. **Merge revision Alembic** 1350 + 1360 → 1 head.
5. **Integrar 1330 limpio** — cablear `GovernanceConnectorAdapter`; reportar salud a continuidad.
6. **Reparent 1330** bajo head convergido (o segunda merge revision si se mantiene orden 1350→1360→1330 lineal).

### Resoluciones previstas (no aplicadas)

| Archivo | Resolución |
|---------|------------|
| `main.py` | Incluir routers `governance`, `continuidad`, `integraciones` + modelos |
| `permissions.py` | Unir `DATOS_*`, `CONTINUIDAD_*`, `INTEGRATION_*`, etc. |
| `migration_ledger.json` | Todas las revisiones protegidas + `baseline_head` final |
| `schema_repair.py` | `HEAD_REVISION` = cabeza única post-merge |
| `api.ts` | Secciones API de los tres módulos |
| `conftest.py` | Imports de los tres `*_models` |
| `1120 migration` | **Siempre versión `eb229806`** |

---

## 1350 — regla obligatoria

| Requisito | Cumplido en análisis |
|-----------|----------------------|
| Fuente: `cursor/1350-gobierno-datos-convergencia-limpia` @ `78493e60` | **SÍ** |
| No usar 1250a / 6352836 / ceedde5 / PR #52 | **SÍ** |
| No duplicar fixes 1110/1120 | **SÍ** |
| 1350 heredado excluido | **SÍ** |

---

## SALIDA

```
EMPLEADOS IA — MAPA DATOS/CONECTORES/CONTINUIDAD TERMINADO

BASE:
eb229806136e29acddc0f592b5f017f5c3cb2958

1330:
5271ae54f62113b231b20541700e102c6dca3320

1350 LIMPIO:
78493e60a604f492f9ff9e31a9723700f06e67ef

1360:
3edc6370488edf3441268b40fde6954f93767ff9

COMMITS EXCLUSIVOS:
1330: 5271ae5 (funcional); 38f7b7d+5eaad7e (1120 heredado, excluir)
1350 limpio: 3d5bf04 (funcional), 78493e6 (doc)
1360: 3edc637 (funcional)

CONFLICTOS REALES:
12 (incluye 1330); 6 entre 1350+1360 solamente

CONFLICTOS PROBABLES:
3 (App.tsx, AppShell.tsx, auth/permissions.ts al integrar 1330)

ALEMBIC HEADS RESULTANTES:
3 (sin merge revision y sin reparent 1330)

MERGE REVISION NECESARIA:
SI

ORDEN RECOMENDADO:
1330 limpio (prep) → 1350 limpio → 1360 → merge Alembic 1350+1360 → 1330 limpio (cableado)

1350 HEREDADO EXCLUIDO:
SI

MODIFICACIONES:
0

VEREDICTO:
REQUIERE REVISIÓN (rama 1330 debe limpiarse como 1350 antes de convergencia integral)
```

---

*Análisis generado sin modificar código, sin merge, sin migraciones nuevas.*
