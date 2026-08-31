# 01 — Corrección P1-D-UX-01 (C1-R1)

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Rama:** `cursor/eiaax-convergencia-v1-v2`  
**Fecha UTC:** 2026-08-31  
**Tipo:** Corrección única de cierre UX — fallback determinístico de ruta inicial `/`

---

## Hallazgo P1

| ID | Descripción | Estado |
|---|---|---|
| P1-D-UX-01 | Usuario autenticado sin `control_center.view` permanece en `/` con mensaje de error y sin redirección a ruta funcional | **CORREGIDO** |

**Caso reproducido:** usuario `restricted_cc` / rol `restricted_cc` sin `control_center.view`.

---

## Causa raíz

La ruta index `/` renderizaba directamente `CentroControlPage`, que exige `control_center.view`. Usuarios autenticados sin ese permiso veían el mensaje *"No tiene permiso para ver el Centro de Control."* sin ser dirigidos a ninguna vista permitida.

El sidebar ya filtraba entradas por permisos (`filterMenuByPermissions`), pero la resolución de home no reutilizaba esa fuente ni `ROUTE_PERMISSIONS`.

---

## Solución implementada

### Fuente única de navegación

- `frontend/src/navigation/menu.ts` — extracción del `MENU` desde `AppShell.tsx` (sidebar + home comparten definición).

### Resolución determinística de home

- `frontend/src/navigation/homeRoute.ts`:
  - `getNavRoutesInOrder()` — orden estable derivado del menú lateral.
  - `resolveHomeRoute(permissions)` — primera ruta accesible vía `canAccessRoute` + `ROUTE_PERMISSIONS`.
  - `HOME_ROUTE_EXCLUDE` — excluye `/mi-seguridad` (ajuste personal, no módulo operativo).

### Comportamiento en `/` y `/centro-control`

- `frontend/src/pages/HomePage.tsx`:
  - **A)** Con `control_center.view` → renderiza `CentroControlPage`.
  - **B)** Sin CC → `<Navigate replace>` a la primera ruta permitida según orden del menú.
  - **C)** Sin módulos operativos → `NoModulesPage` (mensaje seguro en español + cerrar sesión).

- `frontend/src/pages/NoModulesPage.tsx` — vista segura sin datos sensibles ni loops.

- `frontend/src/App.tsx` — rutas `index` y `centro-control` usan `HomePage`.

- `frontend/src/AppShell.tsx` — importa `MENU` desde `navigation/menu.ts`.

### Seguridad preservada

- La selección frontend **no concede permisos**; `ROUTE_PERMISSIONS` y guards backend siguen siendo autoridad.
- API Centro de Control sigue devolviendo **403** sin `control_center.view` (verificado en pruebas).

---

## Orden de evaluación de rutas home

Derivado del menú lateral (`menu.ts`), en este orden (primer match con permiso efectivo gana):

1. `/` (Centro de Control) — requiere `control_center.view`
2. `/trabajo`, `/operaciones`, `/operaciones/solicitud`, `/ejecuciones`, `/aprobaciones`, `/automatizaciones`
3. `/salud/diagnostico`
4. Rutas Empleados IA (`/directorio`, …)
5. Rutas Análisis y control (`/lineas-base`, `/comercial`, …) — **excepto** `/mi-seguridad`
6. Rutas Administración

---

## Archivos modificados

```
frontend/src/navigation/menu.ts              (nuevo)
frontend/src/navigation/homeRoute.ts         (nuevo)
frontend/src/pages/HomePage.tsx              (nuevo)
frontend/src/pages/NoModulesPage.tsx         (nuevo)
frontend/src/App.tsx
frontend/src/AppShell.tsx
tests/test_c1_r1_home_route.py               (nuevo)
tests/test_convergencia_final_fase2.py       (actualizado alias CC)
INTERCAMBIO/SALIDA/EIAAX_CONVERGENCIA_C1_R1/*
```

### No modificado (alcance respetado)

- Migraciones Alembic
- SHAs V1 (`e8cb853`) / V2 (`dc1e6cd`) / tag `fase2-candidato-final-certificado`
- `D:\EMPLEADOS_IA_CERT`
- `ROUTE_PERMISSIONS` (sin segunda matriz divergente)
- Login hotfix C1 (`api.ts`, `LoginPage.tsx`)

---

## P0 / P1 / P2 nuevos

| Severidad | Nuevos hallazgos |
|---|---|
| P0 | **NINGUNO** |
| P1 | **NINGUNO** (P1-D-UX-01 cerrado) |
| P2 | **NINGUNO** introducido por C1-R1 |

---

## Veredicto

**C1-R1 APTO PARA RECERTIFICACIÓN**
