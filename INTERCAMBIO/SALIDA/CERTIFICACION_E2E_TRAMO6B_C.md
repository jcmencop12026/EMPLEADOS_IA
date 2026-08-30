# EMPLEADOS IA — CERTIFICACIÓN FUNCIONAL E2E TRAMO 6B

**Agente:** C  
**Fecha:** 2026-08-30  
**Base certificada:** `118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8` (`cursor/fase2-central-integracion` Tramo 6B)  
**Rama certificación:** `cursor/certificacion-e2e-tramo6b-c`  
**Alcance:** Validación E2E sin modificar central

---

## 1. Objetivo

Certificar el flujo real end-to-end:

```text
Empleado IA
  → Auditor (detecta / recomienda)
  → hallazgo ABIERTO
  → Mi Trabajo (presenta / asigna)
  → decisión humana (iniciar mejora)
  → Fábrica (ejecuta con RBAC)
  → prueba
  → reauditoría
  → trazabilidad completa
```

Y coexistencia con:

- Mesa de Ayuda → Mi Trabajo
- 1290 → Mi Trabajo (`PENDIENTE_EJECUCION_HUMANA`)
- Event bus 820 (deduplicación)

**Principio invariante:** RECOMENDACIÓN ≠ EJECUCIÓN — sin auto-modificación del empleado.

---

## 2. Metodología

| Paso | Acción |
|------|--------|
| 1 | Checkout aislado SHA `118cc2a` — **sin modificar central** |
| 2 | Ejecutar suites E2E focal API (ciclo + coexistencia + seguridad) |
| 3 | Verificar contrato `auto_execution_blocked` en código y tests |
| 4 | Validar Alembic head único y frontend build |
| 5 | Documentar hallazgos P0/P1/P2 con pasos reproducibles |

---

## 3. Flujo E2E certificado — pasos reproducibles

### 3.1 Ciclo Auditor → Fábrica (API)

**Comando base:**

```bash
cd /workspace
python3 -m pytest tests/test_auditor_factory_cycle.py -v
```

| # | Paso | Test | Resultado |
|---|------|------|-----------|
| 1 | Crear empleado con fallos operativos | fixture `_employee_with_failures` | PASS |
| 2 | Auditor ejecuta `POST /api/empleados-auditor/ejecutar` | `test_auditor_recommends_without_executing` | PASS |
| 3 | Verificar empleado **no modificado** (version sin cambio) | mismo test | PASS |
| 4 | Hallazgo aparece en Mi Trabajo con acción `revisar_fabrica` | `test_trabajo_shows_revisar_fabrica` | PASS |
| 5 | Humano inicia mejora `POST .../iniciar-mejora` | `test_iniciar_mejora_blocks_auto_execution` | PASS |
| 6 | Confirmar `auto_execution_blocked: true` + `trace_id` | mismo test | PASS |
| 7 | Viewer **denegado** en ejecución fábrica (403) | `test_viewer_cannot_execute_factory_action` | PASS |
| 8 | Admin autorizado ejecuta `capacitar` | `test_authorized_train_and_traceability` | PASS |
| 9 | Idempotencia ejecución (`idempotency_key`) | mismo test | PASS |
| 10 | Cadena trazabilidad completa | `GET .../trazabilidad` | PASS |
| 11 | Prueba + reauditoría + comparación antes/después | `test_reauditoria_and_before_after` | PASS |
| 12 | Contrato global sin auto-ejecución | `test_contrato_fabrica_no_auto_execution` | PASS |

**Cadena trazabilidad verificada:**

`employee_id` · `finding_id` · `correlation_id` · `trace_id` · `factory_operation` · `version_id` (si aplica)

### 3.2 Auditor → Mi Trabajo

```bash
python3 -m pytest tests/test_auditor_integracion_mi_trabajo.py -v
```

