# CURSOR — SALUD-CONOCIMIENTO-971

**Estado:** `SALUD-CONOCIMIENTO-971 LISTO PARA REAUDITORÍA`
**Fecha:** 2026-08-26
**Rama:** `cursor/integracion-salud-conocimiento-003-12b6`
**NO MERGE**

---

## 1. Bases integradas

| Componente | PR | Rama | HEAD verificado |
|------------|-----|------|-----------------|
| CONOCIMIENTO-930 | #11 | `cursor/knowledge-center-930-12b6` | `2ff59d3` |
| SALUD-960 + OPERACIONES | #17 | `cursor/integracion-salud-workplan-002` | `b3b5e31` |
| SALUD-960 certificado | #14 | `cursor/salud-ips-engine-960` | `9ee91eb` |

HEAD integración final: `9a00625` (previo a push con fixes de consulta)

---

## 2. Arquitectura reutilizada (sin duplicar)

- `KnowledgeDocument`, `KnowledgeChunk`, `KnowledgeActivity`, `EmployeeKnowledgeGrant`
- `retrieve_knowledge()` — contrato RAG V1 existente
- Permisos `knowledge.*` + `salud.*` combinados
- Trazabilidad en `IpsAnalysis.traceability_json` y `summary_json` (sin tablas paralelas)

**Nuevo servicio:** `backend/app/services/salud_knowledge.py`

Flujo:

```
Diagnóstico IPS
→ Orquestador / select_specialists
→ consulta por dominio y especialista (EmployeeKnowledgeGrant)
→ retrieve_knowledge (consultas cortas por token)
→ análisis datos + evidencia documental
→ hallazgos (HECHO / INFERENCIA / INFORMACION_INSUFICIENTE)
→ propuestas
→ plan de acción → Operaciones (vía PR #17)
```

---

## 3. Archivos principales

| Archivo | Cambio |
|---------|--------|
| `backend/app/services/salud_knowledge.py` | **nuevo** — autorización, consulta, conflictos, incumplimiento contractual |
| `backend/app/services/salud_engine.py` | Integra conocimiento en pipeline y diagnóstico |
| `backend/app/services/salud_indicators.py` | `dias_por_factura` para cruce contractual |
| `backend/app/services/salud_questions.py` | Preguntas de cumplimiento contractual |
| `frontend/src/pages/DiagnosticoIpsPage.tsx` | Indicador conocimiento + fuentes en hallazgos/trazabilidad |
| `backend/alembic/versions/971a1b2c3d4e_merge_conocimiento_salud_971.py` | Merge heads `930a1` + `970a1b2c3d4e` |
| `tests/test_salud_conocimiento_971.py` | **nuevo** — 16 tests |

Merge CONOCIMIENTO-930: modelos, router, UI conocimiento, tests `test_knowledge_930.py`.

---

## 4. Comportamiento verificado

| Requisito | Estado |
|-----------|--------|
| Solo conocimiento autorizado (`EmployeeKnowledgeGrant`) | PASS |
| Multi-tenant adversarial | PASS |
| Contrato 10 días vs radicación día 18 | PASS (hallazgo HECHO + fuentes) |
| Documentos contradictorios (10 vs 15 días) | PASS (requiere validación) |
| Documento irrelevante (RRHH) | PASS (filtrado) |
| Sin conocimiento → análisis continúa | PASS |
| Experiencia separada de conocimiento | PASS |
| Pregunta natural contractual | PASS |
| No alucinación de cláusulas | PASS |
| Auditoría `CONSULTA_SALUD` en `KnowledgeActivity` | PASS |

---

## 5. Tests

| Comando | Resultado |
|---------|-----------|
| `pytest tests/test_salud_conocimiento_971.py -q` | **16/16 PASS** |
| `pytest` completo | **145/145 PASS** |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilidades |
| Alembic upgrade/downgrade/upgrade | PASS |

---

## 6. GitHub Actions / PostgreSQL

Pendiente de run en PR de esta rama tras push.

---

## 7. UI

En `/salud/diagnostico`:
- Indicador «Conocimiento documental: utilizado / sin documentos…»
- Fuentes documentales por hallazgo (títulos, sin IDs técnicos)
- Sección trazabilidad con conocimiento consultado

---

## 8. Pendientes reales

1. CI PostgreSQL verde en PR de integración
2. Demo E2E visual «IPS DEMO CON CONOCIMIENTO» (flujo completo hasta Operaciones) — validar en entorno con servidores
3. PR #17 declarado **APTO PARA MERGE** con CI 4/4 PASS (run `32918547155`)

---

## 9. Conclusión

**SALUD-CONOCIMIENTO-971 LISTO PARA REAUDITORÍA** — integración funcional sin duplicar modelos de conocimiento.
