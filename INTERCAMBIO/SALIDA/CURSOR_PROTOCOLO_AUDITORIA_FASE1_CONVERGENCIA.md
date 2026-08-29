# EMPLEADOS_IA — PROTOCOLO DE AUDITORÍA FASE 1 DE CONVERGENCIA

**Tipo:** Control / documentación — **SOLO LECTURA**  
**Fecha:** 2026-08-29  
**Agente:** GENERAL  
**Estado:** PREPARADO — **NO ejecutar** hasta que D entregue HEAD de Fase 1  
**Matriz de referencia:** `CURSOR_MATRIZ_MAESTRA_CONTROL_CONVERGENCIA_1260_1380.md`

---

## 0. Alcance

### 0.1 Qué audita este protocolo

Convergencia **FASE 1** ejecutada por **D**:

```
BASE PUENTE
  → 1360
  → 1350
  → merge Alembic (1350 ∥ 1360)
  → 1300
  → 1370
  → 1380
```

### 0.2 Anclas

| Concepto | Valor |
|----------|-------|
| **BASE funcional fijada** | `4b67183af1d527684e41cad0b02d7a997d3b2499` |
| **Código puro previo a docs** | `d57b831e41b8e017da612c3c442f9f29c981f674` |
| **Rama BASE** | `cursor/base-puente-v1-post-v1` |
| **Rama Fase 1 (D)** | *(registrar al auditar)* `cursor/________________` |
| **HEAD D (a auditar)** | *(registrar al auditar)* `________________` |

> Commits documentales posteriores a `4b67183` en la rama base **no** cambian la huella funcional de comparación.

### 0.3 Qué NO audita

- Bloques 1260, 1270, 1280, 1290, 1310, 1320, 1330, 1340 (fuera de alcance D Fase 1)
- Matriz 94 capacidades (post-convergencia final)
- Wiring completo 1330↔1350↔1360 (Fase 2; receta B)
- Cadena comercial (Fase 2; receta C)
- Extensiones CC de bloques Fase 2 (receta A)

---

## 1. Huella BASE inmutable

La Fase 1 **NO puede perder** ningún elemento de esta huella.

| Artefacto | Conteo BASE | Verificación |
|-----------|-------------|--------------|
| Bloques funcionales | 1100, 1110, 1120, 1200, 1210, 1220, 1230, 1240, 1250 + V1 | §3.1 matriz |
| Artefactos protegidos | **157** | `git diff --name-status BASE..HEAD_D` — sin eliminaciones funcionales |
| Endpoints | **220** | grep `@router` + `main.py` health |
| Permisos | **72** | `ALL_PERMISSIONS` en `permissions.py` |
| Vistas frontend | **42** páginas | `frontend/src/pages/` |
| Migraciones BASE | **30** | árbol `alembic/versions/` |
| Tests BASE | **54** archivos | `tests/test_*.py` |
| Checks seguridad V1 | **14** | §4 matriz |

### 1.1 Comando de comparación BASE vs HEAD D

```bash
git fetch origin
BASE=4b67183af1d527684e41cad0b02d7a997d3b2499
HEAD_D=<SHA entregado por D>

# Archivos eliminados (funcionales)
git diff --name-status $BASE..$HEAD_D | rg '^D' | rg -v 'INTERCAMBIO/|\.md$'

# Routers BASE presentes
for r in oportunidades finops senales linea_base valoracion diagnosticos \
         control_center inteligencia_externa auth admin platform llm_providers; do
  test -f backend/app/routers/${r}.py && echo "OK $r" || echo "FAIL $r"
done

# Permisos BASE (conteo mínimo)
rg -o '"[a-z_]+\.[a-z_]+"' backend/app/permissions.py | sort -u | wc -l
# Esperado: >= 72
```

---

## 2. Expectativa FASE 1 — debe aparecer

