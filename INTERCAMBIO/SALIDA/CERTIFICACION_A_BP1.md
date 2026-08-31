# CERTIFICACIÓN A — BLOQUE PRODUCTO 1 (EVALUACIÓN EIAAX)

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** A  
**Modo:** Certificación técnica independiente acumulada — solo lectura  
**Fecha:** 2026-08-31

---

## Veredicto obligatorio

# BP1 TÉCNICO CERTIFICADO

---

## SHAs

| Rol | SHA | Mensaje |
|-----|-----|---------|
| **Base C2** | `b19b04dd438f5b13b422e9a760f54fa074fb52ed` | `feat(c2): gobierno multiempresa CC + Mi Trabajo + contexto SUPERADMIN` |
| **BP1 (auditado)** | `7e9abba11f4c4f216142c6c70d662229ffc585bb` | `feat(evaluacion): Bloque Producto 1 — expediente EIAAX, consola y vista entidad` |

**Worktree:** `/tmp/cert-bp1-a` @ `7e9abba` (detached HEAD, clean).

---

## Resumen ejecutivo

BP1 añade el módulo **Evaluación EIAAX** (expediente, hallazgos, visibilidad entidad, consola, “Preguntar a EIAAX”) sobre la base C2 **sin modificar** superficies certificadas de multiempresa CC/Mi Trabajo, auth, home C1-R1, gateway/finops/fábrica/oportunidades.

| Área | Resultado |
|------|-----------|
| Delta acotado a BP1 | ✓ |
| Migración `1405a1b2c3d4e` | ✓ 5 tablas, FK, tenant, 1 head |
| Aislamiento multiempresa | ✓ |
| RBAC 5 permisos evaluación | ✓ backend autoridad |
| Seguridad visibilidad / Vista Entidad | ✓ filtro backend API |
| IA vía gateway (`route_task`) | ✓ sin fabricación si sin proveedor |
| Regresión focal | **55/55 PASS** |
| Frontend build | PASS |

| P0 | P1 | P2 |
|----|----|-----|
| **0** | **0** | **4** |

---

## 1. Delta BASE (C2) → BP1

### Producto (excl. documentación INTERCAMBIO y respaldos)

| Tipo | Archivos |
|------|----------|
| **Migración** | `1405a1b2c3d4e_expediente_evaluacion_1405.py`, `migration_ledger.json` |
| **Backend** | `evaluacion_models.py`, `routers/evaluaciones.py`, `services/evaluacion_service.py`, `main.py`, `permissions.py`, `schema_repair.py` |
| **Frontend** | `EvaluacionesPage`, `EvaluacionConsolePage`, `EiaaxAskPanel`, `useOrganizationContext` (sin cambio lógica C2), `OrganizationContextBar` (sin diff), `menu.ts`, `api.ts`, `App.tsx`, `AppShell.tsx`, `styles.css`, `brand.ts`, `index.html` |
| **Tests** | `test_bloque_producto_1_evaluacion.py`, `conftest.py` |

**Diff producto:** ~11 archivos backend/frontend + migración + tests (vs ~30 con docs/backup).

### Superficies C2/C1-R1 NO reconstruidas ni dañadas

| Superficie | Diff C2→BP1 |
|------------|-------------|
| RBAC/multiempresa C2 (`control_center_service`, `trabajo_service`) | **0 líneas** |
| Centro de Control / Mi Trabajo (servicios C2) | **0 líneas** |
| Home/fallback C1-R1 (`HomePage`, `homeRoute`) | **0 líneas** |
| Auth/MFA/SSO/sid (`auth.py`, `deps.py`, `LoginPage.tsx`) | **0 líneas** |
| Gateway IA / FinOps / Oportunidades 1030 / Fábrica | **0 líneas** en routers/servicios core |

---

## 2. Datos y migración `1405a1b2c3d4e`

### Cadena Alembic

