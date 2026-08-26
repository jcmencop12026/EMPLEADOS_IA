# CURSOR — CONOCIMIENTO-930 Centro de Conocimiento V1

**Fecha:** 2026-08-25
**Estado:** CONOCIMIENTO-930 LISTO PARA REAUDITORÍA
**No declarado apto para merge — NO MERGE**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| Código | CONOCIMIENTO-930 |
| Rama | `cursor/knowledge-center-930-12b6` |
| Base | `main` (`b887a2e`) |
| HEAD inicial | `b887a2e77c646a5b0c82d47837dfaaaed9c491ce` |
| HEAD final | *(ver commit en rama)* |

---

## ARQUITECTURA

```
FUENTE (FILE / TEXT / URL* / INTEGRATION*)
  → KnowledgeDocument (metadata + storage_key)
  → Procesamiento (knowledge_processor)
  → processed_content + KnowledgeChunk[]
  → Búsqueda V1 (LIKE) + retrieve_knowledge()
  → EmployeeKnowledgeGrant (contrato Empleado IA)
  → KnowledgeActivity (trazabilidad)
```

\* URL e Integración externa: contrato preparado en `source_type`, sin implementación de conectores en V1.

---

## REUTILIZACIÓN

| Componente existente | Uso |
|---------------------|-----|
| `permissions.py` | Permisos `knowledge.*` |
| `AuditLog` / patrón auditoría | Referencia; actividad documental en `KnowledgeActivity` |
| `EmployeeKnowledgeSource` | **No modificado** — contrato paralelo `EmployeeKnowledgeGrant` |
| `AIEmployee` | Validación tenant en asignaciones |
| `DATA_DIR` / `config.py` | Almacenamiento `data/knowledge/{org}/{doc}/` |
| Frontend `ops-page` + `data-table` | Grilla y detalle compactos |

---

## MODELOS NUEVOS

| Modelo | Tabla | Propósito |
|--------|-------|-----------|
| `KnowledgeDocument` | `knowledge_documents` | Documento/fuente principal |
| `KnowledgeChunk` | `knowledge_chunks` | Fragmentación para recuperación |
| `KnowledgeActivity` | `knowledge_activities` | Trazabilidad por documento |
| `EmployeeKnowledgeGrant` | `employee_knowledge_grants` | Asignación Empleado IA ↔ documento |

---

## MIGRACIONES

| Revisión | Archivo | Resultado |
|----------|---------|-----------|
| `930a1` | `930a1_knowledge_center_v1.py` | upgrade → downgrade → upgrade **PASS** (SQLite) |

**PostgreSQL real:** NO CERTIFICADO en este entorno.

---

