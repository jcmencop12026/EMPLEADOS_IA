# 04 — Plan de integración controlada V1 + V2

**Base convergencia:** `cursor/eiaax-convergencia-v1-v2` @ `dc1e6cda8d3de6695d9a052a2a13afdb5f431077`
**V1 referencia:** `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81`
**Principio:** incremental, verificable, sin merge masivo

---

## Secuencia propuesta

### BLOQUE 0 — Pre-requisitos (sin código)

| Qué | Riesgos | Pruebas |
|---|---|---|
| pg_dump CERT PostgreSQL | Pérdida datos | `pg_restore --list`; tamaño > 0 |
| Verificar SHA-256 respaldos V1/V2 | Restauración incorrecta | `sha256sum` vs manifiesto |
| Crear worktree `D:\EMPLEADOS_IA_EIAAX_CONVERGENCIA` | Contaminar CERT | `git worktree list` |
| Clonar BD a staging | Impacto productivo | BD staging aislada |

**Criterio PASS:** dump PG validado + worktree convergencia + staging BD.

---

### BLOQUE 1 — Hotfix login V1 → convergencia (cherry-pick selectivo)

| Qué integrar | Origen |
|---|---|
| `frontend/src/api.ts` (orden `text`, 401 login) | `beb1760` / hotfix branch |
| `frontend/src/pages/LoginPage.tsx` | idem |
| `frontend/src/styles.css` (password field) | idem |
| `tests/test_v1_hotfix_login.py` | idem |

| Riesgos | Mitigación |
|---|---|
| Conflicto con `api.ts` V2 ampliado | Merge manual; conservar endpoints V2 |
| Regresión MFA login | Probar login con y sin MFA desactivado |

| Pruebas |
|---|
| `test_v1_hotfix_login.py` |
| `npm run build` |
| Login manual staging 401/200 |

**NO incluir:** scripts PASO1/PASO2 V1_CERT (operacional CERT, no convergencia).

---

### BLOQUE 2 — Validación auth/RBAC en staging

| Qué | Detalle |
|---|---|
| Verificar admin `superadmin` + permisos V2 | `/api/auth/me` → 74 permisos |
| MFA opcional / bootstrap | Config `.env` staging |
| Sesiones y CORS | `CORS_ORIGINS` + puertos |

| Pruebas |
|---|
| Login API + SUPERADMIN |
| Tests `test_scim_1380.py` (smoke si SCIM off) |
| `test_migration_control.py` |

---

### BLOQUE 3 — Migraciones Alembic (staging únicamente)

| Qué | Detalle |
|---|---|
| `alembic upgrade head` en BD staging (dump V1) | 32 revisiones |
| Preflight `migration_control.py` | fail-closed |

| Riesgos | CRÍTICO |
|---|---|
| Migración fallida a mitad | Restore PG staging |
| Ledger desincronizado | No `stamp` manual |

| Pruebas |
|---|
| `alembic current` == `1341a1b2c3d4e` |
| Regresión backend completa (~1240 tests) |
| Health `/health/ready` |

---

### BLOQUE 4 — Frontend V2 + hotfix login en staging

| Qué | Detalle |
|---|---|
| Build frontend rama convergencia | Docker compose staging |
| Desplegar solo frontend si backend ya migrado | `--no-deps` pattern |
| Verificar CC, menú, español focal | Walkthrough |

| Pruebas |
|---|
| `test_convergencia_final_fase2.py` |
| `test_correccion_focal_post6e_p1.py` |
| HTTP `/login`, `/centro-control` |

---

### BLOQUE 5 — Módulos V2 por prioridad (selectivo)

Integrar y validar **uno a uno** (no en paralelo masivo):

| Orden | Módulo | Tests clave |
|---|---|---|
| 5.1 | Centro Control + Mi Trabajo | `test_convergencia_final_fase2.py` |
| 5.2 | Comunicaciones MB-11 | `test_mb11_*` |
| 5.3 | Integraciones 1330 | `test_wiring_1330_*` |
| 5.4 | Comercial 1280 | `test_modelo_comercial_1280.py` |
| 5.5 | SSO/SCIM 1370/1380 | `test_scim_1380.py` |
| 5.6 | MFA 1300 | tests security |
| 5.7 | Resto (optimización, TCO, etc.) | tests por módulo |

---

### BLOQUE 6 — Cutover controlado (futuro, NO ahora)

| Qué | Condición |
|---|---|
| Ventana mantenimiento CERT | Solo tras PASS bloques 1-5 en staging |
| pg_dump final pre-cutover | Obligatorio |
| Migrar BD CERT | `alembic upgrade head` |
| Desplegar compose convergencia | Frontend + backend |
| Validar admin + CC + login | Checklist operativo |

| Rollback |
|---|
| Restore pg_dump pre-cutover |
| Checkout imágenes `e8cb853` |
| NO destruir dump |

---

## Qué NO hacer

- Merge masivo `git merge e8cb853` en convergencia
- `git pull` sobre detached HEAD en worktrees CERT
- `alembic upgrade` sobre `D:\EMPLEADOS_IA_CERT` sin staging previo
- `git tag -f` sobre certificados
- `git add .` en commits de integración

---

## Criterios de éxito global

| Criterio | Métrica |
|---|---|
| Login | PASS admin superadmin |
| Migraciones | head `1341a1b2c3d4e` |
| Tests | >= 1240 passed, 0 failed |
| V1 CERT | `e8cb853` intacto hasta cutover |
| V2 tag | `fase2-candidato-final-certificado` sin mover |
| UI login hotfix | Marcadores `password-toggle`, `Olvid`, 401 ES |

---

## Recomendación final

| Veredicto integración |
|---|
| **GO condicionado** — iniciar **solo Bloque 0** en entorno CERT (pg_dump) y **Bloque 1** en rama `cursor/eiaax-convergencia-v1-v2` |

**Siguiente acción autorizada:** Bloque 0 (pg_dump CERT) + Bloque 1 (cherry-pick login) — **no antes de aprobación explícita**.
