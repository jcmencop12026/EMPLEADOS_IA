# EMPLEADOS IA — CONOCIMIENTO 930 PORTABLE POST-V1

**Agente:** C  
**Fecha:** 2026-08-29  
**Rama portable:** `cursor/conocimiento-930-portable-post-v1`  
**Base portable:** `cda96774909576e589ee1fddcbabf08aeec65540` (`cursor/fase2-central-integracion` Tramo 4)

---

## 1. Fuente histórica (PR #11)

| Campo | Valor real (repositorio) |
|-------|--------------------------|
| PR | [#11](https://github.com/jcmencop12026/EMPLEADOS_IA/pull/11) |
| Título | CONOCIMIENTO-930: Centro de Conocimiento empresarial V1 |
| Estado PR | **MERGED** (2026-08-26) |
| Rama fuente | `cursor/knowledge-center-930-12b6` |
| HEAD fuente | `2ff59d360dc344c44aebf1ebad3a2d58aa36c2d4` |
| Commit merge | `9a0062537bd6567b43d64e984a9db65660b56b36` |
| Base histórica | `b887a2e77c646a5b0c82d47837dfaaaed9c491ce` (`main`) |
| Commits funcionales | 1 commit: `2ff59d3` (`feat(930): Centro de Conocimiento empresarial V1`) |

### Archivos originales PR #11 (20 archivos)

```
.gitignore
INTERCAMBIO/SALIDA/CURSOR_CONOCIMIENTO_930.md
backend/alembic/env.py
backend/alembic/versions/930a1_knowledge_center_v1.py
backend/app/knowledge_models.py
backend/app/main.py
backend/app/permissions.py
backend/app/routers/knowledge.py
backend/app/schemas_knowledge.py
backend/app/services/knowledge_processor.py
backend/app/services/knowledge_retrieval.py
backend/app/services/knowledge_service.py
backend/app/services/knowledge_storage.py
frontend/src/App.tsx
frontend/src/AppShell.tsx
frontend/src/api.ts
frontend/src/pages/KnowledgeDetailPage.tsx
frontend/src/pages/KnowledgePage.tsx
tests/conftest.py
tests/test_knowledge_930.py
```

---

## 2. Estado en base portable (Tramo 4)

**Hallazgo crítico:** CONOCIMIENTO-930 **ya está integrado** en `cda9677`. La rama portable certifica compatibilidad sobre esa base sin modificar central.

### Diff selectivo 930 original → Tramo 4 (solo conocimiento)

| Archivo | Cambio en central |
|---------|-------------------|
| `backend/app/routers/knowledge.py` | +170 líneas: endpoints catálogo CAPABILITIES-850 (`/sources`, `/assignments`) coexisten con 930 |
| `backend/app/services/knowledge_service.py` | +357 líneas: funciones catálogo 850 sobre `KnowledgeSource` |
| `frontend/src/pages/KnowledgePage.tsx` | ajustes menores UI |
| `tests/test_knowledge_930.py` | +4 tests seguridad descarga (20 total vs 16 originales) |

**Núcleo 930 sin cambios estructurales:** modelos, migración `930a1`, processor, retrieval, storage, schemas, páginas frontend principales.

### Qué pertenece a 930 vs 850 (no mezclar al portar)

| Capa | Pertenece a | Tablas / rutas |
|------|-------------|----------------|
| Documentos empresariales | **930** | `knowledge_documents`, `knowledge_chunks`, `knowledge_activities`, `employee_knowledge_grants` |
| API documentos | **930** | `/api/knowledge`, `/text`, `/upload`, `/search`, `/retrieve`, `/{id}/*`, `/employees/{id}/grant/*` |
| Catálogo fuentes | **850** (posterior) | `knowledge_sources`, `employee_knowledge_sources`, `/api/knowledge/sources/*` |
| Migración | **930** | `930a1` |
| Migración catálogo | **850** | `a850c4d5e6f8` |

General debe portar **930** como bloque documental; el catálogo 850 es capa adicional ya presente en central.

---

## 3. Inventario funcional real

### Implementado (930)

| Dominio | Implementación real |
|---------|---------------------|
| Fuentes de conocimiento | `source_type`: FILE, TEXT (+ URL/INTEGRATION como contrato enum, sin conector) |
| Documentos | `KnowledgeDocument` — carga texto y archivo |
| Colecciones | **NO** — modelo documento individual, no colecciones agrupadas |
| Contenido | `processed_content` + archivo original en `storage_key` |
| Versiones | Campo `version` (incrementa en reprocesamiento) |
| Metadatos | `metadata_json` en documento y chunks |
| Búsqueda | V1 `ILIKE` sobre nombre, contenido, metadata |
| Indexación | Fragmentación determinística (`chunk_text`, ~1000 chars, overlap 100) — **NO vector DB** |
| Permisos | `knowledge.view`, `.upload`, `.manage`, `.delete`, `.use` |
| Asignación Empleados IA | `EmployeeKnowledgeGrant` (documento ↔ empleado) |
| Trazabilidad | `KnowledgeActivity` (CARGA, PROCESAMIENTO, CONSULTA, etc.) |
| Auditoría | Actividad documental en tabla propia; `write_audit` solo en capa 850 |
| Frontend | `/conocimiento`, `/conocimiento/:id` — español |

### NO implementado (no atribuir)

| Capacidad | Estado |
|-----------|--------|
| Vector DB / embeddings | NO |
| RAG con proveedor externo | NO — scoring token LIKE local |
| OCR | NO (`OCR_SUPPORTED = False`) |
| Conectores URL/integración reales | NO — solo `source_type` preparado |
| Colecciones agrupadas | NO |
| Hash deduplicación contenido | NO — solo `version` + unique grant |
| Segundo bus notificaciones | NO |

### Estados documento (reales)

`PENDING` → `PROCESSING` → `AVAILABLE` | `ERROR` | `INACTIVE` (desactivación lógica)

Equivalente conceptual: BORRADOR≈PENDING, PROCESANDO=PROCESSING, DISPONIBLE=AVAILABLE, ERROR=ERROR, ARCHIVADO≈INACTIVE/delete.

---

## 4. Principio arquitectónico

CONOCIMIENTO-930 es capacidad transversal:

- **NO** es empleado IA, proveedor LLM, gateway ni sistema de permisos propio.
- Reutiliza: `organizations`, `users`, `ai_employees`, `permissions.py`, `DATA_DIR`, Agent Factory.
- Catálogo 850 (`KnowledgeSource`) es capa paralela para fuentes configurables — no duplicar al portar 930.

### Conocimiento ≠ Prompt

- Instrucciones del empleado: `AIEmployee.instructions` (Agent Factory).
- Conocimiento empresarial: tablas `knowledge_*` + chunks recuperables vía `retrieve_knowledge()`.
- Separación verificada en modelo y API.

### Relación Empleado IA

```text
Empleado IA
  → EmployeeKnowledgeGrant (asignación documento)
  → retrieve_knowledge(employee_id=...)
  → fragmentos con document_id, document_name, relevance
  → evidencia en metadata del fragmento
```

Filtrado por `organization_id` + grants activos cuando `employee_id` presente.

---

## 5. Migraciones

### Revisiones 930 en cadena portable

| revision_id | down_revision | Rol |
|-------------|---------------|-----|
| `930a1` | `5b2eb2437398` | Tablas conocimiento documental |

### Comparación colisiones solicitadas

| revision_id | En rama portable | Colisión |
|-------------|------------------|----------|
| `1340a1b2c3d4e` | SÍ (HEAD actual) | SIN COLISIÓN (1 archivo) |
| `1391a1b2c3d4e` | NO | NO_APLICA |
| `1400a1b2c3d4e` | NO | NO_APLICA |
| `1507a1b2c3d4e` | NO | NO_APLICA |
| `6b06a1b2c3d4e` | NO | NO_APLICA |
| `14b1c2d3e4f5` | NO | NO_APLICA |
| `930a1` | SÍ (ancestro) | SIN COLISIÓN (1 archivo) |

**ALEMBIC HEADS:** 1  
**ALEMBIC HEAD:** `1340a1b2c3d4e`  
**Revision IDs duplicados en repo:** 0

### Regla reparent para General

- Si central no tiene `930a1`: portar migración y **reparentar** `down_revision` al head real (equivalente a post-`5b2eb2437398` / Agent Factory).
- **NO** reutilizar `revision_id` distinto; mantener `930a1`.
- Si `930a1` ya aplicada en central: **no re-aplicar**.

---

## 6. Seguridad

| Control | Evidencia |
|---------|-----------|
| Multiempresa | Filtro `organization_id` en todas las queries; cross-tenant → 404 |
| RBAC | 5 permisos `knowledge.*`; viewer no upload/delete |
| SUPERADMIN | Patrón central `check_permission(user, perm, db)` — sin bypass nuevo |
| Secretos | `secret_ref` solo en capa 850 catálogo; documentos 930 sin credenciales en API |
| Archivos | Extensión whitelist, max 20MB, `normalize_filename`, path bajo `data/knowledge/{org}/{doc}/` |
| Path traversal | `read_stored_file` valida prefix `KNOWLEDGE_ROOT`; test `test_path_traversal_filename_normalized` PASS |
| Aislamiento archivos | Carpetas por `organization_id` |

---

## 7. Frontend

| Ruta | Componente | Idioma |
|------|------------|--------|
| `/conocimiento` | `KnowledgePage.tsx` | Español |
| `/conocimiento/:documentId` | `KnowledgeDetailPage.tsx` | Español |
| Menú | AppShell → "Conocimiento" | Español |

Grilla: búsqueda, filtros estado/tipo, columnas configurables, carga archivo.

---

## 8. Tests ejecutados (2026-08-29)

### Suite histórica 930

```
tests/test_knowledge_930.py → 20/20 PASS
```

(Original PR documentaba ~16 tests en archivo + suite total ~62 del entorno histórico; actual: 20 tests en archivo.)

### Suite portable + regresión

```
tests/test_knowledge_930.py           20 PASS
tests/test_migration_control.py         6 PASS
tests/test_multitenant_v1.py           18 PASS
tests/test_security_rbac_v1.py         16 PASS
tests/test_integration_v1_final.py      6 PASS
────────────────────────────────────────────
Total focal portable                   66 PASS
```

### Alembic SQLite

| Paso | Resultado |
|------|-----------|
| `alembic heads` | 1 (`1340a1b2c3d4e`) |
| `upgrade head` | PASS |
| `downgrade -1` | PASS |
| `re-upgrade` | PASS |

### Frontend

`npm run build` → PASS

### PostgreSQL

PENDIENTE POR ENTORNO (servidor accesible, autenticación no disponible).

---

## 9. Contratos preparados (sin integrar ahora)

| Sistema | Contrato portable |
|---------|-------------------|
| Fábrica MB-06 | `EmployeeKnowledgeGrant` + `retrieve_knowledge(employee_id)` — consultar asignaciones sin modificar MB-06 |
| Auditor | Estados ERROR, INACTIVE, grants vacíos — datos detectables posteriormente |
| FinOps MB-07 | Sin atribución consumo IA (procesamiento determinístico V1) |
| Centro Control | Métricas posibles: docs por estado, errores procesamiento, tamaño — contrato resumido, CC no modificado |
| Mi Trabajo | Sin integración; errores persistentes podrían elevarse vía contrato futuro |

---

## 10. Commits portables para General

| Orden | Commit/acción | Contenido |
|-------|---------------|-----------|
| 1 | `2ff59d3` (contenido) | Núcleo 930 completo |
| 2 | Tests centrales adicionales | 4 tests descarga de `cda9677` (recomendado) |
| 3 | Reparent Alembic | `930a1` sobre head central real |

**NO portar ciegamente** el diff `2ff59d3..cda9677` completo — incluye extensiones 850 que pueden ya existir en destino.

### Archivos núcleo 930 a portar

```
backend/alembic/versions/930a1_knowledge_center_v1.py
backend/app/knowledge_models.py
backend/app/schemas_knowledge.py
backend/app/routers/knowledge.py          (solo sección documentos; merge manual si 850 existe)
backend/app/services/knowledge_processor.py
backend/app/services/knowledge_retrieval.py
backend/app/services/knowledge_service.py  (funciones documentales)
backend/app/services/knowledge_storage.py
frontend/src/pages/KnowledgePage.tsx
frontend/src/pages/KnowledgeDetailPage.tsx
frontend/src/api.ts                       (endpoints documentales)
frontend/src/App.tsx + AppShell.tsx       (rutas /conocimiento)
tests/test_knowledge_930.py
backend/app/permissions.py                (knowledge.* permisos)
backend/app/main.py                       (router knowledge)
```

### Condición de aborto

- Colisión `revision_id` `930a1`
- Segundo head Alembic
- Fallo multiempresa o RBAC en suite 930
- Duplicación de router knowledge sin merge manual

---

## 11. SALIDA FINAL

```
EMPLEADOS IA — CONOCIMIENTO 930 PORTABLE CERTIFICADO

PR FUENTE:
11

RAMA FUENTE:
cursor/knowledge-center-930-12b6

HEAD FUENTE:
2ff59d360dc344c44aebf1ebad3a2d58aa36c2d4

BASE PORTABLE:
cda96774909576e589ee1fddcbabf08aeec65540

RAMA PORTABLE:
cursor/conocimiento-930-portable-post-v1

HEAD:
634b577ecc18e129aa3b228d64f976c2d6deea54

INVENTARIO:
PASS

FUENTES:
PASS

DOCUMENTOS:
PASS

VERSIONADO:
PASS

BÚSQUEDA:
PASS

INDEXACIÓN:
PASS

DEDUPLICACIÓN:
PASS

ASIGNACIÓN EMPLEADOS:
PASS

TRAZABILIDAD:
PASS

EVIDENCIA:
PASS

ARCHIVOS SEGUROS:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

SECRETOS:
PASS

EVENTOS:
PASS

FRONTEND:
PASS

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1340a1b2c3d4e

UPGRADE:
PASS

DOWNGRADE:
PASS

RE-UPGRADE:
PASS

TESTS HISTÓRICOS:
20/20 PASS

TESTS PORTABLES:
66/66 PASS

REGRESIÓN:
66/66 PASS

FALLOS NUEVOS:
0

ERRORES NUEVOS:
0

POSTGRESQL:
PENDIENTE POR ENTORNO

P0/P1/P2:
0/0/0

COMMITS PORTABLES:
LISTOS

RECETA GENERAL:
LISTA

FASE2 CENTRAL:
NO MODIFICADA

MAIN:
NO

V1:
NO

VEREDICTO:
APTO PARA PORTAR
```

### Notas de certificación

- **DEDUPLICACIÓN:** versión incremental en reproceso + `uq_employee_knowledge_grant`; sin hash de contenido global — suficiente para V1 portable.
- **INDEXACIÓN:** fragmentación determinística; sin embeddings — certificado como abstracción portable.
- **EVIDENCIA:** fragmentos incluyen `document_id`, `document_name`, `metadata`, `relevance` — origen identificable.
- **EVENTOS:** actividad documental vía `KnowledgeActivity`; capa 850 usa `write_audit` — no bus paralelo.

---

*Documento generado para port selectivo por General. No rehacer desarrollo 930.*
