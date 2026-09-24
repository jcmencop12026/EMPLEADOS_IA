# EMPLEADOS IA — CICLO MEJORA AUDITOR → FÁBRICA

**Agente:** C
**Fecha:** 2026-08-29
**Rama:** `cursor/ciclo-auditor-fabrica-dec7`

## Fuentes certificadas integradas

| Módulo | Rama | HEAD fuente |
|--------|------|-------------|
| Fábrica MB-06 | `cursor/fabrica-empleados-ia-ciclo-vida` | `a5c518b` |
| Auditor MVP | `cursor/auditor-empleados-ia-mvp-deterministico` | `3d066ae` |
| Auditor → Mi Trabajo | `cursor/auditor-integracion-mi-trabajo` | `be761f6` |

**Fase2 central / main / V1:** NO modificados.

---

## 1. Arquitectura

```text
Empleado IA
  → Auditor (detecta / evalúa / recomienda)
  → Hallazgo ABIERTO
  → Mi Trabajo (presenta / asigna)
  → Decisión humana (iniciar mejora)
  → Fábrica (ejecuta con RBAC + guardas)
  → Prueba / reauditoría
  → Resultado clasificado + trazabilidad
```

Principios:

- El **Auditor NO modifica** empleados directamente.
- **Mi Trabajo NO amplía** privilegios; solo navega y registra intención.
- La **Fábrica ejecuta** únicamente con permisos reales (`employee.train`, `employee.publish`, etc.).
- **Recomendación ≠ ejecución** — `auto_execution_blocked: true` en contrato.

---

## 2. Componentes

| Capa | Archivo | Rol |
|------|---------|-----|
| Puente | `backend/app/services/auditor_factory_bridge.py` | Navegación, trazas, ejecución autorizada, reauditoría |
| Persistencia | `employee_improvement_traces` | Cadena auditoría → decisión → fábrica |
| API Auditor | `backend/app/routers/empleados_auditor.py` | `/contrato-fabrica`, `/iniciar-mejora`, `/ejecutar`, `/reauditar`, `/trazabilidad` |
| Mi Trabajo | `backend/app/services/trabajo_service.py` | Acción `revisar_fabrica` → ficha empleado con pestaña contextual |
| Fábrica | `employee_lifecycle_service.auditor_contract()` | Operaciones existentes reutilizadas |
| Frontend | `TrabajoPage` + `EmployeeDetailPage` | Sin vista principal nueva; navegación contextual |

---

## 3. Flujo operativo

1. Auditor ejecuta (`POST /api/empleados-auditor/ejecutar`) → hallazgo con `recommended_action`.
2. Mi Trabajo agrega ítem con acciones: Ver auditoría, Ver empleado, **Revisar en Fábrica**.
3. Usuario autorizado abre `/empleados/{id}?tab=...&finding_id=...&correlation_id=...`.
4. UI registra traza (`POST /hallazgos/{id}/iniciar-mejora`) — idempotente.
5. Usuario ejecuta acción en fábrica (`POST /mejoras/{trace_id}/ejecutar`) — valida permiso real.
6. Opcional: pruebas (`probar`), reauditoría (`reauditar`), comparación antes/después.
7. Resultado: `PENDIENTE_VALIDACION | MEJORADO | SIN_CAMBIO | EMPEORADO | NO_DETERMINADO`.

### Acciones de alto impacto

`publicar`, `rollback`, `retirar` requieren permisos específicos + guardas MB-06 (aprobación, certificación). Sin autoaprobación.

---

## 4. API puente

| Método | Ruta | Permiso mínimo |
|--------|------|----------------|
| GET | `/api/empleados-auditor/contrato-fabrica` | `auditor_empleados.view` |
| GET | `/api/empleados-auditor/hallazgos/{id}/accion-fabrica` | `auditor_empleados.view` |
| POST | `/api/empleados-auditor/hallazgos/{id}/iniciar-mejora` | `auditor_empleados.view` |
| POST | `/api/empleados-auditor/mejoras/{trace_id}/ejecutar` | permiso fábrica real |
| POST | `/api/empleados-auditor/mejoras/{trace_id}/reauditar` | `auditor_empleados.execute` |
| GET | `/api/empleados-auditor/mejoras/{trace_id}/trazabilidad` | `auditor_empleados.view` |

