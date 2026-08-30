# REAUDITORÍA INDEPENDIENTE POST-6D — AGENTE A

**Fecha:** 2026-08-30  
**Modo:** Solo lectura / certificación — sin correcciones, sin integración, sin modificación de rama central  
**Commit congelado:** `7ce2f343e35ebc75850570af7a1fa071f089bb7a`  
**Mensaje:** `docs(gate-post6d): HEAD final en entregable`  
**Worktree de inspección:** `/tmp/reaudit-post6d-a` (detached HEAD, working tree clean)  
**Correcciones evaluadas:** commit `c7ef60f` (`fix(gate-post6d): correcciones consolidadas P1 auditor/trabajo/UX`) incluido en el ancestro del SHA congelado

---

## Verificación SHA

```bash
git -C /tmp/reaudit-post6d-a rev-parse HEAD
# 7ce2f343e35ebc75850570af7a1fa071f089bb7a
```

**CONFIRMADO:** el código auditado corresponde exactamente al SHA congelado obligatorio.

---

## Resumen ejecutivo

Reauditoría independiente de los **cuatro P1** reportados por Agente A en Tramo 6B (`118cc2a`), verificando que las correcciones de General en gate post-6D son **implementación real en servicios**, no solo adaptación de tests.

| Área | Resultado |
|------|-----------|
| G1 — Auditor/Fábrica | **CERTIFICADO** |
| G2 — Auditor/Aprobación | **CERTIFICADO** |
| G3 — 1290/Aprobación | **CERTIFICADO** |
| G4 — AUTOMÁTICA ≠ autoaprobada | **CERTIFICADO** |
| Mi Trabajo único (Auditor, 1290, Mesa, Comunicaciones) | **CERTIFICADO** |

---

## Salida obligatoria

```
SHA: 7ce2f343e35ebc75850570af7a1fa071f089bb7a
G1: CERTIFICADO — _validate_human_factory_decision() separa recomendación/decisión; desviación exige authorize_deviation + justification; auto_execution_blocked=true en contrato y respuesta; operación coincidente (solicitar_aprobacion) y adversariales (publicar sin autorización → 400; cambio post-COMPLETED → idempotente sin re-ejecución) verificadas.
G2: CERTIFICADO — tras solicitar_aprobacion: 0 ítems auditor_empleado + 1 ítem aprobacion con auditor_finding_id y workflow_stage=SOLICITUD_APROBACION; hallazgo/trace/approval_id y endpoint /trazabilidad preservados (no borrado histórico).
G3: CERTIFICADO — oportunidad en PENDIENTE_EJECUCION_HUMANA (1290 HUMANA_EXTERNA) no duplica oportunidad_aprobacion; se muestra solo optimizacion_pendiente_humana; oportunidades distintas no se ocultan.
G4: CERTIFICADO — ejecutar AUTOMATICA rechaza PENDIENTE_APROBACION (400); permite APROBADA autorizada; HUMANA_EXTERNA deja pendiente sin auto-ejecutar; viewer sin permiso → 403; repetición idempotente en EJECUTADA; approve_opportunity eliminado de optimization_service.
AUTOEJECUCIÓN BLOQUEADA: true — get_finding_factory_action, iniciar_mejora y ejecutar_operacion_fabrica devuelven/preservan auto_execution_blocked=true.
TRAZABILIDAD: PRESERVADA — EmployeeImprovementTrace, evidence_json del hallazgo (workflow_stage, approval_id), auditoría factory_decision_recorded/deviation, cadena /mejoras/{id}/trazabilidad operativa.
MI TRABAJO ÚNICO: CERTIFICADO — collect_items() única bandeja vía /api/trabajo/items; módulos auditor_empleados, oportunidades/optimizacion, soporte (Mesa de Ayuda), comunicaciones coexisten con filtros modulo=.
DEDUPLICACIÓN: CERTIFICADA — G2 auditor↔aprobación; G3 1290↔oportunidad_aprobacion; notificaciones 820 vs ítems activos; comunicaciones vs notificaciones; soporte vs casos en bandeja.
MULTIEMPRESA: SIN REGRESIÓN — test_1290_cross_tenant, tests adversariales 820, MB-11 viewer sin permiso comunicaciones: PASS en suite focal.
RBAC: SIN REGRESIÓN — viewer no ejecuta fábrica (403), viewer no ejecuta optimización (403), permisos por operación en bridge antes de decisión humana.
P0: 0
P1: 0
P2: 6
VEREDICTO: APTO PARA 6E (P0=0, P1=0)
```

