# EMPLEADOS IA — CERTIFICACIÓN FOCAL FINAL POST-6D — AGENTE C

**Modo:** SOLO LECTURA (sin modificar central)  
**Rama:** `cursor/certificacion-focal-final-post6d-c-readonly`  
**SHA exacto:** `1db7a7e5b0947cf89108b4cf8606a20497d21385`  
**Commit:** `fix(gate-post6d): concurrencia CAS auditor/fábrica y cierre P1 B/C/D`  
**Fecha:** 2026-08-30  
**Agente:** C (reauditoría adversarial P1-C-01)

---

## 1. OBJETIVO

Intentar romper nuevamente la corrección de **P1-C-01** (carrera TOCTOU en `ejecutar_operacion_fabrica`) tras el fix CAS en `auditor_factory_bridge.py`. No basta con que el test pase: se exige reproducción de la carrera histórica, batería adversarial ampliada, verificación de estado real en BD y regresión focal E2E completa.

---

## 2. CORRECCIÓN BAJO PRUEBA (`1db7a7e`)

| Mecanismo | Descripción |
|---|---|
| `_atomic_claim_trace_execution()` | `UPDATE … WHERE status IN ('PENDING','FAILED')` → `IN_PROGRESS`; solo `rowcount==1` ejecuta |
| Claim anticipado | CAS **antes** de decisión humana y `solicitar_aprobacion` |
| `_response_for_unclaimed_trace()` | Perdedor: `conflict: true` o respuesta idempotente si ya `COMPLETED` |
| Tests ampliados | `_assert_single_effective_approval()` verifica ≤1 `EmployeeFactoryApproval` PENDING en BD |

---

## 3. BATERÍA ADVERSARIAL EJECUTADA

### 3.1 Carrera original (orden histórico que fallaba en `7ce2f34`)

```
pytest tests/test_auditor_factory_cycle.py \
       tests/test_gate_post6d_correcciones.py::test_concurrency_auditor_factory_no_double_execution
```

| Ejecución | Resultado |
|---|---|
| Sesión única adversarial | **10/10 PASS** |
| 5 repeticiones consecutivas (mismo orden) | **50/50 PASS** (10×5) |

**Antes del fix (`7ce2f34`):** ambos hilos HTTP 200 con claves `conc-a`/`conc-b` → doble ejecución efectiva.  
**Tras fix (`1db7a7e`):** ≤1 respuesta 200 no idempotente; `_assert_single_effective_approval` PASS.

### 3.2 Orden inverso

```
pytest test_concurrency… test_auditor_factory_cycle.py
```

**10/10 PASS**

### 3.3 Concurrencia aislada (5×)

```
pytest test_concurrency_auditor_factory_no_double_execution
```

**5/5 PASS**

### 3.4 Suite concurrencia completa (`-k concurrency`)

| Test | Escenario | Resultado |
|---|---|---|
| `test_concurrency_auditor_factory_no_double_execution` | Misma obligación, claves distintas | PASS |
| `test_concurrency_same_obligation_idempotency_keys[same-key,same-key]` | Claves iguales | PASS |
| `test_concurrency_same_obligation_idempotency_keys[conc-x,conc-y]` | Claves distintas | PASS |
| `test_concurrency_different_obligations_both_succeed` | Obligaciones distintas | PASS (2×200) |
| `test_concurrency_unauthorized_user_denied` | Viewer sin permisos | PASS (403/400) |
| `test_concurrency_repeated_adversarial[0..4]` | 5 repeticiones parametrizadas | PASS (5/5) |

**Total suite concurrencia: 10/10 PASS**

---

## 4. VERIFICACIÓN ESTADO REAL EN BD

Script independiente (SQLite test, dos hilos `db-a`/`db-b`, claves distintas, misma traza):

### Ejecución A

| Hilo | HTTP | Comportamiento |
|---|---|---|
| `db-a` | 200 | Ganador — ejecución efectiva |
| `db-b` | 400 | Perdedor — error controlado, sin segunda operación |

