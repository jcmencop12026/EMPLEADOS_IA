# CERTIFICACIÓN A — BLOQUE C2 (INDEPENDIENTE)

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** A  
**Modo:** Solo lectura — sin modificar producto  
**Fecha:** 2026-08-31  
**Base certificada:** C1-R1 @ `3226ba5ee9b998547c7026c98b69972dfacd2d3d`

---

## Veredicto obligatorio

# C2 CERTIFICADO

---

## SHA auditado

| Rol | SHA | Mensaje |
|-----|-----|---------|
| **C1-R1 (base)** | `3226ba5ee9b998547c7026c98b69972dfacd2d3d` | `fix(c1-r1): fallback determinístico ruta inicial /` |
| **C2 (candidato)** | `b19b04dd438f5b13b422e9a760f54fa074fb52ed` | `feat(c2): gobierno multiempresa CC + Mi Trabajo + contexto SUPERADMIN` |

**Worktree:** `/tmp/cert-c2-a` @ `b19b04d` (detached HEAD, clean).

---

## Resumen ejecutivo

El delta C1-R1→C2 comprende **17 archivos** (+1 019 / −22 líneas), acotado al bloque declarado: gobierno multiempresa, contexto SUPERADMIN, Centro de Control y Mi Trabajo. **Cero** cambios en migraciones, modelos, permisos backend, auth/MFA/SSO/sid, HomePage C1-R1, `docker-compose.yml` ni tags.

**Suite C2:** 17/17 PASS. **Regresión representativa:** 44/44 PASS. **Frontend build:** PASS (`vite build` tras `npm ci`).

| Severidad | Nuevos hallazgos |
|-----------|------------------|
| P0 | 0 |
| P1 | 0 |
| P2 | 2 |

---

## 1. Diff C1-R1 → C2 y alcance declarado

### Archivos modificados (producto)

| Archivo | Cambio |
|---------|--------|
| `backend/app/services/control_center_service.py` | `resolve_organization_id` + `ensure_organization_active` |
| `backend/app/services/trabajo_service.py` | Fix notificaciones Mi Trabajo con `org_id` resuelto |
| `frontend/src/hooks/useOrganizationContext.tsx` | **Nuevo** — `OrganizationProvider`, contexto SUPERADMIN |
| `frontend/src/components/OrganizationContextBar.tsx` | **Nuevo** — selector + badge "Viendo:" |
| `frontend/src/pages/CentroControlPage.tsx` | Pasa `organizationQueryParam` a API |
| `frontend/src/pages/TrabajoPage.tsx` | Pasa `organization_id` en items/resumen |
| `frontend/src/AppShell.tsx` | `OrganizationProvider`; badge Mi Trabajo con org activa |
| `frontend/src/api.ts` | `fetchCentroControlResumen` / `fetchTrabajoResumen` + `organizationId` |
| `frontend/src/auth/session.ts` | Evento contexto org (+2 líneas) |
| `frontend/src/styles.css` | Estilos `.org-context-bar` |
| `tests/test_convergencia_c2.py` | **Nuevo** — 17 tests C2 |

### Sin cambios (verificado)

| Área | Diff líneas |
|------|-------------|
| `backend/alembic/` | **0** |
| `backend/app/permissions.py` | **0** (added=0, removed=0) |
| `backend/app/models.py` y `*_models.py` | **0** |
| `auth.py`, `deps.py`, `api.ts` login hotfix | **0** en lógica auth |
| `HomePage.tsx`, `navigation/homeRoute.ts`, `NoModulesPage.tsx` | **0** |
| `docker-compose.yml` | **0** |
| Tags git | **0** |

**Conclusión:** el diff corresponde al alcance C2 declarado.

---

## 2. Verificación por punto de misión

