# EMPLEADOS IA — Diseño ejecutable del Auditor de Empleados IA y mejora continua

**Tipo:** análisis técnico sobre código real (sin implementación en esta entrega).  
**Rama inspeccionada:** `cursor/bandeja-trabajo-humano-unificada` @ `d5acb37`  
**Git root:** repositorio EMPLEADOS_IA (`/workspace`)

---

## 1. Resumen ejecutivo

La plataforma **ya posee piezas suficientes** para un Auditor de Empleados IA sin crear un motor paralelo: lifecycle y certificación (`agent_factory`), ejecución y aprobaciones (`coordinator`, `operations`), FinOps y LLM logs por `employee_id`, conocimiento con grants, experiencia transversal, notificaciones 820, automatizaciones 810C (schedule + `INTERNAL_EVENT`), inteligencia externa 1240 para vigilancia normativa, y bandeja `/trabajo` para trabajo humano.

**No existe** hoy un agregador de cumplimiento por empleado, ni entidades `employee_audit*`, ni score de salud del empleado IA. Los bloques **1260** y **1290** están en ramas remotas (`origin/cursor/1260-aprendizaje-repriorizacion`, `origin/cursor/1290-*`) y **no** en HEAD actual.

**Arquitectura recomendada (contrastada con código):** **HÍBRIDO**

| Capa | Rol | Reutiliza |
|------|-----|-----------|
| Motor determinístico | Métricas, umbrales, disparadores, scoring, dedupe, multiempresa | FinOps, LLM logs, work_plans, tests, grants, límites |
| Servicio de auditoría | Orquesta ciclo, persiste hallazgos, emite eventos | Event bus, notifications 820, 810C |
| Empleado IA Auditor (opcional Fase 2) | Interpretación / recomendaciones en lenguaje natural | `agent_factory` + LLM Gateway 1250 |
| Aprobación humana | Acciones de riesgo | `operations.approve`, `oportunidades.approve`, `/trabajo` |

**Principio validado:** el motor determinístico no debe auto-otorgar permisos ni modificar políticas críticas; las acciones automáticas usan permisos del **usuario/sistema que dispara** o quedan en cola humana.

---

## 2. Alcance y límites (no confundir)

| Capacidad existente | Uso del Auditor | No duplicar |
|--------------------|-----------------|-------------|
| Centro de Control 1230 | Configuración y lectura agregada de salud empleados | Vista ejecutiva read-only |
| Salud IPS (`/api/salud`) | Solo contexto sectorial | Salud operativa del agente |
| FinOps 1110 | Consumo/costo/valor por empleado | Motor de presupuestos |
| Observabilidad `/health` | Salud de plataforma | Salud por empleado |
| 1290 / 1260 | Ciclo mejora post-auditoría (tras merge) | Motor de optimización global |
| 810C | Disparadores periódicos y por evento | Orquestador de negocio |
| 820 | Alertas y escalamiento | Centro de notificaciones |
| Bandeja `/trabajo` | Aprobaciones e intervenciones | Agregador operativo general |

---

## 3. Disparadores (diseño)

### 3.1 Periódicos (A)

**Reutilizar 810C** (`Automation.trigger_type = SCHEDULE`, `schedule_type`: DAILY | WEEKLY | MONTHLY | INTERVAL).

- Patrón: automatización ACTIVE con `employee_id` del **Auditor** o sin empleado (servicio) que invoca `POST /api/empleados-auditor/ejecutar` con `scope=ORG|EMPLOYEE_LIST`.
- Config en `recurrence_config_json` + nueva sección `employee_auditor` en config org (ver §7).
- Frecuencias: diario / semanal / mensual / intervalo — **ya soportadas** por `automation_scheduler` + `recurrence.py`.

### 3.2 Por evento (B)

**Reutilizar:**

1. **Event bus** (`app/events/bus.py`) — ya persiste `work_events` y audita.
2. **810C `INTERNAL_EVENT`** (`automation_events.py` → `trigger_internal_event`) — filtra por `recurrence_config_json.event_type`.
3. **820** — `emit_event` desde coordinator/finops/automation.

**Eventos existentes útiles:**

| Evento | Origen | Disparo auditoría |
|--------|--------|-------------------|
| `EXECUTION_FAILED` / `work.failed` | coordinator, notifications | Auditoría focal empleado del plan |
| `FINOPS_LIMIT_REACHED` | finops_service | Auditoría costo + empleado en scope |
| `AUTOMATION_FAILED` | automation_service | Empleado vinculado a automation |
| `APPROVAL_REJECTED` | notifications | Empleado del plan |
| `employee.tested` / `employee.certification_failed` | agent_factory (`EmployeeEventType`) | Re-certificación |
| `employee.activated` | agent_factory | Auditoría baseline post-activación |
| `TENANT_SECURITY_EVENT` | seguridad | Si payload incluye `employee_id` |

