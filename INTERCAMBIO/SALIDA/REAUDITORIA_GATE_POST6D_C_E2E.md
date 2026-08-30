# EMPLEADOS IA — REAUDITORÍA E2E + CONCURRENCIA POST-6D

**Agente:** C  
**Fecha:** 2026-08-30  
**Modo:** SOLO LECTURA — central NO modificada  
**SHA auditado:** `7ce2f343e35ebc75850570af7a1fa071f089bb7a`  
**Rama referencia gate:** `cursor/gate-consolidado-post6d-85e4` (HEAD código `c7ef60f`)

---

## 1. Alcance

Reauditar que las correcciones post-6D no rompieron:

1. Flujo E2E Auditor → Mi Trabajo → Fábrica → reauditoría → trazabilidad  
2. Nueva prueba de concurrencia (`test_concurrency_auditor_factory_no_double_execution`)  
3. Coexistencia Mi Trabajo: Auditor, Mesa de Ayuda, 1290, Comunicaciones (MB-11)  
4. Los 4 fallos reportados por General en regresión completa  

---

## 2. Flujo E2E completo

### Cadena verificada

```text
Empleado IA
  → POST /api/empleados-auditor/ejecutar
  → Hallazgo ABIERTO
  → GET /api/trabajo/items (revisar_fabrica)
  → POST .../iniciar-mejora (humano)
  → POST .../ejecutar (RBAC + decisión explícita)
  → POST .../ejecutar probar
  → POST .../reauditar
  → GET .../trazabilidad
```

### Evidencia por principio

| Principio | Test / evidencia | Resultado |
|-----------|------------------|-----------|
| Auditor no ejecuta | `test_auditor_recommends_without_executing` — `AIEmployee.version` sin cambio | PASS |
| Humano decide | G1 `test_g1_deviation_requires_explicit_authorization` — desviación exige `authorize_deviation` + justificación | PASS |
| Fábrica respeta autorización | `test_viewer_cannot_execute_factory_action` → 403 | PASS |
| Desviaciones trazadas | `human_decision` + audit `auditor.factory_decision_deviation` en bridge | PASS |
| Sin auto-ejecución | `auto_execution_blocked: true` en iniciar-mejora y `/contrato-fabrica` | PASS |
| Recomendación ≠ ejecución | G1 rechaza `capacitar` sin desviación cuando recomendación es `SOLICITAR_REVISION_HUMANA` | PASS |

### Suite ciclo (post-correcciones G1)

`tests/test_auditor_factory_cycle.py` — **9/9 PASS**  
(incluye `authorize_deviation` en `test_authorized_train_and_traceability`)

**FLUJO E2E:** PASS  
**DECISIÓN HUMANA:** PASS  
**AUTORIZACIÓN:** PASS  
**TRAZABILIDAD:** PASS

---

## 3. Concurrencia — ejecución y semántica

### Test auditado

`tests/test_gate_post6d_correcciones.py::test_concurrency_auditor_factory_no_double_execution`

### Qué hace realmente

1. Crea empleado con fallos → auditoría → hallazgo → `iniciar-mejora` → `trace_id`
2. Lanza **2 hilos** concurrentes sobre la **misma traza**
3. Cada hilo ejecuta `solicitar_aprobacion` con **idempotency_key distinta** (`conc-a`, `conc-b`)
4. Assert: `results.count(200) <= 1` (máximo una ejecución exitosa)
5. Verifica traza en estado terminal válido (`COMPLETED`, `IN_PROGRESS`, `FAILED`)

### Resultados de ejecución

| Escenario | Resultado |
|-----------|-----------|
| Test aislado (5 repeticiones) | **5/5 PASS** |
| Gate completo (orden archivo: concurrencia tras G1-G4) | **PASS** |
| Gate + auditor ciclo (24 tests) | **PASS** |
| **Auditor ciclo ANTES de concurrencia (misma sesión pytest)** | **FAIL reproducible** |
| Suite E2E ampliada (134 tests, gate primero) | **PASS** |

### Fallo reproducible

```bash
python3 -m pytest \
  tests/test_auditor_factory_cycle.py \
  tests/test_gate_post6d_correcciones.py::test_concurrency_auditor_factory_no_double_execution \
  -v --tb=short
```

**Error:**

```
assert results.count(200) <= 1
assert 2 <= 1
where [200, 200] = results
```

### Análisis semántico

