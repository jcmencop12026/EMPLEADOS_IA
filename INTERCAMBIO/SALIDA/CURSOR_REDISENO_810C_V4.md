# CURSOR — Rediseño PR #6 / 810C v4

**Fecha:** 2026-08-24
**Estado:** REDISEÑADO Y LISTO PARA QA FINAL
**No declarado apto para merge**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| PR | #6 |
| Rama | `cursor/automations-scheduler-810` |
| HEAD anterior (auditado) | `80c1e6ab5b7f74f928b2ed3d53928b971a025ae0` |
| HEAD nuevo | `b33190a6d45df4cddb09753287a0fe5b69c04e28` |
| Commit | `feat(810c): v4 execution/materialization boundary redesign` |

---

## ARQUITECTURA ANTERIOR (v3)

```
RUN → Worker (Session completa) → commit_gated() en coordinator
     → timeout → invalidate_run_execution()
```

**Problema:** El worker recibía `Session` con autoridad de `commit()` y acceso a `get_bind()/connection()`. Un parche `commit_gated()` no impedía:

- `session.commit()` directo;
- SQL crudo vía conexión alternativa del engine;
- carrera sincronizada QA: **100/100 efectos tardíos** tras invalidación.

---

## CAUSA RAÍZ

La ejecución cancelable **poseía autoridad irrestricta** para confirmar efectos. `commit_gated` era una convención cooperativa, no una frontera arquitectónica.

---

## ARQUITECTURA NUEVA (v4)

```
USUARIO/ORQUESTADOR
  → RUN CONTROLADO (dispatcher)
  → WORKER AISLADO (WorkerExecutionSession — sin commit/bind)
  → flush_gated() — cambios en transacción NO confirmada
  → VALIDACIÓN generation + estado RUNNING (BD + memoria)
  → materialize_gated() — ÚNICO commit autorizado
  → _apply_run_result()

TIMEOUT/INVALID:
  → invalidate_run_execution() (BD primero, generation++)
  → controller.invalidate() → rollback sesiones worker + kill process tree
  → 0 efectos materializados
```

### Frontera DB

| Componente | Rol |
|------------|-----|
| `WorkerExecutionSession` | Proxy que bloquea `commit()`, `get_bind()`, `connection()` |
| `flush_gated()` | Flush validado en fase worker (sin commit) |
| `materialize_gated()` | Commit único tras validación dispatcher |
| `require_execution_allowed(db)` | Valida token memoria **+** estado BD |
| `RunFenceController` | Registra sesiones worker; rollback en `invalidate()` |
| `GuardedEngine` / `_GuardedConnection` | Bloquea commit en conexión cruda bajo fence |

### Quién puede hacer commit

| Actor | Commit |
|-------|--------|
| Worker (`WorkerExecutionSession`) | **PROHIBIDO** |
| `flush_gated` / `commit_gated` en fase worker | Solo flush |
| `materialize_gated` (dispatcher) | **SÍ** — tras validación |
| `invalidate_run_execution` | Commit terminal de invalidación |
| API/CRUD fuera de fence | Commit normal |

### SQL crudo

- Worker no puede `get_bind()` ni `connection()`.
- Conexiones crudas bajo fence: `GuardedConnection.commit()` bloqueado.
- SQL externo a BD distinta: bloqueado por `require_execution_allowed(db)` antes de efecto.

### Process isolation

- Mantiene v3: padre/hijo, terminación recursiva, Windows `taskkill /T`.
- **Nuevo:** prueba padre → hijo → nieto.

---

## ARCHIVOS MODIFICADOS / NUEVOS

| Archivo | Cambio |
|---------|--------|
| `backend/app/services/execution_workspace.py` | **Nuevo** — WorkerExecutionSession, fases, GuardedEngine |
| `backend/app/services/execution_guard.py` | flush_gated, materialize_gated, require_execution_allowed+BD, rollback sesiones |
| `backend/app/services/automation_service.py` | WorkerExecutionHandle, materialización diferida |
| `backend/app/services/coordinator.py` | require_execution_allowed(db) |
| `tests/test_automations_810c_adversarial.py` | Tests V4: commit directo 100×, SQL crudo 100×, padre-hijo-nieto |

---

## TESTS

| # | Escenario | Resultado |
|---|-----------|-----------|
| 1 | commit directo | PASS — bloqueado |
| 2 | SQL crudo get_bind | PASS — bloqueado |
| 3 | stale generation | PASS |
| 4 | timeout antes materialización | PASS |
| 5 | timeout durante ejecución | PASS |
| 6 | callback tardío | PASS |
| 7 | finally tardío | PASS |
| 8 | parent-child-grandchild | PASS |
| 9 | dos workers (lock order) | PASS |
| 10 | excepción DB / rollback | PASS |
| 11 | race cooperativa 100× | PASS — **0/100** |
| 12 | **QA sync race commit 100×** | PASS — **0/100** |
| 13 | **QA sync race SQL crudo 100×** | PASS — **0/100** |

**Suite total:** 119 passed

---

## VALIDACIÓN

| Control | Resultado |
|---------|-----------|
| `pytest` | **119/119 PASS** |
| Race sincronizada QA | **0/100 efectos tardíos** |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilidades |
| `git diff --check` | PASS |

---

## NO REGRESIÓN

Wizard/deep merge, automatizaciones, recurrencia, tenant isolation, aprobaciones, scheduler — PASS.

---

## ESTADO FINAL

**REDISEÑADO Y LISTO PARA QA FINAL**

No merge. No declarado apto para merge.