| Métrica BD | Valor |
|---|---|
| `TRACE_STATUS` | `COMPLETED` |
| `TRACE_APPROVAL_ID` | 1 (único) |
| `EMPLOYEE_PENDING_APPROVALS` | **1** |
| `NON_IDEMPOTENT_200` | **1** |
| `CONFLICT_RESPONSES` | 0 (perdedor vía HTTP 400) |

### Ejecución B (variación de timing)

| Hilo | HTTP | Comportamiento |
|---|---|---|
| `db-a` | 200 | Perdedor — `idempotent: true`, `conflict: false` |
| `db-b` | 200 | Ganador — resultado completo con `auto_execution_blocked: true` |

| Métrica BD | Valor |
|---|---|
| `NON_IDEMPOTENT_200` | **1** |
| `APPROVALS_LINKED_TO_TRACE` | **1** |

**Conclusión BD:** en ambos timings, máximo **1 transición efectiva**, **1 aprobación efectiva**, **1 ejecución efectiva**. El perdedor concurrente nunca produce segunda operación efectiva (400 con error o 200 idempotente).

---

## 5. PRESERVACIÓN G1–G4 Y DOMINIOS

### G1–G4 (gate post-6D)

| Gate | Test | Resultado |
|---|---|---|
| G1 | Desviación exige autorización explícita + `auto_execution_blocked` | PASS |
| G2 | Sin duplicación obligación en Mi Trabajo | PASS |
| G3 | Dedup oportunidad vs 1290 humana | PASS |
| G4 | AUTOMÁTICA ≠ autoaprobación oportunidad | PASS |

### Suite focal E2E completa (189 tests)

```
tests/test_gate_post6d_correcciones.py
tests/test_auditor_factory_cycle.py
tests/test_auditor_integracion_mi_trabajo.py
tests/test_employee_auditor_mvp.py
tests/test_employee_lifecycle_factory_mb06.py
tests/test_mb11_comunicaciones.py
tests/test_mb11_integracion_mi_trabajo.py
tests/test_bandeja_trabajo_humano.py
tests/test_mesa_ayuda_mb12.py
tests/test_mesa_ayuda_integracion_mi_trabajo.py
tests/test_optimizacion_1290.py
tests/test_notifications_820.py
tests/test_automations_810c.py
tests/test_security_rbac_v1.py
tests/test_multitenant_v1.py
```

**189 passed, 0 failed**

| Dominio | Incluido en focal | Resultado |
|---|---|---|
| Auditor MVP + ciclo Auditor/Fábrica | ✓ | PASS |
| Fábrica ciclo vida (MB-06) | ✓ | PASS |
| Mi Trabajo (bandeja + integraciones) | ✓ | PASS |
| Mesa ayuda (MB-12) | ✓ | PASS |
| 1290 optimización | ✓ | PASS |
| Comunicaciones (MB-11) | ✓ | PASS |
| 820 notificaciones | ✓ | PASS |
| 810C automatizaciones | ✓ | PASS |
| RBAC | ✓ | PASS |
| Multiempresa | ✓ | PASS |
| `auto_execution_blocked` | G1 + ciclo | PASS |
| Decisión humana / trazabilidad | G1 + bridge | PASS |
| Autorización | G1 + RBAC + viewer | PASS |

---

## 6. POSTGRESQL

| Verificación | Resultado |
|---|---|
| `pg_isready localhost:5432` | Servicio activo |
| Autenticación `empleados@empleados_ia` | **FALLA** (credenciales no disponibles en entorno) |
| Esquema PG local | Desactualizado (`last_training_at` ausente) |
| Suite focal sobre PostgreSQL real | **NO EJECUTADA** |

**POSTGRESQL: PENDIENTE POR ENTORNO**

La corrección CAS está diseñada para semántica PostgreSQL (`UPDATE` condicionado con bloqueo de fila). La certificación adversarial se ejecutó sobre SQLite temporal (patrón `conftest.py`), coherente con el gate documentado en `CURSOR_FASE2_GATE_FINAL_POST6D.md`.

---

## 7. CONTEO EXACTO DE PRUEBAS

| Bloque | Tests |
|---|---|
| Suite focal E2E | **189** |
| Suite concurrencia (`-k concurrency`) | **10** |
| Carrera original (1×) | **10** |
| Orden inverso (1×) | **10** |
| Concurrencia aislada (5×) | **5** |
| Orden adversarial (5×) | **50** |
| G1–G4 explícitos | **4** |
| **Total ejecuciones sesión certificación** | **278** |
| **Total pruebas únicas focal (referencia liberación)** | **189** |