## ENDPOINTS REST

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/knowledge` | Listar documentos |
| POST | `/api/knowledge/text` | Crear desde texto |
| POST | `/api/knowledge/upload` | Cargar archivo |
| GET | `/api/knowledge/search` | Búsqueda V1 |
| POST | `/api/knowledge/retrieve` | Contrato recuperación/RAG |
| GET | `/api/knowledge/{id}` | Detalle |
| PATCH | `/api/knowledge/{id}` | Actualización parcial (`exclude_unset`) |
| DELETE | `/api/knowledge/{id}` | Eliminar |
| POST | `/api/knowledge/{id}/process` | Procesar |
| POST | `/api/knowledge/{id}/reprocess` | Reprocesar |
| POST | `/api/knowledge/{id}/activate` | Activar |
| POST | `/api/knowledge/{id}/deactivate` | Desactivar |
| GET | `/api/knowledge/{id}/download` | Descarga autorizada |
| GET | `/api/knowledge/{id}/activity` | Trazabilidad |
| GET | `/api/knowledge/employees/{id}/grants` | Asignaciones |
| POST | `/api/knowledge/employees/{id}/grant/{doc}` | Asignar |
| DELETE | `/api/knowledge/employees/{id}/grant/{doc}` | Revocar |

---

## FORMATOS SOPORTADOS (V1)

| Formato | Carga | Extracción texto |
|---------|-------|------------------|
| TXT | Sí | Sí |
| CSV | Sí | Sí |
| JSON | Sí | Sí |
| DOCX | Sí | Sí (stdlib zip+xml) |
| XLSX | Sí | Sí (stdlib zip+xml) |
| PDF | Sí | Heurística básica; sin OCR — contrato OCR futuro en `knowledge_processor.OCR_SUPPORTED` |

---

## PROCESAMIENTO

- Original preservado en `storage_key` (archivos) o `processed_content` (texto).
- Contenido procesado separado; reprocesamiento regenera chunks.
- Estados: Pendiente, Procesando, Disponible, Con error, Inactivo.
- Fragmentación ~1000 caracteres con solapamiento 100.

---

## BÚSQUEDA Y RECUPERACIÓN

- **Búsqueda V1:** `ILIKE` sobre nombre, contenido y metadata.
- **Contrato RAG:** `retrieve_knowledge(tenant, query, filters, limit, context, employee_id)` en `knowledge_retrieval.py`.
- Sin proveedor de embeddings externo.
- Filtrado por asignación cuando se indica `employee_id`.

---

## PERMISOS

| Permiso | Admin | Operator | Viewer |
|---------|-------|----------|--------|
| `knowledge.view` | Sí | Sí | Sí |
| `knowledge.upload` | Sí | Sí | No |
| `knowledge.manage` | Sí | Sí | No |
| `knowledge.delete` | Sí | No | No |
| `knowledge.use` | Sí | Sí | Sí |

---

## TENANT ISOLATION

- Todas las consultas filtran `organization_id`.
- Cross-tenant devuelve 404 sin filtrar existencia.
- Descarga y búsqueda validan tenant y permiso.

---

## SEGURIDAD DE ARCHIVOS

- Validación de extensión y MIME permitidos.
- Normalización de nombres (anti path traversal).
- Rutas internas no expuestas (`storage_key` relativo a `DATA_DIR`).
- Usuario no controla ruta física final.

---

## TRAZABILIDAD

Acciones registradas en `KnowledgeActivity`: CARGA, MODIFICACION, PROCESAMIENTO, REPROCESAMIENTO, CONSULTA, DESCARGA (vía consulta), ELIMINACION, ASOCIACION, DESASOCIACION, ACTIVACION, DESACTIVACION, ERROR. Sin contenido sensible completo en logs.

---

## FRONTEND

| Vista | Ruta | Características |
|-------|------|-----------------|
| Centro de conocimiento | `/conocimiento` | Grilla, búsqueda, filtros, columnas configurables, carga |
| Detalle documento | `/conocimiento/:id` | Pestañas: Resumen, Contenido, Metadatos, Asociaciones, Actividad |
| Menú | AppShell | Entrada "Conocimiento" |

Todo texto visible en español.

---

## TESTS

```
PYTHONPATH=backend python3 -m pytest -q
→ 62 passed (16 nuevos en test_knowledge_930.py)
```

Cobertura: texto, archivo, formato inválido, vacío, listar, detalle, PATCH parcial, procesamiento, reprocesamiento, búsqueda, recuperación, descarga, eliminar, tenant isolation, permisos, path traversal, DOCX, asignación empleado, actividad.

---

## VALIDACIÓN

| Comando | Resultado |
|---------|-----------|
| `pytest` | PASS (62) |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |
| `git diff --check` | PASS |

---

## GIT

- Rama independiente desde `main`.
- Sin cambios de PR #6–#10.
- Sin cherry-pick de EMPLEADOS-900 / ORQUESTADOR-910 / INTEGRACIONES-920.

---

## PENDIENTES REALES

1. OCR y extracción PDF robusta (requiere infraestructura dedicada).
2. Conectores URL e integración externa (solo contrato `source_type`).
3. Recuperación semántica / embeddings (interfaz preparada, no implementada).
4. UI de asignación masiva Empleado IA desde detalle de empleado (contrato API listo).
5. PostgreSQL real no certificado en este entorno.

---

## ESTADO FINAL

**CONOCIMIENTO-930 LISTO PARA REAUDITORÍA**

No se realizó merge.
