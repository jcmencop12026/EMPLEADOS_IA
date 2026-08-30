# EMPLEADOS IA — REAUDITORÍA GATE POST-6D BD/MIGRACIONES

**Agente:** B (BD/Migraciones)  
**Tipo:** SOLO LECTURA / CERTIFICACIÓN  
**SHA congelado:** `7ce2f343e35ebc75850570af7a1fa071f089bb7a`  
**Rama auditoría:** `reaudit-post6d-b`  
**Fecha:** 2026-08-30  
**Central:** NO modificada

---

## 1. Alcance

Certificar migraciones Alembic, `validate_migrations.py` portable, y determinar **independientemente** la causa de los 4 fallos de regresión reportados por General en `CURSOR_FASE2_GATE_CONSOLIDADO_POST6D.md` (1189 passed, 4 skipped, 4 failed atribuidos a `employee_instructions` UNIQUE + SQLite session-scoped).

---

## 2. Migraciones

### 2.1 Heads y genealogía

| Verificación | Resultado |
|--------------|-----------|
| Alembic heads | **1** |
| Head esperado | `1341a1b2c3d4e` ✓ |
| Revisiones únicas en repo | **53** (ledger protegidas = 53, `validate_migrations` repo count = 53) |
| IDs duplicados | **0** |

**Cadena post-1340 (coherente):**

```
1340a1b2c3d4e → 1391a1b2c3d4e (Mesa Ayuda, branchpoint)
  ├→ 1400a1b2c3d4e (Auditor MVP)
  └→ 6b06a1b2c3d4e (Fábrica MB-06)
1400 + 6b06 → 14b0c1d2e3f4 (merge)
14b0 → 14b1c2d3e4f5 (trazabilidad Auditor→Fábrica)
14b1 → 1507a1b2c3d4e (MB-07 Planificador)
1507 → 1341a1b2c3d4e (MB-11 Comunicaciones, HEAD)
```

### 2.2 Comentario 6b06 (G5)

Archivo `6b06a1b2c3d4e_employee_lifecycle_factory_mb06.py`:

- Cabecera: `Revises: 1391a1b2c3d4e`
- `down_revision`: `1391a1b2c3d4e`
- **Genealogía ejecutable sin cambios** respecto a la cadena central; solo corrección de documentación.

### 2.3 Ledger y schema_repair

| Artefacto | Valor |
|-----------|-------|
| `migration_ledger.json` `baseline_head` | `1341a1b2c3d4e` |
| `schema_repair.py` `HEAD_REVISION` | `1341a1b2c3d4e` |
| Coincidencia head ↔ ledger | **PASS** |

### 2.4 FK, índices, constraints (muestreo MB-11 / 802)

- `employee_instructions`: `UniqueConstraint('employee_id')` en migración `5b2eb2437398` — presente y coherente con modelo ORM.
- `comm_templates`: restricción compuesta `(organization_id, codigo)` — relevante para aislamiento de tests (ver §4).
- Migración `1341a1b2c3d4e`: tablas MB-11 (`comm_templates`, `comm_template_versions`, `communication_events`, etc.) aplican sin error en upgrade.

### 2.5 Ciclo BD (SQLite, `backend/`)

| Paso | Comando / DB | Resultado |
|------|--------------|-----------|
| BD limpia + upgrade head | `ensayo_reaudit.db` → `alembic upgrade head` | **PASS** |
| Downgrade | `1341a1b2c3d4e` → `1507a1b2c3d4e` | **PASS** |
| Re-upgrade | `1507` → `1341` (head) | **PASS** |
| Upgrade desde estado central `1507` | `ensayo_from_1507.db` stamp/upgrade | **PASS** |
| `test_migration_control.py` (7 tests) | BD fresca, `BOOTSTRAP_ADMIN_USERNAME=admin` | **7 PASS** |

---

## 3. validate_migrations (portable)

Ejecutado desde `backend/` **sin** `PYTHONPATH` manual:

```bash
cd backend && python3 scripts/validate_migrations.py
```

Salida:

```
Alembic head único: 1341a1b2c3d4e
Ledger baseline_head: 1341a1b2c3d4e
Revisiones protegidas: 53
Revisiones en repositorio: 53
```

**VALIDATE_MIGRATIONS: PASS** (`scripts/validate_migrations.py` inserta `backend/` en `sys.path` líneas 8–10).

Test gate G6 (`test_validate_migrations_runs_without_pythonpath`) coherente con ejecución manual.

---

## 4. Cuatro fallos de regresión — investigación independiente

### 4.1 Claim de General

En gate consolidado post-6D (rama distinta, HEAD `c7ef60fc…`):

- Regresión: **1189 passed, 4 skipped, 4 failed**
- Fallos atribuidos: `test_mb11_comunicaciones` ×3 + `test_admin_840b` ×1
- Causa declarada: contaminación SQLite session-scoped + **`employee_instructions` UNIQUE**

**Esta reauditoría no acepta esa atribución sin evidencia.** Se ejecutaron experimentos A–D en SHA congelado `7ce2f34`.

### 4.2 Experimento A — tests aislados, BD fresca