| Bloque | Router esperado | Migración | Tests focales | Permisos nuevos |
|--------|-----------------|-----------|---------------|-----------------|
| **1360** | `continuidad.py` | `1360a1b2c3d4e` | `test_continuidad_1360.py` | 10 |
| **1350** | `governance.py` | `1350a1b2c3d4e` | `test_governance_1350.py` | 7 |
| **1300** | `security.py` | `1300a1b2c3d4e` | `test_bloque_1300_seguridad_avanzada.py` | 4 |
| **1370** | `identidad.py` | `1370a1b2c3d4e` | `test_identidad_1370.py` | 5 |
| **1380** | `scim.py` | `1380a1b2c3d4e` | `test_scim_1380.py` | 0 (reusa identidad) |

**Frontend esperado Fase 1:**

| Bloque | Página | Ruta |
|--------|--------|------|
| 1360 | `ContinuidadPage.tsx` | `/continuidad` |
| 1350 | `GobernanzaDatosPage.tsx` | `/gobernanza-datos` |
| 1300 | `MiSeguridadPage.tsx` | `/mi-seguridad` |
| 1370 | `AdminIdentidadPage.tsx` | `/administracion/identidad` |
| 1380 | *(modifica AdminIdentidad)* | sección SCIM |

---

## 3. Expectativa FASE 1 — NO debe aparecer (accidental)

Presencia de estos artefactos **sin acta** = FAIL (scope creep):

| Bloque | Indicador de presencia accidental |
|--------|-----------------------------------|
| 1260 | `aprendizaje.py`, migración `1260a1` |
| 1270 | endpoints `/api/llm/health`, `/api/llm/observability` |
| 1280 | `comercial.py`, migración `1280a1` |
| 1290 | `optimizacion.py`, migración `1290a1` |
| 1310 | `segmentacion.py`, migración `1310a1` |
| 1320 | `tco.py`, migración `1320a1` |
| 1330 | `integraciones.py`, migración `1330a1` |
| 1340 | `implementacion.py`, migración `1340a1` |

```bash
# Detección rápida
for f in aprendizaje comercial optimizacion segmentacion tco integraciones implementacion; do
  test -f backend/app/routers/${f}.py && echo "SCOPE CREEP: $f" || true
done
```

---

## 4. Alembic esperado Fase 1

### 4.1 Árbol conceptual

```
1250f1a2b3c4d
├─ 1360a1b2c3d4e
├─ 1350a1b2c3d4e
└─ <merge_revision_D>     ← verificar ID real creado por D
       ↓
   1300a1b2c3d4e
       ↓
   1370a1b2c3d4e
       ↓
   1380a1b2c3d4e          ← HEAD esperado al cierre Fase 1
```

### 4.2 Verificaciones

| Control | Esperado | Comando |
|---------|----------|---------|
| Cabezas al cierre | **1** | `alembic heads` |
| HEAD final | `1380a1b2c3d4e` | `alembic current` |
| Merge 1350∥1360 | Existe revisión merge con 2 parents | inspeccionar archivo creado por D |
| `schema_repair.HEAD_REVISION` | = HEAD vigente | grep en `schema_repair.py` |
| `migration_ledger.json` | HEAD actualizado | inspeccionar ledger |
| Re-parent 1300a | `down_revision` ≠ `1250a` (fuente) | debe apuntar a HEAD post-merge |

> **No asumir** el ID de la revisión merge hasta recibir salida real de D. Registrar el SHA/revision en el informe de auditoría.

---

## 5. Checklist gate Fase 1 — resultado binario

Marcar cada control: **PASS** | **FAIL** | **NO APLICA** | **PENDIENTE POR ENTORNO**

### 5.1 Preservación BASE

| # | Control | Criterio PASS | Resultado |
|---|---------|---------------|-----------|
| G-01 | **BASE PRESERVADA** | 0 archivos funcionales BASE eliminados | |
| G-02 | **ARCHIVOS ELIMINADOS** | Ninguna eliminación no justificada en diff | |
| G-03 | **ENDPOINTS PERDIDOS** | 220 endpoints BASE presentes | |
| G-04 | **PERMISOS PERDIDOS** | 72 permisos BASE + nuevos F1; ningún BASE ausente | |
| G-05 | **1230 Centro Control** | `control_center.py`, CC página `/`, 2 endpoints | |
| G-06 | **1240 Inteligencia Externa** | router + modelos + migración `1240c3` | |
| G-07 | **1250 convergencia** | migraciones `1250a/b/f` + tests convergencia | |

