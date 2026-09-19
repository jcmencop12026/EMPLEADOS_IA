# Reauditoría final 2 — PR #6 / 810C y PR #9 / 840B

Fecha: 2026-08-24

Repositorio: `D:\EMPLEADOS_IA`. Auditoría ejecutada en worktrees detached; el repositorio principal permaneció en `codex/notifications-alerts-820`. No se modificaron PR #7, #8 ni #10. No se realizó merge, push, rebase, cherry-pick ni corrección de los PR.

## PR #6 — CURSOR-810C

- HEAD auditado: `8db9480c147b0ebb97cc128b9276def6bdace4bf`
- Head anterior: `fa07040e8b38efebb309677d72a2c6bdd7ded082`
- Base: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- Delta: 8 archivos, +839/-83.
- Commit de fencing revisado: `5d0a9ff`.
- Superficies: migración, modelo `AutomationRun`, `automation_service`, `coordinator`, `execution_guard`, tests adversariales e informe.

### Resultado

**NO APTO PARA MERGE**

### Hallazgo PR6-1 — El árbol de procesos sobrevive al timeout

- Severidad: ALTA
- Confianza: ALTA

Prueba independiente en Windows:

1. se registró un proceso padre;
2. el padre creó un hijo;
3. el hijo quedó programado para escribir un marker después del timeout;
4. se invalidó/terminó la ejecución.

Resultado:

- proceso padre terminado: sí (`poll=1`);
- proceso hijo sobrevivió: sí;
- marker tardío: creado;
- contenido: `child`.

La rama Windows de `execution_guard.py` usa `proc.terminate()`/`proc.kill()` sobre el proceso registrado, pero no controla el árbol con Job Objects/process groups ni termina descendientes. También existe una ventana spawn→register; un proceso puede crear efectos o descendientes antes de quedar registrado. `register_subprocess()` no rechaza de forma cerrada un token que ya fue invalidado.

Esto incumple los controles L/M y el criterio absoluto de cero efectos tardíos.

### Hallazgo PR6-2 — Persistencia alcanzable fuera de `commit_gated()`

- Severidad: ALTA
- Confianza: ALTA

Rutas directas encontradas:

- `backend/app/audit.py:22`: `db.commit()` directo;
- `backend/app/events/bus.py:49`: `db.commit()` directo.

El worker llama `publish()` repetidamente desde coordinator antes, entre y después de operaciones gated. Por tanto, no toda persistencia relevante del worker pasa por `commit_gated()`. El fencing sólo puede garantizar las escrituras que usan el gate.

### Hallazgo PR6-3 — Orden de locks deja ventana de carrera

- Severidad: MEDIA
- Confianza: MEDIA-ALTA

`commit_gated()` valida primero el token en memoria y luego obtiene `SELECT FOR UPDATE`. El invalidator marca memoria inválida y después intenta bloquear/persistir el mismo row. Un worker que ya pasó la verificación y obtuvo el lock puede confirmar mientras la invalidación está en progreso. El test incluido de 100 iteraciones no coloca la carrera cerca de un commit SQL: ejecuta `require_execution_allowed()` y después un append en memoria.

PostgreSQL no estaba disponible para reproducir semántica real de `SELECT FOR UPDATE`; la evaluación de esta ventana se basa en el orden del código y pruebas SQLite/locales. Esta limitación impide declarar el fencing productivo totalmente validado.

### Controles de fencing ejecutados

| Control | Resultado |
|---|---|
| Race incluida 100 iteraciones | 0/100, pero no es carrera SQL cercana al commit |
| Token generation viejo | PASS en tests aportados |
| Reutilización run_id con generación nueva | PASS en tests aportados |
| Segundo commit después de invalidación | PASS para rutas gated |
| Dos sesiones / invalidación | PASS funcional básico; riesgo de orden de locks pendiente |
| Error de invalidación DB | Fail-closed en rutas probadas; atomicidad memoria/DB no demostrada ante crash |
| Sesión worker aislada | PASS por inspección/tests; no se observó sesión request compartida en el nuevo camino |
| SQLite side effect gated | PASS en tests aportados |
| Archivo directo no gated | El guard no puede impedir I/O arbitrario; depende de cooperación/aislamiento |
| Subprocess registrado | Padre terminado |
| Process tree | FAIL: hijo sobrevivió y produjo efecto |
| Finally/callback gated | Rechazado en tests cuando usa gate; side effect externo no gated sigue fuera de control |
| Estado terminal | PASS en tests: no sobrescribe TIMED_OUT mediante rutas gated |

### Deep merge

Regresión básica: PASS. Se mantienen campo simple, nested merge, array ausente, array vacío explícito, null y nested null. No se reabrió el diseño ya validado.

### Compatibilidad PR #8 / PR #10

- Partial update/exclude-unset: preservado.
- Tenant checks: PASS en suites.
- El head standalone no contiene la ruta integrada completa de PR #10; debe preservarse al resolver coordinator: `evaluate_tool_execution()` antes de `_run_tool`, con `DENY > REQUIRES_APPROVAL > ALLOW`.
- Los commits directos de audit/event bus constituyen rutas que deben incluirse en el modelo de fencing de la integración.

### Pruebas y calidad PR #6

- Suite completa: `111 passed`, 0 failed, 0 skipped, 3 warnings, 241,76 s.
- Suites fencing/810C adversariales: `24 passed`, 0 failed, 1 warning, 141,00 s.
- Race propia decisiva de process tree: FAIL; hijo tardío produjo marker.
- `npm ci`: PASS, 73 paquetes.
- `npm run build`: PASS, Vite 6.4.3, 57 módulos, 1,78 s; JS 275,64 kB / 84,27 kB gzip.
- `npm audit --audit-level=low`: 0 vulnerabilidades.
- `git diff --check`: PASS.
- Secretos/binarios accidentales: no encontrados.
- PostgreSQL: no disponible; `SELECT FOR UPDATE` productivo no reproducido.

