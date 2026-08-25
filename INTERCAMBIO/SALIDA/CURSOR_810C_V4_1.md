# CURSOR — PR #6 / 810C v4.1

**Fecha:** 2026-08-25  
**Estado:** CORREGIDO Y LISTO PARA QA FINAL  
**No declarado apto para merge**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| PR | #6 |
| Rama | `cursor/automations-scheduler-810` |
| HEAD anterior | `772867b544d6a57693da83d88c31b61df130163b` |
| HEAD nuevo | *(post-commit)* |
| Commit V4 | `b33190a` |
| Commit V4.1 | `fix(810c): close worker session bypass via facade encapsulation` |

---

## CAUSA RAÍZ

V4 bloqueaba `commit()` y `get_bind()` en un proxy con `__getattr__` que delegaba al resto de la API SQLAlchemy, y exponía:

- `db.session` → Session real
- `db._session` → Session real

Codex reprodujo **99/100** commits tardíos y **100/100** SQL crudo vía esos atributos.

---

## SUPERFICIE EXPUESTA ANTERIOR (v4)

| Vector | Problema |
|--------|----------|
| `__getattr__` | Delegaba cualquier método/atributo ORM a Session interna |
| `@property session` | Devolvía `_session` sin restricción |
| `_session` en `__slots__` | Accesible como `db._session` |
| `WorkerExecutionSession(inner)` | Constructor guardaba referencia en el objeto |

---

## DISEÑO CORREGIDO (v4.1)

### Composición con interfaz mínima

`WorkerExecutionSession` es una **fachada sin Session embebida**:

- `__slots__ = ("__weakref__",)` — sin `_session` ni token en el objeto
- Session real en `_facade_registry: WeakKeyDictionary[facade, Session]` (módulo interno)
- Solo dispatcher usa `resolve_inner_session(facade)` / `release_worker_session(facade)`

### API expuesta al worker

`query`, `add`, `add_all`, `delete`, `execute` (con guard SQL), `flush`→`flush_gated`, `refresh`, `expunge`, `merge`, `rollback`

### Bloqueado explícitamente

`commit`, `get_bind`, `connection`, `bind_*`, `begin`, `close`, `session` (property que lanza), `_session` vía `__getattr__`

### SQL crudo transaccional

`execute()` rechaza SQL que empiece con `COMMIT`, `ROLLBACK`, `BEGIN`, `SAVEPOINT`, `RELEASE`, `END TRANSACTION`.

### Controlador interno vs capacidad worker

| Rol | Acceso |
|-----|--------|
| `RunFenceController` | `register_worker_session(inner)` — Session real para rollback en invalidate |
| Worker / route_task | Solo `WorkerExecutionSession` facade |
| Dispatcher | `materialize_gated(resolve_inner_session(facade), token)` |

---

## RESULTADOS 100× (escenario QA sincronizado)

| Escenario | v4 | v4.1 |
|-----------|----|------|
| `db.commit()` | bloqueado | **0/100** |
| `db.get_bind()` | bloqueado | **0/100** |
| `db.session.commit()` | **99/100 bypass** | **0/100** |
| `db._session.commit()` | **100/100 bypass** | **0/100** |
| `db.session.get_bind()` + SQL | bypass | **0/100** |

---

## TESTS NUEVOS

- `test_worker_facade_no_session_surface_leak`
- `test_adversarial_qa_sync_race_session_attr_commit_100_iterations`
- `test_adversarial_qa_sync_race_underscore_session_commit_100_iterations`
- `test_adversarial_qa_sync_race_session_attr_raw_sql_100_iterations`

---

## VALIDACIÓN

| Control | Resultado |
|---------|-----------|
| `pytest` | **123/123 PASS** |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilidades |
| `git diff --check` | PASS |
| Materialización `materialize_gated` | PASS (integración orquestador) |

---

## ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `execution_workspace.py` | Fachada v4.1, registro interno, guard SQL, `unwrap_db_session` |
| `execution_guard.py` | `unwrap_db_session` en flush/materialize/commit |
| `automation_service.py` | `create_worker_execution_session`, handle con facade |
| `test_automations_810c_adversarial.py` | Tests bypass session/_session 100× |

---

## ESTADO FINAL

**CORREGIDO Y LISTO PARA QA FINAL**

No merge. No declarado apto para merge.
