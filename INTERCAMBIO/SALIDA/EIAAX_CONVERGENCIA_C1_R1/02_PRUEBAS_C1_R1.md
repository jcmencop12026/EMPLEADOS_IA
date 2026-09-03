# 02 — Pruebas C1-R1

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Corrección:** P1-D-UX-01 — fallback determinístico `/`  
**Fecha UTC:** 2026-08-31

---

## Pruebas nuevas (`tests/test_c1_r1_home_route.py`)

| # | Caso | Método | Resultado |
|---|---|---|---|
| 1 | Usuario con `control_center.view` → home `/` | `test_resolve_home_superadmin` + `test_backend_rbac_superadmin_has_control_center` | **PASS** |
| 2 | Sin CC, con Mi Trabajo (`notification.view`) → `/trabajo` | `test_resolve_home_without_cc_mi_trabajo` + `test_backend_restricted_cc_without_centro_control` | **PASS** |
| 3 | Sin CC, otro módulo (`comercial.view`) → `/comercial` | `test_resolve_home_without_cc_other_module` | **PASS** |
| 4 | Sin módulos operativos → `null` / vista segura | `test_resolve_home_no_operational_modules` + `test_backend_no_modules_user_still_authenticated` | **PASS** |
| 5 | SUPERADMIN preserva CC | `test_backend_rbac_superadmin_has_control_center` | **PASS** |
| 6 | Sin loop de redirects (`home !== "/"` cuando no hay CC) | `test_resolve_home_no_redirect_loop_to_self` | **PASS** |
| 7 | Backend no concede CC sin permiso (403 API) | `test_backend_restricted_cc_without_centro_control` | **PASS** |
| 8 | Login hotfix C1 intacto | `test_login_hotfix_still_present` | **PASS** |
| — | Wiring `HomePage` en `App.tsx` | `test_app_uses_home_page_for_index` | **PASS** |
| — | Fuente única menu + permissions | `test_home_route_source_uses_menu_and_permissions` | **PASS** |
| — | Lógica redirect en `HomePage` | `test_home_page_redirect_logic` | **PASS** |

---

## Regresión focal ejecutada

| Suite | Resultado |
|---|---|
| `tests/test_c1_r1_home_route.py` | **13 PASS** |
| `tests/test_v1_hotfix_login.py` | **PASS** |
| `tests/test_convergencia_c1.py` | **PASS** |
| `tests/test_security_rbac_v1.py` | **PASS** |
| `tests/test_convergencia_final_fase2.py` | **PASS** (alias CC actualizado a `HomePage`) |
| `npm run build` (frontend) | **PASS** |

**Subtotal focal C1-R1:** 43 passed

---

## Regresión completa

| Suite | Resultado |
|---|---|
| `pytest tests/` | **1263 passed**, 4 skipped, **0 failed** |

Áreas cubiertas: auth/login, RBAC, multiempresa, Centro de Control, Mi Trabajo, navegación, integraciones convergencia.

---

## PASS / FAIL global C1-R1

| Área | PASS/FAIL |
|---|---|
| P1-D-UX-01 corregido | **PASS** |
| Pruebas obligatorias 1–8 | **PASS** |
| Regresión focal | **PASS** |
| Regresión completa | **PASS** |
| Build frontend | **PASS** |
| Sin debilitación RBAC/backend | **PASS** |

**Resultado global: PASS**
