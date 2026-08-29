# CURSOR V1 — Certificación Docker Windows (candidata e8cb853)

## Rama de herramientas

| Campo | Valor |
|-------|-------|
| Rama | `cursor/v1-certificacion-windows-tools` |
| Candidata a certificar | `cursor/v1-candidata-final-release-r2` @ `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| Script | `scripts/CERTIFICAR_V1_DOCKER_WINDOWS_E8CB853.ps1` |

Esta rama contiene **únicamente** las herramientas de certificación Windows.  
**No** modifica la candidata V1, `main` ni PR #32.

---

## Obtener herramientas en Windows

### Opción A — Clonar solo la rama de herramientas

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

git clone --branch cursor/v1-certificacion-windows-tools --single-branch `
  https://github.com/jcmencop12026/EMPLEADOS_IA.git D:\EMPLEADOS_IA_CERT_TOOLS

Set-Location D:\EMPLEADOS_IA_CERT_TOOLS
.\scripts\CERTIFICAR_V1_DOCKER_WINDOWS_E8CB853.ps1
```

### Opción B — Desde clone existente en D:\EMPLEADOS_IA

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Set-Location D:\EMPLEADOS_IA
git fetch origin cursor/v1-certificacion-windows-tools
git checkout cursor/v1-certificacion-windows-tools
.\scripts\CERTIFICAR_V1_DOCKER_WINDOWS_E8CB853.ps1
```

El script **automáticamente**:

1. Clona/actualiza `D:\EMPLEADOS_IA_CERT` con checkout **exacto** `e8cb853`
2. Crea `.env` temporal local (no versionado)
3. Levanta stack Compose proyecto `empleados_ia_cert`
4. Ejecuta todos los gates y escribe evidencia

---

## Parámetros de certificación

| Recurso | Valor |
|---------|-------|
| Workspace candidata | `D:\EMPLEADOS_IA_CERT` |
| Proyecto Compose | `empleados_ia_cert` |
| PostgreSQL (host) | `55432` |
| Backend (host) | `18010` |
| Frontend (host) | `15180` |
| Alembic head esperado | `d1e2f3a4b5c6` (1 head) |

---

## Gates validados

- Windows real + Docker Desktop (`docker version`, `docker compose version`)
- `docker compose config` sin `host.docker.internal`
- Build y stack (postgres, backend, frontend)
- PostgreSQL operativo
- Contraseña PG con `@ # % : / +` (no logueada)
- Round-trip `DATABASE_URL` / `POSTGRES_*` en backend
- Alembic 1 head + upgrade en entrypoint
- Backend `/health/live` y `/health/ready`
- Frontend `http://localhost:15180`
- **Nginx → backend** vía `http://localhost:15180/health/ready` (red Compose)
- **Login** vía `http://localhost:15180/api/auth/login` (no directo backend)
- Persistencia tras reinicio
- Caída/recuperación PostgreSQL
- Backup `pg_dump` + restore en BD `empleados_ia_cert_restore`
- Seguridad prod (JWT, bootstrap, CORS, docs off)
- Secretos redactados en evidencia

**No** incluye OpenAI ni Ollama.

---

## Evidencia generada

```
D:\EMPLEADOS_IA_CERT\INTERCAMBIO\SALIDA\CERT_WINDOWS_E8CB853_EVIDENCIA\
  certificacion.log
  compose-config.txt      (secretos redactados)
  compose-ps.txt
  alembic-heads.txt
  backup_e8cb853_*.sql
  RESUMEN.txt
```

---

## Prerrequisitos

1. Windows 10/11 x64
2. Docker Desktop en ejecución
3. Git para Windows
4. PowerShell 5.1+
5. Puertos **55432**, **18010**, **15180** libres

---

## Notas

- **NO** ejecutar este script en Linux como sustituto de Windows.
- La candidata `e8cb853` **no** incluye el script; se obtiene de esta rama.
- Credenciales de certificación son **temporales** y solo en `.env` local.
- Al finalizar, el stack se detiene (`docker compose stop`); volúmenes se conservan.

---

## Tras certificación exitosa

Guardar evidencia como:

`INTERCAMBIO\SALIDA\CURSOR_V1_CERTIFICACION_DOCKER_WINDOWS_REAL_E8CB853.md`

Mensaje esperado al final del script:

**EMPLEADOS IA. Docker Windows V1 certificado.**
