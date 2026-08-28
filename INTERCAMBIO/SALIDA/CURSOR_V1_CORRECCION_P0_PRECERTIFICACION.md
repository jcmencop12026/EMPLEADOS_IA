# EMPLEADOS_IA — CORRECCIÓN P0 PRE-CERTIFICACIÓN V1

**Rama:** `cursor/v1-integracion-final`  
**PR:** #32 (DRAFT)  
**Fecha:** 2026-08-28

---

## 1. HEAD inicial

`e3875ee291e9702d49e624fb928c2d92bbcdafe2`

---

## 2. HEAD final

*(completar tras commit/push)*

---

## 3. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/services/llm_execution.py` | P0-01 motor LLM |
| `backend/app/services/automation_scheduler.py` | P0-02 tenant inactivo |
| `tests/test_p0_precertificacion_v1.py` | Tests T-LLM + T-TENANT (nuevo) |
| `tests/test_llm_gateway_v1.py` | Ajuste expectativa PYTHON + allowlist |
| `tests/test_integration_v1_final.py` | Ajuste should_use_llm con executor |
| `.env.example` | Nota Ollama Docker host |

---

## 4. Causa raíz P0-01

`is_llm_provider()` trataba cualquier string desconocido como LLM (`normalized not in ("python", "rule", "tool")`), activando LLM para valores como `docint`, `custom` o typos.

`should_use_llm()` activaba LLM cuando `employee.model_provider` parecía LLM **sin exigir** `executor_type == AI_AGENT`, permitiendo que empleados con `model_provider=openai` asociados a ejecutores RULE/PYTHON/TOOL terminaran en `run_llm_for_task`.

---

## 5. Corrección P0-01

- `is_llm_provider()`: allowlist estricta (`openai`, `ollama`, `azure-openai`, `anthropic`, `gemini`) + denylist explícita (`docint`, `rips`, `custom`, motores determinísticos).
- `should_use_llm()`: **solo** retorna `True` cuando `tool_executor_type == ExecutorType.AI_AGENT`.
- `model_provider` selecciona proveedor **dentro** del camino LLM, no convierte ejecutores determinísticos en LLM.

---

## 6. Tests T-LLM-01..08

| ID | Descripción | Estado |
|----|-------------|--------|
| T-LLM-01 | RULE + rule-engine → sin LLM | PASS |
| T-LLM-02 | PYTHON + openai → sin LLM | PASS |
| T-LLM-03 | TOOL + openai → sin LLM | PASS |
| T-LLM-04 | determinístico + docint → sin LLM | PASS |
| T-LLM-05 | determinístico + custom → sin LLM | PASS |
| T-LLM-06 | AI_AGENT + openai → LLM | PASS |
| T-LLM-07 | AI_AGENT + ollama → LLM | PASS |
| T-LLM-08 | Sin proveedor LLM → RULE/PYTHON/TOOL OK | PASS |

T01–T05 verifican: cero `LlmInferenceLog` y cero FinOps categoría "Modelo IA".

---

## 7. Causa raíz P0-02

`automation_scheduler._tick()` filtraba `Automation.status == ACTIVE` pero **no** validaba `Organization.status == ACTIVE`, permitiendo `AutomationRun` para empresas inactivas.

---

## 8. Corrección P0-02

Join con `Organization` y filtro `Organization.status == ORG_STATUS_ACTIVE` antes de `trigger_run()`.

- Empresa INACTIVE: skip silencioso (sin run, sin error, sin borrar histórico).
- Empresas ACTIVE: comportamiento normal.

Rutas API/LLM ya cubiertas por `get_current_user` → `ensure_organization_active`.

---

## 9. Tests T-TENANT-01..06

| ID | Descripción | Estado |
|----|-------------|--------|
| T-TENANT-01 | Org ACTIVE + automation due → ejecuta | PASS |
| T-TENANT-02 | Org INACTIVE + automation due → no run | PASS |
| T-TENANT-03 | A activa / B inactiva → solo A | PASS |
| T-TENANT-04 | Desactivar después → siguiente tick skip | PASS |
| T-TENANT-05 | JWT previo + org inactiva → API 403 | PASS |
| T-TENANT-06 | Histórico AutomationRun preservado | PASS |

---

## 10. Ollama / Docker config

`.env.example` documenta:

- `OLLAMA_BASE_URL=http://127.0.0.1:11434` — backend en host
- `OLLAMA_BASE_URL=http://host.docker.internal:11434` — backend en Docker, Ollama en host Windows

Sin hardcode único; configurable por entorno.

---

## 11. Alembic heads

`d1e2f3a4b5c6` — **UN SOLO HEAD** (sin migración nueva)

---

## 12. Tests focales

`tests/test_p0_precertificacion_v1.py`: **14/14 PASS**

---

## 13. Tests regresión

| Suite | Resultado |
|-------|-----------|
| SQLite completa (excl. certification) | **561 PASS** (547 previos + 14 nuevos) |
| Integración A–J | **10/10 PASS** |
| LLM gateway | PASS |
| Multitenant | PASS |
| Automations 810/810b/810c | PASS |

---

## 14. Frontend

`npm run build`: **PASS**

---

## 15. PostgreSQL

**SKIP AMBIENTAL** — sin BD PostgreSQL de prueba en Cloud Agent.

---

## 16. Secret scan

Sin API keys, passwords ni tokens reales en el diff.

---

## 17. Git status

Solo archivos de corrección P0 staged explícitamente. Sin `git add .`.

---

## 18. PR #32

Actualizado en rama `cursor/v1-integracion-final`. Sin merge a `main`.

---

## 19. Riesgos restantes P1/P2 (backlog, no corregidos)

- Atomicidad completa create organization
- `execute_plan` defensa interna adicional
- FinOps `except Exception: pass`
- `technical_detail` exposición
- Trazabilidad fallback LLM
- Respuesta LLM vacía
- `knowledge_source_ids`
- Concurrencia slug
- Mejoras UI adicionales
- TLS / nuevos proveedores

---

## 20. Veredicto

# APTO PARA CERTIFICACIÓN FINAL V1

Condicionado a validación PostgreSQL/Docker en entorno con infraestructura real (pendiente ambiental).
