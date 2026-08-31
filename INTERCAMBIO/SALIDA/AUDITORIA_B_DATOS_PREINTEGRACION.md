# EIAAX / EMPLEADOS_IA — AUDITORÍA B DATOS PRE-INTEGRACIÓN

**Agente:** B  
**Modo:** SOLO LECTURA (análisis git / migraciones / modelos)  
**Fecha:** 2026-08-31  
**Sin ejecución:** migraciones destructivas, modificaciones BD, cambios de código

---

## 1. SHAs comparados

| Versión | SHA | Commit | Alembic head |
|---------|-----|--------|--------------|
| **V1** | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` | `docs: HEAD final 25d73fc en informe candidata R2` | `d1e2f3a4b5c6` |
| **V2** | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` | `docs: HEAD final convergencia` | `1341a1b2c3d4e` |

---

## 2. Resumen ejecutivo

V2 **extiende** V1 con una cadena Alembic **continua** desde el head V1 (`d1e2f3a4b5c6`) hasta `1341a1b2c3d4e`. No hay divergencia de heads entre repositorios: V1 termina donde V2 continúa.

Las migraciones V2 son **predominantemente aditivas** (nuevas tablas, nuevas columnas nullable o con `server_default`, backfills SQL). **No se detectaron** `drop_table` ni `drop_column` en funciones `upgrade()` de las 32 migraciones nuevas.

**Veredicto:** **APTO DATOS PARA CONVERGENCIA** — con prerequisitos operativos documentados (backup, verificar `alembic_version`, `bootstrap_permissions` post-upgrade).

---

## 3. Alembic

### 3.1 Heads

| SHA | Heads | Head |
|-----|-------|------|
| V1 `e8cb853` | **1** | `d1e2f3a4b5c6` |
| V2 `dc1e6cda` | **1** | `1341a1b2c3d4e` |

**Divergencia de heads entre V1 y V2:** **NO** — V2 es extensión lineal ramificada desde `d1e2f3a4b5c6`.

### 3.2 Archivos de migración

| Métrica | V1 | V2 | Delta |
|---------|----|----|-------|
| Archivos `versions/` | 21 | 53 | **+32** |
| `migration_ledger` `baseline_head` | `d1e2f3a4b5c6` | `1341a1b2c3d4e` | actualizado |
| `schema_repair` `HEAD_REVISION` | `d1e2f3a4b5c6` | `1341a1b2c3d4e` | actualizado |
| Revisiones protegidas ledger | 21 | 53 | +32 |

### 3.3 Migraciones que agrega V2 (32 revisiones)

Desde `d1e2f3a4b5c6` hasta `1341a1b2c3d4e`:

| Rev | Bloque / dominio |
|-----|------------------|
| `1110a1b2c3d4e` | FinOps trazabilidad (opportunity_id, alertas presupuesto) |
| `1120a1b2c3d4e` | Señales reales / fuentes |
| `1200a1b2c3d4e` | Línea base e impacto |
| `1210b2c3d4e5f` | Valoración económica / ROI |
| `1220a1b2c3d4e` | Diagnóstico transversal |
| `1240c3d4e5f6a` | Inteligencia externa |
| `1250a1b2c3d4e` | Merge convergencia post-V1 fase 1 |
| `1250b1c2d3e4f` | Merge 1220 + 1240 |
| `1250f1a2b3c4d` | Merge convergencia final post-V1 |
| `1260a1b2c3d4e` | Aprendizaje / repriorización |
| `1270a1b2c3d4e` | Multiproveedor observabilidad |
| `1280a1b2c3d4e` | Modelo comercial valor |
| `1280b2c3d4e5f` | Comercial scope externo |
| `1290a1b2c3d4e` | Optimización |
| `1300a1b2c3d4e` | Seguridad MFA / sesiones |
| `1310a1b2c3d4e` | Segmentación / planes |
| `1320a1b2c3d4e` | TCO / aliados |
| `1330a1b2c3d4e` | Integraciones / conectores |
| `1330b1b2c3d4f` | Wiring integraciones ↔ gobierno |
| `1340a1b2c3d4e` | Implementación / éxito cliente |
| `1350a1b2c3d4e` | Gobierno datos / privacidad |
| `1360a1b2c3d4e` | Continuidad / resiliencia |
| `1365a1b2c3d4e` | Merge 1350 + 1360 |
| `1370a1b2c3d4e` | Identidad SSO/OIDC/SAML |
| `1380a1b2c3d4e` | SCIM 2.0 |
| `1391a1b2c3d4e` | Mesa de Ayuda MB-12 |
| `1400a1b2c3d4e` | Auditor empleados MVP |
| `6b06a1b2c3d4e` | Fábrica / ciclo de vida MB-06 |
| `14b0c1d2e3f4` | Merge fábrica + auditor |
| `14b1c2d3e4f5` | Trazabilidad auditor → fábrica |
| `1507a1b2c3d4e` | Planificador MB-07 |
| `1341a1b2c3d4e` | Comunicaciones MB-11 |