### 5.2 Seguridad V1

| # | Control | Criterio PASS | Resultado |
|---|---------|---------------|-----------|
| G-08 | **V1 SEGURIDAD** | 14 checks §4 matriz intactos | |
| G-09 | **DATABASE_URL** | `db_url.py` + `test_docker_database_url` PASS | |
| G-10 | **KNOWLEDGE AUTH** | descarga autenticada; `test_knowledge_930` PASS | |
| G-11 | **UI ESPAÑOL** | sin regresión labels visibles BASE + F1 | |
| G-12 | **SUPERADMIN** | roles protegidos; tests protección PASS | |
| G-13 | **RBAC** | deny-by-default; `test_security_rbac_v1` PASS | |
| G-14 | **MULTIEMPRESA** | `organization_id`; `test_multitenant_v1` PASS | |
| G-15 | **SECRETOS** | 0 secretos versionados | |

### 5.3 Incorporación Fase 1

| # | Control | Criterio PASS | Resultado |
|---|---------|---------------|-----------|
| G-16 | **1360** | router + migración + tests + UI | |
| G-17 | **1350** | router + migración + tests + UI | |
| G-18 | **1300** | router + migración + tests + UI | |
| G-19 | **1370** | router + migración + tests + UI | |
| G-20 | **1380** | scim + migración + tests + UI SCIM | |
| G-21 | **SCOPE CREEP** | ausencia 1260/1270/1280/1290/1310/1320/1330/1340 | |
| G-22 | **ALEMBIC 1 HEAD** | `alembic heads` = 1; HEAD = `1380a1` | |

### 5.4 Pruebas y build

| # | Control | Criterio PASS | Resultado |
|---|---------|---------------|-----------|
| G-23 | **SQLITE** | 0 fallos en batería Fase 1 (BASE + F1 focal) | |
| G-24 | **POSTGRESQL** | upgrade/downgrade/upgrade + 1 head + focal — ver §6 | |
| G-25 | **FRONTEND** | `npm run build` PASS | |
| G-26 | **REGRESIÓN** | 0 fallos nuevos vs BASE (774+ baseline) | |

**Total controles gate:** **26**

---

## 6. PostgreSQL — criterio de certificación

### 6.1 Si D reporta PostgreSQL PASS

General **debe exigir evidencia** de:

| Evidencia | Requerido |
|-----------|-----------|
| `alembic upgrade head` en PG real | SÍ |
| `alembic downgrade -1` (o paso controlado) | SÍ |
| `alembic upgrade head` (roundtrip) | SÍ |
| `alembic heads` = 1 | SÍ |
| Tests focales Fase 1 en PG | SÍ |
| Sin deadlocks en migraciones merge | SÍ |
| Log / captura de salida | SÍ |

Sin evidencia → marcar G-24 como **PENDIENTE POR ENTORNO**, no PASS.

### 6.2 Si D reporta PENDIENTE POR ENTORNO

| Campo | Valor |
|-------|-------|
| G-24 | **PENDIENTE POR ENTORNO** |
| Veredicto máximo | **B. FASE 1 FUNCIONALMENTE APTA — POSTGRESQL PENDIENTE** |
| Certificación acumulativa | **NO** hasta PG real |

> No marcar PostgreSQL PASS sin prueba real ejecutada y documentada.

---

## 7. P0 / P1 / P2

### 7.1 Reglas de rechazo

| Severidad | Regla Fase 1 |
|-----------|--------------|
| **P0 > 0** | **RECHAZAR FASE** — veredicto C |
| **P1 > 0** | **RECHAZAR FASE** — veredicto C |
| **P2** | Puede aceptarse solo si cumple **todas** las condiciones §7.2 |

### 7.2 P2 aceptable (condiciones simultáneas)

- Documentado explícitamente en informe D
- No compromete seguridad
- No compromete integridad de datos
- No rompe V1 (§4 matriz)
- No rompe multiempresa
- No bloquea Fase 2

### 7.3 P2 conocidos permitidos

