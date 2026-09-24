# 02 — Deltas V1 preservados en C1

**Base C1:** V2 certificado `dc1e6cd` + integración selectiva hotfix acceso
**Auditoría:** comparación estática `e8cb853` ↔ rama C1

---

## Deltas verificados como PRESERVADOS (sin regresión en C1)

| Delta V1 | Evidencia C1 | Prueba |
|---|---|---|
| **DATABASE_URL** segura (contraseñas especiales, sin leak en logs) | Sin cambios en `backend/app/database.py`, `config` | `test_docker_database_url.py` PASS |
| **Docker compose** topología 3 servicios | `docker-compose.yml` idéntico V1↔V2↔C1 | diff vacío `e8cb853`↔`dc1e6cd` |
| **`.env.example`** configuración versionada | Sin cambios entre V1 y V2 base | diff vacío |
| **`security_config.py`** validación producción | Sin cambios V1↔V2 | diff vacío |
| **`tenant_scope.py`** aislamiento multiempresa | `ensure_organization_active` en deps | `test_multitenant_v1.py` PASS |
| **Knowledge auth** — descarga protegida por token | Router `/api/knowledge/{id}/download` requiere auth | `test_knowledge_930.py`, `test_convergencia_c1` PASS |
| **Knowledge cross-org** bloqueado | Aislamiento por organización | `test_convergencia_c1` PASS |
| **RBAC base** permisos en `/api/auth/me` | `superadmin` + lista permisos | `test_convergencia_c1` PASS |
| **Usuarios/organizaciones/roles** modelo base | `User`, `Organization` sin retroceso | tests multitenant PASS |
| **Migraciones V1** en ledger protegidas | 21 revisiones V1 en `protected_revisions` | `test_convergencia_c1` |
| **Auth login endpoint** | `POST /api/auth/login` 401 en credenciales inválidas | `test_v1_hotfix_login` PASS |

---

## Deltas V1 REINCORPORADOS en C1 (no estaban en V2 cert)

| Delta | Origen | Estado C1 |
|---|---|---|
| Fix `api.ts` orden lectura body | hotfix `1a85532` | **INTEGRADO** |
| Ojo mostrar/ocultar contraseña | hotfix | **INTEGRADO** |
| Panel "¿Olvidó su contraseña?" informativo | hotfix | **INTEGRADO** (texto adaptado a convergencia) |
| Scripts `inspect_admin_user` / `reset_admin_password` | hotfix | **AÑADIDOS** |

---

## Deltas V1 sustituidos intencionalmente por V2 (NO regresión — evolución)

| Capacidad V1 | V2/C1 | Nota |
|---|---|---|
| Login simple sin MFA | Auth + MFA + sesiones | V2 superset; MFA conservado en LoginPage C1 |
| Sin SSO | SSO/OIDC en login | Conservado en C1 |
| Menú reducido | Shell expandido + CC | V2 intencional; no revertido en C1 |
| 21 migraciones head | 53 migraciones head | Salto pendiente C2+staging; no aplicado en C1 |

---

## Deltas V1 NO reintegrados en C1 (fuera alcance / operacional)

| Item | Razón |
|---|---|
| Scripts `INTERCAMBIO/SALIDA/V1_CERT/*.ps1` | Operacionales CERT Windows; no código plataforma |
| SHA/worktree `D:\EMPLEADOS_IA_V1_HOTFIX` | Entorno operativo separado |
| Estado admin CERT recuperado | Cerrado en CERT; no afecta código C1 |

---

## Riesgos de pérdida residual (monitorear en certificación B)

| Riesgo | Mitigación planificada |
|---|---|
| MFA bloquea admin tras migración BD | Bloque 2 plan integración |
| 32 migraciones en BD real | Solo staging; Agente B en CERT |
| Hotfix login vs auth V2 edge cases | Tests C1 + walkthrough manual |

---

## Conclusión

Los deltas críticos V1 identificados en pre-integración están **preservados o reincorporados** en C1. No se detectó debilitación de tests de seguridad.