### 3.4 Orden correcto de migración

**`alembic upgrade head`** desde `d1e2f3a4b5c6` aplica la cadena completa; Alembic resuelve merges (`1250a`, `1250b`, `1250f`, `1365`, `14b0`). **No reordenar manualmente.**

---

## 4. Cambios destructivos (upgrade)

Análisis estático de las 32 migraciones V2 (`upgrade()` únicamente):

| Tipo | En upgrade() |
|------|----------------|
| `drop_table` | **0** |
| `drop_column` | **0** |
| `alter_column nullable=False` sin backfill | **0** detectados |
| `add_column nullable=False` sin `server_default` | **0** detectados |

**Cambios en tablas V1 existentes (aditivos / backfill):**

| Migración | Tabla V1 | Cambio |
|-----------|----------|--------|
| `1110` | `finops_records` | `opportunity_id` nullable + FK |
| `1110` | `finops_budgets` | `alert_threshold_pct` NOT NULL default `90` |
| `1120` | `proactive_signals` | `source_id` nullable; `modo_ingesta` NOT NULL default `REAL` |
| `6b06` | `employee_versions`, `employee_test_cases`, `ai_employees` | columnas nullable + UPDATE backfill `organization_id` |
| `1330b` | `integration_connectors` | `gov_catalog_entry_id` nullable + FK |
| `1310`, `1370`, `1380` | `users`, `organizations` | extensiones aditivas (tablas nuevas dominio) |

**Downgrade V2 → V1:** **destructivo** — elimina ~169 tablas nuevas y columnas V2. No usar en producción sin backup y ventana de mantenimiento.

---

## 5. Modelos y dominios

### 5.1 Archivos modelo nuevos en V2 (20)

`baseline_models`, `commercial_models`, `communications_models`, `consumption_planner_models`, `continuidad_models`, `diagnostic_models`, `employee_audit_models`, `external_models`, `governance_models`, `identity_models`, `implementacion_models`, `integration_models`, `learning_models`, `optimization_models`, `scim_models`, `security_models`, `segmentation_models`, `support_models`, `tco_models`, `valuation_models`

### 5.2 Modelos V1 extendidos (sin ruptura de `models.py` base)

| Archivo | Cambio |
|---------|--------|
| `models.py` (users, orgs, roles) | **Sin diff** V1↔V2 |
| `finops_models.py` | +24 líneas (presupuesto alert states) |
| `llm_models.py` | +41 líneas |
| `orchestration_models.py` | +45 líneas (factory approvals, etc.) |
| `opportunity_models.py` | +33 líneas |
| `notifications.py` | +6 líneas (eventos soporte/auditor/comunicaciones) |
| `automation_models.py` | **Sin cambio** |
| `knowledge_models.py` | **Sin cambio** |

### 5.3 Tablas nuevas (migraciones V2)