## PR #9 — CURSOR-840B

- HEAD auditado: `666eb3840e5673bb3a01f9d752df662faec5dabe`
- Head anterior: `0e25e3e0189b5ed9c029ee9d863d0f40782a1349`
- Base: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- Delta: 5 archivos, +439/-38.
- Superficies: `permissions.py`, migración `b840c3e4f5a6`, tests e informe.

### Resultado

**NO APTO PARA MERGE**

### Hallazgo PR9-1 — Valores `is_active` corruptos fallan abiertos en SQLite

- Severidad: ALTA
- Confianza: ALTA

Valores insertados directamente en storage y rehidratados por SQLAlchemy:

- `'true'` → Python `True` → permiso concedido;
- `'TRUE'` → `True` → concedido;
- `'1'` → `True` → concedido;
- `'false'` → `True` → concedido;
- entero `1` → `True` → concedido;
- `0` → false/deny;
- `NULL` → rechazado por NOT NULL.

`is_role_strictly_active()` (`backend/app/permissions.py:116-118`) recibe el booleano ya coercionado y no puede distinguir un valor corrupto. La prueba aportada sólo muta un objeto Python y no cubre la hidratación real desde SQLite.

Esto incumple el requisito de aceptar únicamente `True` inequívoco según storage real.

### Hallazgo PR9-2 — Migración deduplica arbitrariamente y rompe integridad referencial

- Severidad: ALTA
- Confianza: ALTA

SQLite `b840c3e4f5a6:27-38` usa `GROUP_CONCAT` sin `ORDER BY`, conserva el primer ID retornado y elimina los demás sin reconciliar `role_permissions`.

Reproducción con duplicados globales:

- rol `z` más nuevo con permisos `safe + power`;
- rol `a` más antiguo con `safe`;
- upgrade conservó `z` —el más permisivo— de manera dependiente del orden;
- eliminó `a`;
- dejó `role_permissions` huérfano;
- `PRAGMA foreign_key_check` devolvió `('role_permissions', 3, 'roles', 0)`.

La migración limpia pasa, pero el caso que motivó la migración produce pérdida/ambigüedad y corrupción referencial.

En PostgreSQL, la deduplicación por `created_at` no resuelve empates ni `NULL` (columna nullable), por lo que duplicados pueden sobrevivir y hacer fallar el índice parcial. Los DELETE directos también pueden fallar por FK sin cascade. No se demostró compatibilidad segura con datos contradictorios.

### Matriz runtime PR #9

| Caso | Resultado |
|---|---|
| Rol inexistente | DENY — PASS |
| Nombre hardcoded inexistente | DENY — PASS |
| Inactivo False | DENY — PASS |
| is_active NULL | No insertable por schema — PASS |
| is_active corrupto storage | ALLOW para múltiples valores — FAIL |
| Rol vacío | DENY — PASS |
| Duplicado global runtime | Ambigüedad detectada/deny — PASS |
| Duplicado organizacional | Constraint/runtime deny — PASS |
| Global vs organizacional | Org tiene precedencia explícita, sin unión — PASS |
| Error DB | DENY — PASS |
| Error parcial de permisos | DENY — PASS |
| Cache tras inactivar | N/A; no existe cache, nueva solicitud niega |
| Cross-tenant | PASS en suite |

### Fallbacks y compatibilidad

- El fallback hardcoded permanece sólo para seed/legacy setup; no se encontró una segunda concesión runtime que anule `user_permissions()`.
- Runtime deny-by-default para rol inexistente, inactive, empty, ambiguo y error DB: corregido.
- `operations.approve` no aparece en este árbol standalone.
- Coordinator standalone todavía ejecuta `_run_tool` antes de calcular approval; esto pertenece a integración con PR #8/#10 y no es introducido por el delta 840B, pero impide certificar compatibilidad transversal desde esta rama sola.

### Migración y pruebas PR #9

- Upgrade limpio SQLite: PASS.
- Downgrade: sólo elimina índice.
- Upgrade con duplicados/permisos divergentes: FAIL por selección arbitraria y FK huérfana.
- PostgreSQL: no disponible; análisis estático detecta empates/NULL/FK no resueltos.
- Suite completa: `87 passed`, 0 failed, 0 skipped, 3 warnings, 112,87 s.
- `npm run build`: PASS, 59 módulos, 2,14 s.
- `npm audit`: 0 vulnerabilidades.
- `git diff --check`: PASS.
- Secretos/binarios accidentales: no encontrados.

## Tabla final

| Control | PR #6 | PR #9 |
|---|---|---|
| Hallazgos anteriores cerrados | FAIL | FAIL |
| Adversarial tests | FAIL | FAIL |
| Race ≥100 | PASS nominal / FAIL representatividad | N/A |
| Commit fencing | FAIL | N/A |
| Subprocess isolation | FAIL | N/A |
| Estado terminal | PASS gated | N/A |
| Rol inexistente | N/A | PASS |
| Rol corrupto | N/A | FAIL |
| Rol ambiguo | N/A | PASS runtime / FAIL migración |
| Migración | N/A | FAIL |
| Cross-tenant | PASS | PASS |
| Suite | PASS | PASS |
| Build | PASS | PASS |
| npm audit | PASS | PASS |
| git diff --check | PASS | PASS |
| RESULTADO | NO APTO | NO APTO |

## Conclusión

- PR #6 / `8db9480`: **NO APTO PARA MERGE**.
- PR #9 / `666eb38`: **NO APTO PARA MERGE**.
- **NO MERGE REALIZADO.**