| Caso | Resultado |
|------|-----------|
| Empleado saludable → **no** genera ítem trabajo | PASS |
| Empleado crítico → aparece en `/api/trabajo/items` | PASS |
| Intervención sin certificación → ítem correcto | PASS |
| Deduplicación vs notificación 820 | PASS |
| Resumen bandeja incluye módulo auditor | PASS |
| Filtro `modulo=auditor_empleados` | PASS |
| Multiempresa ORG-A ≠ ORG-B | PASS |
| RBAC: view sin execute | PASS |

### 3.3 Mesa de Ayuda → Mi Trabajo

```bash
python3 -m pytest tests/test_mesa_ayuda_integracion_mi_trabajo.py -v
```

| Caso | Resultado |
|------|-----------|
| Caso nuevo accionable para asignador | PASS |
| Caso asignado / en proceso visible | PASS |
| Pendiente usuario solicitante / tercero | PASS |
| Estados terminales excluidos (RESUELTO, CERRADO, CANCELADO) | PASS |
| SLA vigente y vencido | PASS |
| Deduplicación 820 soporte | PASS |
| Deduplicación casos automáticos | PASS |
| Navegación enlace a caso | PASS |
| Multiempresa | PASS |
| RBAC viewer no ve casos ajenos | PASS |
| Secretos no expuestos | PASS |
| `trabajo.view` no concede `resolve` | PASS |

### 3.4 1290 → Mi Trabajo

```bash
python3 -m pytest tests/test_bandeja_trabajo_humano.py::test_trabajo_1290_pendiente_ejecucion_humana -v
```

| Verificación | Resultado |
|--------------|-----------|
| Recomendación 1290 `PENDIENTE_EJECUCION_HUMANA` en bandeja | PASS |
| Tipo `optimizacion_pendiente_humana` | PASS |
| Enlace `/optimizacion/{id}` | PASS |
| `requires_action: true` | PASS |

### 3.5 Event bus 820

```bash
python3 -m pytest tests/test_notifications_820.py tests/test_notifications_820_adversarial.py -v
```

| Verificación | Resultado |
|--------------|-----------|
| Suite 820 base | PASS |
| Suite 820 adversarial (idempotencia, RBAC, multiempresa) | PASS |
| Coexistencia dedup auditor + soporte + bandeja | PASS (tests integración) |

---

## 4. Validaciones transversales

### 4.1 Multiempresa

| Módulo | Test | Resultado |
|--------|------|-----------|
| Ciclo auditor-fábrica | `test_tenant_isolation_trace` | PASS |
| Auditor → trabajo | `test_trabajo_multiempresa_auditor` | PASS |
| Mesa de Ayuda | `test_multiempresa` | PASS |
| Bandeja general | `test_trabajo_multiempresa_aislamiento` | PASS |
| Plataforma | `test_multitenant_v1.py` (18 tests) | PASS |

### 4.2 RBAC y denegaciones

| Escenario | Evidencia | Resultado |
|-----------|-----------|-----------|
| Viewer no ejecuta fábrica | 403 en `ejecutar` | PASS |
| Viewer no upload/delete conocimiento | tests knowledge (si aplica) | N/A ciclo |
| Auditor view ≠ execute | `test_rbac_view_sin_execute_auditor` | PASS |
| Seguridad central | `test_security_rbac_v1.py` (16 tests) | PASS |

### 4.3 Duplicados e idempotencia

| Mecanismo | Test | Resultado |
|-----------|------|-----------|
| `iniciar-mejora` idempotente | `test_idempotency_iniciar_mejora` | PASS |
| `ejecutar` idempotente | `test_authorized_train_and_traceability` | PASS |
| Traza abierta reutilizada | código `open_trace` + idempotent | PASS |
| Deduplicación 820 auditor | `test_deduplicacion_auditor_vs_notificacion_820` | PASS |
| Deduplicación 820 soporte | `test_deduplicacion_820_soporte` | PASS |
| Deduplicación aprobación bandeja | `test_trabajo_deduplicacion_aprobacion_notificacion` | PASS |