---

## G1 — AUDITOR/FÁBRICA

### Causa P1-1 (Tramo 6B)

`ejecutar_operacion_fabrica` aceptaba `operation` arbitraria sin atarla a la recomendación del hallazgo.

### Corrección verificada (código real)

`backend/app/services/auditor_factory_bridge.py`:

- `_recommended_factory_operation()` deriva operación desde `trace.recommendation`.
- `_validate_human_factory_decision()` implementa **RECOMENDACIÓN ≠ DECISIÓN HUMANA**.
- Desviación: `authorize_deviation=true` + `deviation_justification` (mín. 5 caracteres).
- Auditoría: `auditor.factory_decision_recorded`, `auditor.factory_decision_deviation`.
- Decisión humana inmutable: rechaza cambio de `authorized_operation` si ya existe decisión distinta.
- Ejecución usa `decision["authorized_operation"]`, no el parámetro crudo.
- `auto_execution_blocked: True` en contrato, iniciar-mejora y respuesta de ejecución.

### Pruebas independientes

| Escenario | Resultado |
|-----------|-----------|
| Operación distinta sin autorización (`capacitar` vs recomendación `solicitar_aprobacion`) | 400 — exige `authorize_deviation` |
| Operación distinta con autorización + justificación | 200 — `is_deviation=true`, `auto_execution_blocked=true` |
| Operación coincidente (`solicitar_aprobacion`) | 200 — sin desviación |
| Adversarial `publicar` sin desviación | 400 |
| Post-COMPLETED con operación distinta | 200 idempotente — no re-ejecuta ni muta decisión |
| RBAC viewer ejecutar fábrica | 403 |

**Test dedicado:** `test_g1_deviation_requires_explicit_authorization` — PASS  
**Conclusión:** corrección **sustantiva**, no tautológica.

---

## G2 — AUDITOR/APROBACIÓN

### Causa P1-2 (Tramo 6B)

Tras `solicitar_aprobacion`, coexistían ítem `auditor_empleado` + ítem `aprobacion` para el mismo hallazgo.

### Corrección verificada (código real)

- `trabajo_service.collect_items()`: construye `auditor_finding_ids_pending_approval` desde trazas con `approval_id` PENDING; **omite** hallazgo auditor si está en ese set (líneas 822–823).
- Enriquece ítem `aprobacion` con `auditor_finding_id`, `workflow_stage=SOLICITUD_APROBACION`, enlace a hallazgo.
- `auditor_factory_bridge`: al solicitar aprobación, persiste `workflow_stage`, `approval_id`, `trace_id` en `finding.evidence_json`.

### Pruebas independientes

| Escenario | Resultado |
|-----------|-----------|
| Post `solicitar_aprobacion` en Mi Trabajo | 0 filas auditor + 1 fila aprobacion |
| Trazabilidad histórica | `trace.approval_id` presente; `evidence_json.workflow_stage=SOLICITUD_APROBACION`; GET `/trazabilidad` → 200 |
| Hallazgo no cerrado en solicitar_aprobacion | `status=ABIERTO` — supresión es de **bandeja**, no borrado |

**Test dedicado:** `test_g2_solicitar_aprobacion_transitions_trabajo` — PASS  
**Conclusión:** deduplicación real; trazabilidad histórica **no eliminada**.

---

## G3 — 1290/APROBACIÓN

### Causa P1-3 (Tramo 6B)

