# CURSOR — 1330 limpio sobre base puente definitiva

## Resumen

Pieza portátil **1330 Integraciones** construida sobre la base puente oficial `4b67183af1d527684e41cad0b02d7a997d3b2499`, sin cableado 1350/1360 ni WIRING-01…14.

**Rama:** `cursor/1330-base-puente-definitiva-limpia`

**Método:** cherry-pick selectivo del commit funcional `9fd0118` (no tip histórico `99bf38f` ni documentación de receta `13b1382`).

---

## 0. Prevalidación

| Verificación | Resultado |
|--------------|-----------|
| Git root | `/workspace` (= `D:\EMPLEADOS_IA`) |
| `origin/cursor/base-puente-v1-post-v1` en SHA pedido | **4b67183a** existe (HEAD remoto avanzó a `f0af7c6` solo en docs; rama creada desde SHA exacto) |
| Fuente funcional `9fd0118` | Confirmada |
| Base contiene 1230, 1240, 1250f | **SÍ** |
| Working tree al crear rama | Limpio (e2e locales stasheados) |

---

## 1. Rama y commits

| Commit | SHA | Contenido |
|--------|-----|-----------|
| Base | `4b67183af1d527684e41cad0b02d7a997d3b2499` | Base puente definitiva |
| PORT-1330 FUNCIONAL | `4f802c44070d20e502f139e5313b9da5ff285452` | Cherry-pick `9fd0118`: backend 1330, frontend, tests, migración, hub mínimo |
| DOCUMENTACIÓN | *(este commit)* | Entregable portabilidad |

**Commit funcional portátil para cherry-pick futuro:** `4f802c44070d20e502f139e5313b9da5ff285452`

Equivalente de contenido a `9fd0118`, rebaseado sobre `4b67183` (incluye V1 fixes d57b831 ya en base).

---

## 2. Archivos portados (23)

### Nuevos
- `backend/app/integration_enums.py`
- `backend/app/integration_models.py`
- `backend/app/integration_security.py`
- `backend/app/routers/integraciones.py`
- `backend/app/schemas_integration.py`
- `backend/app/services/integration_executors.py`
- `backend/app/services/integration_service.py`
- `backend/alembic/versions/1330a1b2c3d4e_integraciones_reales_conectores.py`
- `frontend/src/pages/IntegracionesPage.tsx`
- `frontend/src/pages/IntegracionWizardPage.tsx`
- `frontend/src/pages/IntegracionDetailPage.tsx`
- `tests/test_integraciones_1330.py`

### Hub (auto-merge sin conflicto manual)
- `backend/app/main.py` — routers `integraciones` + preserva `control_center`, `inteligencia_externa`
- `backend/app/permissions.py`
- `backend/alembic/migration_ledger.json`
- `backend/scripts/schema_repair.py`
- `frontend/src/App.tsx`
- `frontend/src/AppShell.tsx`
- `frontend/src/api.ts`
- `frontend/src/auth/permissions.ts`
- `tests/conftest.py`
- `tests/test_migration_control.py`

### No modificados (V1 puente preservada)
- `security_config.py`, `db_url.py`, `config.py`, `docker-compose.yml` — **0 diff** vs base

---

## 3. Conflictos reales contra base puente

| Archivo hub (receta wiring) | Conflicto real 1330 vs 4b67183 |
|-----------------------------|--------------------------------|
| `main.py` | **NO** — auto-merge |
| `permissions.py` | **NO** |
| `migration_ledger.json` | **NO** |
| `schema_repair.py` | **NO** |
| `api.ts` | **NO** |
| `App.tsx` | **NO** |
| `AppShell.tsx` | **NO** |
| `auth/permissions.ts` | **NO** |
| `conftest.py` | **NO** |

**Total conflictos reales contra base puente:** **0**

Los 9 conflictos de la receta wiring aparecen al combinar **1330 + 1350 + 1360** simultáneamente, no al portar 1330 solo.

---

## 4. Migración Alembic (portátil temporal)