**Eventos lifecycle ya emitidos pero no en 820** (`EmployeeEventType`): `employee.tested`, `employee.published`, `employee.certification_failed` — **brecha:** suscriptor notifications no los incluye en `SUPPORTED_EVENTS` (solo `EMPLOYEE_CREATED/CERTIFIED/ACTIVATED`).

**Nuevos eventos propuestos (implementación):**

- `employee.audit.scheduled`
- `employee.audit.completed`
- `employee.audit.critical`
- `employee.training.recommended`
- `employee.normative.impact_detected`

### 3.3 Por umbral (C)

Evaluación en **motor determinístico** al cerrar ventana (o en cada run periódico), usando datos reales:

| Umbral | Fuente real | Campo / agregación |
|--------|-------------|-------------------|
| Errores | `work_plans` FAILED por `employee_id` | count / rate en ventana |
| Reintentos | `automation_runs.attempt`, task retries en payload | parcial |
| Latencia | `llm_inference_logs.latency_ms`, `employee_test_runs.latency_ms` | avg, p95 si se calcula |
| Consumo tokens | `llm_inference_logs.tokens_total` | sum por ventana |
| Costo | `finops_records.cost`, `llm_inference_logs.cost` | sum vs `employee_limits` / presupuesto empleado |
| Tasa éxito | work_plans COMPLETED vs FAILED | rate |
| Calidad | `employee_experience_records.estado`, feedback | parcial |
| Cumplimiento objetivo | `employee_experience_records` valor/tiempo esperado vs real | parcial |
| Aprobaciones humanas | `approval_requests` por planes del empleado | ratio reject |

**No inventar:** exactitud automática sin golden tests; hoy solo smoke tests de herramientas.

### 3.4 Manual (D)

`POST /api/empleados-auditor/ejecutar` con permiso `employee.audit` (nuevo) o `employee.admin`.

Alcance: un empleado, lista, o “todos ACTIVE/PUBLISHED” de la org.

### 3.5 Qué reutiliza 810C (resumen)

| Necesidad | 810C hoy | Acción |
|-----------|----------|--------|
| Cron diario/semanal/mensual | SCHEDULE + scheduler | Reutilizar |
| Disparo por evento dominio | INTERNAL_EVENT + event_type en config | Reutilizar + ampliar eventos |
| Aprobación previa ejecución sensible | `requires_approval` + WAITING_APPROVAL | Reutilizar para acciones auto con límites |
| Idempotencia | `occurrence_key` | Reutilizar para auditorías programadas |

---

## 4. Qué auditar — métricas disponibles vs brechas

### 4.1 Inventario por dimensión

| Dimensión | ¿Existe? | Fuente código | Granularidad |
|-----------|----------|---------------|--------------|
| Calidad operativa | Parcial | `employee_test_runs`, `employee_experience_records.estado` | Por empleado |
| Exactitud | Limitada | Tests smoke (`agent_factory.test_employee`) | Por empleado |
| Cumplimiento objetivo | Parcial | `employee_experience_records` KPI antes/después | Por empleado |
| Tasa de éxito ejecución | Sí | `work_plans.status` | Por empleado |
| Errores | Sí | `work_plans.error`, `llm_inference_logs.error_*` | Por empleado |
| Reintentos | Parcial | `automation_runs.attempt` | Indirecto |
| Latencia | Sí | `llm_inference_logs`, test runs | Por empleado |
| Consumo tokens | Sí | `llm_inference_logs` | Por empleado |
| Costo | Sí | `finops_records`, LLM cost | Por empleado |
| Herramientas | Sí | `employee_tool_grants`, ejecución tool denied | Por empleado |
| Fuentes conocimiento | Sí | `employee_knowledge_grants`, `employee_knowledge_sources` | Por empleado |
| Conocimiento documentos | Sí | `knowledge_documents.status`, `version` | Org + grants |
| Modelo / proveedor | Sí | `ai_employees.model_*`, `llm_inference_logs` | Por empleado |
| Política modelo | Sí | `employee_model_policies` | Por empleado |
| Límites | Sí | `employee_limits` | Por empleado |
| Aprobaciones humanas | Sí | `approval_requests` vía `work_plans` | Por empleado |
| Rechazos humanos | Sí | approval status REJECTED | Por empleado |
| Resultados posteriores | Parcial | experience + oportunidades materializadas | Parcial |
| Valor generado | Parcial | `finops_values`, valoración 1210 vía oportunidad | Indirecto |
| Certificación vigente | Sí | `employee_certifications`, `certified_at` | Por empleado |
| Lifecycle | Sí | `lifecycle_status`, `published_at` | Por empleado |
| Automatizaciones | Sí | `automations.employee_id`, runs | Por empleado |