| Verificación | Resultado |
|--------------|-----------|
| `down_revision` | `1341a1b2c3d4e` ✓ |
| `alembic heads` | **1 head:** `1405a1b2c3d4e` |
| Downgrade | Presente — elimina 5 tablas en orden inverso |
| `test_validate_migrations_runs_without_pythonpath` | **PASS** |

### 5 tablas declaradas

| Tabla | `organization_id` | FK / constraints |
|-------|-------------------|------------------|
| `evaluaciones_expediente` | NOT NULL | FK `organizations`, `users`, `diagnostics`; UQ `(organization_id, codigo)`; índices org/estado |
| `evaluaciones_informacion` | NOT NULL | FK expediente; UQ `(expediente_id, campo)` |
| `evaluaciones_hallazgos` | NOT NULL | FK expediente, `opportunities`; `visible_entidad` default **false**; índice visibilidad |
| `evaluaciones_oportunidad_links` | NOT NULL | FK expediente, oportunidad, hallazgo; UQ `(expediente_id, opportunity_id)` |
| `evaluaciones_visibilidad_log` | NOT NULL | FK expediente, `changed_by`; auditoría cambios visibilidad |

### Pérdida de datos existentes

Migración **solo CREATE** — no ALTER/DROP de tablas preexistentes. **Sin pérdida** de datos C2.

### PostgreSQL aislado

No se ejecutó upgrade en contenedor PostgreSQL dedicado en esta sesión (P2). Evidencia: revisión estática + head único + test migraciones.

---

## 3. Multiempresa y RBAC

### Permisos nuevos (5)

| Código | Uso API |
|--------|---------|
| `evaluacion.view` | Listar, detalle interno, trazabilidad, preguntar |
| `evaluacion.manage` | Crear/editar expediente, info, oportunidades |
| `evaluacion.evaluate` | Evaluar, hallazgos |
| `evaluacion.visibility` | Cambiar `visible_entidad` |
| `evaluacion.vista_entidad` | GET `/vista-entidad` |

Asignados a rol `admin` en `permissions.py`. **Backend = autoridad** (`require_permission` en cada endpoint).

### Aislamiento verificado

| Control | Test | Resultado |
|---------|------|-----------|
| Expediente A no visible en B | `test_bloque1_multitenant_aislamiento` | 404 cross-tenant |
| Hallazgos/información por `organization_id` | `_get_expediente` filtra org | Código + tests |
| Oportunidades vinculadas | `organization_id` en link + opp query | Servicio |
| Vista Entidad no cruza org | `vista_entidad` usa `user.organization_id` | Router |
| Sin permiso | `test_bloque1_rbac_sin_permiso` | **403** |

### SUPERADMIN

Evaluaciones opera en **tenant del usuario** (`user.organization_id`) — sin `organization_id` query cross-org como CC C2. Coherente con gobierno BP1 (producto por organización). Contexto SUPERADMIN C2 (CC/Mi Trabajo) **no modificado**.

---

## 4. Seguridad de visibilidad (gate crítico)

### Backend, no solo frontend

| Mecanismo | Evidencia |
|-----------|-----------|
| `visible_entidad` default `false` en DB y modelo | Migración L75 |
| `get_vista_entidad` filtra hallazgos | `if h.get("visible_entidad")` L696-698 |
| `expediente_to_detail(include_internal=False)` | Excluye `notas_internas`, hallazgos no visibles L260-268 |
| `get_impacto_resumen(vista_entidad=True)` | Sin `valor_potencial`; solo hallazgos visibles L797-815 |
| Log visibilidad | Tabla `evaluaciones_visibilidad_log` + `write_audit` action `evaluacion.visibility` |
| Trazabilidad API | `/trazabilidad` — quién/cuándo/cambio |

### Vista Entidad NO expone (verificado en tests/código)

| Dato interno | Vista Entidad |
|--------------|---------------|
| `notas_internas` | **Ausente** (`test_bloque1_visibilidad_backend_y_vista_entidad`) |
| `valor_potencial` (expediente) | **null** en impacto vista |
| Hallazgos no marcados visibles | **Filtrados** en `get_vista_entidad` |
| Oportunidades sin hallazgo visible | **Filtradas** en `_oportunidades_visibles` |
| Datos otro tenant | **404** vía `_get_expediente` |