| # | Verificación | Resultado | Evidencia |
|---|--------------|-----------|-----------|
| 1 | Diff acotado a C2 | **PASS** | 17 archivos; ver tabla §1 |
| 2 | Aislamiento org A/B | **PASS** | `test_c2_org_a_no_ve_datos_org_b`, `test_c2_org_b_no_ve_datos_org_a` |
| 3 | `resolve_organization_id()` | **PASS** | CC service L921-934; usado en trabajo router |
| 4 | `ensure_organization_active()` | **PASS** | Invocado en home org y cross-org; `test_c2_superadmin_inactive_org_rejected` → 403 |
| 5 | Fix Mi Trabajo `org_id` resuelto | **PASS** | `_notification_visible_query(db, user, org_id)`; `test_c2_superadmin_trabajo_notificaciones_solo_org_activa` |
| 6 | SUPERADMIN cross-org explícito | **PASS** | Query `organization_id`; permiso `platform.organization.view`; tests SA A/B |
| 7 | OrganizationProvider / ContextBar | **PASS** | Archivos nuevos; wiring estático `test_c2_frontend_org_context_wiring` |
| 8 | `organization_id` en CC/Mi Trabajo | **PASS** | `api.ts` + pages; params en fetch |
| 9 | Badge Mi Trabajo respeta org activa | **PASS** | `AppShell.tsx` L63 `fetchTrabajoResumen(organizationQueryParam)` |
| 10 | Backend autoridad RBAC | **PASS** | Tenant admin cross-org → 403; sin permiso CC → 403 |
| 11 | C1-R1 Home intacto | **PASS** | `test_c2_c1_r1_home_route_preservado` |
| 12 | Login/MFA/SSO/sid intactos | **PASS** | Sin diff auth; `test_c2_login_hotfix_preservado` + `test_v1_hotfix_login` 6/6 |
| 13 | Sin cambios indebidos V1/V2/tags | **PASS** | Solo 2 servicios backend + frontend C2 |
| 14 | Alembic head único | **PASS** | `1341a1b2c3d4e` (1 head); `test_c2_alembic_head_unico` |
| 15 | Sin regresiones materiales | **PASS** | Regresión 44 tests PASS |

---

## 3. Pruebas ejecutadas (independiente)

### Suite C2 obligatoria

```bash
cd /tmp/cert-c2-a
python -m pytest tests/test_convergencia_c2.py -q --tb=short
# → 17 passed in 8.56s
```

### Regresión representativa

```bash
python -m pytest tests/test_convergencia_c2.py \
       tests/test_c1_r1_home_route.py \
       tests/test_v1_hotfix_login.py \
       tests/test_gate_post6d_correcciones.py::test_g2_solicitar_aprobacion_transitions_trabajo \
       tests/test_gate_post6d_correcciones.py::test_g3_dedup_oportunidad_vs_1290_humana \
       tests/test_bandeja_trabajo_humano.py -q
# → 44 passed in 13.27s
```

### Frontend build

```bash
cd frontend && npm ci && npm run build
# → ✓ built in 1.39s
```

---

## 4. Hallazgos P0 / P1 / P2

### P0

**Ninguno.**

### P1

**Ninguno.**

### P2

| ID | Hallazgo | Nota |
|----|----------|------|
| P2-C2-A01 | Chunk JS >500 kB (warning Vite) | Preexistente; no bloqueante C2 |
| P2-C2-A02 | `test_c2_alembic_head_unico` es smoke de archivos, no sustituye `alembic heads` CLI | Complementado por verificación CLI: 1 head |

---

## 5. Salida obligatoria

```
SHA C2: b19b04dd438f5b13b422e9a760f54fa074fb52ed ✓
VEREDICTO: C2 CERTIFICADO

Tests C2: 17/17 PASS
Regresión: 44/44 PASS
Frontend build: PASS

P0: 0 | P1: 0 | P2: 2

Migraciones nuevas: 0
Permisos nuevos/eliminados: 0
Alembic head: 1341a1b2c3d4e (único)
C1-R1 HomePage: preservado
Login hotfix: preservado
```

---

## Restricciones respetadas

- ✓ No modificar producto  
- ✓ No iniciar C3  
- ✓ No revisar PR históricos masivamente  

---

*Certificación A — Agente A — 2026-08-31*
