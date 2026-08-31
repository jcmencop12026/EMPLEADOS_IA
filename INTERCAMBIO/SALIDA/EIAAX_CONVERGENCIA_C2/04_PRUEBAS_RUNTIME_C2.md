# 04 — Pruebas y Runtime C2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Fecha UTC:** 2026-08-31

---

## Matriz obligatoria A–P

| ID | Caso | Prueba | Resultado |
|---|---|---|---|
| A | Org A no ve datos B | `test_c2_org_a_no_ve_datos_org_b` | **PASS** |
| B | Org B no ve datos A | `test_c2_org_b_no_ve_datos_org_a` | **PASS** |
| C | SUPERADMIN consulta org explícita | `test_c2_superadmin_consulta_organizacion_explicita` | **PASS** |
| D | Sin permiso → 403 backend | `test_c2_tenant_admin_no_puede_cross_org_*`, `test_c2_usuario_sin_permiso_cc_403` | **PASS** |
| E | Menú coherente con permisos | `test_c2_frontend_org_context_wiring` | **PASS** |
| F | `/` C1-R1 preservado | `test_c2_c1_r1_home_route_preservado` + `test_c1_r1_home_route.py` | **PASS** |
| G | CC tenant correcto | `test_c2_centro_control_datos_tenant_correcto` | **PASS** |
| H | Mi Trabajo tenant/usuario correcto | `test_c2_mi_trabajo_elementos_tenant_usuario` | **PASS** |
| I | Sin duplicados G2/G3 | `test_c2_dedup_g2_g3_tests_exist` + gate post6d | **PASS** |
| J | Navegación a recurso | `test_c2_trabajo_enlace_recurso_correcto` | **PASS** |
| K | Cambio contexto no mezcla | `test_c2_superadmin_cambio_contexto_no_mezcla_datos` | **PASS** |
| L | Conteos contexto activo | `test_c2_superadmin_cambio_contexto_no_mezcla_datos` | **PASS** |
| M | Login/MFA/SSO/sid | `test_c2_login_hotfix_preservado` + `test_v1_hotfix_login.py` | **PASS** |
| N | Regresión V1 relevante | `test_multitenant_v1.py`, `test_security_rbac_v1.py` | **PASS** |
| O | Frontend build | `npm run build` | **PASS** |
| P | Alembic head único | `alembic heads` → `1341a1b2c3d4e` | **PASS** |

### Prueba adicional C2
| Caso | Prueba | Resultado |
|---|---|---|
| Notificaciones cross-org | `test_c2_superadmin_trabajo_notificaciones_solo_org_activa` | **PASS** |
| Org inactiva rechazada | `test_c2_superadmin_inactive_org_rejected` | **PASS** |

---

## Regresión focal ejecutada

| Suite | Resultado |
|---|---|
| `tests/test_convergencia_c2.py` | **17 PASS** |
| C1-R1 + multitenant + trabajo + CC + RBAC + gate G2/G3 | **110 PASS** |
| `npm run build` | **PASS** |

Regresión completa `pytest tests/`: ver `05_SHA_CANDIDATO_C2.md`.

---

## Runtime representativo

**Entorno:** uvicorn `127.0.0.1:8010` (SQLite dev)

| Paso | Resultado |
|---|---|
| Login `admin` + `/api/auth/me` | **PASS** — CC y platform perms presentes |
| CC home `resumen-ejecutivo` | **PASS** — `organization_id` coherente |
| Crear org vía `/api/platform/organizations` | **PASS** |
| CC cross-org `?organization_id=` | **PASS** — datos de org creada |
| Mi Trabajo cross-org `?organization_id=` | **PASS** — `organization_id` correcto |

Evidencia capturada en ejecución del agente (JSON runtime 2026-08-31).

---

## PASS / FAIL global

**PASS** — C2 APTO PARA CERTIFICACIÓN