| ID | Descripción | Bloque |
|----|-------------|--------|
| P2-SCIM-01 | Rate limiting SCIM en memoria | 1380 |
| P2-CC-01..04 | 4 gaps UI Centro Control (receta A) | 1230 ext. |

---

## 8. Control de pérdidas (diff BASE vs HEAD D)

### 8.1 Detecciones obligatorias

| Tipo pérdida | Detección | Resultado si ocurre |
|--------------|-----------|---------------------|
| Archivo funcional eliminado | `git diff --name-status` líneas `D` | **FAIL** G-02 |
| Router desaparecido | lista routers §1.1 | **FAIL** G-03 |
| Endpoint desaparecido | diff OpenAPI o grep rutas | **FAIL** G-03 |
| Permiso desaparecido | diff `permissions.py` | **FAIL** G-04 |
| Vista desaparecida | diff `App.tsx` rutas BASE | **FAIL** G-02 |
| Test desaparecido | diff `tests/` focal BASE | **FAIL** G-26 |
| Migración truncada | diff `alembic/versions/` | **FAIL** G-22 |
| Config V1 perdida | diff `security_config.py`, `db_url.py`, `config.py` | **FAIL** G-08 |

### 8.2 Pérdidas críticas instantáneas (FAIL automático)

- `control_center.py` eliminado o vaciado
- `inteligencia_externa.py` eliminado
- `external_models.py` eliminado
- Migraciones `1250b1c2d3e4f`, `1250f1a2b3c4d` ausentes
- `CentroControlPage` no es ruta `/`
- `security_config.py` debilitado (bootstrap/JWT/CORS)

---

## 9. Control de conflictos — archivos hub

Verificar que D aplicó **unión de contenidos**, no resolución ciega (theirs/ours).

| # | Archivo hub | Verificación PASS |
|---|-------------|-------------------|
| H-01 | `backend/app/main.py` | Todos los routers BASE + F1 `include_router` |
| H-02 | `backend/app/permissions.py` | Unión 72 BASE + permisos 1360/1350/1300/1370 |
| H-03 | `backend/alembic/migration_ledger.json` | HEAD = `1380a1`; protected_revisions completas |
| H-04 | `backend/scripts/schema_repair.py` | `HEAD_REVISION` = `1380a1b2c3d4e` |
| H-05 | `frontend/src/api.ts` | Funciones API BASE + F1 |
| H-06 | `frontend/src/App.tsx` | Rutas BASE + rutas F1 |
| H-07 | `frontend/src/AppShell.tsx` | Sidebar BASE + entradas F1; español |
| H-08 | `frontend/src/auth/permissions.ts` | Espejo permisos backend |
| H-09 | `tests/conftest.py` | Imports modelos BASE + `security_models`, `identity_models`, `scim_models` |

**Conflictos previstos (receta B, hub 1350∥1360):** 9 — verificar resolución manual documentada por D.

---

## 10. Batería de pruebas Fase 1

### 10.1 Ejecutar al auditar (cuando D entregue HEAD)

```bash
# BASE + regresión V1
pytest tests/test_migration_control.py
pytest tests/test_convergencia_final_1250.py
pytest tests/test_bloque_1230_centro_control.py
pytest tests/test_inteligencia_externa_1240.py
pytest tests/test_security_rbac_v1.py
pytest tests/test_docker_database_url.py
pytest tests/test_knowledge_930.py
pytest tests/test_multitenant_v1.py
pytest tests/test_p0_precertificacion_v1.py

# FASE 1 focal
pytest tests/test_continuidad_1360.py
pytest tests/test_governance_1350.py
pytest tests/test_bloque_1300_seguridad_avanzada.py
pytest tests/test_identidad_1370.py
pytest tests/test_scim_1380.py

# Alembic
python -c "from scripts.migration_control import assert_single_head; assert_single_head()"

# Frontend
cd frontend && npm run build
```

### 10.2 Criterio SQLite PASS

- 0 fallos en comandos anteriores
- 0 regresiones vs baseline BASE (774+ passed)

---

## 11. Resultado del gate — veredictos

### 11.1 Matriz de decisión

