# EMPLEADOS_IA — CORRECCIÓN PRE-RELEASE DE SEGURIDAD

**Agente:** B
**Rama:** `cursor/v1-fix-seguridad-produccion`
**Base:** `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` (`4c03cbe`)
**PR #32 / `cursor/v1-integracion-final`:** no tocados

---

## Objetivo

Cerrar P1 de auditoría final de seguridad: contraseña bootstrap predeterminada en `docker-compose.yml`, y endurecer validación de configuración productiva (JWT, CORS).

---

## Cambios

### 1. `docker-compose.yml`

- **Antes:** `BOOTSTRAP_ADMIN_PASSWORD: ${BOOTSTRAP_ADMIN_PASSWORD:-Admin2026*}`
- **Ahora:** `BOOTSTRAP_ADMIN_PASSWORD: ${BOOTSTRAP_ADMIN_PASSWORD:?Defina BOOTSTRAP_ADMIN_PASSWORD en .env}`

Sin fallback inseguro en stack Docker/PostgreSQL. Arranque falla con mensaje claro si falta la variable.

### 2. `backend/app/security_config.py`

- Bootstrap password por defecto (`Admin2026*`) → **RuntimeError** en PostgreSQL/producción (antes solo warning).
- JWT corto (&lt; 32 caracteres) → **RuntimeError** fuera de SQLite dev.
- `APP_ENV=prod` + `CORS_ORIGINS` vacío o `*` → **RuntimeError**.
- SQLite local + `ALLOW_INSECURE_DEV_DEFAULTS` mantiene experiencia dev documentada.

### 3. `backend/app/main.py`

- Pasa `app_env` y `cors_origins` a `validate_security_settings`.

### 4. `.env.example`

- `BOOTSTRAP_ADMIN_PASSWORD=CAMBIAR_PASSWORD_EN_PROD` (sin contraseña conocida versionada).
- Nota sobre defaults SQLite solo en dev local.

### 5. Sin cambios (confirmado)

| Área | Estado |
|------|--------|
| JWT en compose | Ya exigía `${JWT_SECRET:?...}` |
| API docs prod | `api_docs_enabled` = false si `APP_ENV=prod` y sin `ENABLE_API_DOCS` |
| OPENAI_API_KEY | Opcional; no modificado |
| `config.py` defaults dev SQLite | Mantenidos para tests y dev local sin Docker |

---

## Pruebas

```
tests/test_security_rbac_v1.py — 15 passed, 0 failed
```

Nuevas pruebas:

- `test_security_config_rejects_default_bootstrap_on_postgresql`
- `test_security_config_rejects_short_jwt_on_postgresql`
- `test_security_config_rejects_wildcard_cors_in_production`
- `test_docker_compose_requires_bootstrap_password`

---

## Clasificación post-fix

| Nivel | Cantidad |
|-------|----------|
| P0 | 0 |
| P1 | 0 |

---

## Veredicto

**APTO** para liberación respecto al hallazgo P1 de bootstrap y condiciones de producción auditadas.

---

## Despliegue Docker (recordatorio)

En `.env` local (no versionar):

```env
JWT_SECRET=<clave-aleatoria-min-32-chars>
BOOTSTRAP_ADMIN_PASSWORD=<contraseña-segura>
POSTGRES_PASSWORD=<contraseña-segura>
CORS_ORIGINS=https://app.ejemplo.com
APP_ENV=prod
```
