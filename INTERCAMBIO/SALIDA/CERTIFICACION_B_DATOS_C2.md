# CERTIFICACIÓN B — DATOS C2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** B (BD / migraciones / datos / multiempresa)  
**Misión:** Certificar impacto de datos, multiempresa y contexto organizacional C2  
**Fecha UTC:** 2026-08-31  

---

## SHA C2

| Campo | Valor |
|---|---|
| SHA exacto certificado | `b19b04dd438f5b13b422e9a760f54fa074fb52ed` |
| Mensaje | `feat(c2): gobierno multiempresa CC + Mi Trabajo + contexto SUPERADMIN` |
| Base C1-R1 | `3226ba5ee9b998547c7026c98b69972dfacd2d3d` |
| Alembic head esperado | `1341a1b2c3d4e` |

---

## Resumen ejecutivo

| Campo | Resultado |
|---|---|
| Migraciones nuevas C1-R1 → C2 | **0** |
| Head único Alembic | **SÍ** (`1341a1b2c3d4e`) |
| Cambios modelo/esquema | **0** |
| Permisos añadidos/eliminados | **0** (181 códigos, idénticos a C1-R1) |
| `resolve_organization_id()` | **VALIDADO** |
| `ensure_organization_active()` | **VALIDADO** |
| Org inactiva rechazada en contexto cross-org | **SÍ** |
| Mi Trabajo usa `org_id` resuelto | **SÍ** |
| Aislamiento multiempresa A/B | **SÍ** |
| SUPERADMIN sin mezcla de tenants | **SÍ** |
| Cambio de org sin datos del tenant anterior | **SÍ** |
| Conteos/indicadores por org activa | **SÍ** |
| Certificación PostgreSQL C1 vigente | **SÍ** (sin repetición migración profunda) |

---

## VEREDICTO

# C2 DATOS APTO

---

## Restricciones cumplidas

| Restricción | Cumplida |
|---|---|
| No modificar producto | **SÍ** (solo certificación / informe) |
| No tocar BD CERT | **SÍ** |
| No iniciar C3 | **SÍ** |
| No repetir migración profunda innecesaria | **SÍ** (diff sin Alembic ni modelos) |

---

## 1. Cero migraciones C1-R1 → C2

**Método:** `git diff 3226ba5..b19b04d -- backend/alembic/`

| Control | Resultado |
|---|---|
| Archivos nuevos/modificados en `alembic/versions/` | **0** |
| Cambios en `migration_ledger.json` | **0** |
| `alembic heads` | `1341a1b2c3d4e (head)` |
| `scripts/validate_migrations.py` | **PASS** |

**Conclusión:** GENERAL confirmado — sin migraciones nuevas en C2.

---

## 2. Head único `1341a1b2c3d4e`

```
1341a1b2c3d4e (head)
```

Ledger `baseline_head`: `1341a1b2c3d4e` — 53 revisiones, 53 protegidas.

---

## 3. Cero cambios incompatibles de modelos/esquema

**Método:** diff C1-R1 → C2 sobre `models.py`, `orchestration_models.py`, `permissions.py`, `alembic/`.

| Área | Cambios |
|---|---|
| Modelos SQLAlchemy | **Ninguno** |
| Alembic | **Ninguno** |
| `permissions.py` (`ALL_PERMISSIONS`) | **Ninguno** (181 ↔ 181) |
| Backend datos (único delta) | `control_center_service.py`, `trabajo_service.py` (lógica de resolución/scope) |

**Conclusión:** C2 es cambio de **comportamiento de contexto organizacional**, no de esquema.

---

## 4–5. `resolve_organization_id()` y `ensure_organization_active()`

### `ensure_organization_active()` (`backend/app/tenant_scope.py`)

- Rechaza `org is None` o `status != ACTIVE` con HTTP **403**.
- Invocada en `deps.py` al autenticar usuario (sesión propia).

### `resolve_organization_id()` (`backend/app/services/control_center_service.py`)

| Caso | Comportamiento C2 |
|---|---|
| Sin `organization_id` o igual a `user.organization_id` | Resuelve org del usuario + `ensure_organization_active(org)` |
| `organization_id` distinto (cross-org) | Requiere `platform.organization.view` + org existente + `ensure_organization_active(org)` |

**Delegaciones:** `trabajo_service`, `consumption_planner_service`, `employee_audit_service`, routers CC/trabajo/auditor.

---

## 6. Organización inactiva no utilizable como contexto cross-org

| Prueba | Resultado |
|---|---|
| `test_c2_superadmin_inactive_org_rejected` | **PASS** — GET `/api/centro-control/resumen-ejecutivo?organization_id=<INACTIVE>` → **403** |

---

## 7. Mi Trabajo usa `org_id` resuelto

