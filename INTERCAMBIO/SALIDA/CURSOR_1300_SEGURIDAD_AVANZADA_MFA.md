# CURSOR 1300 — Seguridad avanzada, MFA, sesiones y protección de acceso

## Base y rama

| Campo | Valor |
|-------|-------|
| Base | `cursor/1250a-fix-aislamiento-tests` @ `6352836` |
| Rama | `cursor/1300-seguridad-avanzada-mfa` |
| Migración | `1300a1b2c3d4e` (head único) |

## Arquitectura

Capa compatible que evoluciona el JWT existente sin reemplazarlo:

1. **Login** — contraseña válida → sesión en BD + JWT con `sid` y `type=access`.
2. **MFA** — si la política lo exige y el usuario tiene MFA activo → token `mfa_pending` (5 min, solo para `/api/auth/mfa/verify`).
3. **Revocación** — `get_current_user` valida `sid` contra `user_sessions` (PK indexada).
4. **Políticas** — por organización en `organization_security_policies`.
5. **Eventos** — `security_events` + publicación `TENANT_SECURITY_EVENT` para alertas futuras.

## Modelo de datos

| Tabla | Propósito |
|-------|-----------|
| `organization_security_policies` | MFA, sesiones, lockout, revocación al cambiar contraseña |
| `user_mfa_settings` | Secreto TOTP cifrado (Fernet derivado de `JWT_SECRET`) |
| `user_mfa_recovery_codes` | Hash bcrypt de códigos de un solo uso |
| `user_sessions` | Sesiones activas/revocadas |
| `security_events` | Auditoría operativa de seguridad |
| `login_attempts` | Fuerza bruta / bloqueo temporal |
| `password_reset_tokens` | Recuperación de contraseña (hash SHA-256) |

## Secretos MFA

- Cifrado Fernet con clave derivada de `JWT_SECRET`.
- Secreto solo expuesto en `POST /api/security/mfa/enroll/start` (antes de confirmar).
- Tras confirmar: solo almacenamiento cifrado; nunca en logs, auditoría ni errores.
- QR generado localmente con `qrcode` (sin servicios externos).

## Flujo MFA

```
CONFIGURAR → enroll/start (QR + secreto temporal)
→ confirmar primer código → MFA activo + códigos recuperación (única visualización)
→ login con MFA → mfa_pending → verify → sesión completa
```

## Sesiones y revocación

- JWT incluye `sid` (UUID de sesión).
- Sesión revocada → 401 aunque JWT no haya expirado.
- Tokens legacy sin `sid` siguen válidos (no revocables server-side).
- Política `max_active_sessions`: `RECHAZAR_NUEVA` o `REVOCAR_MAS_ANTIGUA`.

## Rate limiting

| Endpoint | Mecanismo |
|----------|-----------|
| Login | `login_attempts` + bloqueo temporal configurable |
| MFA verify | Contador en memoria por usuario/IP |
| Forgot password | Contador en memoria por IP |

## Políticas por organización

- `mfa_mode`: DESACTIVADO | OPCIONAL | OBLIGATORIO
- `mfa_required_roles_json`: roles con MFA obligatorio
- `session_duration_minutes`, `max_active_sessions`
- `login_max_attempts`, `lockout_minutes`
- `revoke_sessions_on_password_change`
- `excess_session_policy`

## API

### Auth (`/api/auth`)

- `POST /login` — login con o sin desafío MFA
- `POST /mfa/verify` — completar login MFA
- `POST /change-password`
- `POST /forgot-password` — sin enumeración de usuarios
- `POST /reset-password`

### Seguridad (`/api/security`)

- MFA: `/mfa/status`, `/mfa/enroll/start`, `/mfa/enroll/confirm`, `/mfa/disable`, `/mfa/recovery/regenerate`
- Sesiones: `/sessions`, `/sessions/{id}`, `/sessions/revoke-others`
- Admin: `/policy`, `/events`, `/admin/sessions`, `/overview`

## RBAC

| Permiso | Uso |
|---------|-----|
| `seguridad.view` | Resumen administrativo |
| `seguridad.manage_policy` | Políticas |
| `seguridad.revoke_sessions` | Revocar sesiones de la org |
| `seguridad.audit` | Eventos de seguridad |

Usuarios autenticados: MFA y sesiones propias sin permiso extra.

## Multiempresa

Todas las consultas administrativas filtran por `organization_id` del actor. Revocación y políticas limitadas al tenant.

## UI (español)

- `/mi-seguridad` — Mi seguridad (MFA, recuperación, sesiones, cambio contraseña)
- `/administracion/seguridad` — Panel admin ampliado (política, sesiones, eventos)
- Login con paso MFA integrado

## Tests

`tests/test_bloque_1300_seguridad_avanzada.py` — 20 tests cubriendo:

login sin MFA, enrolamiento, códigos inválidos/válidos, login MFA, recovery codes, regeneración, deshabilitación, MFA obligatorio, sesiones, revocación, JWT revocado, máximo sesiones, cambio/recuperación contraseña, rate limit, no enumeración, RBAC, multiempresa, secretos.

Regresión: `tests/test_security_rbac_v1.py` — 11 tests PASS.

## Hallazgos P0/P1/P2

| Nivel | Cantidad | Detalle |
|-------|----------|---------|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 1 | Rate limit MFA/recuperación en memoria (aceptable para MVP; migrar a BD en escala) |

## Veredicto

**APTO** — Implementación completa, tests PASS, build frontend PASS, migración 1300 head único.

**NO MERGE** — según instrucciones operativas.