### 4.2 API métricas actual (insuficiente)

`GET /api/agent-factory/employees/{id}/metrics` (`agent_factory.get_employee_metrics`) devuelve solo:

- `test_runs`, `test_passed`, `avg_latency_ms` (tests)
- `finops_available` (booleano org, **no** desglose empleado)

**Brecha P0:** servicio `employee_metrics_service` que consolide ventana temporal para el Auditor.

### 4.3 Centro de control (lectura auxiliar)

`control_center_service._employees_section`: `ultima_actividad`, `ejecuciones_activas`, `errores` — útil para dashboard, no para reglas de auditoría.

---

## 5. Resultado de auditoría (diseño de salida)

### 5.1 Estructura propuesta (nueva persistencia)

```text
employee_auditor_runs
  id, organization_id, trigger_type, trigger_ref, scope_json,
  started_at, finished_at, status, cost_ref, correlation_id

employee_auditor_assessments
  id, run_id, employee_id, organization_id,
  estado,           -- SALUDABLE | OBSERVAR | REQUIERE_MEJORA | REQUIERE_INTERVENCION | CRITICO
  score_numeric,    -- opcional 0-100 determinístico
  metric_snapshot_json,
  estado_dominio_employee,  -- lifecycle_status copiado
  last_certification_id,
  created_at

employee_auditor_findings
  id, assessment_id, employee_id,
  codigo, titulo, disciplina,  -- HECHO | INFERENCIA | RECOMENDACION
  evidencia_json, causa_text, severidad,
  accion_recomendada,  -- enum §5.3
  estado,              -- ABIERTO | ACEPTADO | DESCARTADO | EN_ACCION | CERRADO
  correlation_id
```

### 5.2 Estados de evaluación

Reglas determinísticas ejemplo (configurables por org):

| Estado | Condición ilustrativa (datos reales) |
|--------|--------------------------------------|
| SALUDABLE | success_rate ≥ umbral, costo dentro límite, cert vigente, 0 hallazgos CRITICAL |
| OBSERVAR | 1–2 hallazgos MEDIA o tendencia negativa |
| REQUIERE_MEJORA | tests fallidos, grants inactivos, costo > 80% límite |
| REQUIERE_INTERVENCION | lifecycle ACTIVE con certificación FAIL o costo > límite |
| CRITICO | repetición FAILED > N, TOOL_DENIED SECURITY, presupuesto empleado alcanzado |

Siempre conservar `estado_dominio` original (`lifecycle_status`, `work_plan.status`, etc.) en snapshot.

### 5.3 Acciones recomendadas (enum)

`CAPACITAR`, `ACTUALIZAR_CONOCIMIENTO`, `MEJORAR_INSTRUCCIONES`, `AGREGAR_HERRAMIENTA`, `CAMBIAR_HERRAMIENTA`, `CAMBIAR_MODELO`, `CAMBIAR_PROVEEDOR`, `AJUSTAR_AUTOMATIZACION`, `REDISEÑAR_EMPLEADO`, `SOLICITAR_REVISION_HUMANA`

Mapeo a APIs existentes (ejecución humana o auto segura):

| Acción | API / flujo existente |
|--------|----------------------|
| MEJORAR_INSTRUCCIONES | `PATCH` employee + `employee_instructions` |
| ACTUALIZAR_CONOCIMIENTO | knowledge grant + process document |
| AGREGAR/CAMBIAR_HERRAMIENTA | `agent_factory` assignments |
| CAMBIAR_MODELO/PROVEEDOR | patch employee + `employee_model_policies` + aprobación |
| AJUSTAR_AUTOMATIZACION | `/api/automations` |
| CAPACITAR | test_lab + re-certify flow |
| REDISEÑAR_EMPLEADO | wizard + nueva versión (humano) |
| SOLICITAR_REVISION_HUMANA | ítem bandeja `/trabajo` |

---

## 6. Autonomía y clasificación de acciones

Configurable en `employee_auditor_config` (org):