| Evidencia | Detalle |
|---|---|
| Código | `trabajo_service.list_items()` / `resumen()` → `cc_svc.resolve_organization_id(db, user, organization_id)` |
| Fix C2 | `_notification_visible_query(db, user, org_id)` filtra por org resuelta (antes: `user.organization_id`) |
| Prueba | `test_c2_mi_trabajo_elementos_tenant_usuario` → **PASS** |
| Prueba cross-org notif | `test_c2_superadmin_trabajo_notificaciones_solo_org_activa` → **PASS** |

---

## 8. Aislamiento A/B en datos

| Prueba | Resultado |
|---|---|
| `test_c2_org_a_no_ve_datos_org_b` | **PASS** |
| `test_c2_org_b_no_ve_datos_org_a` | **PASS** |

Marcador `solo-a` / `solo-b` en `WorkPlan` FAILED no aparece en tenant contrario.

---

## 9. SUPERADMIN cross-org no mezcla tenants

| Prueba | Resultado |
|---|---|
| `test_c2_superadmin_consulta_organizacion_explicita` | **PASS** |
| `test_c2_superadmin_cambio_contexto_no_mezcla_datos` | **PASS** |
| `test_c2_superadmin_trabajo_notificaciones_solo_org_activa` | **PASS** |

`resumen` org A ≠ `resumen` org B; notificaciones scoped por org activa.

---

## 10. Cambio de organización no conserva datos incorrectos del tenant anterior

| Control | Resultado |
|---|---|
| Notificaciones Mi Trabajo | Filtradas por `org_id` resuelto, no por `user.organization_id` del token |
| Prueba notificaciones A/B | Solo aparece notif del org activo en query |
| Prueba resumen contexto | `organization_id` en respuesta coincide con query explícita |

---

## 11. Conteos/indicadores corresponden a organización activa

| Prueba | Resultado |
|---|---|
| `test_c2_centro_control_datos_tenant_correcto` | **PASS** — `organization_id` en resumen CC = tenant del usuario |
| `test_c2_superadmin_cambio_contexto_no_mezcla_datos` | **PASS** — `resumen` por org con `organization_id` distinto |
| `test_c2_mi_trabajo_elementos_tenant_usuario` | **PASS** — `filtros_aplicados.organization_id` correcto |

---

## 12. Certificación PostgreSQL C1 previa — vigencia

| Control | Estado |
|---|---|
| C1 certificado (`25ad1021`) upgrade `d1e2f3a4b5c6` → `1341a1b2c3d4e` | **Vigente** |
| C2 altera cadena Alembic | **No** |
| C2 altera modelos/tablas | **No** |
| BD prueba PG (`empleados_ia_ensayo_test`) en head | `1341a1b2c3d4e` |
| Permisos en BD prueba post-tests | 181 |

**Decisión Agente B:** No se repite migración profunda V1→head. El veredicto **C1 DATOS APTO** sigue aplicable; C2 no invalida el camino de datos certificado.

---

## Pruebas ejecutadas (Agente B)

| Suite | Resultado |
|---|---|
| `tests/test_convergencia_c2.py` | **17 PASS** |
| `tests/test_c1_r1_home_route.py` + `tests/test_convergencia_c1.py` | **17 PASS** (regresión C1/C1-R1) |
| **Subtotal focal datos C2** | **34 PASS** |

Entorno: PostgreSQL `empleados_ia_ensayo_test` (BD de prueba segura; no CERT).

---

## RBAC tenant (muestra)

| Prueba | Resultado |
|---|---|
| `test_c2_tenant_admin_no_puede_cross_org_cc` | **403** |
| `test_c2_tenant_admin_no_puede_cross_org_trabajo` | **403** |
| `test_c2_usuario_sin_permiso_cc_403` | **403** |

---

## P0 / P1 / P2

| ID | Severidad | Estado | Descripción |
|---|---|---|---|
| — | P0 | Cerrado | Sin bloqueadores de datos en C2 |
| PG-CERT-PROD | P1 | Abierto (integración) | Backup validado sobre BD CERT real antes de operación en producción (heredado de C1; C2 no lo resuelve ni lo empeora) |
| C2-CTX-UI | P2 | Registrado | Coherencia de contexto org en frontend depende de `OrganizationProvider` + query param; fuera alcance BD pero cubierto por tests estáticos C2 |
| C3 | P2 | No iniciado | Mandato cumplido |

---

## Notificación

**EIAAX — CERTIFICACIÓN DATOS C2 FINALIZADA**

---

## Firma Agente B

Certificación de datos C2 sobre SHA `b19b04dd438f5b13b422e9a760f54fa074fb52ed`. Sin cambios de esquema ni permisos. Veredicto: **C2 DATOS APTO**. C3 no iniciado.
