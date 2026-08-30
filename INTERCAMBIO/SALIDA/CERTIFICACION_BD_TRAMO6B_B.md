# CERTIFICACIÓN BD / MIGRACIONES — TRAMO 6B (Agente B)

**Fecha:** 2026-08-30  
**SHA congelado auditado:** `118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8`  
**Commit:** `docs(tramo6b): entregable Auditor, Fábrica y ciclo de mejora`  
**Rama auditoría:** `audit-tramo6b-b` (solo entregable; **central NO modificada**)

---

## 1. Resumen ejecutivo

| Criterio | Resultado |
|----------|-----------|
| Alembic heads | **1** (`14b1c2d3e4f5`) |
| Revision IDs únicas (51 total) | **PASS** (0 duplicados) |
| Cadena 1391 → 1400/6b06 → 14b0 → 14b1 | **PASS** |
| FK / índices / constraints (aplicación) | **PASS** (upgrade sin error) |
| Instalación BD limpia (SQLite) | **PASS** |
| Actualización desde Tramo 6A (`1391`) | **PASS** |
| Datos preservados en upgrade | **PASS** (evidencia org) |
| Ledger ↔ schema_repair ↔ head | **PASS** |
| migration_control (fresh DB) | **7 passed** |
| PostgreSQL roundtrip | **PENDIENTE POR ENTORNO** |
| **Veredicto** | **APTO** (SQLite certificado; PG pendiente) |

---

## 2. Cadena Alembic real (Tramo 6B)

```text
1340a1b2c3d4e  (Implementación éxito cliente — entrada Tramo 4/5)
        ↓
1391a1b2c3d4e  (Mesa de Ayuda MB-12)          ← HEAD Tramo 6A
    ┌───┴───┐
    ↓       ↓
1400a1b2c3d4e  6b06a1b2c3d4e  (Auditor MVP | Fábrica MB-06)
    └───┬───┘
        ↓
14b0c1d2e3f4   (merge vacío)
        ↓
14b1c2d3e4f5   (employee_improvement_traces)   ← HEAD Tramo 6B
```

### Tabla de dependencias

| revision | archivo | down_revision |
|----------|---------|---------------|
| `1391a1b2c3d4e` | `1391a1b2c3d4e_mesa_ayuda_soporte_mb12.py` | `1340a1b2c3d4e` |
| `1400a1b2c3d4e` | `1400a1b2c3d4e_employee_auditor_mvp.py` | `1391a1b2c3d4e` |
| `6b06a1b2c3d4e` | `6b06a1b2c3d4e_employee_lifecycle_factory_mb06.py` | `1391a1b2c3d4e` |
| `14b0c1d2e3f4` | `14b0c1d2e3f4_merge_factory_auditor_mb06.py` | (`6b06a1b2c3d4e`, `1400a1b2c3d4e`) |
| `14b1c2d3e4f5` | `14b1c2d3e4f5_auditor_factory_improvement_trace.py` | `14b0c1d2e3f4` |

**Nota:** `1390a1b2c3d4e` **NO** existe en esta cadena (renombrado histórico → `1400a1b2c3d4e`).

---

## 3. Objetos creados / alterados (Tramo 6B)

### 1391 — Mesa de Ayuda
- Tablas: `support_sla_policies`, `support_cases`, `support_case_history`, `support_case_comments`, `support_auto_dedup`
- FK: `organizations`, `users`, `support_cases`
- Índices: por org, caso, estado, dedup
- UQ: `uq_support_dedup_org_key`

### 1400 — Auditor MVP
- Tablas: `employee_audit_policies`, `employee_audit_runs`, `employee_audit_assessments`, `employee_audit_findings`
- FK: org, employees, users, automations, notifications, runs/assessments
- UQ: `uq_employee_audit_policy_org_emp`, `uq_employee_audit_run_idempotency`, `uq_employee_audit_assessment_run_emp`
- Índices: org, status, severity, health, started_at

### 6b06 — Fábrica MB-06
- Alter: `employee_versions`, `employee_test_cases`, `ai_employees` (+`last_training_at`)
- Tablas nuevas (si no existen): `employee_trainings`, `employee_factory_approvals`
- FK: org, employees, users, approval_requests, test_runs
- Índices: org, employee, kind

### 14b0 — Merge
- Sin DDL (upgrade/downgrade `pass`)

### 14b1 — Ciclo de mejora
- Tabla: `employee_improvement_traces`
- FK: org, `ai_employees`, `employee_audit_runs`, `employee_audit_findings`, users, `employee_versions`, `approval_requests`, `employee_test_runs`
- UQ: `uq_emp_improvement_idempotency` (org + idempotency_key)
- Índices: org, employee, finding, status

**Orden de dependencias FK en 14b1:** requiere tablas de **1400** (audit) y **6b06** (versions, test_runs) — coherente con merge previo.

---

## 4. Ledger y schema_repair

| Artefacto | Valor |
|-----------|--------|
| `migration_ledger.json` `baseline_head` | `14b1c2d3e4f5` |
| `schema_repair.py` `HEAD_REVISION` | `14b1c2d3e4f5` |
| `protected_revisions` (Tramo 6B) | `1391`, `1400`, `6b06`, `14b0`, `14b1` incluidos |
| `validate_migration_ledger()` | head=`14b1c2d3e4f5`, 51 revisiones en repo = ledger |