```
1250f1a2b3c4d
    ↓
1330a1b2c3d4e   (head única)
```

- `down_revision`: `1250f1a2b3c4d`
- `baseline_head` en ledger: `1330a1b2c3d4e`

### Re-parent después de Fase 1 (DEFINIDO)

Cuando D consolide Fase 1 (1300, 1350, 1360, 1370, 1380, merges):

1. Obtener HEAD Alembic real de Fase 1 (probablemente tras `1380a`).
2. Editar **solo** `down_revision` de `1330a1b2c3d4e` → ese HEAD.
3. **No** rehacer migraciones de Fase 1.
4. Si wiring futuro requiere `gov_catalog_entry_id`, añadir migración **1330b** colgando de `1330a` (receta wiring WIRING-01).

Ver `CURSOR_RECETA_WIRING_1330_1350_1360.md` secciones 11–12.

---

## 5. Funcionalidad 1330 conservada

| Capacidad | Estado |
|-----------|--------|
| Conectores CRUD | OK |
| Catálogo/configuración | OK |
| Ejecución integración | OK |
| Credenciales protegidas (`secret_ref`, env) | OK |
| Health | OK |
| Circuit breaker | OK |
| Estado conexión | OK |
| Auditoría | OK |
| Errores normalizados | OK |
| Aislamiento por empresa | OK |
| Configuración | OK |
| Pruebas de conexión | OK |
| Integración 1120 señales | OK |

**No implementado (etapa wiring posterior):** gobierno 1350, continuidad 1360, `gov_catalog_entry_id`, reportar-salud automático.

---

## 6. Seguridad

| Control | Resultado |
|---------|-----------|
| Credenciales no en respuestas API | PASS (`_connector_public`, filtro config) |
| Credenciales no en logs auditoría | PASS (`test_audit_no_secrets`) |
| Secretos no en errores | PASS (`integration_security` redact) |
| `organization_id` obligatorio en servicio | PASS |
| Aislamiento A/B | PASS (`test_rbac_and_tenant_isolation`) |
| RBAC viewer/create | PASS |
| SUPERADMIN | Preservado de base |
| Sin acceso cruzado conectores | PASS (404 cross-org) |

---

## 7. Preservación base puente

| Bloque | Preservado |
|--------|------------|
| V1 puente (security, db_url, Docker, Knowledge) | **SÍ** |
| 1100–1250 post-V1 | **SÍ** |
| 1230 Centro Control | **SÍ** (`control_center.router` en main) |
| 1240 Inteligencia Externa | **SÍ** (`inteligencia_externa.router`) |
| 1250f | **SÍ** (parent migración) |

---

## 8. P1 de la receta wiring

| ID | En pieza aislada |
|----|------------------|
| **P1-01** cross-org catálogo gov | **NO APLICA** — no existe `gov_catalog_entry_id` ni catálogo 1350 en esta pieza |
| **P1-02** `organization_id` en helpers cross-módulo | **NO APLICA** — no hay llamadas a 1350/1360; `integration_service` ya exige `organization_id` en todas las operaciones |

**P1 abiertos en esta pieza:** **0**

**Corrección preparada para wiring:** receta WIRING-01 y WIRING-02.

---

## 9. P2

| ID | En pieza aislada |
|----|------------------|
| **P2-01** `proveedor_ref` backup | **NO APLICA** — continuidad 1360 no cableada |

**P2 abiertos:** **0**

---

## 10. Resultados de pruebas

### Focales 1330 (`test_integraciones_1330.py`)

| Entorno | Resultado |
|---------|-----------|
| SQLite | **14 passed**, 0 failed, 0 errors |
| PostgreSQL (`empleados_ia_test`) | **14 passed**, 0 failed, 0 errors |

Cubre: crear, actualizar, ejecutar, error, credenciales, health, circuit breaker, org A/B, permisos, auditoría, SSRF, webhook, mapping, idempotency, señales 1120.

### Regresión backend (`tests/`)

| passed | skipped | failed | errors |
|--------|---------|--------|--------|
| **788** | **4** | **0** | **0** |

