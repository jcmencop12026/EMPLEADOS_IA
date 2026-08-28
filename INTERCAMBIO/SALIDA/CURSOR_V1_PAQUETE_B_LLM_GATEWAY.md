# CURSOR V1 PAQUETE B — LLM GATEWAY

## 1. Rama

`cursor/v1-llm-gateway`

## 2. Base

`dc51d5c` (`dc51d5ce4852d37e5eef8b5112d1260a002ee3bf`)

## 3. HEAD final

`026ee00` (`026ee00...` — feat(llm): agregar gateway de inferencia V1)

## 4. PR

(Pendiente de creación contra `main`)

## 5. Precheck

```
git fetch origin --prune          → OK
git rev-parse --show-toplevel     → /workspace (equivalente D:\EMPLEADOS_IA)
git branch --show-current         → cursor/v1-llm-gateway
git rev-parse HEAD                → dc51d5ce4852d37e5eef8b5112d1260a002ee3bf
git rev-parse origin/main         → dc51d5ce4852d37e5eef8b5112d1260a002ee3bf
git status --short                → limpio en precheck inicial
```

Rama exacta `cursor/v1-llm-gateway`. Base `dc51d5c`. Sin archivos no versionados modificados en precheck.

## 6. Arquitectura Gateway

```
COORDINATOR (_run_execution)
    → llm_execution.run_llm_for_task (si AI_AGENT o proveedor LLM)
        → prompt_builder (instrucciones + conocimiento + usuario)
        → gateway.complete
            → select_primary_provider (config DB + política empleado)
            → Provider Adapter (OpenAI / Ollama)
            → fallback controlado (si error elegible)
            → LlmInferenceLog (auditoría)
            → finops_service.registrar_consumo (tokens/costo)
    → _run_tool (RULE/PYTHON/TOOL — sin cambios)
```

Contrato normalizado `GatewayRequest` / `GatewayResponse` en `backend/app/gateway/types.py`.

## 7. Archivos reutilizados

| Archivo | Uso |
|---------|-----|
| `services/coordinator.py` | Punto de integración mínima |
| `services/finops_service.py` | `registrar_consumo()` |
| `orchestration_models.py` | `EmployeeModelPolicy`, `EmployeeInstructions`, `FinOpsRecord` |
| `services/knowledge_retrieval.py` | Contexto RAG keyword |
| `finops_models.py` | `FinOpsRate` |
| `audit.py` | `write_audit()` |
| `events/bus.py` | Eventos de ejecución existentes |
| `permissions.py` | RBAC extendido |
| `schemas_finops.py` | Tarifas existentes |

## 8. Archivos nuevos

| Archivo | Descripción |
|---------|-------------|
| `backend/app/llm_models.py` | `LlmProviderConfig`, `LlmInferenceLog` |
| `backend/app/gateway/` | Gateway, adapters, errors, secrets, prompt_builder |
| `backend/app/schemas_llm.py` | Schemas API |
| `backend/app/services/llm_execution.py` | Integración coordinator/knowledge/finops |
| `backend/app/services/llm_provider_service.py` | CRUD proveedores |
| `backend/app/routers/llm_providers.py` | API `/api/llm/*` |
| `backend/app/seed_llm.py` | Bootstrap proveedores y tarifas |
| `backend/alembic/versions/b950a1b2c3d4_llm_gateway_v1.py` | Migración |
| `frontend/src/pages/admin/AdminLlmProvidersPage.tsx` | UI administración |
| `tests/test_llm_gateway_v1.py` | Suite automática con mocks |

## 9. OpenAI

- Adaptador real HTTP (`openai_adapter.py`) vía `httpx`
- API key desde variable de entorno (`env:OPENAI_API_KEY`), nunca hardcodeada
- Manejo: auth, rate limit, modelo no encontrado, timeout, respuesta inválida, usage/tokens
- Endpoint configurable por proveedor

## 10. Ollama

- Adaptador `ollama_adapter.py` — `/api/chat`
- Base URL configurable (`OLLAMA_BASE_URL` / endpoint proveedor)
- No instala ni descarga modelos
- Error normalizado si no responde

## 11. Selección de provider

- Prioridad por `LlmProviderConfig.priority`
- Preferencia empleado vía `EmployeeModelPolicy` / `AIEmployee.model_*`
- Fallback por `is_fallback` o siguiente proveedor habilitado
- Sin modificar código para cambiar proveedor/modelo

## 12. Modelos

- `LlmProviderConfig`: nombre, tipo, modelo, endpoint, timeout, prioridad, habilitado, fallback, secret_ref
- `LlmInferenceLog`: trazabilidad inferencia (sin prompts completos)
- Reutiliza `EmployeeModelPolicy`, `EmployeeInstructions`, `FinOpsRate`, `FinOpsRecord`

## 13. Secretos

- **NO** se almacena API key en texto plano en BD
- `secret_ref` = `env:OPENAI_API_KEY` (referencia)
- Resolución en runtime vía `gateway/secrets.py`
- API/UI: `secret_configured`, `secret_masked` — nunca valor completo
- Logs sanitizados (`sanitize_for_log`)
- `.env.example` documenta `OPENAI_API_KEY`, `OLLAMA_BASE_URL`

## 14. Fallback