| Condición | Veredicto |
|-----------|-----------|
| Todos G-01..G-26 PASS; G-24 PASS con evidencia PG | **A. FASE 1 CERTIFICADA** |
| G-01..G-23, G-25, G-26 PASS; G-24 PENDIENTE POR ENTORNO; P0=P1=0 | **B. FASE 1 FUNCIONALMENTE APTA — POSTGRESQL PENDIENTE** |
| Cualquier G FAIL; o P0>0; o P1>0; o pérdida BASE | **C. FASE 1 REQUIERE CORRECCIÓN** |

### 11.2 Prohibido

- Usar veredicto ambiguo «APTA» sin calificador A/B/C
- Marcar PASS en PostgreSQL sin evidencia real
- Aprobar con scope creep (§3)

### 11.3 Plantilla de informe (completar al auditar)

```
EMPLEADOS IA — INFORME AUDITORÍA FASE 1

FECHA:
AUDITOR: GENERAL

BASE: 4b67183af1d527684e41cad0b02d7a997d3b2499
HEAD D: <SHA>
RAMA D: <rama>

CONTROLES GATE: <PASS>/<FAIL>/<PENDIENTE>
P0: <n>  P1: <n>  P2: <n>

ALEMBIC HEAD: <revision>
MERGE REVISION D: <revision real>

SQLITE: PASS/FAIL
POSTGRESQL: PASS/PENDIENTE POR ENTORNO/FAIL
FRONTEND: PASS/FAIL

PÉRDIDAS DETECTADAS: <lista o NINGUNA>
SCOPE CREEP: SI/NO

VEREDICTO: A / B / C
```

---

## 12. Transición a Fase 2 (si veredicto A o B)

| Paso | Acción |
|------|--------|
| 1 | Registrar HEAD D certificado como **nueva base acumulativa** |
| 2 | Anclar Alembic en `1380a1b2c3d4e` (o HEAD real D) |
| 3 | Fase 2 incorpora: **1330** (post-1380), cadena **C** (1280→1320→1340→1310), **1260/1290/1270**, extensiones **CC** (A) |
| 4 | Aplicar wiring **B** al integrar 1330 con 1350/1360 ya presentes |
| 5 | **NO iniciar Fase 2** hasta acta formal de cierre Fase 1 |

---

## 13. Matriz 94 capacidades

**NO actualizar todavía.**

Actualizar **DESPUÉS** de convergencia final 1260–1380 según mecanismo §11 de la matriz maestra.

---

## Restricciones respetadas en este documento

- NO modificado código
- NO ejecutada auditoría (D no ha terminado / no se audita sin HEAD)
- NO cherry-pick / merge / rebase / migraciones
- NO main, V1, PR #32
- NO recálculo porcentaje proyecto
- NO duplicado desarrollo A/B/C/D

---

## Salida final (estado preparación)

```
EMPLEADOS IA — MATRIZ ACTUALIZADA Y GATE FASE 1 PREPARADO

BASE FUNCIONAL:
4b67183af1d527684e41cad0b02d7a997d3b2499

PLACEHOLDER A: SUSTITUIDO
PLACEHOLDER B: SUSTITUIDO
PLACEHOLDER C: SUSTITUIDO

CAPACIDADES CONTROLADAS: 68
ARTEFACTOS PROTEGIDOS: 157
ENDPOINTS CONTROLADOS: 220
PERMISOS CONTROLADOS: 72
VISTAS CONTROLADAS: 42
PRUEBAS CONTROLADAS: 54 (+ refs A/B/C)
CHECKS SEGURIDAD V1: 14
CONTROLES GATE FASE 1: 26

ALEMBIC FASE 1: DEFINIDO
POSTGRESQL: CRITERIO DEFINIDO
P0: CRITERIO DEFINIDO
P1: CRITERIO DEFINIDO
P2: CRITERIO DEFINIDO

TRANSICIÓN A FASE 2: DEFINIDA
MATRIZ 94 RECALCULADA: NO
MODIFICACIONES FUNCIONALES: 0

VEREDICTO:
LISTO PARA AUDITAR HEAD DE D
```
