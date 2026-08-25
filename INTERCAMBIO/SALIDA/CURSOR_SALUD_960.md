# CURSOR — SALUD-960 — INFORME DE IMPLEMENTACIÓN

**Estado:** `SALUD-960 LISTO PARA REAUDITORÍA`  
**Rama:** `cursor/salud-ips-engine-960`  
**Base:** `main`  
**NO MERGE**

---

## 1. Qué ya existía

| Componente | Estado previo |
|------------|---------------|
| Orquestador (`coordinator.py`) | Ruteo RIPS/DOCINT, selección primer empleado ACTIVE |
| WorkPlan / EmployeeTask | Ciclo de vida completo |
| Agent Factory | AIEmployee, Capability, Tool, grants |
| Herramientas RIPS/DOCINT | Validación rule-based con hallazgos inline |
| Seed orquestación | 2 empleados (docint, rips), 4 plantillas |
| Centro Operaciones UI | Workspace Salud con muestras RIPS |
| Permisos base | admin/operator/viewer para empleados |
| Tenant isolation | `organization_id` en queries |

## 2. Qué se reutilizó

- Modelo base `AIEmployee` para todos los especialistas IPS (sin 7 modelos distintos)
- `WorkPlan` / `EmployeeTask` para contrato con ORQUESTADOR-910 / OPERACIONES-940
- `Capability` / `Tool` / `EmployeeToolGrant` para capacidades y herramientas
- `coordinator._detect_route` extendido (no reemplazado)
- `coordinator._find_employee_for_capability` con scoring por experiencia
- Patrón router `/api/<dominio>` + `check_permission` fail-closed
- `EmployeeKnowledgeSource` preparado para integración CONOCIMIENTO-930
- Patrón de tests E2E (`conftest.py`, `auth_headers`, tenant isolation)

## 3. Qué faltaba

- Modelos persistentes IPS (datasets, análisis, hallazgos, propuestas, experiencia)
- Capa de normalización con perfiles por fuente
- Indicadores determinísticos (facturación, radicación, glosas, cartera, contratos)
- Trazabilidad Facturado→Radicado→Glosado→CxC→Pagado
- Hallazgos estructurados con confianza basada en criterios
- Propuestas con estructura obligatoria y priorización explicable
- Plan de acción convertible en tareas
- Experiencia/casos, feedback humano, resultado posterior
- Perfil histórico IPS y comparación actual vs histórico
- `buscar_casos_similares()` con similitud estructurada
- Desempeño por especialidad y selección por experiencia
- 7 perfiles de especialistas IPS
- Vista Diagnóstico IPS en español
- Permisos salud.* y tests de aislamiento tenant

## 4. Qué se implementó

### Backend — Modelos (`salud_models.py`)

- `IpsDataset`, `IpsAnalysis`, `IpsHallazgo`, `IpsPropuesta`
- `IpsActionPlan`, `IpsExperienceCase`, `IpsFeedback`, `IpsActionResult`
- `IpsHistoricalProfile`, `IpsEmployeePerformance`

### Migración

- `960a1b2c3d4e_salud_ips_engine_960.py` (revises `5b2eb2437398`)
- 10 tablas IPS con índices por `organization_id`

### Servicios

| Servicio | Función |
|----------|---------|
| `salud_normalization.py` | Perfiles de mapeo, perfilado de calidad |
| `salud_indicators.py` | Cálculos determinísticos, trazabilidad |
| `salud_findings.py` | Hallazgos, propuestas, priorización, resumen ejecutivo |
| `salud_engine.py` | Pipeline completo + plan de acción + diagnóstico |
| `salud_specialist_selection.py` | Selección por capacidades/herramientas/experiencia |
| `salud_experience.py` | Casos, feedback, `buscar_casos_similares`, desempeño |
| `salud_questions.py` | Preguntas naturales sobre indicadores calculados |

### Herramientas analíticas (`tools/salud_analytics.py`)

- `salud-facturado-radicado`, `salud-aging`, `salud-dias-pago`
- `salud-concentracion`, `salud-glosas`, `salud-tendencias`
- `salud-anomalias`, `salud-trazabilidad`, `salud-indicadores`
- `salud-contratos`, `salud-perfil-datos`

### API (`/api/salud/*`)

- `POST /datasets` — carga con perfilado
- `POST /analisis` — ejecuta pipeline
- `GET /diagnostico/{id}` — vista completa 8 secciones
- `POST /analisis/{id}/plan-accion` — convierte propuestas en tareas
- `POST /feedback`, `POST /propuestas/{id}/resultado`
- `POST /pregunta/{id}`, `POST /especialistas/seleccionar`
- `GET /casos-similares`, `GET /desempeno`, `GET /demo/datasets`