---

## 5. Trazabilidad

Cadena reconstruible en `employee_improvement_traces`:

`employee_id` · `audit_run_id` · `finding_id` · `recommendation` · `work_item_ref` · `correlation_id` · `factory_operation` · `version_id` · `approval_id` · `test_run_id` · `outcome_classification`

Sin secretos en respuestas API.

---

## 6. Idempotencia y concurrencia

- `iniciar-mejora`: clave única por org (`idempotency_key`).
- `ejecutar`: clave por operación en `evidence_json.exec_keys`.
- Traza abierta (`PENDING`/`IN_PROGRESS`) bloquea duplicados sobre mismo hallazgo.
- `IN_PROGRESS` por otro usuario → rechazo.

---

## 7. RBAC y multiempresa

- Ver hallazgo (`auditor_empleados.view`) ≠ ejecutar (`employee.train`, etc.).
- Cada operación valida permiso fábrica en `ejecutar_operacion_fabrica`.
- Aislamiento org en hallazgos, trazas y empleados — tests explícitos.

---

## 8. Alembic

| Revisión | Tipo |
|----------|------|
| `6b06a1b2c3d4e` | Fábrica MB-06 (existente) |
| `1400a1b2c3d4e` | Auditor MVP (existente) |
| `14b0c1d2e3f4` | **Merge** factory + auditor |
| `14b1c2d3e4f5` | **Puente** `employee_improvement_traces` |

**HEAD único:** `14b1c2d3e4f5`
Revisiones NO reutilizadas para nueva persistencia: `1390`, `1400`, `6b06` (solo como ancestros).

---

## 9. Tests

| Suite | Casos | Resultado |
|-------|-------|-----------|
| `test_auditor_factory_cycle.py` | 9 | PASS |
| `test_auditor_integracion_mi_trabajo.py` | 8 | PASS |
| `test_employee_auditor_mvp.py` | 12 | PASS |
| `test_bandeja_trabajo_humano.py` | 6 | PASS |
| `test_employee_lifecycle_factory_mb06.py` | 19 | PASS |
| `test_agent_factory_e2e.py` | 10 | PASS |
| `test_migration_control.py` | 6 | PASS |
| **Total focal** | **70** | **PASS** |
| `npm run build` | — | PASS |

---

## 10. Receta de port para General

```text
ORIGEN: cursor/ciclo-auditor-fabrica-dec7
BASE DESTINO: rama de integración vigente (NO fase2-central directo)

ARCHIVOS NUEVOS/MODIFICADOS CLAVE:
  backend/app/services/auditor_factory_bridge.py
  backend/app/employee_audit_models.py (EmployeeImprovementTrace)
  backend/app/routers/empleados_auditor.py (endpoints puente)
  backend/app/services/trabajo_service.py (revisar_fabrica)
  backend/alembic/versions/14b0c1d2e3f4_*.py
  backend/alembic/versions/14b1c2d3e4f5_*.py
  frontend/src/pages/EmployeeDetailPage.tsx (contexto auditor)
  tests/test_auditor_factory_cycle.py

ORDEN:
  1. Merge selectivo sobre base destino
  2. alembic upgrade head → 14b1c2d3e4f5
  3. pytest tests/test_auditor_factory_cycle.py + suites focales MB-06/Auditor/Mi Trabajo
  4. npm run build

NO PORTAR:
  Centro de Control (solo contrato portable en bridge)
  MB-07 FinOps (sin cambios)
```

---

## 11. Salida final (ciclo funcional)

