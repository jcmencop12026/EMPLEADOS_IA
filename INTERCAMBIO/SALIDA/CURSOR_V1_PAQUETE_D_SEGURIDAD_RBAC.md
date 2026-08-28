# CURSOR — V1 PAQUETE D — SEGURIDAD, RBAC Y HARDENING

**Fecha/hora UTC:** 2026-08-28 16:28:00 UTC
**Proyecto:** EMPLEADOS_IA
**Paquete:** V1 Paquete D — Seguridad / RBAC / Hardening

---

## 1. RAMA, BASE, HEAD, PR

| Campo | Valor |
|-------|-------|
| **Rama** | `cursor/v1-seguridad-rbac` |
| **Base V1** | `dc51d5ce4852d37e5eef8b5112d1260a002ee3bf` |
| **HEAD final** | `56f6778` (commit código: `8e1d158`) |
| **PR** | [#28](https://github.com/jcmencop12026/EMPLEADOS_IA/pull/28) (draft, sin merge) |

---

## 2. MATRIZ DE HALLAZGOS

| ID | HALLAZGO | SEVERIDAD | EXPLOTABLE | BLOQUEA V1 | CORRECCIÓN |
|----|----------|-----------|------------|------------|------------|
| H-01 | `GET /api/audit/logs` sin `audit.view` | Alta | Sí | No* | `require_permission("audit.view")` |
| H-02 | `POST /api/assistant/ask` sin RBAC ejecución | Crítica | Sí | No* | `operations.execute` + `operations.manage` si `auto_execute` |
| H-03 | `POST /api/agent-factory/coordinator/route` sin RBAC | Crítica | Sí | No* | Igual H-02 |
| H-04 | `operations.execute` definido pero no aplicado | Media | Indirecta | No | Cableado en assistant/coordinator |
| H-05 | JWT secret por defecto en PostgreSQL | Alta | Sí (prod) | **Sí prod** | `validate_security_settings()` en startup |
| H-06 | Bootstrap password por defecto en PG | Media | Sí (prod) | Parcial | Warning en startup (no bloquea CI) |
| H-07 | Menú frontend sin filtro permisos | Media | Parcial | No | `filterMenuByPermissions` en `AppShell` |
| H-08 | Rutas admin/auditoría sin guard frontend | Media | Parcial | No | `RequirePermission` en `App.tsx` |
| H-09 | `AuthorizationError` → HTTP 400 | Baja | No | No | Cambio a **403** |
| H-10 | Mass assignment `organization_id` | N/A | No | No | Ya mitigado por schema Pydantic |
| H-11 | Escalación rol `admin` por operator | Baja | No | No | Ya mitigado `assert_role_assignable` + test |
| H-12 | Rate limiting ausente | Baja | No | **No** | Documentado V1.1 |
| H-13 | OpenAPI `/docs` expuesto | Baja | Recon | No | Documentado V1.1 (Paquete A prod) |
| H-14 | Tests PG `viewer830` duplicado | Baja | No | No | **Dependencia Paquete E** — no implementado aquí |

\*No bloquea entrega funcional V1 demo; bloquea hardening cliente.

---

## 3. VULNERABILIDADES CORREGIDAS

| ID | Corrección aplicada |
|----|---------------------|
| H-01 | `backend/app/routers/audit.py` — `require_permission("audit.view")` |
| H-02 | `backend/app/routers/assistant.py` — RBAC ejecución |
| H-03 | `backend/app/routers/agent_factory.py` — RBAC en `coordinator/route` |
| H-04 | Permiso `operations.execute` aplicado |
| H-05 | `backend/app/security_config.py` + validación en `main.py` lifespan |
| H-07 | `frontend/src/AppShell.tsx` + `auth/permissions.ts` |
| H-08 | `frontend/src/RequirePermission.tsx` + rutas admin/auditoría |
| H-09 | `backend/app/main.py` — handler 403 |

---

## 4. HALLAZGOS DESCARTADOS (YA MITIGADOS)

| Hallazgo | Motivo descarte |
|----------|-----------------|
| Escalación `organization_id` en usuarios | Schema sin campo; Pydantic ignora/rechaza extra |
| Escalación `role` sin control | `assert_role_assignable` + tests 840B |
| Login usuario inactivo | Ya bloqueado en `auth.py` + `deps.py` |
| Cross-tenant audit | Filtro `organization_id` presente |
| JWT claims como fuente RBAC | Permisos desde BD (`user_permissions`) |
| Multi-tenant bypass | Fuera alcance — requiere Paquete C si aplica |

---

## 5. AUTH

| Control | Estado |
|---------|--------|
| Credenciales incorrectas | OK — 401 español |
| Usuario inactivo/bloqueado | OK — test adversarial añadido |
| Token inválido/expirado | OK — tests existentes + nuevo test expirado |
| Token ausente | OK — tests shell 830 |
| Arquitectura JWT | Sin cambios — correcta |

---

## 6. RBAC

| Control | Estado |
|---------|--------|
| Endpoints audit/assistant/coordinator | **CORREGIDO** — permisos reales |
| Admin endpoints | Sin cambios — ya protegidos |
| Escalación privilegios | Test operator→admin 403 |
| Roles 840B | Sin regresión — 64+ tests PASS |
| `operations.execute` | Ahora aplicado |

---

## 7. AISLAMIENTO ORGANIZACIONAL

- Sin desarrollo multi-tenant (GAP-002 / Paquete C).
- Verificado: audit filtra por `organization_id` del usuario.
- Mass assignment `organization_id` no explotable vía API.

---

## 8. SECRETOS Y CONFIGURACIÓN

| Item | Acción |
|------|--------|
| `JWT_SECRET` default | Falla startup en PostgreSQL sin override |
| `ALLOW_INSECURE_DEV_DEFAULTS` | Escape hatch documentado para dev |
| SQLite local | Warning, no bloquea |
| Bootstrap password | Warning en no-SQLite |
| Secretos en repo | No añadidos |

---

## 9. ERRORES

| Item | Acción |
|------|--------|
| `AuthorizationError` | HTTP **403** (antes 400) |
| Mensajes usuario | Español — sin stack traces |
| Logs | Sin cambios — no exponen secretos en respuestas |

---

## 10. FRONTEND

| Item | Acción |
|------|--------|
| Menú por permisos | `ROUTE_PERMISSIONS` + filtro |
| Rutas admin/auditoría | `RequirePermission` |
| 401/403 | Comportamiento existente en `api.ts` |
| Rediseño | No aplicado |

---

## 11. MIGRACIONES

**Ninguna.** Sin cambio de esquema.

---

## 12. ARCHIVOS MODIFICADOS

### Backend
- `backend/app/routers/audit.py`
- `backend/app/routers/assistant.py`
- `backend/app/routers/agent_factory.py`
- `backend/app/main.py`
- `backend/app/security_config.py` *(nuevo)*

### Frontend
- `frontend/src/RequirePermission.tsx` *(nuevo)*
- `frontend/src/auth/permissions.ts` *(nuevo)*
- `frontend/src/AppShell.tsx`
- `frontend/src/App.tsx`

### Tests
- `tests/test_security_rbac_v1.py` *(nuevo — 11 tests adversariales)*

---

## 13. PRUEBAS EJECUTADAS (SQLite — CI default)

```
tests/test_security_rbac_v1.py        11 passed
tests/test_admin_840b.py              (incluido en suite)
tests/test_shell_830.py               PASS
tests/test_shell_830b.py              PASS
tests/test_orchestrator_e2e.py        PASS
────────────────────────────────────────────
Suite Paquete D + RBAC relevante:     64 passed
Frontend build:                       PASS
git diff --check (archivos paquete):  PASS
```

Entorno: `JWT_SECRET=test-secret-mvp-cert803`, `DATABASE_URL` no definido (SQLite temporal).

---

## 14. RIESGOS

| Riesgo | Mitigación |
|--------|------------|
| Operator pierde auto_execute assistant | Correcto — viewer/limited no deben ejecutar |
| Startup falla en PG sin JWT_SECRET | Comportamiento deseado para prod |
| Menú oculto pero API directa | Backend sigue siendo autoridad |

---

## 15. PENDIENTES V1.1

- Rate limiting en login (no bloqueante V1)
- Deshabilitar `/docs` en producción (Paquete A)
- CORS methods/headers más estrictos en deploy
- MFA / refresh tokens
- Paquete E: aislamiento PostgreSQL tests (`viewer830` en PG compartido)

---

## 16. DEPENDENCIAS OTROS PAQUETES

| Paquete | Dependencia |
|---------|-------------|
| **A** | Docs/OpenAPI prod, CORS deploy |
| **B** | Ninguna |
| **C** | Multi-tenant provisioning — no implementado aquí |
| **E** | Tests PG compartidos — recomendado integrar antes de CI PG local completo |

---

## 17. VEREDICTO

### **APTO PARA INTEGRACIÓN**

- Bypass RBAC crítico conocido en audit/assistant/coordinator: **CERRADO**
- Endpoints protegidos en backend: **SÍ**
- Escalación privilegios demostrable: **NO**
- Secretos nuevos versionados: **NO**
- Tests adversariales: **11/11 PASS**
- RBAC 840B: **sin regresión**
- Alcance limitado al paquete: **SÍ**
- Migraciones: **ninguna**
- PR creado, **no mergeado**

---

*Ciclo 810C–1030 no reabierto. Sin LLM, multi-tenant, Docker ni Paquete E.*
