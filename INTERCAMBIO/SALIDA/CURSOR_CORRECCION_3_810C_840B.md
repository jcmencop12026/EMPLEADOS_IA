# CURSOR — Tercera corrección PR #6 / 810C y PR #9 / 840B

**Estado global:** CORREGIDO Y LISTO PARA NUEVA REAUDITORÍA

**Fecha:** 2026-08-24

---

## PR #6 — CURSOR-810C

| Campo | Valor |
|-------|-------|
| PR | #6 |
| Rama | `cursor/automations-scheduler-810` |
| HEAD anterior | `8db9480c147b0ebb97cc128b9276def6bdace4bf` |
| HEAD nuevo | `146047a` |
| Commit | `fix(810c): process tree termination, lock order, and gated persistence v3` |

### Estrategia process-tree

- Windows: `CREATE_NEW_PROCESS_GROUP` + `taskkill /PID <pid> /T /F` encapsulado en `terminate_process_tree()`.
- Linux: `start_new_session` + `killpg(SIGTERM/SIGKILL)` + terminación recursiva de hijos vía `/proc`.
- Registro de subprocess en `RunFenceController`; invalidación tras commit BD.
- Helpers: `process_tree_alive()`, `terminate_process_tree()` exportables para tests.

### Inventario de persistencia (commits)

| Archivo | Función | Tipo | Gate | Justificación |
|---------|---------|------|------|---------------|
| `execution_guard.py` | `commit_gated` | commit | Sí | Único commit autorizado durante ejecución cancelable |
| `execution_guard.py` | `invalidate_run_execution` | commit | N/A | Invalidación terminal atómica (BD primero, memoria después) |
| `automation_service.py` | `_apply_run_result` | UPDATE+commit | Parcial | UPDATE con `generation`+`RUNNING`; commit tras rowcount>0 |
| `automation_service.py` | retry reset | UPDATE+commit | Parcial | UPDATE atómico `FAILED→RUNNING` con generation |
| `automation_service.py` | CRUD/trigger pre/post fence | commit | No | Fuera de ejecución cancelable |
| `coordinator.py` | `route_task`/`execute_plan` | commit_gated | Sí | Orquestación bajo fence |
| `bus.py` | `_persist_subscriber` | flush/commit | Condicional | Sin commit si hay fence token |
| `audit.py` | `write_audit` | flush/commit | Condicional | Sin commit si hay fence token |
| `agent_factory.py` | varios | commit | No | No asociado a ejecución cancelable de automation run |

### Lock ordering

1. `invalidate_run_execution`: `SELECT FOR UPDATE` → actualizar BD → commit → invalidar memoria/procesos.
2. `commit_gated`: lectura SQL autoritativa → validar generation/estado → validar token memoria → `FOR UPDATE` → flush → revalidar → commit.
3. Worker aislado usa el mismo `db_bind` que la sesión principal (corrige desincronización de BD en tests/runtime).

### Pruebas añadidas / resultados

| Prueba | Resultado |
|--------|-----------|
| Process tree padre+hijo (×3) | PASS — 0 efectos tardíos |
| Subprocess tree unit | PASS |
| Commit fuera de gate detectado | PASS |
| Lock order A (invalidación→commit) | PASS |
| Lock order B (commit tras invalidación) | PASS |
| Race 100 iteraciones | PASS — 0/100 efectos tardíos |
| Suite adversarial 810c previa | PASS |
| `pytest` total rama 810 | **116 passed** |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilidades |
| `git diff --check` | PASS |

---

## PR #9 — CURSOR-840B

| Campo | Valor |
|-------|-------|
| PR | #9 |
| Rama | `cursor/admin-users-roles-840` |
| HEAD anterior | `666eb3840e5673bb3a01f9d752df662faec5dabe` |
| HEAD nuevo | `9ddc51d` |
| Commit | `fix(840b): strict is_active from SQLite and safe duplicate migration v3` |

### Tratamiento `is_active`

- `is_canonical_active_value()`: solo `True` o `1` equivalen a ACTIVE.
- `read_role_is_active_raw()` + `is_role_strictly_active(role, db)` leen valor persistido en SQLite antes de autorizar.
- Cualquier valor corrupto (`yes`, `TRUE`, `2`, `on`, etc.) → DENY.

### Casos SQLite corruptos probados

| Valor insertado | Resultado |
|-----------------|-----------|
| `1` (canónico) | ALLOW si tiene permiso |
| `yes`, `TRUE`, `2`, `on`, `false`, `0`, `""`, `null` | DENY |

### Estrategia migración `b840c3e4f5a6`

- Normalización previa de `is_active` corruptos → `0/1`.
- Superviviente determinístico: `ORDER BY created_at ASC, id ASC`.
- Permisos duplicados: **intersección** (mínimo privilegio).
- `is_active` final: activo solo si **todos** los duplicados eran canónicamente activos.
- Remapeo de `role_permissions` al superviviente antes de `DELETE` del duplicado.
- Índice único parcial `uq_roles_global_code` tras consolidación.

### Matriz de duplicados (fixtures)

| Caso | Resultado |
|------|-----------|
| A — mismos permisos | 1 rol, permisos preservados |
| B — permisos distintos | 1 rol, intersección vacía (mínimo privilegio) |
| C — uno inactivo | superviviente inactivo |
| D — ambos activos | superviviente activo con intersección |
| E-H — FK `role_permissions` | remapeo, 0 huérfanos verificado |

### Roundtrip migración

- `upgrade head` → `downgrade a840c4d5e6f7` → `upgrade head` PASS
- 0 huérfanos en `role_permissions`

### Resultados suites

| Control | Resultado |
|---------|-----------|
| `pytest` | **101 passed** |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilidades |
| `git diff --check` | PASS |

---

## Tabla de control

| Control | PR #6 | PR #9 |
|---------|-------|-------|
| Process tree | PASS | N/A |
| Child process survivor | PASS | N/A |
| Commits gated | PASS | N/A |
| Lock ordering | PASS | N/A |
| Race 100 | PASS (0/100) | N/A |
| SQLite corrupt boolean | N/A | PASS |
| Duplicate migration | N/A | PASS |
| Orphan relations | N/A | PASS |
| Least privilege | N/A | PASS |
| Migration roundtrip | N/A | PASS |
| Tests | PASS | PASS |
| Build | PASS | PASS |
| npm audit | PASS | PASS |
| Git | PASS | PASS |

---

## Bloqueos / no realizados

- NO merge (por instrucción).
- NO cambios en PR #7, #8, #10.
- NO declaración "APTO PARA MERGE".

## Ubicación del informe

`INTERCAMBIO/SALIDA/CURSOR_CORRECCION_3_810C_840B.md`