```
EMPLEADOS IA — CICLO AUDITOR → FÁBRICA TERMINADO

RAMA: cursor/ciclo-auditor-fabrica-dec7
HEAD: 0de93ec5abf03670fc2e6d27635b3bc9314e8b39

AUDITOR RECOMIENDA: PASS
EJECUCIÓN AUTOMÁTICA BLOQUEADA: PASS
MI TRABAJO: PASS
CAPACITACIÓN: PASS
VERSIONADO: PASS
PRUEBAS: PASS
APROBACIÓN: PASS (guardas MB-06 preservadas)
PUBLICACIÓN: PASS (guardas MB-06 preservadas)
ROLLBACK: PASS
PAUSA: PASS
RETIRO: PASS
REAUDITORÍA: PASS
ANTES/DESPUÉS: PASS
IDEMPOTENCIA: PASS
CONCURRENCIA: PASS
TRAZABILIDAD: PASS
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS
SECRETOS: PASS
FRONTEND: PASS
REGRESIÓN: 70/70 PASS
ALEMBIC HEADS: 1
P0/P1/P2: 0/0/0
CENTRO CONTROL: NO MODIFICADO
MB-07: NO MODIFICADO
VEREDICTO: APTO PARA PORTAR
```

---

## 12. CERTIFICACIÓN FINAL DE PORTABILIDAD

**Fecha certificación:** 2026-08-29
**Receta detallada:** `INTERCAMBIO/SALIDA/EMPLEADOS_IA_RECETA_PORT_AUDITOR_FABRICA.md`

### 12.1 Inventario de dependencias

| Módulo | HEAD certificado | Commits funcionales exactos |
|--------|------------------|----------------------------|
| Mi Trabajo núcleo | `40e76bc` | `40e76bc` |
| Auditor MVP | `3d066ae` | `9fbe416`, `1033fcd` |
| Auditor → Mi Trabajo | `be761f6` | `599d69b` |
| Fábrica MB-06 | `a5c518b` | `6430da8`, `dccc40f`, `8759bb9` |
| Puente final | `0de93ec` | `d575d06` (merge selectivo), `817f501`, `0de93ec` |

**DEPENDENCIAS IDENTIFICADAS:** PASS

### 12.2 Grafo de dependencias — orden REAL

```text
Prerrequisitos central (head Alembic conocido)
  → Mi Trabajo (40e76bc)
  → Auditor MVP (9fbe416 + 1033fcd)     ─┐ paralelos Alembic desde mismo padre
  → Auditor → Mi Trabajo (599d69b)        │ (requiere 1 + 2)
  → Fábrica MB-06 (6430da8→8759bb9)     ─┘
  → Merge Alembic 14b0 (6b06 + 1400)
  → Puente 14b1 + código bridge (d575d06 selectivo + 817f501)
```

**ORDEN DE PORT:** PASS

**COMMITS EXACTOS:** PASS

### 12.3 Migraciones inventariadas

Revisiones presentes en rama para el ciclo:

| revision_id | down_revision (origen) | Único | Cabeza |
|-------------|------------------------|-------|--------|
| `6b06a1b2c3d4e` | `1330b1b2c3d4f` | SÍ | parcial |
| `1400a1b2c3d4e` | `1330b1b2c3d4f` | SÍ | parcial |
| `14b0c1d2e3f4` | `6b06` + `1400` | SÍ | merge |
| `14b1c2d3e4f5` | `14b0c1d2e3f4` | SÍ | **HEAD** |

**MIGRACIONES INVENTARIADAS:** PASS
**REVISION 6B06:** PASS
**REVISION 1400:** PASS
**REVISION 14B1:** PASS
**ALEMBIC HEADS:** 1

### 12.4 Colisiones revision_id

Comparación contra inventario accesible del repositorio:

| revision_id | En rama ciclo | Colisión |
|-------------|---------------|----------|
| `1390a1b2c3d4e` | NO (renombrado → 1400) | NO_APLICA |
| `1391a1b2c3d4e` | NO | NO_APLICA |
| `1400a1b2c3d4e` | SÍ (1 archivo) | SIN COLISIÓN |
| `1507a1b2c3d4e` | NO | NO_APLICA |
| `6b06a1b2c3d4e` | SÍ (1 archivo) | SIN COLISIÓN |
| `14b1c2d3e4f5` | SÍ (1 archivo) | SIN COLISIÓN |

**COLISIONES:** 0

### 12.5 Contrato del ciclo

```text
Auditor detecta → Mi Trabajo presenta → humano decide → Fábrica ejecuta
  → prueba → reauditoría → resultado clasificado → trazabilidad completa
```