---

## 8. HALLAZGOS P0 / P1 / P2

| Nivel | Count | Detalle |
|---|---|---|
| **P0** | **0** | — |
| **P1** | **0** | P1-C-01 no reproducido; carrera histórica contenida |
| **P2** | 0 en alcance | Cosmética/UI fuera de alcance focal |

**Criterio liberación 6E:** P0=0, P1=0 → **CUMPLIDO** (pendiente PG real para cierre operativo completo).

---

## 9. NOTIFICACIÓN

```
══════════════════════════════════════════════════════════════
 EMPLEADOS IA — CERTIFICACIÓN FOCAL FINAL POST-6D — AGENTE C
 SHA: 1db7a7e5b0947cf89108b4cf8606a20497d21385
 P1-C-01: NO REPRODUCIDO — corrección CAS resiste carrera adversarial
 PRUEBAS FOCAL: 189/189 PASS | ADVERSARIAL: 89/89 PASS
 P0=0 | P1=0 | VEREDICTO: APTO PARA LIBERAR 6E*
 *PostgreSQL real: PENDIENTE POR ENTORNO
══════════════════════════════════════════════════════════════
```

Voz: no disponible en entorno cloud (`notify-send`/`espeak` ausentes). Ausencia no bloquea certificación.

---

## 10. SALIDA FINAL

```
SHA: 1db7a7e5b0947cf89108b4cf8606a20497d21385
CARRERA ORIGINAL: PASS (10/10 × 6 sesiones = 60/60 incl. 5× adversarial)
ORDEN ADVERSARIAL: PASS (50/50 en 5 repeticiones consecutivas)
5X: PASS (concurrencia aislada 5/5 + repeated_adversarial 5/5)
CLAVES IGUALES: PASS (same-key,same-key — ≤1 aprobación BD)
CLAVES DIFERENTES: PASS (conc-x,conc-y — ≤1 no-idempotente)
MISMA OBLIGACIÓN: PASS (≤1 transición, ≤1 aprobación, ≤1 ejecución efectiva)
OBLIGACIONES DIFERENTES: PASS (2 ejecuciones independientes, 2×200)
DOBLE TRANSICIÓN: NO (verificado BD + assertions)
DOBLE APROBACIÓN: NO (EmployeeFactoryApproval PENDING ≤ 1)
DOBLE EJECUCIÓN: NO (NON_IDEMPOTENT_200 ≤ 1)
ESTADO BD: PASS (1 approval_id, 1 PENDING, trace COMPLETED; perdedor 400 o 200 idempotente)
G1-G4: PASS (4/4)
AUTOEJECUCIÓN: PASS (auto_execution_blocked=true preservado)
E2E: PASS (189/189 focal)
MI TRABAJO: PASS (bandeja + integraciones auditor/mesa/mb11)
RBAC: PASS (security_rbac_v1 + viewer denegado)
MULTIEMPRESA: PASS (test_multitenant_v1)
POSTGRESQL: PENDIENTE POR ENTORNO
PRUEBAS: 189 focal | 278 ejecuciones totales sesión
P0: 0
P1: 0
P2: 0 (alcance focal)
VEREDICTO: APTO PARA LIBERAR 6E (condicionado a certificación PostgreSQL real en entorno operativo)
```

---

## 11. COMPARATIVA HISTÓRICA

| Aspecto | Pre-fix (`7ce2f34`) | Post-fix (`1db7a7e`) |
|---|---|---|
| Carrera tras `test_auditor_factory_cycle.py` | **FAIL** — 2× HTTP 200 efectivos | **PASS** — ≤1 efectivo |
| Claves distintas misma obligación | Doble ejecución | CAS por traza causal |
| Perdedor concurrente | Segunda operación | 400 error o 200 idempotente |
| BD aprobaciones PENDING | >1 posible | ≤1 verificado |

---

*Documento generado en modo SOLO LECTURA. Sin modificaciones a `cursor/fase2-central-integracion` ni código de central.*