### Alembic

| Entorno | upgrade → downgrade -1 → upgrade | heads |
|---------|----------------------------------|-------|
| SQLite | **PASS** | 1 × `1330a1b2c3d4e` |
| PostgreSQL | **PASS** (BD cert + BD test) | 1 × `1330a1b2c3d4e` |

### Frontend

`npm run build` — **PASS** (93 módulos, 1.06s)

Rutas preservadas: operaciones/solicitud (1230), inteligencia-externa (1240), integraciones (1330).

---

## 11. Portado futuro sobre Fase 1 de D

### A. Commit a portar

```
4f802c44070d20e502f139e5313b9da5ff285452
```

Alternativa equivalente de contenido: `9fd0118` (mismo diff funcional, pero base distinta — preferir `4f802c4`).

### B. Archivos en conflicto esperados (con Fase 1 completa)

Los 9 hub de la receta wiring **más** posibles entradas de 1350/1360/identidad en los mismos archivos. Resolver manualmente según `CURSOR_RECETA_WIRING_1330_1350_1360.md` §10.

### C. Re-parent `1330a`

```python
# backend/alembic/versions/1330a1b2c3d4e_integraciones_reales_conectores.py
down_revision = "<HEAD_ALEMBIC_FASE_1>"  # ej. tras 1380a
```

### D. Pruebas inmediatas tras portar

```bash
env -u BOOTSTRAP_ADMIN_USERNAME DATABASE_URL=sqlite:///./test.db python3 -m pytest tests/test_integraciones_1330.py -v
python3 -m alembic upgrade head && python3 -m alembic downgrade -1 && python3 -m alembic upgrade head
python3 -m pytest tests/ -q
cd frontend && npm run build
```

PostgreSQL: `DATABASE_URL` a BD `*_test` + `BOOTSTRAP_ADMIN_PASSWORD` definido.

### E. Cuándo comenzar WIRING-01…14

**Solo después** de:
1. Fase 1 D cerrada y mergeada en rama de convergencia.
2. 1330 portado con re-parent Alembic verde.
3. 9 conflictos hub resueltos si 1350/1360 ya presentes.

Seguir orden en `CURSOR_RECETA_WIRING_1330_1350_1360.md` § orden implementación.

---

## 12. Criterios de aborto (esta pieza)

No se activó ninguno: P0=0, P1=0, regresión verde, multiempresa verde, secretos verdes, 1 head Alembic.

---

## SALIDA FINAL

```
EMPLEADOS IA — 1330 LIMPIO SOBRE BASE PUENTE TERMINADO

BASE:
4b67183af1d527684e41cad0b02d7a997d3b2499

RAMA:
cursor/1330-base-puente-definitiva-limpia

HEAD:
eaff3e56b1885164a33d42a5929718eb5805f610

COMMIT FUNCIONAL PORTÁTIL:
4f802c44070d20e502f139e5313b9da5ff285452

MIGRACIÓN:
1330a1b2c3d4e

DOWN_REVISION TEMPORAL:
1250f1a2b3c4d

RE-PARENT DESPUÉS DE FASE 1:
DEFINIDO

ALEMBIC HEADS:
1

SQLITE:
PASS

POSTGRESQL:
PASS

FOCALES 1330:
14 passed / 0 failed / 0 errors

REGRESIÓN:
788 passed / 4 skipped / 0 failed / 0 errors

FRONTEND:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS (preservado base)

SECRETOS:
PASS

1230 PRESERVADO:
SI

1240 PRESERVADO:
SI

1250 PRESERVADO:
SI

V1 PUENTE PRESERVADA:
SI

WIRING IMPLEMENTADO:
NO

P1:
0 (receta: NO APLICA / preparado para wiring)

P2:
0

CONFLICTOS REALES CONTRA BASE PUENTE:
0

RAMA D MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR DESPUÉS DE FASE 1
```

---

*Pieza portátil certificada — wiring cruzado pendiente de Fase 1 + receta wiring.*