| Suite | Env | Resultado |
|-------|-----|-----------|
| `test_mb11_comunicaciones.py` | `BOOTSTRAP_ADMIN_USERNAME=admin_cert` (VM cert) | **4 failed, 4 passed** |
| `test_mb11_comunicaciones.py` | `BOOTSTRAP_ADMIN_USERNAME=admin` | **8 passed** |
| `test_admin_840b.py` | `admin_cert`, BD fresca | **26 passed** |

**Traza mb11 con `admin_cert` (reproducible):**

```
sqlalchemy.exc.NoResultFound: No row was found when one was required
```

Origen: consultas hardcodeadas `User.username == "admin"` en `tests/test_mb11_comunicaciones.py` (líneas 104, 133, 215, 255, 359) mientras bootstrap crea `admin_cert`. `auth_headers` usa `settings.bootstrap_admin_username` correctamente; el fallo es la búsqueda DB con literal `"admin"`.

Patrón correcto en gate: `tests/test_gate_post6d_correcciones.py` → `_admin_user()` con `settings.bootstrap_admin_username`.

**En ningún experimento A se observó `IntegrityError` en `employee_instructions`.**

### 4.3 Experimento B — secuencia mínima contaminación

| Secuencia | Resultado |
|-----------|-----------|
| `test_employee_lifecycle_factory_mb06` + `test_agent_factory_e2e` + `test_auditor_factory_cycle` + `test_mb11` (BD compartida, session client, `admin`) | **45 PASS** |
| Suite completa (`tests/`, BD fresca, `admin`) | **1193 passed, 4 skipped, 0 failed** (~15 min) |
| **Re-ejecución** `test_mb11` + `test_admin_840b` sobre **misma BD** tras suite completa (`test_reaudit_full.db`) | **3 failed** mb11, **26 passed** admin_840b |

Traza del fallo post-suite (reproducible):

```
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: comm_templates.organization_id, comm_templates.codigo
INSERT INTO comm_templates ... codigo='SLA_RIESGO' ...
```

**Contaminación SQLite session-scoped: DEMOSTRADA**, pero sobre **`comm_templates`**, no `employee_instructions`. Causa: fixture `client` con `scope="session"` en SQLite (`tests/conftest.py` 194–196) sin reset per-test (PostgreSQL sí tiene `_postgresql_test_isolation`).

### 4.4 Experimento C — suite completa BD fresca

`DATABASE_URL=sqlite:///./backend/test_reaudit_full.db`, `BOOTSTRAP_ADMIN_USERNAME=admin`:

**1193 passed, 4 skipped, 0 failed**

No reproduce los 4 fallos de General en un único paso de regresión en este SHA.

### 4.5 Experimento D — riesgo productivo

| Pregunta | Hallazgo |
|----------|----------|
| ¿Producto puede colisionar `employee_instructions`? | Código productivo (`seed_orchestration.py`, `agent_factory.py`) consulta antes de insertar; UNIQUE es constraint legítimo de dominio, no bug de migración. |
| ¿Colisión mb11 en producto? | Templates usan códigos de negocio; en producción (PostgreSQL, sesiones por request) el patrón de re-ejecución idempotente de tests no aplica igual. |
| ¿Fallo es solo aislamiento de tests? | **Sí** para UNIQUE post-suite; **Sí** para NoResultFound con `admin_cert`. |

---

## 5. Clasificación de los 4 fallos reportados

| # | Test (según General) | Clasificación | Evidencia |
|---|----------------------|---------------|-----------|
| 1 | `test_mb11_comunicaciones` (×3) | **DEFECTO DE TEST/AISLAMIENTO** | Con env cert: `NoResultFound` por `"admin"` hardcodeado. Re-run post-suite: `comm_templates` UNIQUE. **No** `employee_instructions`. |
| 2 | `test_mb11_comunicaciones` (contaje ×3 del reporte) | (mismo caso) | General agrupa 3 tests mb11; clasificación uniforme. |
| 3 | — | — | — |
| 4 | `test_admin_840b` (×1) | **INDETERMINADO** | **No reproducido** en SHA `7ce2f34` (26/26 PASS aislado y en combo post-suite). Posible fallo transitorio en rama gate o orden distinto no replicado aquí. |

**Nota:** En SHA congelado, regresión completa única paso = 0 failed. Los 4 fallos de General no son regresión de producto demostrada en este SHA; los fallos mb11 reproducibles son defectos de test/env o aislamiento SQLite.

| Categoría | Conteo |
|-----------|--------|
| REGRESIÓN PRODUCTO | 0 |
| DEFECTO TEST/AISLAMIENTO | 3 (mb11, evidencia directa) |
| DEFECTO MIGRACIÓN | 0 |
| INDETERMINADO | 1 (`test_admin_840b` según General; no reproducido) |

---

## 6. PostgreSQL

`psql` / `pg_isready` **no disponibles** en entorno Cloud Agent.

**POSTGRESQL: PENDIENTE POR ENTORNO** (no simulado PASS).

---

## 7. P0 / P1 / P2

### P0 — 0

Sin defectos de migración, head múltiple, ledger incoherente, ni regresión producto demostrada en migraciones.

