# QA técnico final — PR #6 / CURSOR-810C y PR #9 / CURSOR-840B

Fecha: 2026-08-24  
Repositorio: `D:\EMPLEADOS_IA`  
Modalidad: QA funcional, concurrencia, procesos y migraciones en worktrees detached, sin modificar ni integrar código.

## Identidad auditada

- PR #6, rama `cursor/automations-scheduler-810`: `80c1e6ab5b7f74f928b2ed3d53928b971a025ae0` (commit de código informado y presente: `146047a`).
- PR #9, rama `cursor/admin-users-roles-840`: `be23541b08e07e19bf104fe2fdd369e2fe735c9c` (commit de código informado y presente: `9ddc51d`).
- Ambos heads parten del ancestro esperado `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`.

## Resultado ejecutivo

| Control                      | PR #6        | PR #9        |
| ---------------------------- | ------------ | ------------ |
| Bloqueos anteriores cerrados | FAIL         | FAIL         |
| Process tree                 | PASS         | N/A          |
| Race child creation          | FAIL         | N/A          |
| Commit tardío                | FAIL         | N/A          |
| Lock order                   | FAIL         | N/A          |
| Race 100                     | FAIL         | N/A          |
| SQLite corrupto              | N/A          | FAIL         |
| Duplicados                   | N/A          | PASS         |
| Mínimo privilegio            | N/A          | PASS         |
| FK/huérfanos                 | N/A          | PASS         |
| Migración                    | N/A          | FAIL         |
| Runtime final                | N/A          | FAIL         |
| Tests                        | FAIL         | PASS         |
| Build                        | PASS         | PASS         |
| npm audit                    | PASS         | PASS         |
| Git                          | PASS         | PASS         |
| RESULTADO                    | **NO APTO**  | **NO APTO**  |

## PR #6 — controles pendientes

### Árbol de procesos registrado

La prueba real en Windows de un árbol ya registrado `padre → hijo → nieto`, terminado mediante `taskkill /PID <pid> /T /F`, no dejó marcadores tardíos del padre, hijo ni nieto. Resultado: **PASS** para el árbol que ya alcanzó el registro del controlador.

### Race de creación de hijo

La implementación ejecuta `Popen` antes de registrar el proceso en el controlador (`backend/app/services/execution_guard.py:224-238`). Si `invalidate()` incrementa la generación y vacía la lista entre esas dos operaciones (`execution_guard.py:47-57`), `register_subprocess()` agrega después el proceso a un controlador ya invalidado, sin volver a comprobar la generación ni terminarlo.

- Sonda sincronizada determinista: `1/1` proceso escapó y creó efecto tardío.
- Repetición final sincronizada: **100/100 efectos tardíos**.
- Todos los intentos alcanzaron explícitamente la ventana `Popen → register_subprocess`.

Resultado: **FAIL**. Incumple el requisito obligatorio `0/100`.

### Persistencia protegida

Con token vencido (token generación 1, controlador generación 2), sondas directas sobre una sesión SQLAlchemy demostraron:

- `db.add(...)` + `db.commit()`: **1 cambio tardío persistido**;
- `db.execute(raw SQL)` + `db.commit()`: **1 cambio tardío persistido**.

`commit_gated()` (`execution_guard.py:134-181`) protege únicamente a los callers que lo invocan; no intercepta `Session.commit`, SQL crudo, `flush` o autoflush. El test agregado en `tests/test_automations_810c_adversarial.py:385-409` confirma primero los datos y solo después invalida y llama al gate, por lo que no demuestra que un commit directo tardío quede bloqueado.

Resultado: **FAIL**, commits tardíos distintos de cero.

### Orden de locks

Los casos incorporados por el PR son secuenciales y no reproducen contención real entre worker e invalidación. Además, el escenario timeout primero / creación simultánea queda refutado por la carrera anterior y produce efectos tardíos. No se puede certificar el requisito conjunto “sin deadlock, sin commit tardío y estado consistente”. Resultado: **FAIL**.

### Suite y validaciones

