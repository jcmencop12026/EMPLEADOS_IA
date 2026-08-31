# CERTIFICACIÓN B — DATOS C2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** B  
**SHA:** `b19b04dd438f5b13b422e9a760f54fa074fb52ed`  
**Base:** C1-R1 `3226ba5ee9b998547c7026c98b69972dfacd2d3d`  
**Fecha:** 2026-08-31  
**Modo:** Solo lectura

---

## Veredicto obligatorio

# C2 DATOS APTO

---

## Resumen

C2 **no altera esquema ni modelos**. El impacto de datos es **lógico/contextual**: resolución de `organization_id` en runtime para CC y Mi Trabajo, validación de organización activa, y corrección de filtro de notificaciones por `org_id` resuelto (no `user.organization_id` fijo).

La certificación PostgreSQL previa del Agente B **mantiene validez** — no se requiere migración profunda repetida.

| P0 | P1 | P2 |
|----|----|-----|
| 0 | 0 | 1 |

---

## Verificación por punto

| # | Control | Resultado | Evidencia |
|---|---------|-----------|-----------|
| 1 | Cero migraciones C1-R1→C2 | **PASS** | `git diff … -- backend/alembic/` → 0 líneas |
| 2 | Head único `1341a1b2c3d4e` | **PASS** | `alembic heads` → 1 revisión |
| 3 | Cero cambios modelos/esquema | **PASS** | `git diff … -- backend/app/*models*` → 0 |
| 4 | `resolve_organization_id()` | **PASS** | `control_center_service.py` L921-934; reutilizado en `trabajo_service` |
| 5 | `ensure_organization_active()` | **PASS** | En rama home y cross-org |
| 6 | Org inactiva rechazada como contexto | **PASS** | `test_c2_superadmin_inactive_org_rejected` → 403 |
| 7 | Mi Trabajo usa `org_id` resuelto | **PASS** | `collect_items(db, user, org_id, …)`; router L1153-1202 |
| 8 | Aislamiento A/B en datos | **PASS** | `test_c2_org_a_no_ve_datos_org_b`, `test_c2_org_b_no_ve_datos_org_a` |
| 9 | SUPERADMIN no mezcla tenants | **PASS** | `test_c2_superadmin_cambio_contexto_no_mezcla_datos`; notificaciones solo org activa |
| 10 | Cambio org no conserva datos previos | **PASS** | Resumen A ≠ resumen B por `organization_id` |
| 11 | Conteos/indicadores = org activa | **PASS** | `filtros_aplicados.organization_id` y `organization_id` en CC |
| 12 | Certificación PostgreSQL previa válida | **PASS** | Sin cambio esquema; sin nueva migración |

---

## Cambio de datos relevante (único)

### Fix notificaciones Mi Trabajo (`trabajo_service.py`)

**Antes (C1-R1):** `_notification_visible_query` filtraba por `user.organization_id` fijo.  
**Después (C2):** filtra por `org_id` resuelto vía `resolve_organization_id`.

**Riesgo mitigado:** SUPERADMIN viendo org B ya no arrastra notificaciones de su org home.

**Evidencia:** `test_c2_superadmin_trabajo_notificaciones_solo_org_activa` — "Notif solo B" visible, "Notif solo A" ausente.

### `resolve_organization_id` (comportamiento)

| Caso | Comportamiento |
|------|----------------|
| Sin `organization_id` o = org del usuario | Retorna `user.organization_id` tras `ensure_organization_active` |
| `organization_id` distinto | Requiere `platform.organization.view`; valida org existe y activa |
| Org inactiva | `ensure_organization_active` → excepción → 403 |

---

## Permisos

| Métrica | Valor |
|---------|-------|
| Permisos eliminados vs C1-R1 | **0** |
| Permisos añadidos | **0** |

Cross-org usa permiso existente `platform.organization.view` (sin cambio de matriz).

---

## P2

| ID | Hallazgo |
|----|----------|
| P2-C2-B01 | `sessionStorage` (`eaios_selected_org_id`) guarda preferencia UI SUPERADMIN — no es dato de negocio en BD; documentar en runbook despliegue |

---

## Comandos de evidencia

```bash
cd /tmp/cert-c2-a/backend && alembic heads
# 1341a1b2c3d4e (head)

git diff 3226ba5 b19b04d -- backend/alembic/ backend/app/models.py
# (vacío)

python -m pytest tests/test_convergencia_c2.py -q
# 17 passed
```

---

*Certificación B Datos — 2026-08-31*
