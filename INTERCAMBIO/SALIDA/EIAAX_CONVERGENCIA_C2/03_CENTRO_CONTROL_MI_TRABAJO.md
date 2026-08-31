# 03 — Centro de Control y Mi Trabajo (C2)

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Fecha UTC:** 2026-08-31

---

## Centro de Control

### Preservado de V2
- `CentroControlPage` y adapters ejecutivos intactos.
- Permiso `control_center.view` obligatorio.
- Indicadores, salud, cadena ejecutiva, Mi Trabajo embebido en resumen.

### Consolidación C2
- `fetchCentroControlResumen(periodo, organizationId?)` envía `organization_id` cuando SUPERADMIN selecciona otra org.
- Cabecera muestra organización activa cuando difiere del contexto home.
- Datos corresponden al tenant resuelto (verificado en pruebas y runtime).

---

## Mi Trabajo

### Bandeja operativa
- `/api/trabajo/items` y `/api/trabajo/resumen` con scope organizacional correcto.
- Elementos del usuario/tenant correcto; sin fugas cross-tenant.
- Conteos (`pendientes`, `vencidas`, `requieren_aprobacion`) alineados al `organization_id` activo.

### Deduplicación G2/G3
- Lógica existente en `trabajo_service.collect_items()` **preservada**.
- Regresión: `test_gate_post6d_correcciones.py` (G2/G3) en suite focal.

### Navegación
- Campo `enlace` en items verificado (`test_c2_trabajo_enlace_recurso_correcto`).
- Badge sidebar usa `fetchTrabajoResumen(organizationQueryParam)` — coherente con contexto activo.

---

## Navegación C1-R1

**Sin cambios funcionales.** Certificado preservado:
- `navigation/menu.ts`
- `navigation/homeRoute.ts`
- `HomePage` / `NoModulesPage`
- Fallback determinístico `/`

El selector de organización afecta **alcance de datos**, no la resolución de home.