```json
{
  "acciones": {
    "ACTUALIZAR_CONOCIMIENTO": "REQUIERE_APROBACION_HUMANA",
    "MEJORAR_INSTRUCCIONES": "AUTOMATICA_CON_LIMITES",
    "marcar_notificacion_leida": "AUTOMATICA_SEGURA",
    "CAMBIAR_PROVEEDOR": "PROHIBIDA_AUTOMATICAMENTE",
    "REDISEÑAR_EMPLEADO": "PROHIBIDA_AUTOMATICAMENTE"
  },
  "limites_auto": { "max_costo_accion_usd": 5, "max_acciones_por_run": 3 }
}
```

| Clase | Ejemplos | Mecanismo |
|-------|----------|-----------|
| AUTOMÁTICA SEGURA | Registrar hallazgo, emitir notificación INFO, programar re-test smoke | Sin cambio de config empleado |
| AUTOMÁTICA CON LÍMITES | Re-ejecutar smoke tests, pausar empleado si CRITICO + policy | `employee.admin` del actor sistema; audit log |
| REQUIERE APROBACIÓN | Cambio modelo, grants conocimiento, publicar instrucciones | `ApprovalRequest` o ítem bandeja |
| PROHIBIDA | Cambio RBAC, políticas seguridad, auto-certify, auto-activate | Solo humano con permisos explícitos |

**El Auditor no puede:** asignarse `employee.certify`, `admin.role.*`, `seguridad.manage_policy`, ni modificar su propia config de autonomía sin `employee.audit.manage`.

---

## 7. Capacitación (diseño de ciclo — sin implementar)

Ciclo objetivo reutilizando piezas:

```text
auditoría (nuevo servicio)
  → hallazgo brecha (finding RECOMENDACION: CAPACITAR)
  → [1260] ciclo aprendizaje si desviación valor/costo (rama remota)
  → [1290] recomendación priorizada (rama remota)
  → aprobación humana (operations / oportunidades / bandeja)
  → actualizar conocimiento (930) o instrucciones (employee_instructions)
  → probar (employee.test / test_lab)
  → comparar métricas ventana anterior vs posterior (nuevo snapshot en assessment)
  → aceptar (cerrar finding) o revertir (employee_versions snapshot)
```

**En HEAD actual:**

- **930:** `POST /api/knowledge/.../process`, grants `employee_knowledge_grants`
- **1010:** `crear_experiencia`, `actualizar_resultado_experiencia` (`experience_core.py`)
- **1030:** `register_opportunity_learning` — solo si oportunidad tiene `equipo_json.lider.employee_id`
- **1260:** `CicloAprendizaje`, recalibraciones APROBADA/APLICADA (rama remota)
- **1290:** recomendaciones APROBADA → ejecución; `PENDIENTE_EJECUCION_HUMANA` en rama ejecución

**Brecha:** no hay entidad “plan de capacitación empleado” — usar `employee_auditor_findings` + `work_plan` opcional de tipo capacitación.

---

## 8. Normatividad y conocimiento (diseño)

### 8.1 Fuentes reales reutilizables

| Bloque | Componente |
|--------|------------|
| 1240 | `external_sources`, `external_signal_extensions` (`regulation_json`, `hecho_observado`, `interpretacion`, `validated_at`) |
| 1220 | dominio `EXTERNO_REGULACION` en `DIAGNOSTIC_DOMAINS` |
| 930 | `knowledge_documents` + `metadata_json` (jurisdicción/vigencia manual) |
| 1350 | catálogo gobierno, políticas conector |
| 1120 | señales proactivas incorporadas |

### 8.2 Proceso diseñado

```text
1. Ingesta / schedule (810C + 1240 ingest)
2. Clasificar fuente (1240 classification, confiabilidad — NO asumir verdad)
3. Aplicabilidad (organization_external_context.sector, geografias, dominios_json)
4. Empleados afectados:
   - specialty / dominio empleado vs dominio señal
   - knowledge grants que referencian documento/tag
   - herramientas/regulación en employee policies
5. Impacto (hallazgo INFERENCIA + evidencia HECHO)
6. Propuesta actualización (RECOMENDACION → knowledge document o instructions)
7. Aprobación según riesgo (governance + operations.approve)
8. Actualizar conocimiento (930 process + grant)
9. Pruebas (employee.test)
10. Publicación (knowledge activate; employee publish si cambia config)
11. Trazabilidad: correlation_id + audit_logs + knowledge_activities
```

**Persistencia recomendada:** `normative_watch_items` o extensión de `external_signal_extensions` con:

