# EMPLEADOS_IA — Corrección final pre-release V1

**Agente:** D / Integrador
**Rama:** `cursor/v1-integracion-final`
**PR:** #32 (DRAFT — NO MERGE)
**HEAD anterior:** `3745b5ab6811834b8a3128457020fcf77ef116cb`
**HEAD nuevo:** `b3b2eaf8c82cce8b17625c940e0342c387e2a197`
**Commit:** `fix(v1): close prerelease ia onboarding and pg certification gaps`
**Alembic head:** `d1e2f3a4b5c6` (único head, sin migración nueva)

---

## Correcciones aplicadas

| # | Bloque | Cambio |
|---|--------|--------|
| 1 | Providers LLM | `EXECUTABLE_LLM_PROVIDERS = {openai, ollama}`; gateway y `create_provider` rechazan azure-openai/anthropic/gemini con `CONFIGURATION_ERROR` (no HTTP 500). |
| 2 | preferred_provider inválido | `require_explicit_preferred` en `complete()` / `run_llm_for_task`; sin fallback silencioso si fue explícito. |
| 3 | FinOps observable | `registrar_consumo` fallido → auditoría `finops.registration.failed` + flag `finops_registration_failed`; inferencia exitosa se preserva. |
| 4 | technical_detail | `to_public_dict()` sin detalle interno; API `/complete` y errores de ejecución usan respuesta pública. |
| 5 | Onboarding atómico | `bootstrap_orchestration` / `bootstrap_salud` con `commit=False`; `create_organization` hace flush + commit único; rollback ante fallo. |
| 6 | Slug race | `IntegrityError` → HTTP 409 mensaje en español, sin stack trace. |
| 7 | PostgreSQL harness | `conftest`: schema vía `alembic upgrade head` (no `create_all` en PG); advisory lock en TRUNCATE. |
| 8 | StopIteration password reset | Test crea usuario en org del admin (no org aislada → 404). |
| 9 | Natural question flaky | Aserción por `clasificacion` contractual estable, no keywords frágiles. |
| 10 | Deadlocks suite PG | Lock de serialización `_pg_reset_lock` + `pg_advisory_lock` en reset (preserva lógica Paquete E). |

### V1.1 — no abordado (registrado)

- Timeout global ≈2× en fallback
- `LlmInferenceLog` sin cost/user_id
- Persistencia completa del primer error de fallback
- Hardening extra prompt injection
- Edición de rol global preexistente
- Observabilidad adicional, nuevas IAs/providers, CONNECTOR, branding

---

## Pruebas focales

| Área | Resultado |
|------|-----------|
| `tests/test_prerelease_v1_corrections.py` (16 tests) | PASS |
| Providers sin adaptador | PASS |
| preferred_provider inválido | PASS |
| FinOps failure observable | PASS |
| technical_detail oculto (401/429/404/invalid/config/unavailable) | PASS |
| Onboarding rollback / success | PASS |
| Slug duplicate 409 | PASS |
| Fallback válido no roto (`test_llm_gateway_v1`) | PASS |

---

## Regresión SQLite

```
604 passed, 2 skipped, 0 failed
```

(Referencia previa: 588 passed — incremento por nuevos tests focales.)

---

## Regresión PostgreSQL

**SKIP AMBIENTAL** — No hay daemon PostgreSQL en el entorno Cloud Agent actual.

Proceso documentado para certificación local:

1. Crear BD limpia `empleados_ia_v1_final_test`
2. `alembic upgrade head` → confirmar `d1e2f3a4b5c6`
3. `DATABASE_URL=postgresql://.../empleados_ia_v1_final_test pytest` × 2
4. Paquete E (7 tests) × 2

Harness corregido en `tests/conftest.py` para cuando PG esté disponible.

---

## Paquete E (7 tests PostgreSQL)

**SKIP AMBIENTAL** (requiere PostgreSQL).

Tests objetivo:

- `test_shell_830::test_forbidden_returns_403_spanish_detail`
- `test_finops_950::test_registrar_consumo_con_tarifa`
- `test_salud_conocimiento_971::test_authorized_retrieval`
- `test_salud_conocimiento_971::test_contract_relevant_finding`
- `test_salud_conocimiento_971::test_inactive_grant_denied`
- `test_salud_workplan_bridge::test_responsable_unique_assigns_employee`
- `test_agent_factory_e2e::test_finops_limit_reached_is_published_from_real_execution`

---

## Multitenant / P0 / RBAC / Scheduler

```
70 passed (test_p0_precertificacion_v1 + integration_v1_final + multitenant_v1 + security_rbac_v1 + automations_810c_adversarial)
```

P0 regresados: **0**

---

## Frontend

```
npm run build — PASS
```

---

## Alembic

```
d1e2f3a4b5c6 (head) — único head confirmado
```

---

## P1 / P2

| Prioridad | Restantes V1 |
|-----------|--------------|
| P0 | 0 |
| P1 seleccionados | 0 (cerrados en este commit) |
| P2 | slug race cerrado; demás P2 → V1.1 |

---

## Git final

Ver commit en rama `cursor/v1-integracion-final` tras push.

---

## Veredicto

**SQLite + focales + P0/multitenant/RBAC + frontend + Alembic: APROBADO en entorno actual.**

**PostgreSQL completa (pasada 1 y 2) + Paquete E × 2: PENDIENTE AMBIENTAL** — no se declara certificación PostgreSQL completa desde Cloud Agent sin daemon PG.
