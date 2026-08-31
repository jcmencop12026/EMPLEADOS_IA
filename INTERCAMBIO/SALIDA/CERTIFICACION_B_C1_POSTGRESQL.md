# CERTIFICACIÓN B — C1 DATOS (PostgreSQL)

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** B (BD / migraciones / datos)  
**Misión:** Certificación datos C1  
**Prioridad:** CRÍTICA  
**Fecha UTC:** 2026-08-31  

---

## SHA C1

| Campo | Valor |
|---|---|
| SHA único certificado | `25ad1021ee6ea0322aceb0622252e7b748706d32` |
| Mensaje | `feat(c1): base segura convergencia V1+V2 con hotfix login selectivo` |
| Alembic V1 esperado | `d1e2f3a4b5c6` |
| Alembic V2/C1 esperado | `1341a1b2c3d4e` |

---

## Resumen ejecutivo (SALIDA)

| Campo | Resultado |
|---|---|
| PostgreSQL real | **SÍ** |
| Backup | **SÍ** |
| Backup validado | **SÍ** |
| Alembic inicial | `d1e2f3a4b5c6` |
| Alembic final | `1341a1b2c3d4e` |
| Head único | **SÍ** (`1341a1b2c3d4e`) |
| `bootstrap_permissions` | **SÍ** (idempotente ×2) |
| Integridad (sin pérdida datos semilla) | **SÍ** |
| Multiempresa | **SÍ** |
| Backfill `6b06` | **SÍ** |
| `validate_migrations` | **PASS** |

---

## VEREDICTO

# C1 DATOS APTO

---

## Restricciones cumplidas

| Restricción | Cumplida |
|---|---|
| No modificar `D:\EMPLEADOS_IA_CERT` / BD CERT original | **SÍ** |
| No migrar directamente BD CERT original | **SÍ** |
| No modificar V1/V2 certificados (solo lectura SHA C1) | **SÍ** |
| Entorno/base aislada y recuperable | **SÍ** (`empleados_ia_c1_b_cert`) |
| No ejecutar downgrade destructivo | **SÍ** |
| No modificar producto / no corregir código | **SÍ** |
| No iniciar C2 | **SÍ** |

---

## Entorno PostgreSQL

| Campo | Valor |
|---|---|
| Cliente | PostgreSQL 16.15 (Ubuntu) |
| Servidor | PostgreSQL 16.15 |
| Host | `localhost:55432` (entorno Cloud Agent) |
| Base aislada | `empleados_ia_c1_b_cert` (creada y destruible; no CERT) |
| Herramientas | `psql`, `pg_dump`, `pg_restore` instaladas y usadas |

---

## Backup previo (V1, antes de `upgrade head`)

| Campo | Valor |
|---|---|
| Origen | Copia aislada `empleados_ia_c1_b_cert` en revisión `d1e2f3a4b5c6` |
| Formato | `pg_dump -Fc` |
| Archivo local | `INTERCAMBIO/SALIDA/c1_cert_artifacts/c1_v1_pre_upgrade.dump` |
| Tamaño | 184 845 bytes |
| SHA-256 | `65d17b4cf846e4ba756f42c0402b5525974da4eb02790686e848bbae2fff0109` |
| Validación | `pg_restore --list` → **438 entradas** (PASS) |
| Credenciales | No expuestas en este informe |

---

## Cadena de certificación ejecutada

1. `DROP/CREATE DATABASE empleados_ia_c1_b_cert`
2. `alembic upgrade d1e2f3a4b5c6` → `alembic_version = d1e2f3a4b5c6`
3. Semilla V1-compatible (SQL directo: 2 orgs, 2 users, 2 `ai_employees`, 2 `employee_versions` sin `organization_id` — columna aún no existente en V1)
4. Conteos pre-upgrade registrados
5. Backup `pg_dump -Fc` + validación `pg_restore --list` + SHA-256
6. `alembic upgrade head` → `alembic_version = 1341a1b2c3d4e`
7. `alembic heads` → una sola cabeza `1341a1b2c3d4e`
8. `scripts/validate_migrations.py` → PASS
9. `bootstrap_permissions` ejecutado **dos veces** (idempotencia verificada)
10. Verificación integridad, multiempresa, backfill `6b06`, FK muestra, tablas V2 muestra

**Runner reproducible:** `INTERCAMBIO/SALIDA/c1_cert_artifacts/run_c1_b_cert.py`  
**Resultados JSON:** `INTERCAMBIO/SALIDA/c1_cert_artifacts/cert_results.json`

---

## Conteos de datos (semilla controlada)

| Tabla | Pre-upgrade (V1) | Post-upgrade (head) | Pérdida |
|---|---|---|---|
| `organizations` | 2 | 2 | No |
| `users` | 2 | 2 | No |
| `ai_employees` | 2 | 2 | No |
| `employee_versions` | 2 | 2 | No |
| `permissions` | — | 181 | Bootstrap esperado |
| `roles` | — | 4 | Bootstrap esperado |

---

## `bootstrap_permissions`

| Ejecución | Permisos | Roles sistema |
|---|---|---|
| 1ª | 181 | 4 |
| 2ª | 181 | 4 |
| Idempotente | **SÍ** | **SÍ** |

---

## Backfill migración `6b06a1b2c3d4e`

| Control | Resultado |
|---|---|
| `employee_versions.organization_id` NULL tras upgrade | **0** (2 filas backfilled) |
| `employee_test_cases.organization_id` NULL | **0** |
| Columna `ai_employees.last_training_at` presente | **SÍ** |
| Backfill coherente con `ai_employees.organization_id` | **SÍ** |

---

## Multiempresa

| Organización | `ai_employees` propios |
|---|---|
| Org C1 Cert A | 1 |
| Org C1 Cert B | 1 |
| Cruce indebido detectado | **No** |

---

## Estructuras V2 (muestra post-head)

| Tabla | Existe |
|---|---|
| `employee_trainings` | SÍ |
| `employee_factory_approvals` | SÍ |
| `comm_channels` (MB-11 / 1341) | SÍ |
| `gov_classification_levels` (1350) | SÍ |

---

## FK / constraints (muestra)

| Control | Resultado |
|---|---|
| `ai_employees` sin `organizations` huérfanos | **0 violaciones** |

---

## P0 / P1 / P2

| ID | Severidad | Estado | Descripción |
|---|---|---|---|
| — | P0 | Cerrado | Sin bloqueadores de datos en certificación C1 aislada |
| PG-CERT-PROD | P1 | **Abierto (integración)** | Antes de migrar la BD CERT real de producción: repetir `pg_dump` validado sobre origen real (fuera de esta certificación aislada) |
| C1-BOOTSTRAP-V1 | P2 | Registrado | `bootstrap()` con código C1 contra esquema solo-V1 falla (ORM espera columnas post-`6b06`); en integración real usar app alineada con revisión o semilla SQL / restore V1 |
| C2-MIGRATE | P2 | Pendiente | C2 no iniciado (mandato cumplido) |

---

## Notificación

**EIAAX — CERTIFICACIÓN B DE C1 FINALIZADA**

---

## Firma Agente B

Certificación de datos C1 sobre PostgreSQL real en entorno aislado. Veredicto: **C1 DATOS APTO**. Sin cambios de producto. C2 no iniciado.