- Errores elegibles: `PROVIDER_UNAVAILABLE`, `TIMEOUT`, `RATE_LIMIT`, `MODEL_NOT_FOUND`
- Registra: proveedor inicial, error inicial, proveedor fallback, resultado
- No oculta error original (`initial_error` en respuesta)
- Sin loops infinitos (un intento fallback)
- Configurable vía `is_fallback` y prioridad

## 15. Coordinator

- `_run_execution()` bifurca LLM vs `_run_tool()`
- `should_use_llm()`: `ExecutorType.AI_AGENT` o `model_provider` LLM
- RULE/PYTHON/TOOL preservados sin cambio de lógica
- FinOps LLM vía `registrar_consumo`; herramientas determinísticas mantienen `FinOpsRecord` directo

## 16. Agent Factory

- Reutiliza `EmployeeModelPolicy` (provider, model, temperature, max_tokens, timeout, fallback_model)
- Reutiliza `EmployeeInstructions` para prompts
- Sin duplicar configuración de empleado

## 17. Knowledge

- `retrieve_knowledge()` en ejecución LLM cuando hay contexto
- `build_knowledge_context()` limita tamaño
- Sin segundo sistema RAG

## 18. FinOps

- `registrar_consumo()` con provider, model, tokens_in/out, duration_ms, employee, work_plan, task
- Tarifas seed: OpenAI gpt-4o-mini, Ollama llama3.2
- VALOR POTENCIAL ≠ VALOR MATERIALIZADO — sin alteración de reglas PX

## 19. Tarifas

- Tabla `finops_rates` existente reutilizada
- Seed editable en `seed_llm.py`
- `find_active_rate()` en runtime — sin consulta Internet

## 20. Auditoría

- `LlmInferenceLog`: timestamp, trace, employee, provider, model, duración, tokens, estado, fallback, error sanitizado
- `write_audit()`: `llm.inference.success` / `llm.inference.error`
- Sin secretos ni prompts completos por defecto

## 21. Frontend

- `Administración → Proveedores IA` (`/administracion/proveedores-ia`)
- Listar, crear, habilitar/deshabilitar, probar conexión
- Texto en español, diseño compacto existente
- Secretos: solo indicador enmascarado

## 22. Migraciones

- `b950a1b2c3d4` → revises `1030a1b2c3d4e`
- Tablas: `llm_provider_configs`, `llm_inference_logs`
- Downgrade reversible (drop tables)
- Head único tras merge
- Conflicto futuro posible: ningún otro paquete toca estas tablas en V1

## 23. Pruebas

### LLM Gateway (`test_llm_gateway_v1.py`)

18 tests — **18 PASS**

- Contrato gateway, OpenAI, Ollama, selección, timeout, auth, rate limit, invalid response
- Fallback, all providers failed, provider deshabilitado, FinOps, coordinator, auditoría
- Secreto no expuesto en API

### Regresión

| Suite | Resultado |
|-------|-----------|
| `test_finops_950.py` | PASS |
| `test_knowledge_930.py` | PASS |
| `test_orchestrator_e2e.py` | PASS |
| `test_agent_factory_e2e.py` | PASS |
| `test_automations_810.py` | PASS |
| `test_capabilities_850.py` | PASS |
| **Total regresión** | **87 PASS** |

### Smoke Ollama

No ejecutado — Ollama no verificado operativo en VM. No bloqueante.

## 24. Resultados exactos

```
pytest tests/test_llm_gateway_v1.py     → 18 passed
pytest (regresión 6 suites)             → 87 passed
git diff --check                          → limpio
```

## 25. Regresión

RULE, PYTHON, TOOL, coordinator, Agent Factory, Knowledge, FinOps, oportunidades (no incluidas en subset), auditoría — **sin fallos en suites ejecutadas**.

## 26. Limitaciones V1

- Sin Azure OpenAI, Anthropic, Gemini (arquitectura preparada)
- Secretos solo vía variables de entorno (sin vault/cifrado BD)
- Knowledge retrieval keyword (sin embeddings)
- Multi-tenant no implementado (organization_id en modelos para Paquete C)
- `azure-openai` en create aceptado pero sin adaptador

## 27. Riesgos

- Secretos en `.env` dependen de Paquete A para producción
- Ollama local puede no estar disponible en todos los entornos
- Fallback aumenta latencia en fallos de proveedor principal
- Tests usan mocks — validación real requiere credenciales/infra

## 28. Dependencias A/C/D

| Paquete | Dependencia |
|---------|-------------|
| A (Docker/infra) | `OPENAI_API_KEY`, `OLLAMA_BASE_URL` en `.env` producción |
| C (multiempresa) | `organization_id` en configs/logs — contrato listo |
| D (RBAC) | Permisos `llm.view`, `llm.manage`, `llm.use` |

## 29. Conflictos potenciales

- Nuevo head Alembic `b950a1b2c3d4` — merge con otras ramas requiere un solo head
- Permisos nuevos requieren `bootstrap_permissions` en despliegue
- Coordinador: empleados con `model_provider=openai` usarán LLM real si proveedor habilitado

## 30. Veredicto

**APTO PARA INTEGRACIÓN**

- Gateway desacoplado ✓
- OpenAI + Ollama implementados ✓
- Provider/model configurables ✓
- Secretos no expuestos ✓
- Fallback probado ✓
- Coordinator conserva RULE/PYTHON/TOOL ✓
- FinOps + auditoría ✓
- Frontend mínimo ✓
- Tests PASS ✓
- Regresión PASS ✓
- PR creado, NO mergeado (pendiente push)