### P1 — 3 (bloquean gate 6E según criterio P1=0)

| ID | Descripción |
|----|-------------|
| P1-B-01 | `test_mb11_comunicaciones.py`: username `"admin"` hardcodeado vs `BOOTSTRAP_ADMIN_USERNAME=admin_cert` → 4 FAIL reproducibles (`NoResultFound`). |
| P1-B-02 | SQLite: fixture `client` session-scoped sin reset → UNIQUE en `comm_templates` al re-ejecutar mb11 post-suite (contaminación demostrada, tabla distinta a la citada por General). |
| P1-B-03 | Fallo `test_admin_840b` reportado por General: **INDETERMINADO** (no reproducido en `7ce2f34`). |

### P2 — 2

| ID | Descripción |
|----|-------------|
| P2-B-01 | PostgreSQL real: PENDIENTE POR ENTORNO. |
| P2-B-02 | Tests SQLite usan `create_all` + bootstrap en import, no Alembic (divergencia conocida, no bloqueante migraciones). |

---

## 8. Riesgo productivo

| Área | Nivel | Nota |
|------|-------|------|
| Cadena Alembic / HEAD | Bajo | Certificado PASS |
| `employee_instructions` UNIQUE | Bajo | Constraint correcto; sin IntegrityError observado en investigación |
| Comunicaciones MB-11 | Bajo en producto | Colisiones observadas solo en re-run tests SQLite compartida |
| Entorno cert vs tests | Medio | `admin_cert` rompe mb11 por hardcode |

**RIESGO PRODUCTIVO (migraciones/BD): BAJO**  
**RIESGO GATE (tests/env): MEDIO** hasta corregir P1-B-01/B-02 y cerrar B-03.

---

## 9. Veredicto

| Ámbito | Veredicto |
|--------|-----------|
| Migraciones / BD en SHA `7ce2f34` | **CERTIFICADO — APTO** |
| Gate 6E (criterio P0=0, P1=0) | **NO APTO** — P1=3 |
| Explicación General `employee_instructions` UNIQUE | **NO DEMOSTRADA** — contaminación real apunta a `comm_templates` + hardcode `admin` |

**CONTAMINACIÓN SQLITE DEMOSTRADA:** **SÍ** (aislamiento session-scoped); **NO** en la forma atribuida por General (`employee_instructions`).

---

## SALIDA FINAL

```
SHA: 7ce2f343e35ebc75850570af7a1fa071f089bb7a
ALEMBIC HEADS: 1
ALEMBIC HEAD: 1341a1b2c3d4e
REVISIONES ÚNICAS: 53 (0 duplicados)
CADENA: PASS (1340→1391→{1400|6b06}→14b0→14b1→1507→1341)
BD LIMPIA: PASS
UPGRADE: PASS
DOWNGRADE: PASS (head→1507)
RE-UPGRADE: PASS
VALIDATE_MIGRATIONS: PASS (portable desde backend/)
4 FALLOS CLASIFICADOS: 3 DEFECTO TEST/AISLAMIENTO (mb11) + 1 INDETERMINADO (admin_840b no reproducido)
CONTAMINACIÓN SQLITE DEMOSTRADA: SÍ (comm_templates UNIQUE re-run); NO (employee_instructions como dijo General)
RIESGO PRODUCTIVO: BAJO (migraciones); MEDIO (tests/env cert)
POSTGRESQL: PENDIENTE POR ENTORNO
P0: 0
P1: 3
P2: 2
VEREDICTO: MIGRACIONES APTO — GATE 6E NO APTO (P1>0)
```

---

## 10. Evidencia reproducible (comandos)

```bash
# SHA
git checkout 7ce2f343e35ebc75850570af7a1fa071f089bb7a

# validate_migrations portable
cd backend && python3 scripts/validate_migrations.py

# mb11 falla en env cert (4 FAIL NoResultFound)
rm -f backend/test_reaudit_mb11.db
DATABASE_URL=sqlite:///./backend/test_reaudit_mb11.db \
  BOOTSTRAP_ADMIN_USERNAME=admin_cert \
  python3 -m pytest tests/test_mb11_comunicaciones.py -q

# mb11 PASS con admin
rm -f backend/test_reaudit_mb11_admin.db
DATABASE_URL=sqlite:///./backend/test_reaudit_mb11_admin.db \
  BOOTSTRAP_ADMIN_USERNAME=admin \
  python3 -m pytest tests/test_mb11_comunicaciones.py -q

# Regresión completa SHA congelado (0 failed)
rm -f backend/test_reaudit_full.db
DATABASE_URL=sqlite:///./backend/test_reaudit_full.db \
  BOOTSTRAP_ADMIN_USERNAME=admin \
  python3 -m pytest tests/ -q

# Contaminación post-suite (comm_templates UNIQUE, 3 FAIL mb11)
DATABASE_URL=sqlite:///./backend/test_reaudit_full.db \
  BOOTSTRAP_ADMIN_USERNAME=admin \
  python3 -m pytest tests/test_mb11_comunicaciones.py -q --tb=short
```

---

**EMPLEADOS IA. Reauditoría gate post-6D BD terminada.**