---

## 5. Evidencia reproducible (SQLite)

### 5.1 Heads únicos

```bash
cd backend && python3 -m alembic heads
# 14b1c2d3e4f5 (head)
```

### 5.2 Revision IDs únicas

```bash
cd backend/alembic/versions && python3 -c "
import re,glob,collections
r=collections.defaultdict(list)
for f in glob.glob('*.py'):
    m=re.search(r'revision[^=]*=\s*[\"\\']([^\"\\']+)[\"\\']', open(f).read())
    if m: r[m.group(1)].append(f)
print('duplicates', [k for k,v in r.items() if len(v)>1])
"
# duplicates []
```

### 5.3 Instalación limpia + roundtrip completo Tramo 6B

```bash
rm -f /tmp/tramo6b_clean.db
export DATABASE_URL=sqlite:////tmp/tramo6b_clean.db
cd backend
python3 -m alembic upgrade head          # PASS
python3 -m alembic downgrade 14b0c1d2e3f4  # PASS
python3 -m alembic downgrade 6b06a1b2c3d4e  # PASS
python3 -m alembic downgrade 1391a1b2c3d4e  # PASS (rama fábrica)
python3 -m alembic upgrade head          # PASS
```

### 5.4 Downgrade -1 + re-upgrade (última revisión)

```bash
rm -f /tmp/tramo6b_roundtrip.db
export DATABASE_URL=sqlite:////tmp/tramo6b_roundtrip.db
cd backend
python3 -m alembic upgrade head
python3 -m alembic downgrade -1
python3 -m alembic upgrade head
python3 -m alembic current
# 14b1c2d3e4f5 (head)
```

### 5.5 Actualización desde Tramo 6A + datos preservados

```bash
# Upgrade a 1391, insert org, upgrade a head
# Resultado: org count 1→1, tabla employee_improvement_traces existe, head 14b1
# FROM_6A_PASS
```

### 5.6 migration_control

```bash
rm -f /tmp/tramo6b_migctl.db
export DATABASE_URL=sqlite:////tmp/tramo6b_migctl.db JWT_SECRET=test-secret
cd /workspace && python3 -m pytest tests/test_migration_control.py -q
# 7 passed
```

---

## 6. PostgreSQL

| Prueba | Resultado |
|--------|-----------|
| `psql` / `pg_isready` | No disponible en entorno de auditoría |
| Roundtrip PostgreSQL | **PENDIENTE POR ENTORNO** |

No se declara PASS PostgreSQL.

---

## 7. P0 / P1 / P2

### P0 — Bloqueantes

| ID | Hallazgo | Evidencia | Estado |
|----|----------|-----------|--------|
| — | Sin hallazgos P0 | Cadena aplicable, 1 head, upgrade/downgrade OK | **0 P0** |

### P1 — Importantes (no bloquean migración en SQLite)

| ID | Hallazgo | Evidencia | Reprodución |
|----|----------|-----------|-------------|
| P1-01 | Comentario de cabecera en `6b06a1b2c3d4e_employee_lifecycle_factory_mb06.py` indica `Revises: 1330b1b2c3d4f` pero `down_revision` real es `1391a1b2c3d4e` | Líneas 3–4 del archivo vs `revision`/`down_revision` | Abrir archivo; `alembic history` confirma padre `1391` |
| P1-02 | `tests/test_migration_control.py` falla si `DATABASE_URL` apunta a BD sin migración MB-06 (`last_training_at` missing) | Error SQLAlchemy al usar BD residual | Ejecutar tests sin fresh DB vs con `DATABASE_URL=sqlite:////tmp/...` |

### P2 — Menores / tooling

| ID | Hallazgo | Evidencia |
|----|----------|-----------|
| P2-01 | `python3 scripts/validate_migrations.py` desde `backend/` → `ModuleNotFoundError: scripts` | Ejecutar desde `/workspace` con `python3 -m` o PYTHONPATH |

---

## 8. Restricciones cumplidas

| Restricción | Cumplido |
|-------------|----------|
| NO modificar central | Sí — auditoría en SHA congelado, solo entregable |
| NO corregir central | Sí — hallazgos documentados, sin parches |
| PostgreSQL PASS solo con PG real | Sí — PENDIENTE |
| Centro de Control / main / V1 | No auditados aquí (alcance BD/migraciones) |

---

## 9. Comandos de verificación rápida (General)

```bash
git checkout 118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8
cd backend && python3 -m alembic heads
export DATABASE_URL=sqlite:///./cert_tramo6b.db
python3 -m alembic upgrade head
python3 -m alembic downgrade -1 && python3 -m alembic upgrade head
cd /workspace && DATABASE_URL=sqlite:///./cert_tramo6b.db python3 -m pytest tests/test_migration_control.py -q
```

---

## 10. Veredicto final

**TRAMO 6B — CERTIFICACIÓN BD/MIGRACIONES: APTO (SQLite)**  
**PostgreSQL: PENDIENTE POR ENTORNO**  
**P0: 0 | P1: 2 | P2: 1**