### Seed (`seed_salud.py`)

7 especialistas sobre `AIEmployee`:
- Analista de Facturación, Radicación, Glosas, Cartera, Contractual, RIPS, Estratégico

8 capacidades IPS + 11 herramientas analíticas + 6 plantillas

### Frontend

- `DiagnosticoIpsPage.tsx` — ruta `/salud/diagnostico`
- 8 secciones en español: Resumen ejecutivo, Calidad de datos, Indicadores, Hallazgos, Oportunidades, Plan de acción, Seguimiento, Experiencia
- Nav actualizado en `AppShell.tsx`

### Permisos

- `salud.cargar_datos`, `salud.ejecutar_analisis`, `salud.consultar_diagnostico`
- `salud.aceptar_recomendaciones`, `salud.administrar_experiencia`
- admin: todos; operator: sin administrar experiencia; viewer: solo consultar

## 5. Arquitectura real

```
DATOS IPS (IpsDataset / inline)
    → NORMALIZACIÓN (perfiles por fuente)
    → PERFILADO (calidad, campos, duplicados)
    → INDICADORES (Python determinístico)
    → HALLAZGOS (estructurados + confianza por criterios)
    → CAUSAS PROBABLES (separadas de hechos)
    → PROPUESTAS (estructura obligatoria + priorización)
    → PLAN DE ACCIÓN (IpsActionPlan → tareas)
    → SEGUIMIENTO (IpsActionResult)
    → EXPERIENCIA (IpsExperienceCase + feedback)
```

Orquestador:
1. `_detect_route` detecta solicitudes IPS
2. `select_specialists()` evalúa capacidades, herramientas, especialidad, experiencia
3. Asigna especialistas por dominio + consolidador estratégico
4. Resultados persistidos con trazabilidad de fuentes

## 6. Perfiles de agentes

Todos usan `AIEmployee` con `specialty` distinta:

| Código | Nombre | Capacidad |
|--------|--------|-----------|
| ips-facturacion-analyst | Analista de Facturación IA | ips-facturacion |
| ips-radicacion-analyst | Analista de Radicación IA | ips-radicacion |
| ips-glosas-analyst | Analista de Glosas IA | ips-glosas |
| ips-cartera-analyst | Analista de Cartera IA | ips-cartera |
| ips-contractual-analyst | Analista Contractual IA | ips-contractual |
| ips-rips-analyst | Analista RIPS IA | rips |
| ips-estrategico-analyst | Analista Estratégico IPS IA | ips-estrategico |

## 7. Selección del Orquestador

Factores evaluados (sin hardcode por nombre):
- Capacidades requeridas vs asignadas (35%)
- Herramientas disponibles (15%)
- Coincidencia de especialidad (20%)
- Disponibilidad lifecycle (15%)
- Experiencia histórica `IpsEmployeePerformance` (15%)

## 8. Tests

Archivo: `tests/test_salud_960.py` — **25 tests**

Cubre: dataset completo/parcial, campos faltantes, normalización, indicadores (facturación, radicación, glosas, cartera), histórico, hallazgo, confianza, propuesta, priorización, experiencia, feedback, resultado posterior, selección especialistas, tenant isolation, permisos, no alucinación, plan acción, preguntas naturales, migración.

**Suite completa: 71 passed**

## 9. Validación

| Comando | Resultado |
|---------|-----------|
| `pytest` | PASS (71 tests) |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |
| `git diff --check` | PASS |

## 10. HEAD y commits

Se actualizará tras commit final en rama `cursor/salud-ips-engine-960`.

## 11. Pendientes reales

- Integración activa con CONOCIMIENTO-930 (interfaz preparada vía `EmployeeKnowledgeSource`)
- Vinculación automática `IpsActionPlan.work_plan_id` con WorkPlan del orquestador
- Embeddings para `buscar_casos_similares` (V1 usa filtros estructurados)
- Análisis colaborativo multi-tarea con consolidación por agente estratégico en WorkPlan
- Desarrollo de ideas no numéricas (arquitectura de planes lista, flujo ideación pendiente de UI dedicada)
- Alembic en entorno local con revisiones legacy (`820a1`) requiere reparación de cadena (pre-existente)

---

**SALUD-960 LISTO PARA REAUDITORÍA**
