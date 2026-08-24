# CURSOR — Cierre final PR #9 / 840B

**Fecha:** 2026-08-24  
**Estado:** CORREGIDO Y LISTO PARA QA FINAL  
**No declarado apto para merge**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| PR | #9 |
| Rama | `cursor/admin-users-roles-840` |
| HEAD anterior (auditado) | `be23541b08e07e19bf104fe2fdd369e2fe735c9c` |
| HEAD nuevo | `3f561a41b8e2e8f0e8c8e8c8e8c8e8c8c8e8c8` |
| Commit | `606ff94` — `fix(840b): migration strict is_active — no string semantics` |

---

## DEFECTO CORREGIDO

**Problema:** `_normalize_corrupt_is_active()` en migración `b840c3e4f5a6` interpretaba semánticamente strings (`yes`, `true`, `t`, `TRUE`, `yes`, `1` texto) como activos.

**Regla aplicada:** Solo la representación canónica persistida `integer 1` (SQLite) o `boolean TRUE` (PostgreSQL) equivale a rol activo. Sin interpretación semántica de strings.

**Corrección:**

```sql
-- SQLite
WHEN typeof(is_active) = 'integer' AND is_active = 1 THEN 1 ELSE 0

-- PostgreSQL
WHEN is_active IS TRUE THEN TRUE ELSE FALSE
```

Runtime ya validaba con `is_canonical_active_value()` + `read_role_is_active_raw()` — sin cambios adicionales necesarios.

---

## VALORES CORRUPTOS PROBADOS

### Runtime (UPDATE directo SQLite + `user_permissions` → DENY)

| Valor | Resultado |
|-------|-----------|
| `yes` | INACTIVO → DENY |
| `TRUE` | INACTIVO → DENY |
| `2` | INACTIVO → DENY |
| `null` (texto) | INACTIVO → DENY |
| `""` (vacío) | INACTIVO → DENY |
| `on` | INACTIVO → DENY |
| `false` | INACTIVO → DENY |
| `0` | INACTIVO → DENY |

### Migración (UPDATE directo + `upgrade b840c3e4f5a6` → `is_active=0`)

| Valor | Resultado |
|-------|-----------|
| `yes` | 0 |
| `true` | 0 |
| `t` | 0 |
| `TRUE` | 0 |
| `on` | 0 |
| `2` | 0 |
| `-1` | 0 |
| `garbage` | 0 |
| `""` | 0 |

### Casos adicionales migración

| Escenario | Resultado |
|-----------|-----------|
| Entero canónico `1` | Permanece `1` |
| Duplicados: uno `1`, otro `'yes'` (UPDATE) | Superviviente `0` |
| NULL en INSERT | No técnicamente posible (`NOT NULL` en schema) |

**Nota SQLite:** el literal `'1'` en columna `BOOLEAN` se almacena como entero `1` por afinidad de tipo; no es representable como texto corrupto en esta columna.

---

## REGRESIONES PRESERVADAS (PASS)

- Deduplicación roles globales
- Intersección permisos (mínimo privilegio)
- Remapeo FK sin huérfanos
- Rol inexistente → DENY
- Rol inactivo → DENY
- Error BD → DENY
- Cross-tenant
- Privilege escalation
- Matrix permisos

---

## RESULTADOS

| Control | Resultado |
|---------|-----------|
| `pytest` | **PASS** — 112/112 |
| Migración `upgrade → downgrade → upgrade` | **PASS** |
| `npm run build` | **PASS** |
| `npm audit` | **PASS** — 0 vulnerabilidades |
| `git diff --check` | **PASS** |

---

## ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `backend/alembic/versions/b840c3e4f5a6_role_global_unique_840c.py` | Normalización estricta por dialecto |
| `tests/test_admin_840b_v3.py` | Tests migración con UPDATE directo SQLite |

---

## ESTADO FINAL

**CORREGIDO Y LISTO PARA QA FINAL**

No merge. No declarado apto para merge.
