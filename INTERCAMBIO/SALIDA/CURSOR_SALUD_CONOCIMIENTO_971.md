# CURSOR — SALUD-CONOCIMIENTO-971

**Estado:** `APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN`
**Fecha cierre:** 2026-08-26
**Rama:** `cursor/integracion-salud-conocimiento-003-12b6`
**HEAD final:** `119d56b`
**PR:** #18 (draft)
**NO MERGE a main**

---

## 1. CI real (GitHub Actions)

| Job | Run `32924491837` | HEAD |
|-----|-------------------|------|
| Backend y PostgreSQL | **PASS** | `119d56b` |
| Frontend | **PASS** | `119d56b` |
| Validación Git | **PASS** | `119d56b` |
| Pruebas Windows | **PASS** | `119d56b` |

**Resultado: 4/4 PASS**

### Correcciones aplicadas en esta rama

| Commit | Causa raíz | Fix |
|--------|------------|-----|
| `fc7aabd` | `IpsHallazgo.kind = "INFORMACION_INSUFICIENTE"` (24 chars) excedía `String(20)` en PostgreSQL | `kind = "INSUFICIENTE"` en hallazgos de conflicto |
| `119d56b` | `DELETE knowledge_documents` violaba FK `knowledge_activities_document_id_fkey` (actividades `CONSULTA_SALUD`) | Borrar `KnowledgeActivity` asociadas antes del documento en `delete_document()` |

---

## 2. Bases integradas (grafo de contenido)

| Componente | PR | Rama | HEAD | Contenido en #18 |
|------------|-----|------|------|------------------|
| CONOCIMIENTO-930 | #11 | `cursor/knowledge-center-930-12b6` | `2ff59d3` | **Sí** (ancestro) |
| OPERACIONES-940 | #13 | `cursor/operations-center-940-12b6` | `7c536d2` | **Sí** (ancestro) |
| SALUD-960 | #14 | `cursor/salud-ips-engine-960` | `9ee91eb` | **Sí** (ancestro) |
| SALUD→WorkPlan | #17 | `cursor/integracion-salud-workplan-002` | `6728b11` | **Parcial** — #18 contiene base `b3b5e31`; commit doc `6728b11` de #17 no está en #18 |

**Conclusión:** mergear #11, #13, #14 y #17 por separado es redundante si se mergea **#18** como paquete SALUD+Operaciones+Conocimiento.

---

## 3. Reauditoría adversarial focal (15/15)

| # | Control | Evidencia |
|---|---------|-----------|
| 1 | Tenant A no recupera documento/chunk de B | `test_cross_tenant_knowledge_denied`, `test_direct_document_id_cross_tenant_denied` |
| 2 | Empleado sin `EmployeeKnowledgeGrant` → DENY | `test_employee_without_grant_gets_no_fragments` |
| 3 | Grant inactivo/inexistente → DENY | `test_inactive_grant_denied`, `test_permission_fail_closed_retrieve` |
| 4 | Documento no autorizado por ID directo → DENY | `test_direct_document_id_cross_tenant_denied` |
| 5 | Búsqueda no infiere contenido de otro tenant | `test_cross_tenant_knowledge_denied` |
| 6 | Documento irrelevante no contamina análisis | `test_irrelevant_document_not_used` |
| 7 | Documentos contradictorios no producen certeza falsa | `test_contradictory_documents_flag_validation`, `test_apply_knowledge_does_not_promote_hypothesis_to_fact` |
| 8 | Sin conocimiento adicional SALUD continúa | `test_without_knowledge_analysis_still_runs` |
| 9 | Experiencia y conocimiento separados | `test_experience_separate_from_knowledge` |
| 10 | Pregunta contractual sin contrato → insuficiente | `test_contractual_question_without_contract` |
| 11 | Contrato 10 días + radicación 18 días → diferencia correcta | `test_contract_relevant_finding` |
| 12 | No inventar cláusulas, páginas o fuentes | `test_no_hallucination_invented_clause` |
| 13 | Fuente mostrada pertenece al documento utilizado | `test_source_visible_in_hallazgo`, `test_source_reference_preserves_document_title` |
| 14 | Especialista no recibe todo el conocimiento | `test_specialist_scoped_consultation` |
| 15 | Fallo de recuperación no abre acceso | `test_permission_fail_closed_retrieve` (fail closed) |

---

## 4. Regresión local

| Comando | Resultado |
|---------|-----------|
| `pytest tests/test_salud_conocimiento_971.py -q` | **20/20 PASS** |
| `pytest` completo | **149/149 PASS** |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilidades |
| `git diff --check` | PASS |
| Alembic `upgrade head` (SQLite) | PASS → head `971a1b2c3d4e` |
| Alembic `downgrade -1` | Ambiguous walk (merge migration — esperado en rama aislada) |

PostgreSQL confirmado en CI run `32924491837`.

---

## 5. Arquitectura (sin rediseño)

- Servicio: `backend/app/services/salud_knowledge.py`
- Integración: `salud_engine.py`, `salud_questions.py`, `salud_indicators.py`
- UI: `frontend/src/pages/DiagnosticoIpsPage.tsx`
- Migración merge: `971a1b2c3d4e_merge_conocimiento_salud_971.py`
- Reutiliza `retrieve_knowledge()`, `EmployeeKnowledgeGrant`, `KnowledgeActivity` — sin modelos paralelos

---

## 6. Conclusión

**PR #18 — APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN**

Integración SALUD↔Conocimiento certificada (CI 4/4, 20 tests adversariales, PostgreSQL verde). Pendiente de integración consolidada con PRs de plataforma (#6, #7, #9, #16) según mapa `CURSOR_MAPA_INTEGRACION_CONSOLIDADA_001.md`.
