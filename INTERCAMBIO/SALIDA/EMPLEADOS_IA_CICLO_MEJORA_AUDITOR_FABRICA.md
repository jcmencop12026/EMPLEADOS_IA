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

## 11. Salida final

```
EMPLEADOS IA — CICLO AUDITOR → FÁBRICA TERMINADO

RAMA: cursor/ciclo-auditor-fabrica-dec7
HEAD: 817f5018ef234a31591c6d64d04e7db1f2277b34

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
