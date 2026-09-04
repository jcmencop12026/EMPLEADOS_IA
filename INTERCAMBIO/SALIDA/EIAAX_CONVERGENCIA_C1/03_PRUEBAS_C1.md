# 03 — Pruebas Bloque C1

**Fecha UTC:** 2026-08-31
**Entorno:** agente cloud (SQLite test DB; sin PostgreSQL CERT)

---

## Build

| Prueba | Comando | Resultado |
|---|---|---|
| Frontend compile | `npm run build` | **PASS** (1.69s) |

---

## Suite focal C1 (seguridad + convergencia)

| Archivo | Tests | Resultado |
|---|---|---|
| `test_v1_hotfix_login.py` | 6 | **PASS** |
| `test_convergencia_c1.py` | 5 | **PASS** |
| `test_knowledge_930.py` | 15 | **PASS** |
| `test_multitenant_v1.py` | 12 | **PASS** (2 skipped) |
| `test_docker_database_url.py` | 11 | **PASS** |
| `test_migration_control.py` | 23 | **PASS** |
| **Subtotal focal** | **72** | **PASS** (2 skipped) |

### Cobertura por dominio

| Dominio | Tests ejecutados |
|---|---|
| Autenticación / login 401 | `test_v1_hotfix_login`, `test_convergencia_c1` |
| RBAC / permisos | `test_convergencia_c1::test_auth_me_returns_permissions` |
| Multiempresa | `test_multitenant_v1`, `test_convergencia_c1::test_multitenant_*` |
| Knowledge auth/download | `test_knowledge_930`, `test_convergencia_c1::test_knowledge_*` |
| DATABASE_URL | `test_docker_database_url` |
| Alembic head único | `test_migration_control`, `test_convergencia_c1::test_alembic_*` |
| V2 routers preservados | `test_convergencia_c1::test_v2_routers_*` |

---

## Regresión completa V2

| Métrica | Valor |
|---|---|
| Comando | `pytest tests/ -q` |
| Passed | **1251** |
| Failed | **0** |
| Skipped | 4 |
| Duración | ~16 min |

**Conclusión:** C1 no degradó capacidades V2 existentes.

---

## Pruebas NO ejecutadas (fuera entorno cloud)

| Prueba | Motivo |
|---|---|
| PostgreSQL CERT pg_dump/restore | NO EJECUTABLE cloud |
| `alembic upgrade` sobre BD V1 real | Prohibido en C1 |
| Windows PASO1/PASO2 | Entorno CERT local |
| Walkthrough visual login | Pendiente Agente B |

---

## Tests no debilitados

- No se eliminaron tests V2
- No se modificaron assertions para forzar PASS
- No se desactivaron guards de `migration_control` ni `DATABASE_URL`

---

## Resumen PASS/FAIL

| Bloque | PASS | FAIL |
|---|---|---|
| Build frontend | 1 | 0 |
| Focal C1 | 72 | 0 |
| Regresión V2 | 1251 | 0 |
| **TOTAL** | **1324** | **0** |
