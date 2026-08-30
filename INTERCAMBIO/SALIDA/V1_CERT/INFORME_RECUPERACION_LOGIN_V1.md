# Informe final — Recuperación acceso + mejora login V1

**Proyecto:** EMPLEADOS_IA_CERT  
**BASE SHA certificado:** `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` (NO modificado)  
**Rama hotfix:** `cursor/v1-hotfix-login-acceso-85e4`  
**Fecha:** 2026-08-30

---

## 1. Causa exacta del fallo de login

Se identificaron **dos causas independientes** auditando el código real del SHA `e8cb853`:

### Causa A — Bug crítico en `frontend/src/api.ts` (confirmada)

En la función `api()`, el bloque `if (!res.ok)` invoca `parseDetail(text)` **antes** de `const text = await res.text()`.

Efecto:
- Cualquier respuesta HTTP no exitosa (401 credenciales incorrectas, 500, etc.) lanza `ReferenceError: text is not defined`.
- `LoginPage` captura el error genérico → **"No se pudo iniciar sesión. Intente nuevamente."**
- Enmascara el mensaje correcto "Usuario o contraseña incorrectos." incluso cuando el backend responde 401 correctamente.

**Nota:** Si la contraseña fuera correcta y el backend respondiera 200, el login podría funcionar; el bug afecta principalmente el manejo de errores y puede impedir diagnóstico.

### Causa B — Contraseña real desconocida vs bootstrap (probable)

- Tabla: `users` (`User` en `backend/app/models.py`)
- Campos: `username`, `password_hash` (bcrypt), `is_active`, `status`, `role`, `organization_id`
- Seed (`backend/app/seed.py`): crea `admin` solo si no existe, con `hash_password(settings.bootstrap_admin_password)`
- En Docker V1, `BOOTSTRAP_ADMIN_PASSWORD` viene de `.env` — **puede diferir** del valor por defecto en código (`Admin2026*`)
- El intento PowerShell anterior **falló antes de ejecutar** → BD probablemente **no fue modificada**

---

## 2. Modelo real auditado (SHA e8cb853)

| Elemento | Valor real |
|---|---|
| Tabla usuarios | `users` |
| Login endpoint | `POST /api/auth/login` |
| Hash | `bcrypt` vía `app.security.hash_password` / `verify_password` |
| Rol SUPERADMIN | `role = "superadmin"` (seed eleva `admin` → `superadmin`) |
| Bloqueos login | `is_active=False`, `status != "ACTIVE"`, org inactiva |
| Recuperación email V1 | **NO existe** (sin SMTP/servicio reset) |
| MFA en V1 auth | **NO** (auth.py simple: login + me) |

---

## 3. Recuperación de acceso (ejecutar en Windows)

### Paso 1 — Inspeccionar (sin secretos)

```powershell
cd D:\EMPLEADOS_IA_CERT
.\INTERCAMBIO\SALIDA\V1_CERT\Inspect-AdminUser-Inline-e8cb853.ps1
```

### Paso 2 — Restablecer contraseña (prompt oculto, sin guardar en archivos)

```powershell
.\INTERCAMBIO\SALIDA\V1_CERT\Reset-AdminPassword-Inline-e8cb853.ps1
```

Este script usa **módulos oficiales ya en la imagen e8cb853** — no requiere rebuild.

### Paso 3 — Probar login API

```powershell
.\INTERCAMBIO\SALIDA\V1_CERT\Test-LoginApi.ps1 -BackendUrl "http://localhost:18010"
```

### Paso 4 (recomendado) — Desplegar hotfix frontend para corregir api.ts

```powershell
git fetch origin cursor/v1-hotfix-login-acceso-85e4
git checkout cursor/v1-hotfix-login-acceso-85e4
docker compose build frontend --no-cache
docker compose up -d frontend
```

**URL ingreso:** `http://localhost:5180/login` (o puerto `FRONTEND_PORT` en `.env`)

**USUARIO:** `admin`  
**CONTRASEÑA:** la nueva establecida localmente por usted (no se muestra ni almacena en este informe)

---

## 4. Cambios hotfix (rama separada, NO merge)

| Archivo | Cambio |
|---|---|
| `frontend/src/api.ts` | Lee `text` antes de `!res.ok`; mensaje 401 login correcto |
| `frontend/src/pages/LoginPage.tsx` | Ojo mostrar/ocultar; panel "¿Olvidó su contraseña?" |
| `frontend/src/styles.css` | Estilos campo contraseña y panel recuperación |
| `backend/scripts/inspect_admin_user.py` | Inspección segura admin |
| `backend/scripts/reset_admin_password.py` | Reset con prompt oculto (post-rebuild backend) |
| `INTERCAMBIO/SALIDA/V1_CERT/*.ps1` | Scripts Windows validados |
| `tests/test_v1_hotfix_login.py` | 4 pruebas focales |

**NUEVO SHA hotfix:** ver `git rev-parse HEAD` en rama `cursor/v1-hotfix-login-acceso-85e4`

---

## 5. Recuperación de contraseña (producto)

| Estado | Detalle |
|---|---|
| Infraestructura email V1 | **NO existe** |
| Implementado | Panel informativo "¿Olvidó su contraseña?" en español |
| Comportamiento | Indica que recuperación automática no está habilitada; deriva a administrador |
| Evolución post-V1 | Requiere SMTP + tokens un solo uso + expiración + auditoría |

**NO** se implementó reset inseguro por correo.

---

## 6. Pruebas ejecutadas (entorno agente)

| Prueba | Resultado |
|---|---|
| `test_v1_hotfix_login.py` (4) | **PASS** |
| Login 401 rechazado | **PASS** |
| `npm run build` | **PASS** |
| api.ts orden lectura body | **PASS** |
| Ojo contraseña / español UI | **PASS** (código) |
| Login real Windows Docker | **PENDIENTE ejecución local** (scripts entregados) |
| SUPERADMIN post-reset | **PENDIENTE ejecución local** |
| PostgreSQL integridad | **NO alterado** (scripts solo UPDATE usuario admin) |

---

## 7. Restricciones respetadas

- SHA `e8cb853` **no reescrito**
- Fase 2 **no tocada**
- PostgreSQL **no destruido**
- Sin `git clean` / reset destructivo
- Sin contraseñas en logs/código/commits

---

## VEREDICTO

| Campo | Valor |
|---|---|
| **ACCESO RECUPERADO** | **PENDIENTE ejecución local** de `Reset-AdminPassword-Inline-e8cb853.ps1` (herramientas listas) |
| **LOGIN MEJORADO** | **LISTO en rama hotfix** (requiere rebuild frontend) |
| **APTO** | **APTO** tras ejecutar scripts locales y desplegar hotfix frontend |