| Aspecto | Hallazgo |
|---------|----------|
| Intención del test | Evitar doble ejecución simultánea sobre la misma obligación/traza |
| Implementación bajo prueba | `auditor_factory_bridge.ejecutar_operacion_fabrica` — bloqueo `IN_PROGRESS` por otro usuario, idempotencia por `exec_key` |
| Gap detectado | Dos hilos con **distintas** `idempotency_key` pueden ambos obtener **200** si cruzan antes del `commit` de `IN_PROGRESS` (TOCTOU) |
| Impacto funcional | Posible **doble `solicitar_aprobacion`** → dos `ApprovalRequest` sobre mismo empleado en carrera |
| ¿Doble aprobación en bandeja? | G2 suprime hallazgo duplicado, pero **no garantiza** un solo approval si ambas ejecuciones completan |
| Estado imposible en traza | No observado — traza queda en estado válido; el riesgo es duplicación de efecto lateral |

**CONCURRENCIA (test ejecutado):** PASS en orden gate / FAIL bajo orden adversarial  
**DOBLE EJECUCIÓN:** RIESGO CONFIRMADO (condicional a carrera)  
**DOBLE APROBACIÓN:** RIESGO TEÓRICO (no verificado en DB en esta reauditoría; semántica del test lo contempla)

---

## 4. Mi Trabajo — coexistencia

### Suites ejecutadas juntas (80 tests)

| Módulo | Suite | Tests | Resultado |
|--------|-------|-------|-----------|
| Auditor | `test_auditor_integracion_mi_trabajo.py` | 8 | PASS |
| Mesa Ayuda | `test_mesa_ayuda_integracion_mi_trabajo.py` | 18 | PASS |
| 1290 | `test_bandeja_trabajo_humano.py` + `test_optimizacion_1290.py` | 7 + 12 | PASS |
| Comunicaciones MB-11 | `test_mb11_integracion_mi_trabajo.py` | 7 | PASS |
| Comunicaciones MB-11 | `test_mb11_comunicaciones.py` | 8 | PASS |
| Gate G2/G3 | dedup auditor/aprobación, 1290/opp | 2 | PASS |
| 820 | `test_notifications_820*.py` | 12+ | PASS |

### Comunicaciones — aspectos verificados

| Caso | Test | Resultado |
|------|------|-----------|
| Fallo recuperable NO en bandeja | `test_recoverable_failure_not_in_trabajo` | PASS |
| Fallo terminal aparece una vez | `test_terminal_failure_appears_once` | PASS |
| Resuelto desaparece | `test_resolved_failure_disappears` | PASS |
| Scheduler retry sin bandeja prematura | `test_scheduler_retry_no_premature_trabajo` | PASS |
| 820 no duplicado por comunicación | `test_820_not_duplicated_by_communication_event` | PASS |
| Multiempresa + RBAC | `test_multiempresa_rbac` | PASS |
| Navegación + filtros + secretos | varios | PASS |

**MI TRABAJO:** PASS (bandeja única `/trabajo`)  
**COMUNICACIONES:** PASS  
**1290:** PASS  
**MESA:** PASS  
**AUDITOR:** PASS

---

## 5. Los 4 fallos de General — análisis funcional

### Reporte General (gate doc)

| Fallo | Causa atribuida |
|-------|-----------------|
| `test_mb11_comunicaciones` ×3 | Contaminación SQLite session-scoped |
| `test_admin_840b` ×1 | Contaminación SQLite session-scoped |
| Mecanismo | `employee_instructions` UNIQUE (`employee_id`) |

### Reproducción Agente C

| Intento | Comando | Resultado |
|---------|---------|-----------|
| Regresión completa monolítica | `pytest tests/` | **1193 passed, 4 skipped, 0 failed** |
| Suite larga + mb11 + admin (2 procesos) | 1159 + 34 | **0 failed** |
| mb11 + admin aislados | directo | **34/34 PASS** |

**Conclusión:** Los 4 fallos **NO se reprodujeron** en esta reauditoría sobre `7ce2f34`.

### ¿Existe escenario E2E real para colisión UNIQUE `employee_instructions`?

| Factor | Evidencia |
|--------|-----------|
| Constraint | `EmployeeInstructions.employee_id` UNIQUE (`orchestration_models.py` L211) |
| Creación | `agent_factory.create_employee` inserta fila; `seed_orchestration` verifica antes de insertar |
| E2E capacitar | `train_employee` actualiza fila existente, no inserta duplicado en ruta normal |
| Escenario plausible | **Solo bajo carrera/concurrencia** o contaminación session-scoped si otro test deja empleado a medias y un segundo test intenta `db.add(EmployeeInstructions(...))` sin guard |
| Ciclo auditor→capacitar concurrente | El test de concurrencia usa `solicitar_aprobacion`, no `capacitar` — **colisión instructions menos probable en ese test** |
| Impacto funcional E2E | **Bajo para flujo nominal**; **medio** como artefacto de suite larga SQLite (infra test, no bug de negocio confirmado) |