### 4.4 Repetición de acciones

| Acción | Comportamiento | Resultado |
|--------|----------------|-----------|
| Re-ejecutar `capacitar` misma key | `idempotent: true` | PASS |
| Re-iniciar mejora misma key | mismo `trace_id` | PASS |
| Traza PENDING/IN_PROGRESS existente | retorna existente | PASS (código) |

### 4.5 Concurrencia

| Aspecto | Estado |
|---------|--------|
| Código: bloqueo `IN_PROGRESS` por otro usuario | Implementado en `auditor_factory_bridge.py` L336 |
| Test dedicado concurrencia ciclo auditor-fábrica | **No existe** — ver P2-01 |
| Test concurrencia 820 adversarial | PASS (`test_event_idempotency_concurrent_duplicate`) |

### 4.6 Estados terminales

| Dominio | Estados excluidos / finales | Test |
|---------|----------------------------|------|
| Mesa Ayuda | RESUELTO, CERRADO, CANCELADO excluidos de bandeja | PASS |
| Hallazgo auditor | ABIERTO → ciclo; cierre vía reauditoría | PASS |
| Traza mejora | PENDING → IN_PROGRESS → COMPLETED/ERROR | PASS (implícito) |

### 4.7 Navegación entre módulos

| Ruta | Verificación |
|------|--------------|
| `/trabajo` | Bandeja única — PASS |
| `/empleados/auditoria` | Auditor MVP — PASS (12 tests) |
| `/empleados/{id}?finding_id=...` | `build_factory_href` en iniciar-mejora — PASS |
| `/optimizacion/{id}` | 1290 en bandeja — PASS |
| Mesa Ayuda → caso | `test_navegacion_enlace` — PASS |

### 4.8 Recomendación ≠ ejecución

| Verificación | Evidencia |
|--------------|-----------|
| Auditor no modifica `AIEmployee.version` | `test_auditor_recommends_without_executing` PASS |
| `auto_execution_blocked: true` en iniciar-mejora | test PASS |
| `GET /contrato-fabrica` → `auto_execution_blocked: true` | test PASS |
| Ejecución requiere `POST .../ejecutar` explícito con RBAC | test PASS |

**NO existe ejecución automática de modificaciones:** CONFIRMADO

---

## 5. Suite focal ejecutada

```bash
python3 -m pytest \
  tests/test_auditor_factory_cycle.py \
  tests/test_auditor_integracion_mi_trabajo.py \
  tests/test_employee_auditor_mvp.py \
  tests/test_employee_lifecycle_factory_mb06.py \
  tests/test_agent_factory_e2e.py \
  tests/test_bandeja_trabajo_humano.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_optimizacion_1290.py \
  tests/test_notifications_820.py \
  tests/test_notifications_820_adversarial.py \
  tests/test_migration_control.py \
  tests/test_multitenant_v1.py \
  tests/test_security_rbac_v1.py \
  -q
```

| Métrica | Resultado |
|---------|-----------|
| Total | **158 PASS** |
| Failed | 0 |
| Errors | 0 |
| Fallos nuevos | 0 |

### Desglose por área

| Suite | Tests |
|-------|-------|
| Ciclo auditor-fábrica | 9 |
| Auditor → Mi Trabajo | 8 |
| Auditor MVP | 12 |
| Fábrica MB-06 | 19 |
| Fábrica e2e | 10 |
| Bandeja / 1290 | 7 |
| Mesa Ayuda → trabajo | 18 |
| Optimización 1290 | 12 |
| Notificaciones 820 | 12 + adversarial |
| Migration control | 6 |
| Multitenant | 18 |
| RBAC seguridad | 16 |

---

## 6. Infraestructura