- **RECOMENDACIÓN ≠ EJECUCIÓN:** `auto_execution_blocked: true` en contrato y API puente — **PASS**
- Cadena trazabilidad: `employee_id` · `audit_run_id` · `finding_id` · `work_item` · `decision` · `factory_operation` · `version_id` · `approval_id` · `test result` · `reaudit` · `correlation_id` — **PASS** (tabla `employee_improvement_traces`)

### 12.6 Clasificación antes/después

Estados soportados: `PENDIENTE_VALIDACION`, `MEJORADO`, `SIN_CAMBIO`, `EMPEORADO`, `NO_DETERMINADO`.

- `MEJORADO` solo con evidencia suficiente (comparación snapshots + reauditoría) — implementado en `auditor_factory_bridge._classify_outcome` — **PASS**
- Sin inferencia causal sin evidencia — **PASS**

### 12.7 No duplicación

Un solo workflow, una bandeja `/trabajo`, un `ApprovalRequest`, un Auditor, una Fábrica, un motor de pruebas MB-06, Knowledge `930a1` reutilizado — **PASS**

### 12.8 Seguridad revalidada

| Control | Resultado |
|---------|-----------|
| Multiempresa | PASS |
| RBAC (view ≠ execute) | PASS |
| SUPERADMIN | PASS |
| Secretos (no en API) | PASS |
| Idempotencia | PASS |
| Concurrencia | PASS |

### 12.9 Regresión y Alembic (evidencia 2026-08-29)

| Verificación | Resultado |
|--------------|-----------|
| Suite focal (60 tests core) | 60/60 PASS |
| `test_agent_factory_e2e.py` | 10/10 PASS |
| **Regresión total** | **70/70 PASS** |
| `alembic heads` | 1 (`14b1c2d3e4f5`) |
| SQLite upgrade head | PASS |
| SQLite downgrade -1 | PASS (tabla traces eliminada) |
| SQLite re-upgrade | PASS (tabla traces recreada) |
| Frontend `npm run build` | PASS |
| PostgreSQL | PENDIENTE POR ENTORNO (servidor accesible, credenciales no disponibles) |

### 12.10 Regla para General

- **NO** copiar ciegamente `down_revision = 1330b1b2c3d4f`
- **REPARENTAR** `6b06` y `1400` sobre cadena central real
- **PORTAR** `14b0` y `14b1` tras existir dependencias de tablas
- **NO PORTAR** arrastre CC/1220/1240 del merge `d575d06`
- Ver receta completa en `EMPLEADOS_IA_RECETA_PORT_AUDITOR_FABRICA.md`

**RECETA GENERAL:** LISTA

### 12.11 Alcance NO modificado

| Rama/módulo | Estado |
|-------------|--------|
| `cursor/fase2-central-integracion` | NO MODIFICADA |
| `main` | NO |
| `V1` | NO |
| MB-07 | NO |
| MB-11 | NO |
| Mesa de Ayuda | NO |
| Centro de Control | NO (solo contrato portable en bridge) |

---

## 13. SALIDA FINAL — PORTABILIDAD

```
EMPLEADOS IA — CICLO AUDITOR/FÁBRICA PORTABLE CERTIFICADO

RAMA:
cursor/ciclo-auditor-fabrica-dec7

HEAD:
0de93ec5abf03670fc2e6d27635b3bc9314e8b39

DEPENDENCIAS IDENTIFICADAS:
PASS

ORDEN DE PORT:
PASS

COMMITS EXACTOS:
PASS

MIGRACIONES INVENTARIADAS:
PASS

REVISION 6B06:
PASS

REVISION 1400:
PASS

REVISION 14B1:
PASS

COLISIONES:
0

ALEMBIC HEADS:
1

UPGRADE:
PASS

DOWNGRADE:
PASS

RE-UPGRADE:
PASS

RECOMENDACION ≠ EJECUCION:
PASS

TRAZABILIDAD:
PASS

ANTES/DESPUES:
PASS

IDEMPOTENCIA:
PASS

CONCURRENCIA:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

SECRETOS:
PASS

FRONTEND:
PASS

REGRESION:
70/70 PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

P0/P1/P2:
0/0/0

RECETA GENERAL:
LISTA

FASE2 CENTRAL:
NO MODIFICADA

MAIN:
NO

V1:
NO

VEREDICTO:
APTO PARA PORTAR
```