**~169 tablas** creadas en `upgrade()` de migraciones V2 (dominios Fase 2 completos).

### 5.4 Constraints / FK / índices

- Nuevas tablas incluyen FK a `organizations.id` sistemáticamente (multiempresa).
- UUID/tipos: IDs `String(36)` / `character varying` — **igual que V1** (no migración a tipo UUID nativo PG).
- Índices y UNIQUE en dominios críticos verificados en certificación PG previa (`uq_comm_template_org_codigo`, etc.).

### 5.5 Enums

Sin enums PostgreSQL nativos nuevos detectados; estados en columnas `String` con convención textual (coherente con V1).

---

## 6. Seeds, RBAC, multiempresa

| Área | V1 → V2 |
|------|---------|
| **Organizations** | `slug` ya en V1 (`c1a2b3c4d5e6`); modelo sin cambio |
| **Users / roles base** | `models.py` sin cambio |
| **Permisos** | `permissions.py` **+418 líneas** — nuevos conjuntos Fase 2 (comunicaciones, soporte, auditor, TCO, gobierno, SCIM, etc.) |
| **seed_permissions.py** | Sin diff de archivo (lógica en `bootstrap_permissions`) |
| **Multiempresa** | Todas las tablas V2 con `organization_id`; backfills en `6b06` |

**Post-upgrade obligatorio:** ejecutar `bootstrap_permissions()` (o arranque bootstrap) para registrar permisos V2 — **no implica pérdida de datos**, pero RBAC V2 incompleto sin este paso.

---

## 7. Dominios revisados

| Dominio | Compatibilidad V1→V2 upgrade |
|---------|------------------------------|
| Auditoría (`audit_logs`) | Extendida (SCIM audit); sin drop |
| IA / proveedores (`llm_*`) | Tablas nuevas + extensión modelo |
| Conocimiento (`knowledge_*`) | **Sin cambio modelo V1** |
| Automatizaciones | **Sin cambio modelo V1** |
| Notificaciones | Eventos ampliados en código; esquema V1 preservado |
| FinOps / MB-07 / TCO | Nuevas tablas + columnas aditivas en `finops_*` |
| Comunicaciones MB-11 / Soporte MB-12 | Tablas nuevas |
| Consumo IA (MB-07) | Tablas `consumption_planner_*` nuevas |

---

## 8. Riesgo de pérdida de datos en convergencia

| Escenario | Pérdida de datos |
|-----------|------------------|
| `alembic upgrade head` desde V1 `@ d1e2f3a4b5c6` | **NO** — aditivo |
| Datos V1 en tablas core (`users`, `organizations`, `ai_employees`, `work_plans`, `finops_records`, etc.) | **Preservados** |
| Datos solo en tablas V2 nuevas | No existen en V1 — N/A |
| `alembic downgrade` a `d1e2f3a4b5c6` | **SÍ** — destructivo (tablas/columnas V2) |
| Stamp incorrecto / BD `create_all` sin Alembic | **Riesgo P1** — preflight puede abortar |

**Convergencia de código sin upgrade BD:** **NO APTO** — aplicación V2 requiere esquema `1341a1b2c3d4e`.

---

## 9. PostgreSQL

| Aspecto | Evaluación |
|---------|------------|
| Compatibilidad PG | **SÍ** — V2 certificado en PostgreSQL 16.15 (auditoría previa agente B) |
| Tipos datetime | `DateTime(timezone=True)` consistente |
| SQLite-only paths | Tests usan PG; producto soporta ambos |
| Rollback/recuperación | Backup + restore; downgrade no recomendado en prod |

---

## 10. Pruebas recomendadas (antes / después)

### Antes de upgrade en entorno representativo

1. `SELECT version_num FROM alembic_version` → debe ser `d1e2f3a4b5c6`
2. Backup completo BD (pg_dump)
3. Conteos baseline: `organizations`, `users`, `ai_employees`, `work_plans`, `finops_records`, `opportunities`, `notifications`
4. `run_database_preflight` / `validate_migrations` en staging