`fuente_id`, `fecha_fuente`, `jurisdiccion`, `vigencia_desde/hasta`, `evidencia_url`, `version_doc`, `empleados_afectados_json`, `estado_pipeline`.

---

## 9. Gobierno desde Centro de Control (configuración — sin nueva vista ejecutiva)

**Hoy 1230 es read-only** (`control_center_service`, `GET /api/centro-control/resumen-ejecutivo`). No hay persistencia de umbrales auditor en Centro de Control.

**Diseño:** extender **config org** (no duplicar CC):

- Opción A: `organizations.config_json.employee_auditor` (ya existe `config_json` en `Organization`)
- Opción B: tabla `employee_auditor_config` (1:1 org) — preferida para auditoría y migraciones claras

Campos configurables desde UI futura en CC (sección “Auditor empleados”):

- frecuencia auditoría (enlace a automation id)
- disparadores evento habilitados
- umbrales (JSON por métrica)
- empleados incluidos / excluidos (lista id o tags specialty)
- acciones automáticas permitidas (mapa §6)
- fuentes normativas activas (ids 1240)
- presupuesto auditor FinOps (`finops_budgets` scope `proceso` código `EMPLOYEE_AUDITOR`)
- modelos/proveedores permitidos para el propio Auditor
- notificaciones (820 rules)
- escalamiento (severidad → recipient_role)

**API propuesta:** `GET/PATCH /api/centro-control/auditor-empleados-config` que delega a `employee_auditor_config` (permiso `employee.audit.manage`).

---

## 10. Salud de Empleados IA (conexión conceptual)

Jerarquía:

```text
salud_plataforma (build_health_report en CC)
  └── salud_empleados_ia (nuevo agregado)
        ├── por empleado: estado auditor §5.2
        ├── última / próxima auditoría (runs)
        ├── hallazgos abiertos (findings ABIERTO)
        ├── acciones pendientes (bandeja + approvals)
        ├── mejoras aplicadas (findings CERRADO + experience)
        └── antes/después (metric_snapshot_json diff)
```

**Datos hoy:** `ai_employees.status` (runtime), `lifecycle_status` — **no** score de salud.

**Extensión futura CC:** nuevo adapter `EmpleadosSaludAdapter` en `control_center_adapters.py` leyendo `employee_auditor_assessments` — **no implementar vista ahora**.

---

## 11. Integración Bandeja Mi Trabajo (futura — no modificar bandeja ahora)

La bandeja (`trabajo_service.py`, `/api/trabajo/items`) ya soporta tipos extensibles.

**Tipos futuros:**

| tipo bandeja | Origen | requires_action |
|--------------|--------|-----------------|
| `auditoria_revision` | finding + SOLICITAR_REVISION_HUMANA | true |
| `auditoria_aprobacion_accion` | cambio modelo/instrucciones | true |
| `capacitacion_pendiente` | finding CAPACITAR | true |
| `normativa_impacto` | normative_watch | true |

**Deduplicación:** si hay `ApprovalRequest` para mismo `employee_id` + acción, ocultar notificación duplicada (misma regla que aprobaciones hoy).

**Acciones bandeja:** navegar a empleado, aprobar acción vía APIs existentes; **no** marcar auditoría completa sin confirmación backend.

---

## 12. Matriz de capacidades (inspección real)

| Bloque | Veredicto | Evidencia / uso auditor |
|--------|-----------|-------------------------|
| **810C** Automatizaciones | **REUTILIZABLE** | Schedule, INTERNAL_EVENT, approval, `employee_id` en automation |
| **820** Notificaciones | **REUTILIZABLE** | `emit_event`, `alert_rules`, idempotency |
| **930** Conocimiento | **REUTILIZABLE** | Grants, versiones, activity log |
| **1000** Analítica | **PARCIAL** | `motor_analitico/*` — priorización/hypothesis; no empleado IA |
| **1010** Orquestación / Experiencia | **REUTILIZABLE** | work_plans, experience records, event bus |
| **1030** Oportunidades | **PARCIAL** | `equipo_json.lider.employee_id`, learning hook |
| **1110** FinOps | **REUTILIZABLE** | Records, budgets scope empleado, alertas |
| **1120** Señales | **PARCIAL** | Sin `employee_id`; alimenta contexto org |
| **1200** Línea base | **PARCIAL** | `lineas_base.employee_id` opcional |
| **1210** Valor | **PARCIAL** | Valoración por oportunidad, no empleado directo |
| **1220** Diagnóstico | **PARCIAL** | Dominios incl. `EXTERNO_REGULACION`; sin dominio EMPLEADOS_IA |
| **1230** Centro Control | **REUTILIZABLE** | Indicadores, empleados actividad; extender config |
| **1250** IA / LLM | **REUTILIZABLE** | `llm_inference_logs` por employee_id |
| **1260** Aprendizaje | **PARCIAL** | Modelos en rama remota; ciclos por oportunidad |
| **1270** Multiproveedor | **REUTILIZABLE** | `llm_provider_configs`, fallback en logs |
| **1290** Optimización | **PARCIAL** | Rama remota; portafolio, no auditor empleado |
| **1330** Integraciones | **PARCIAL** | Salud conector; no métrica empleado |
| **1350** Gobierno | **PARCIAL** | Catálogo/políticas; approvals datos sensibles |
| **1360** Continuidad | **PARCIAL** | Incidentes plataforma; `integracion_1260_prep` stub |
| **1380** Identidad | **NO RELACIONADA** | SSO/SCIM; no auditoría empleado |