**4 FALLOS — IMPACTO FUNCIONAL:** NO REPRODUCIDO / atribuible a infraestructura de test session-scoped, no a regresión E2E del gate en ejecución fresca

---

## 6. Regresión focal ampliada

### Comando

```bash
python3 -m pytest \
  tests/test_gate_post6d_correcciones.py \
  tests/test_auditor_factory_cycle.py \
  tests/test_auditor_integracion_mi_trabajo.py \
  tests/test_employee_auditor_mvp.py \
  tests/test_employee_lifecycle_factory_mb06.py \
  tests/test_mb11_integracion_mi_trabajo.py \
  tests/test_mb11_comunicaciones.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_bandeja_trabajo_humano.py \
  tests/test_optimizacion_1290.py \
  tests/test_notifications_820.py \
  tests/test_notifications_820_adversarial.py \
  -q
```

| Métrica | Resultado |
|---------|-----------|
| Passed | **134** |
| Failed | **0** |
| Errors | **0** |

### Regresión completa (referencia)

| Métrica | Resultado |
|---------|-----------|
| `pytest tests/` | **1193 passed, 4 skipped, 0 failed** |
| Duración | ~15 min |

### Orden adversarial adicional (hallazgo)

| Métrica | Resultado |
|---------|-----------|
| `auditor_factory_cycle` → concurrencia | **1 failed** (doble 200) |

---

## 7. P0 / P1 / P2

### P0 — Bloqueantes

**Ninguno.** Flujo E2E nominal intacto.

### P1 — Importantes (para 6E)

#### P1-C-01: Carrera en ejecución concurrente de fábrica

| Campo | Valor |
|-------|-------|
| Descripción | Dos `ejecutar` simultáneos con distintas `idempotency_key` pueden ambos retornar 200 |
| Reproducir | `pytest tests/test_auditor_factory_cycle.py tests/test_gate_post6d_correcciones.py::test_concurrency_auditor_factory_no_double_execution` |
| Evidencia | `assert results.count(200) <= 1` falla con `[200, 200]` |
| Impacto | Posible doble `solicitar_aprobacion`; contradice espíritu anti-doble-ejecución |
| Relación gate | Test nuevo pasa en orden nominal pero **no es robusto** ni garantiza mutex de traza |
| Acción 6E | Mutex a nivel traza/op (DB lock o unique constraint operación) — **fuera de alcance Agente C (solo lectura)** |

### P2 — Observaciones

#### P2-C-01: Test de concurrencia con semántica ambigua

Usa claves idempotentes distintas pero espera serialización total — mezcla idempotencia por clave con exclusión mutua por obligación.

#### P2-C-02: PostgreSQL no certificado

PENDIENTE POR ENTORNO.

#### P2-C-03: 4 fallos General no reproducidos

Documentar como flaky de infraestructura test; PASS en BD fresca.

---

## 8. SALIDA FINAL

```
SHA:
7ce2f343e35ebc75850570af7a1fa071f089bb7a

FLUJO E2E:
PASS

DECISIÓN HUMANA:
PASS

AUTORIZACIÓN:
PASS

CONCURRENCIA:
PASS (orden nominal) / FAIL (orden adversarial post-ciclo)

DOBLE EJECUCIÓN:
RIESGO CONFIRMADO bajo carrera (P1-C-01)

DOBLE APROBACIÓN:
NO OBSERVADO / RIESGO TEÓRICO

TRAZABILIDAD:
PASS

MI TRABAJO:
PASS

COMUNICACIONES:
PASS

1290:
PASS

MESA:
PASS

AUDITOR:
PASS

4 FALLOS — IMPACTO FUNCIONAL:
NO REPRODUCIDO (0/4 en regresión completa 1193 tests)

P0:
0

P1:
1

P2:
3

VEREDICTO:
REQUIERE CORRECCIÓN (P1 concurrencia) antes de cerrar 6E con P1=0
```

---

## 9. Criterio 6E

| Criterio objetivo | Estado reauditoría |
|-------------------|-------------------|
| P0 = 0 | **CUMPLE** |
| P1 = 0 | **NO CUMPLE** (P1-C-01) |
| Flujo E2E sin regresión | **CUMPLE** |
| Correcciones G1-G9 no rompen coexistencia | **CUMPLE** |

---

*Reauditoría Agente C — solo lectura, central no modificada.*