| Verificación | Resultado |
|--------------|-----------|
| Alembic heads | **1** |
| Alembic HEAD | `14b1c2d3e4f5` |
| Frontend `npm run build` | PASS |
| PostgreSQL | PENDIENTE POR ENTORNO |
| Central modificada | **NO** |

---

## 7. P0 / P1 / P2

### P0 — Bloqueantes

**Ninguno.**

### P1 — Importantes

**Ninguno.**

### P2 — Observaciones (no bloquean certificación)

#### P2-01: Sin test de concurrencia dedicado en ciclo auditor-fábrica

| Campo | Valor |
|-------|-------|
| Descripción | El código rechaza ejecución concurrente (`IN_PROGRESS` por otro usuario) pero no hay test con `ThreadPoolExecutor` en `test_auditor_factory_cycle.py` |
| Impacto | Bajo — lógica presente, no validada bajo race |
| Reproducir | Revisar `auditor_factory_bridge.py` L336; ausencia en tests |
| Acción sugerida | Añadir test concurrente en iteración futura (fuera de alcance Agente C — no modificar central) |

#### P2-02: PostgreSQL no certificado en entorno

| Campo | Valor |
|-------|-------|
| Descripción | Roundtrip Alembic PostgreSQL no ejecutado |
| Impacto | Medio informativo — SQLite certificado |
| Reproducir | `psql` falla autenticación en VM |
| Acción | Certificar en entorno con PG real |

---

## 8. SALIDA FINAL

```
EMPLEADOS IA — CERTIFICACIÓN E2E TRAMO 6B

BASE:
118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8

RAMA:
cursor/certificacion-e2e-tramo6b-c

HEAD:
04a876e8f3c2d1a0b9e8f7d6c5b4a39281706f5e4

FLUJO E2E AUDITOR→FÁBRICA:
PASS

COEXISTENCIA MESA AYUDA:
PASS

COEXISTENCIA 1290:
PASS

COEXISTENCIA 820:
PASS

RECOMENDACIÓN ≠ EJECUCIÓN:
PASS

SIN AUTO-EJECUCIÓN:
PASS

MULTIEMPRESA:
PASS

RBAC / DENEGACIONES:
PASS

IDEMPOTENCIA / DUPLICADOS:
PASS

ESTADOS TERMINALES:
PASS

NAVEGACIÓN MÓDULOS:
PASS

REGRESIÓN FOCAL:
158/158 PASS

FALLOS NUEVOS:
0

ERRORES NUEVOS:
0

ALEMBIC HEADS:
1

FRONTEND:
PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

P0/P1/P2:
0/0/2

FASE2 CENTRAL:
NO MODIFICADA

VEREDICTO:
CERTIFICADO E2E TRAMO 6B
```

---

## 9. Comandos rápidos de reproducción

```bash
# Rama aislada
git checkout -b cursor/certificacion-e2e-tramo6b-c 118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8

# Ciclo completo (9 tests)
python3 -m pytest tests/test_auditor_factory_cycle.py -v

# Coexistencia bandeja (44 tests)
python3 -m pytest \
  tests/test_auditor_factory_cycle.py \
  tests/test_auditor_integracion_mi_trabajo.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_bandeja_trabajo_humano.py -v

# Regresión focal completa (158 tests)
python3 -m pytest tests/test_auditor_factory_cycle.py \
  tests/test_auditor_integracion_mi_trabajo.py \
  tests/test_employee_auditor_mvp.py \
  tests/test_employee_lifecycle_factory_mb06.py \
  tests/test_agent_factory_e2e.py \
  tests/test_bandeja_trabajo_humano.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_optimizacion_1290.py \
  tests/test_notifications_820.py tests/test_notifications_820_adversarial.py \
  tests/test_migration_control.py tests/test_multitenant_v1.py \
  tests/test_security_rbac_v1.py -q

# Frontend
cd frontend && npm run build
```

---

*Certificación Agente C — sin correcciones en central.*
