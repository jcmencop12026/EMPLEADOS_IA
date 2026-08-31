# RECERTIFICACIÓN A — DELTA C1 → C1-R1

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** A  
**Modo:** Control independiente delta — solo lectura  
**Fecha:** 2026-08-31  
**Certificación base:** `CERTIFICACION_A_C1.md` (C1 CERTIFICADO @ `25ad102`)

---

## Veredicto obligatorio

# CERTIFICACIÓN A C1 MANTIENE VALIDEZ SOBRE C1-R1

---

## SHAs comparados

| Rol | SHA | Mensaje |
|-----|-----|---------|
| **C1 (base certificada)** | `25ad1021ee6ea0322aceb0622252e7b748706d32` | `feat(c1): base segura convergencia V1+V2 con hotfix login selectivo` |
| **C1-R1 (nuevo)** | `3226ba5ee9b998547c7026c98b69972dfacd2d3d` | `fix(c1-r1): fallback determinístico ruta inicial / (P1-D-UX-01)` |

**Worktree auditado:** `/tmp/delta-c1-r1` @ `3226ba5` (detached HEAD, clean).

---

## Resumen ejecutivo

El delta C1→C1-R1 comprende **13 archivos** (7 código frontend, 2 tests, 4 documentación INTERCAMBIO). **Cero cambios** en `backend/`, `docker-compose.yml`, `api.ts`, `LoginPage.tsx`, migraciones, modelos, permisos backend, auth/MFA/SSO/sid o Knowledge.

El cambio está **estrictamente acotado** a la corrección UX **P1-D-UX-01**: resolución determinística de la ruta inicial `/` para usuarios sin `control_center.view`. La certificación A previa de C1 **no queda invalidada**; no se requiere recertificación completa M1–M8.

| Métrica | Valor |
|---------|-------|
| Archivos código productivo | 7 (solo frontend navegación) |
| Archivos backend | **0** |
| Regresión mínima ejecutada | 23 tests — **23 PASS** |
| P0 nuevos | **0** |
| P1 nuevos | **0** |
| P2 nuevos | **2** |

---

## Inventario de archivos modificados

| Estado | Ruta | Alcance |
|--------|------|---------|
| M | `frontend/src/App.tsx` | `CentroControlPage` → `HomePage` en `/` y `/centro-control` |
| M | `frontend/src/AppShell.tsx` | `MENU` extraído a módulo compartido |
| A | `frontend/src/navigation/menu.ts` | Fuente única menú lateral |
| A | `frontend/src/navigation/homeRoute.ts` | `resolveHomeRoute`, `getNavRoutesInOrder`, exclusiones |
| A | `frontend/src/pages/HomePage.tsx` | Router UX: CC / redirect / NoModules |
| A | `frontend/src/pages/NoModulesPage.tsx` | Vista segura sin módulos |
| A | `tests/test_c1_r1_home_route.py` | 14 tests C1-R1 + verificación hotfix api.ts |
| M | `tests/test_convergencia_final_fase2.py` | Aserciones alineadas a `HomePage` (2 líneas) |
| M/A | `INTERCAMBIO/SALIDA/EIAAX_CONVERGENCIA_C1*` | Documentación convergencia (no producto) |

**Total diff:** +13 archivos tocados; sin eliminaciones de código backend.

---

## Revisión por criterio solicitado

| Criterio | Resultado | Evidencia |
|----------|-----------|-----------|
| **navigation/menu.ts** | ✓ Presente | Extracción 1:1 del `MENU` de `AppShell.tsx`; sin cambio semántico de rutas |
| **navigation/homeRoute.ts** | ✓ Presente | `resolveHomeRoute` usa `canAccessRoute` + orden menú; excluye `/mi-seguridad` |
| **HomePage.tsx** | ✓ Presente | CC si `control_center.view`; else redirect; else `NoModulesPage` |
| **NoModulesPage.tsx** | ✓ Presente | Mensaje ES + logout; sin datos sensibles |
| **Pruebas agregadas** | ✓ | `test_c1_r1_home_route.py` (14 tests) |
| **Sin cambios migraciones** | ✓ | `git diff C1..C1-R1 -- backend/alembic/` → vacío |
| **Sin cambios modelos** | ✓ | `git diff C1..C1-R1 -- backend/app/` → vacío |
| **Sin cambios permisos backend** | ✓ | `permissions.py` idéntico byte-a-byte |
| **Sin cambios auth/MFA/SSO/sid** | ✓ | Sin diff en `auth.py`, `deps.py`, `security/*`, `api.ts`, `LoginPage.tsx` |
| **Sin cambios Knowledge** | ✓ | Sin diff en routers/servicios knowledge |
| **Sin cambios DATABASE_URL/Docker** | ✓ | `docker-compose.yml` sin diff |
| **Sin cambios fuera de alcance** | ✓ | Solo frontend navegación + tests + docs INTERCAMBIO |