Misma oportunidad podía aparecer como `oportunidad_aprobacion` y `optimizacion_pendiente_humana` tras `HUMANA_EXTERNA`.

### Corrección verificada (código real)

- Scan previo en `collect_items()`: `opp_ids_human_exec_pending` desde recomendaciones con `execution_status=PENDIENTE_EJECUCION_HUMANA`.
- Al iterar oportunidades `PENDIENTE_APROBACION`, `continue` si `opp.id in opp_ids_human_exec_pending` (líneas 513–514).
- Ítem 1290 humano: tipo `optimizacion_pendiente_humana` con acciones de confirmación.

### Pruebas independientes

| Escenario | Resultado |
|-----------|-----------|
| Opp en PENDIENTE_APROBACION + rec APROBADA con PENDIENTE_EJECUCION_HUMANA | 0 `oportunidad_aprobacion`, 1 `optimizacion_pendiente_humana` |
| Obligaciones realmente distintas (otra opp sin vínculo 1290) | Siguen apareciendo por separado — no ocultadas |

**Test dedicado:** `test_g3_dedup_oportunidad_vs_1290_humana` — PASS

---

## G4 — AUTOMÁTICA

### Causa P1-4 (Tramo 6B)

`ejecutar_recomendacion(AUTOMATICA)` auto-aprobaba oportunidades vía `approve_opportunity`.

### Corrección verificada (código real)

`optimization_service.ejecutar_recomendacion()`:

- `PENDIENTE_APROBACION` → `ValueError` explícito (no auto-aprobación).
- Solo estados `APROBADA`, `EN_EJECUCION`, `EN_SEGUIMIENTO` para AUTOMATICA.
- `HUMANA_EXTERNA` → `PENDIENTE_EJECUCION_HUMANA` sin activar oportunidades.
- **Confirmado:** `approve_opportunity` **ausente** en `optimization_service.py` (grep sin coincidencias).

### Pruebas independientes

| Escenario | Resultado |
|-----------|-----------|
| Pendiente aprobación + AUTOMATICA | 400 — "requiere aprobación humana" |
| Oportunidad ya APROBADA + AUTOMATICA | 200 — ejecución legítima |
| HUMANA_EXTERNA | 200 — estado rec APROBADA, ejecución humana pendiente |
| Usuario viewer sin `optimizacion.execute` | 403 |
| Repetición sobre rec EJECUTADA | Idempotente (`estado=EJECUTADA`) |

**Test dedicado:** `test_g4_automatica_no_autoaprueba_oportunidad` — PASS

---

## MI TRABAJO — bandeja única

`trabajo_service.collect_items()` integra en un solo endpoint `/api/trabajo/items`:

| Módulo | Origen | Dedup / transición |
|--------|--------|-------------------|
| Auditor | `auditor_empleados` | Suprimido si aprobación pendiente (G2) |
| 1290 | `optimizacion_pendiente_humana`, `oportunidad_aprobacion` | Dedup G3 |
| Mesa de Ayuda | `support_service` → casos activos | Dedup notificaciones/casos |
| Comunicaciones | `communications_service.collect_trabajo_items()` | Dedup msg/correlation vs notificaciones |

**Tests:** `test_bandeja_trabajo_humano.py`, `test_mesa_ayuda_integracion_mi_trabajo.py`, `test_mb11_integracion_mi_trabajo.py` — PASS en suite focal.

---

## AUTOEJECUCIÓN BLOQUEADA

Verificado en:

- `get_finding_factory_action()` → `auto_execution_blocked: True`
- `iniciar_mejora()` → `auto_execution_blocked: True`
- `ejecutar_operacion_fabrica()` → respuesta incluye `auto_execution_blocked: True`
- Auditoría `factory_decision_recorded` incluye flag en detalle

No se encontró ruta adversarial que ejecute fábrica sin paso humano explícito en la traza auditada.

---

## TRAZABILIDAD