**Conteo:** REUTILIZABLE **8** · PARCIAL **10** · NO RELACIONADA **1** (1380)  
*(1010 cuenta orquestación+experiencia; 1250+1270 unificados como LLM Gateway)*

---

## 13. Agente dedicado vs servicio

### Preguntas acordadas

| Pregunta | Respuesta técnica |
|----------|-------------------|
| ¿Empleado IA Auditor dedicado? | **Opcional (Fase 2)** — plantilla en `employee_templates` como otros empleados; **no** obligatorio para MVP |
| ¿Servicio determinístico? | **Sí (MVP)** — `employee_auditor_service.py` |
| ¿Híbrido? | **Sí (recomendado)** — determinístico + LLM opcional para narrativa hallazgos |

### Por qué híbrido (código)

- Certificación actual es **100% determinística** (`certify_employee` score fijo).
- Diagnóstico 1220 y externo 1240 ya separan **HECHO / interpretación / hipótesis**.
- LLM Gateway ya audita inferencias sin guardar prompts completos (`llm_inference_logs`).
- Empleado IA dedicado duplicaría orquestación si se usa como **único** motor; debe limitarse a interpretación bajo política y costo FinOps.

### Arquitectura propuesta

```text
┌─────────────────────────────────────────────────────────┐
│  Disparadores: 810C SCHEDULE / INTERNAL_EVENT / Manual  │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│  employee_auditor_service (determinístico)              │
│  - collect_metrics(employee_id, window)                   │
│  - evaluate_rules(config thresholds)                      │
│  - persist assessments + findings                         │
│  - emit employee.audit.* + notifications 820            │
└──────────────────────────┬──────────────────────────────┘
                           ▼
              ┌────────────┴────────────┐
              ▼                         ▼
   ┌──────────────────┐      ┌──────────────────────┐
   │ Acciones auto    │      │ Cola humana          │
   │ (policy §6)      │      │ /trabajo + approvals │
   └──────────────────┘      └──────────────────────┘
                           ▼
              ┌────────────────────────────┐
              │ Opcional: Empleado Auditor │
              │ (LLM narrativa hallazgos)  │
              └────────────────────────────┘
```

---

## 14. Multiempresa

**Patrón existente:** `organization_id` en todas las tablas empleado; `resolve_organization_id` (como `control_center_service`).

**Diseño auditor:**

- Todas las tablas `employee_auditor_*` con `organization_id` NOT NULL + FK
- Queries siempre `filter(organization_id == resolved_org)`
- SUPERADMIN: `platform.organization.view` + param `organization_id`
- Hallazgos, métricas, conocimiento: **nunca** join cross-org
- Empleado Auditor (si existe) es **per-org** (`ai_employees.organization_id`)

**Veredicto diseño:** PASS

---

## 15. Costos (FinOps integración)

### Reutilizar

- `finops_records` al finalizar cada `employee_auditor_run` (categoría `AUDITORIA_EMPLEADO`)
- `llm_inference_logs` si se usa Empleado Auditor LLM
- Presupuesto: `FinOpsBudget` con `scope_type=proceso`, `scope_id=EMPLOYEE_AUDITOR`, `policy` configurable
- Alertas: reutilizar `finops_service` umbral → `FINOPS_LIMIT_REACHED` → **no** re-auditar en loop (guard en auditor: skip si trigger es finops y run es del auditor)

### Diseño anti-consumo

- Frecuencia adaptativa: si costo auditor > X% valor protegido, reducir a semanal/mensual
- Modelo LLM: usar proveedor económico / shadow para narrativa; umbral tokens por run
- Ventana métricas: agregar en SQL, no re-leer logs completos sin límite
- Límite empleados por run (config `max_employees_per_run`)