---

## Análisis del cambio funcional (P1-D-UX-01)

### Antes (C1)

- `/` y `/centro-control` renderizaban `CentroControlPage` directamente.
- Usuario sin `control_center.view` veía error en home sin redirección.

### Después (C1-R1)

| Condición | Comportamiento |
|-----------|----------------|
| `control_center.view` | Renderiza `CentroControlPage` (igual que C1 para superadmin) |
| Sin CC, con otro módulo | `<Navigate replace>` a primera ruta permitida del menú |
| Sin módulos operativos | `NoModulesPage` |
| API `/api/centro-control/*` sin permiso | **403** (sin cambio backend) |

**Seguridad:** la resolución frontend **no concede permisos**; `ROUTE_PERMISSIONS` y guards backend intactos. Verificado en `test_backend_restricted_cc_without_centro_control`.

---

## Regresión mínima ejecutada

No se repitió suite M1–M8 completa: el diff no justifica recertificación integral (0 cambios backend/infra/auth).

### Comando

```bash
cd /tmp/delta-c1-r1
python -m pytest tests/test_c1_r1_home_route.py \
       tests/test_convergencia_final_fase2.py \
       tests/test_v1_hotfix_login.py \
       -q --tb=short
```

### Resultados

| Suite | Tests | PASS | FAIL |
|-------|-------|------|------|
| `test_c1_r1_home_route.py` | 14 | 14 | 0 |
| `test_convergencia_final_fase2.py` | 5 | 5 | 0 |
| `test_v1_hotfix_login.py` | 6 | 6 | 0 |
| **Total** | **23** | **23** | **0** |

### Integridad hotfix C1 preservada

`test_c1_r1_home_route.py::test_login_hotfix_still_present` y `test_v1_hotfix_login.py` (6/6) confirman:

- Orden `const text = await res.text()` antes de `if (!res.ok)` en `api.ts`
- `userMessage(res.status, detail, path)` con rama login 401
- Scripts admin recovery presentes
- MFA/SSO conservados en `LoginPage.tsx`

---

## Hallazgos P0 / P1 / P2

### P0 — nuevos

**Ninguno.**

### P1 — nuevos

**Ninguno.** El propósito declarado P1-D-UX-01 es corrección UX acotada; no introduce regresión en RBAC, auth, knowledge ni infraestructura certificada en C1.

### P2 — nuevos (no invalidan certificación)

| ID | Hallazgo | Nota |
|----|----------|------|
| P2-R1-01 | `test_convergencia_final_fase2.py` actualizado para esperar `HomePage` en lugar de `CentroControlPage` en rutas index | Alineación esperada con C1-R1; M8 de certificación original requeriría misma aserción si se re-ejecutara íntegramente |
| P2-R1-02 | `HomePage` trata `/` y `/centro-control` idénticamente | Coherente con alias previo; usuario sin CC en `/centro-control` también redirige (mejora UX) |

---

## Validez de controles C1 previos

| Área certificada C1 | ¿Afectada por C1-R1? | Conclusión |
|---------------------|----------------------|------------|
| Hotfix login (`api.ts`, scripts) | No | Válido |
| DATABASE_URL / Docker | No | Válido |
| Knowledge auth/descarga | No | Válido |
| RBAC / multitenant backend | No | Válido |
| MFA / sesiones / sid | No | Válido |
| Routers V1/V2 | No | Válido |
| Alembic head único | No | Válido |
| G1–G4 gobierno | No | Válido |
| Navegación home UX | **Sí** — corregida P1-D-UX-01 | Mejora acotada; no invalida resto |

---

## Conclusión

| Pregunta | Respuesta |
|----------|-----------|
| ¿C1-R1 limitado a P1-D-UX-01? | **Sí** — evidencia diff + 0 cambios backend |
| ¿Certificación A C1 sigue válida? | **Sí** — salvo actualización documental de comportamiento home (P2) |
| ¿Recertificación completa M1–M8? | **No requerida** |

---

## Restricciones respetadas

- ✓ No modificar producto  
- ✓ No iniciar C2  
- ✓ No tocar SHAs V1/V2/C1 certificados (solo lectura comparativa)  
- ✓ No repetir M1–M8 salvo regresión mínima justificada  

---

*Control delta A — Agente A — 2026-08-31*
