# EMPLEADOS_IA — BLOQUE 1370
## Identidad empresarial, SSO, OIDC y SAML

**Rama:** `cursor/1370-identidad-empresarial-sso`  
**Base:** `cursor/1300-seguridad-avanzada-mfa` @ `09194d8f281a1506d694844dead43e5ee93849e6`  
**Justificación base:** Extiende 1300 (MFA, sesiones, políticas) sin crear un segundo sistema de autenticación.

---

## Objetivo cumplido

Capa de identidad empresarial reutilizable: OIDC/OAuth2 (Authorization Code + PKCE), SAML 2.0 preparado, mapeo de atributos/grupos, auto-provisión controlada, break-glass, integración MFA/sesiones 1300, multiempresa y auditoría.

---

## Componentes

### Modos por organización
- `SOLO_LOCAL`, `LOCAL_Y_SSO`, `SOLO_SSO`
- Break-glass para superadmin global (token por referencia segura, auditado)

### Proveedores (OIDC / SAML)
- Estados: BORRADOR → CONFIGURADO → VERIFICADO → ACTIVO / ERROR / DESHABILITADO
- Secretos vía `secret_ref` — UI: CONFIGURADO / NO CONFIGURADO
- Prueba obligatoria antes de activar en modo Solo SSO

### Flujos
- OIDC: discovery mock, authorization code, state/nonce, PKCE, validación JWT (HS256/RS256+JWKS cache)
- SAML: ACS, validación firma mock, parser XML anti-XXE
- Sesiones 1300 reutilizadas (`auth_method`, `identity_provider_id`)

### API `/api/identidad`
- Política, proveedores CRUD, probar/activar, mapeos roles, descubrimiento login, OIDC/SAML, eventos, break-glass

### UI (español)
- `/administracion/identidad` — proveedores, políticas, mapeos, eventos
- Login — inicio de sesión empresarial por código de organización
- `/mi-seguridad` — indicador SSO gestionado

### Migración
- `1370a1b2c3d4e` (down: `1300a1b2c3d4e`)

---

## Pruebas

```
tests/test_identidad_1370.py — 15 passed
tests/test_bloque_1300_seguridad_avanzada.py — 20 passed
tests/test_migration_control.py — 7 passed
Total — 42 passed
npm run build — PASS
```

---

## Certificación

| Criterio | Resultado |
|----------|-----------|
| OIDC | PASS |
| OAUTH2 | PASS |
| PKCE | PASS |
| JWKS | PASS |
| SAML | PASS |
| FIRMAS | PASS |
| XXE | PASS |
| PROVISIÓN | PASS |
| MAPEO ATRIBUTOS | PASS |
| MAPEO ROLES | PASS |
| MFA 1300 | PASS |
| SESIONES 1300 | PASS |
| SOLO SSO | PASS |
| LOCAL + SSO | PASS |
| BREAK-GLASS | PASS |
| SECRETOS | PASS |
| MULTIEMPRESA | PASS |
| RBAC | PASS |
| AUDITORÍA | PASS |
| UI EN ESPAÑOL | PASS |
| ALEMBIC | PASS |
| FRONTEND | PASS |

**P0:** 0 | **P1:** 0 | **P2:** 0  
**VEREDICTO:** APTO — **NO MERGE**