---

## 16. Auditor del Auditor

Controles diseñados:

| Riesgo | Control |
|--------|---------|
| Autorreferencia infinita | Auditor runs no disparan `INTERNAL_EVENT` sobre `employee.audit.*` (`automation_loop_guard` pattern) |
| Ciclos auto-mejora | Acciones sobre empleado Auditor requieren humano distinto (`decided_by != system_auditor_user`) |
| Modificación recursiva permisos | PROHIBIDA automática para RBAC; servicio no llama `bootstrap_permissions` |
| Cambio políticas críticas | PROHIBIDA; solo `employee.audit.manage` humano |
| Auto-aprobación hallazgos CRITICO | Siempre `SOLICITAR_REVISION_HUMANA` |
| Auditor audita auditor | Run tipo `META_AUDIT` mensual determinístico, **sin** LLM, revisa solo métricas del servicio |

---

## 17. APIs necesarias (propuesta)

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/api/empleados-auditor/config` | `employee.audit.view` |
| PATCH | `/api/empleados-auditor/config` | `employee.audit.manage` |
| POST | `/api/empleados-auditor/ejecutar` | `employee.audit.run` |
| GET | `/api/empleados-auditor/runs` | `employee.audit.view` |
| GET | `/api/empleados-auditor/runs/{id}` | `employee.audit.view` |
| GET | `/api/empleados-auditor/empleados/{id}/estado` | `employee.view` + audit |
| GET | `/api/empleados-auditor/hallazgos` | `employee.audit.view` |
| POST | `/api/empleados-auditor/hallazgos/{id}/decidir` | `employee.audit.manage` |
| GET | `/api/centro-control/auditor-empleados-resumen` | `control_center.view` |

Extensión bandeja (futura): `trabajo_service` importa hallazgos ABIERTO con `requires_action`.

---

## 18. RBAC propuesto (nuevos permisos)

| Permiso | Uso |
|---------|-----|
| `employee.audit.view` | Ver runs, hallazgos, estado salud |
| `employee.audit.run` | Ejecutar manual |
| `employee.audit.manage` | Config, cerrar hallazgos, aprobar acciones |
| `employee.audit.approve_action` | Ejecutar acción recomendada de riesgo medio |

Reutilizar: `employee.view`, `employee.test`, `employee.certify`, `employee.admin`, `notification.manage`, `finops.view`.

**Veredicto diseño RBAC:** PASS (fail closed, sin ampliar privilegios por defecto)

---

## 19. Modelo de datos — resumen migración futura

**Nueva migración (cuando se implemente):**

1. `employee_auditor_config`
2. `employee_auditor_runs`
3. `employee_auditor_assessments`
4. `employee_auditor_findings`
5. (Opcional) `normative_watch_items`

**Sin duplicar:** métricas crudas permanecen en tablas origen; snapshots JSON en assessments.

---

## 20. Plan de implementación por etapas

### Etapa 0 — Pre-requisitos (P1 integración)

- Merge o portar ramas 1260/1290 si se requiere ciclo mejora completo
- Ampliar `SUPPORTED_EVENTS` 820 con lifecycle empleado

### Etapa 1 — MVP determinístico (P0)

- Migración tablas auditor
- `employee_metrics_service` (ventana 7d/30d)
- `employee_auditor_service.run()` manual + programado vía 810C
- Hallazgos + notificaciones CRITICAL/HIGH
- Permisos RBAC seed
- Tests multiempresa + dedupe

### Etapa 2 — Gobierno y CC (P1)

- Config org + endpoint CC
- Presupuesto FinOps auditor
- Adapter salud empleados (solo API, sin vista)

### Etapa 3 — Bandeja y acciones (P1)

- Tipos ítem `/trabajo`
- Flujo aprobación acciones recomendadas
- Integración approvals operaciones

### Etapa 4 — Normativa (P1)

- Pipeline 1240 → empleados afectados
- Hallazgos normativos + knowledge workflow

### Etapa 5 — Capacitación cerrada (P2)

- Ciclo antes/después con experience + re-test
- 1260 recalibración pesos si disponible

### Etapa 6 — Híbrido LLM (P2)

- Plantilla Empleado Auditor opcional
- Narrativa hallazgos con límite costo

---

## 21. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Métricas incompletas | Declarar HECHO solo con evidencia; INFERENCIA explícita |
| Costo auditor > valor | Presupuesto + frecuencia adaptativa |
| Loop eventos | loop guard + tipos evento excluidos |
| 1260/1290 no en main | Etapa 0 port; MVP sin ellos |
| Certificación débil actual | Auditor no reemplaza certify; exige gaps adicionales |
| Fuentes externas no verificadas | 1240 validation + humano para cambios conocimiento |

---

## 22. Referencias de código (muestra)

| Tema | Archivo |
|------|---------|
| Lifecycle / certify | `backend/app/services/agent_factory.py` |
| Métricas actuales (limitadas) | `get_employee_metrics` líneas 570–582 |
| Eventos empleado | `backend/app/enums.py` `EmployeeEventType` |
| Automatización evento | `backend/app/services/automation_events.py` |
| Notificaciones | `backend/app/notifications.py` |
| Experiencia | `backend/app/experience_models.py` |
| LLM por empleado | `backend/app/llm_models.py` `LlmInferenceLog` |
| FinOps empleado | `backend/app/finops_models.py`, `finops_service` |
| Conocimiento grants | `backend/app/knowledge_models.py` |
| Externo / normativa | `backend/app/external_models.py` |
| Centro control empleados | `control_center_service._employees_section` |
| Bandeja trabajo | `backend/app/services/trabajo_service.py` |
| 1260 (rama remota) | `learning_models.CicloAprendizaje` |
| 1290 (rama remota) | `optimization_models.OptimizacionRecomendacion` |

---

## SALIDA FINAL

```
EMPLEADOS IA — DISEÑO AUDITOR IA TERMINADO