### Después de `alembic upgrade head`

1. `alembic_version = 1341a1b2c3d4e`
2. Recontar tablas core — deben coincidir con baseline
3. `bootstrap_permissions` + verificar permisos V2 en BD
4. Suite focal PG: `test_migration_control`, `test_finops_*`, `test_consumption_planner_mb07`, `test_tco_1320`, tenant/cross-org
5. Smoke API: login, org scope, centro control, finops dashboard

**No repetir** suite completa si ya certificada en `dc1e6cda` — focal pre/post upgrade en staging es suficiente.

---

## 11. Clasificación P0 / P1 / P2

### P0 — 0 (bajo prerequisito V1 estándar)

Sin cambios destructivos en `upgrade()` detectados. Riesgo P0 solo si BD V1 **no** está en `d1e2f3a4b5c6` (revision huérfana, esquema manual incompatible).

### P1 — 3 (operativos pre-convergencia)

| ID | Descripción |
|----|-------------|
| P1-B-PRE-01 | Verificar `alembic_version = d1e2f3a4b5c6` antes de upgrade |
| P1-B-PRE-02 | Ejecutar `bootstrap_permissions` tras upgrade para RBAC V2 |
| P1-B-PRE-03 | Backup obligatorio; downgrade a V1 head es destructivo para datos V2 |

### P2 — 2

| ID | Descripción |
|----|-------------|
| P2-B-PRE-01 | Backfill `6b06`: filas huérfanas sin `ai_employees` podrían dejar `organization_id` NULL |
| P2-B-PRE-02 | Funcionalidades V2 vacías hasta configuración/seed de módulos nuevos (no es pérdida V1) |

---

## 12. Respuestas a los 10 puntos del mandato

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 1 | Migraciones que agrega V2 | **32 revisiones**, ~169 tablas nuevas (ver §3.3) |
| 2 | Divergencia heads | **NO** — V1 head = parent de cadena V2 |
| 3 | Convergencia puede perder datos | **NO** en upgrade forward; **SÍ** en downgrade |
| 4 | Cambios destructivos upgrade | **NO** detectados |
| 5 | Nullable / non-nullable | Adiciones con default o nullable; sin endurecimiento sin default |
| 6 | Defaults | `server_default` en columnas NOT NULL nuevas (ej. `alert_threshold_pct=90`, `modo_ingesta=REAL`) |
| 7 | PostgreSQL | **Compatible** (certificado V2 PG real) |
| 8 | Rollback/recuperación | Backup/restore; downgrade destruye esquema V2 |
| 9 | Orden migración | `alembic upgrade head` desde `d1e2f3a4b5c6` |
| 10 | Pruebas necesarias | Backup + preflight + upgrade staging + focal PG + bootstrap_permissions |

---

## VEREDICTO

```
APTO DATOS PARA CONVERGENCIA

Condiciones:
- BD V1 en alembic_version = d1e2f3a4b5c6
- Backup previo
- alembic upgrade head (no stamp salvo reparación documentada)
- bootstrap_permissions post-upgrade
- Validación focal post-upgrade en staging PostgreSQL
```

---

## Evidencia (comandos reproducibles, solo lectura)

```bash
git rev-parse e8cb853a2c447fd5e136a0907e44d68ce2c8cf81
git rev-parse dc1e6cda8d3de6695d9a052a2a13afdb5f431077

git checkout e8cb853 && cd backend && python3 -m alembic heads
git checkout dc1e6cda && cd backend && python3 -m alembic heads
git checkout dc1e6cda && cd backend && python3 -m alembic history -r d1e2f3a4b5c6:head

comm -23 \
  <(git ls-tree -r --name-only dc1e6cda backend/alembic/versions/ | sort) \
  <(git ls-tree -r --name-only e8cb853 backend/alembic/versions/ | sort)
```

---

**EIAAX / EMPLEADOS_IA. Auditoría B datos pre-integración terminada.**