- Backend focal: `28 passed, 1 failed`.
- Suite completa: `115 passed, 1 failed` en `247.81s`.
- Fallo: `test_adversarial_process_tree_parent_child_no_late_effects`; en Windows el comando hijo contiene una ruta sin escape y provoca `SyntaxError: unicodeescape`. Además, `process_tree_alive()` informa vivo un proceso ya finalizado porque no consulta `proc.poll()`.
- Frontend: `npm ci` y `npm run build` **PASS**; 57 módulos, bundle JS aproximado `275.64 kB`.
- `npm audit`: **PASS**, 0 vulnerabilidades.
- `git diff --check`, `git fsck` y worktree: **PASS**.
- `pip-audit`: no certificado porque no está instalado; no forma parte de la tabla solicitada.

**Veredicto PR #6: NO APTO PARA MERGE.**

## PR #9 — controles pendientes

### Estado persistido `is_active`

La lectura runtime desde SQLite fue probada con inserciones directas: `1` permitió; `0`, `2`, `-1` y textos corruptos denegaron. `NULL` no puede persistirse con el esquema normal por la restricción `NOT NULL`.

Sin embargo, la migración `b840c3e4f5a6` normaliza explícitamente `'1'`, `'true'`, `'TRUE'`, `'t'`, `'yes'` y `'YES'` a activo (`backend/alembic/versions/b840c3e4f5a6_role_global_unique_840c.py:29-40`). Una sonda con duplicados `is_active='yes'` y `is_active=1` dejó al superviviente con `is_active=1` de tipo entero. Un valor corrupto/no canónico queda así convertido en autorización activa.

Resultado SQLite corrupto: **FAIL**. Aunque el lector runtime aislado es estricto, el flujo real post-migración no es fail-closed.

### Duplicados, mínimo privilegio y relaciones

Fixture adversarial de tres duplicados:

- superviviente: el menor por `created_at`, con `id` como desempate;
- permisos iniciales: `{p1,p2}`, `{p1,p3}` y `{p1}`;
- permisos finales: `{p1}` (intersección);
- relaciones huérfanas: `0`.

Las pruebas de permisos disjuntos produjeron conjunto vacío y la combinación activo/inactivo produjo superviviente inactivo. La migración elimina asociaciones de duplicados antes de eliminar sus roles y reconstruye únicamente la intersección en el superviviente. Resultado para deduplicación, mínimo privilegio y `foreign_key_check`: **PASS**.

### Migración y runtime final

- Inyección de fallo durante `DELETE`: rollback íntegro; permanecieron ambos roles, la revisión anterior y ningún índice parcial.
- `upgrade → downgrade → upgrade`: **PASS** en SQLite, índice final restaurado y 0 huérfanos. Los duplicados eliminados no se reconstruyen en downgrade, pérdida esperadamente irreversible.
- No obstante, el upgrade completo es funcionalmente inseguro porque activa representaciones textuales corruptas. Por el criterio del pedido, control Migración: **FAIL** y Runtime final: **FAIL**.
- Rol inexistente, inactivo, sin permisos y errores de resolución: DENY en pruebas; aislamiento cross-tenant: PASS.
- **POSTGRESQL REAL: NO CERTIFICADO.** Existe un servicio PostgreSQL 18 local, pero no hubo credenciales utilizables. Además, debe verificarse antes de aprobar que el SQL compartido `is_active IN (1, '1', ...)` sea válido para una columna PostgreSQL `BOOLEAN`.

### Suite y validaciones

- Pruebas objetivo: `55 passed`.
- Suite completa: `101 passed` en `129.63s`.
- Frontend: `npm ci` y `npm run build` **PASS**; 59 módulos, bundle `275.37 kB` (`84.17 kB` gzip).
- `npm audit`: **PASS**, 0 vulnerabilidades.
- `git diff --check`, `git fsck` y worktree: **PASS**.
- `pip-audit`: detectó 2 avisos en dependencias de desarrollo/runtime (`pytest 8.4.2`, `ecdsa 0.19.2`); no forma parte de la tabla solicitada.

**Veredicto PR #9: NO APTO PARA MERGE.**

## Integridad de la auditoría

No se modificó código de los PR, no se hizo merge, push, rebase ni cherry-pick, y no se tocó el contenido de PR #7, #8 o #10. La única escritura realizada para esta solicitud es este informe de QA.