CAPACIDADES EXISTENTES REUTILIZABLES:
8

BRECHAS REALES:
12

AGENTE DEDICADO:
HÍBRIDO (servicio determinístico MVP; Empleado Auditor LLM opcional Fase 2)

MOTOR DETERMINÍSTICO:
SI

AUDITORÍA PERIÓDICA:
DISEÑADA

AUDITORÍA POR EVENTO:
DISEÑADA

AUDITORÍA POR UMBRAL:
DISEÑADA

AUDITORÍA MANUAL:
DISEÑADA

CAPACITACIÓN:
DISEÑADA

VIGILANCIA NORMATIVA:
DISEÑADA

CENTRO CONTROL:
INTEGRACIÓN DISEÑADA

MI TRABAJO:
INTEGRACIÓN DISEÑADA

FINOPS:
INTEGRACIÓN DISEÑADA

MULTIEMPRESA:
PASS DE DISEÑO

RBAC:
PASS DE DISEÑO

P0:
6

P1:
8

P2:
4

CÓDIGO FUNCIONAL MODIFICADO:
NO

FASE2 CENTRAL:
NO

MAIN:
NO

V1:
NO

VEREDICTO:
LISTO PARA IMPLEMENTACIÓN
```

### Brechas reales enumeradas (12)

1. Sin tablas `employee_auditor_*`
2. Sin agregador métricas por empleado (API metrics insuficiente)
3. Sin score/estado salud empleado IA
4. Sin eventos 820 para lifecycle completo (`employee.tested`, etc.)
5. 1260 no en HEAD — repriorización post-ejecución
6. 1290 no en HEAD — recomendaciones / `PENDIENTE_EJECUCION_HUMANA`
7. Sin dominio diagnóstico `EMPLEADOS_IA`
8. Sin entidad “plan capacitación empleado”
9. Sin config auditor en Centro de Control (solo read today)
10. Certificación no cruza FinOps/políticas/conocimiento
11. Sin presupuesto FinOps tipo `EMPLOYEE_AUDITOR`
12. Bandeja sin tipos auditoría (integración futura diseñada)

### P0 (6)

1. Migración + servicio auditor determinístico
2. `employee_metrics_service` ventana temporal
3. API ejecutar manual + listar hallazgos
4. Disparo periódico vía 810C
5. RBAC + multiempresa
6. Notificaciones hallazgos CRITICAL

### P1 (8)

1. Config org + endpoint CC
2. Disparadores por evento (bus + INTERNAL_EVENT)
3. Umbrales configurables
4. Integración bandeja `/trabajo`
5. FinOps presupuesto auditor
6. Pipeline normativo 1240
7. Port 1260
8. Port 1290 ejecución humana

### P2 (4)

1. Empleado IA Auditor LLM narrativa
2. Ciclo capacitación antes/después automatizado
3. Vista CC salud empleados
4. Acciones automáticas con límites avanzados

---

**EMPLEADOS IA. Diseño del Auditor de Empleados IA y mejora continua terminado.**