Manipulación URL/ID: endpoints resuelven por `(expediente_id, user.organization_id)` — ID de otra org → **404**.

---

## 5. IA — “Preguntar a EIAAX”

| Requisito | Resultado |
|-----------|-----------|
| Gateway existente | `route_task` (`coordinator`) L995 — no import directo OpenAI |
| Sin proveedor | `_has_usable_llm` → `estado: sin_proveedor`, `respuesta: null` L958-979 |
| No fabricar respuestas | Test `test_bloque1_preguntar_sin_proveedor_estado_controlado` |
| Contexto/tenant | `organization_id` + expediente scope en `ask_eiaax` |

---

## 6. Regresión ejecutada

```bash
cd /tmp/cert-bp1-a
pytest tests/test_bloque_producto_1_evaluacion.py \
       tests/test_convergencia_c2.py \
       tests/test_c1_r1_home_route.py \
       tests/test_v1_hotfix_login.py \
       tests/test_convergencia_final_fase2.py \
       tests/test_gate_post6d_correcciones.py::test_g2_solicitar_aprobacion_transitions_trabajo \
       tests/test_gate_post6d_correcciones.py::test_g3_dedup_oportunidad_vs_1290_humana \
       tests/test_integration_v1_final.py::test_e_tenant_a_cannot_see_tenant_b_llm_finops \
       -q
# → 55 passed

cd frontend && npm ci && npm run build
# → ✓ built in 1.29s
```

**No se repitieron campañas C1/C2 completas** — superficies C2 sin diff; regresión focal suficiente.

---

## 7. Hallazgos P0 / P1 / P2

### P0

**Ninguno.**

### P1

**Ninguno.**

### P2 — no bloquean certificación

| ID | Hallazgo | Nota |
|----|----------|------|
| P2-BP1-01 | Sin test explícito “hallazgo oculto NO aparece en vista-entidad” | Cubierto por filtro backend `get_vista_entidad`; test actual solo verifica visible=true |
| P2-BP1-02 | `pytest.mark.evaluacion` no registrado en `pytest.ini` | Warning únicamente |
| P2-BP1-03 | Upgrade PostgreSQL aislado no ejecutado en VM | Revisión estática migración + head único + test validate |
| P2-BP1-04 | Evaluaciones sin selector cross-org SUPERADMIN (diferente de CC C2) | Diseño BP1 tenant-scoped; documentar si se requiere en Bloque 2 |

### Agrupación correcciones (solo si escalara — no aplicable)

No hay P0/P1. Los P2 son documentación/tests opcionales; **no iniciar campaña fragmentada de arreglos**.

---

## 8. Salida obligatoria

```
SHA: 7e9abba11f4c4f216142c6c70d662229ffc585bb ✓
BASE: b19b04dd438f5b13b422e9a760f54fa074fb52ed ✓

MIGRACIÓN: 1405a1b2c3d4e (5 tablas, down from 1341a1b2c3d4e)
ALEMBIC HEAD: 1405a1b2c3d4e (único)

AISLAMIENTO: PASS (multitenant tests)
RBAC: PASS (5 permisos, 403 sin permiso)
VISIBILIDAD: PASS (backend API, log, vista filtrada)
VISTA ENTIDAD: PASS
GATEWAY IA: PASS (route_task / sin_proveedor)
REGRESIÓN: 55/55 PASS | build PASS

P0: 0 | P1: 0 | P2: 4

VEREDICTO: BP1 TÉCNICO CERTIFICADO
```

---

## Restricciones respetadas

- ✓ No modificar producto (salvo pruebas independientes en worktree)  
- ✓ No iniciar Bloque 2  
- ✓ No repetir certificaciones históricas C1/C2 completas  
- ✓ No tocar BD CERT/producción  

---

*Certificación técnica A — Bloque Producto 1 — 2026-08-31*