- Trazas `EmployeeImprovementTrace` con `evidence_json.human_decision`, `exec_keys`, snapshots before/after.
- Hallazgos conservan evidencia ampliada (workflow, approval_id) — no se borran al deduplicar bandeja.
- Optimización: `trazabilidad_json.ejecucion` con `execution_type`, `execution_status`, `correlation_id`.
- Auditoría de sistema: `auditor.factory_decision_*`, `recomendacion.ejecutada`, `recomendacion.pendiente_ejecucion_humana`.

---

## MULTIEMPRESA / RBAC

Sin regresión detectada en suite focal:

- Aislamiento tenant 1290 (`test_1290_cross_tenant`)
- Notificaciones adversariales 820
- Viewer sin permisos en fábrica y optimización
- Comunicaciones: viewer sin `communications.view` no ve ítems

---

## P0

**0** — Sin fugas multiempresa explotables, bypass RBAC crítico ni auto-ejecución no autorizada en rutas G1–G4.

---

## P1

**0** — Los cuatro P1 de Tramo 6B (A) están **corregidos con lógica de servicio verificada**, no solo con tests adaptados.

| ID Tramo 6B | Estado post-6D |
|-------------|----------------|
| P1-1 Override Fábrica | **CERRADO** (G1) |
| P1-2 Doble obligación auditor+aprobación | **CERRADO** (G2) |
| P1-3 Solapamiento 1290+oportunidad | **CERRADO** (G3) |
| P1-4 AUTOMATICA auto-aprueba | **CERRADO** (G4) |

---

## P2 (observaciones no bloqueantes)

**6** — Persisten mejoras de cobertura/comportamiento secundario del informe Tramo 6B y gate:

1. Hallazgo cerrado en `probar` sin validar resultado de tests.
2. `iniciar-mejora` accesible con solo `auditor_empleados.view` (viewer crea trazas).
3. Evento `EMPLOYEE_AUDIT_INTERVENTION` definido pero no emitido.
4. Cobertura E2E visual de dedup G2/G3 en frontend (backend certificado).
5. Concurrencia: segundo intento post-COMPLETED devuelve idempotente (aceptable; no re-ejecuta).
6. Validación de migraciones depende de SQLite `create_all` en tests — usar `DATABASE_URL` fresco (documentado).

---

## Metodología y pruebas reproducibles

### 1. Verificación SHA

```bash
git -C /tmp/reaudit-post6d-a rev-parse HEAD
# Debe ser 7ce2f343e35ebc75850570af7a1fa071f089bb7a
```

### 2. Suite focal (SQLite limpio obligatorio)

```bash
export DATABASE_URL="sqlite:////tmp/reaudit-post6d-a-fresh.db"
export JWT_SECRET="reaudit-post6d-a-secret"
rm -f /tmp/reaudit-post6d-a-fresh.db

cd /tmp/reaudit-post6d-a
python -m pytest \
  tests/test_gate_post6d_correcciones.py \
  tests/test_bandeja_trabajo_humano.py \
  tests/test_optimizacion_1290.py \
  tests/test_mb11_integracion_mi_trabajo.py \
  tests/test_auditor_factory_cycle.py \
  tests/test_auditor_integracion_mi_trabajo.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_notifications_820.py \
  tests/test_notifications_820_adversarial.py \
  -q
```

**Resultado independiente Agente A:** `96 passed, 0 failed` (~49 s)

### 3. Revisión estática

- `auditor_factory_bridge.py` — G1
- `trabajo_service.py` — G2, G3, Mi Trabajo
- `optimization_service.py` — G4 (sin `approve_opportunity`)

---

## VEREDICTO

**APTO PARA 6E**

- **P0 = 0**
- **P1 = 0**
- Correcciones General **reales** en capa de servicio, corroboradas por tests dedicados `test_gate_post6d_correcciones.py` y verificación adversarial independiente.
- Mi Trabajo único, deduplicación y `auto_execution_blocked` preservados.

---

*Reauditoría independiente Agente A — modo solo lectura. Rama central no modificada.*
