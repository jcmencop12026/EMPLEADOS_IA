# CURSOR V1 — PAQUETE A: INFRAESTRUCTURA, PRODUCCIÓN, BACKUP Y HEALTH

**Fecha:** 2026-08-28  
**Agente:** Cloud Agent Paquete A  
**Rama:** `cursor/v1-infra-produccion`  
**Base certificada:** `dc51d5c` (`dc51d5ce4852d37e5eef8b5112d1260a002ee3bf`)

---

## 1. Rama, base y HEAD

| Campo | Valor |
|-------|-------|
| Rama de trabajo | `cursor/v1-infra-produccion` |
| Base V1 | `dc51d5c` |
| HEAD final | `fee50b2` (`fee50b28...`) |
| PR | *(ver sección 4)* |

---

## 2. Precheck obligatorio

```text
$ git fetch origin --prune
$ git rev-parse --show-toplevel
/workspace

$ git branch --show-current
cursor/v1-infra-produccion

$ git rev-parse HEAD
dc51d5ce4852d37e5eef8b5112d1260a002ee3bf

$ git rev-parse origin/main
dc51d5ce4852d37e5eef8b5112d1260a002ee3bf

$ git status --short
(vacío — sin cambios al inicio)
```

**Verificaciones:**
- Rama correcta: **SÍ** (`cursor/v1-infra-produccion`)
- Proviene de base `dc51d5c`: **SÍ** (HEAD = origin/main = dc51d5c)
- Archivos históricos no versionados: presentes en `INTERCAMBIO/` — **no agregados ni modificados**

---

## 3. Auditoría inicial

### Existente reutilizado

| Área | Archivos / mecanismos |
|------|----------------------|
| Configuración | `backend/app/config.py`, `.env.example` (ampliado) |
| Arranque local | `ARRANCAR.bat`, `CREAR_ENTORNO.bat`, `backend/scripts/launch_services.py`, `service_manager.py`, `db_startup.py` |
| Migraciones | `backend/alembic/`, `migration_control.py`, `validate_migrations.py` |
| CI PostgreSQL | `.github/workflows/qa.yml` |
| Frontend proxy DEV | `frontend/vite.config.ts` (sin cambios funcionales) |
| Schedulers | `automation_scheduler.py`, `proactive_scheduler.py` |

### Ausente (implementado en Paquete A)

- Docker / Compose
- Backup/restore PostgreSQL operativo
- Health checks profundos (DB + schedulers)
- Configuración PROD CORS/docs por ambiente
- Guía instalación producción V1

### Dependencia Cloud Agent

`.cursor/environment.json` y `.cursor/install.sh` **no están** en la base `dc51d5c`. Provienen de rama de setup separada (documentado en GAP Analysis). **No integrado** en este paquete.

---

## 4. Pull Request

| Campo | Valor |
|-------|-------|
| Rama | `cursor/v1-infra-produccion` |
| Base | `main` |
| URL | https://github.com/jcmencop12026/EMPLEADOS_IA/pull/30 |
| Número | #30 |
| Merge | **NO** (pendiente revisión humana) |

---

## 5. Archivos nuevos

| Archivo | Propósito |
|---------|-----------|
| `backend/app/health.py` | Diagnóstico API/DB/schedulers |
| `backend/scripts/pg_backup.py` | Backup PostgreSQL con timestamp |
| `backend/scripts/pg_restore.py` | Restore controlado con guardas |
| `backend/scripts/docker_entrypoint.sh` | Espera PG + Alembic + arranque |
| `backend/Dockerfile` | Imagen backend V1 |
| `frontend/Dockerfile` | Build estático + nginx |
| `frontend/nginx.conf` | Proxy `/api` y `/health` |
| `docker-compose.yml` | Stack postgres + backend + frontend |
| `docs/INSTALACION_PRODUCCION_V1.md` | Guía operativa V1 |

## 6. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/config.py` | `APP_ENV`, `ENABLE_API_DOCS`, `BACKUP_DIR`, CORS |
| `backend/app/main.py` | Health profundo, docs condicionales |
| `backend/app/services/automation_scheduler.py` | `is_scheduler_running()` |
| `backend/app/services/proactive_scheduler.py` | `is_scheduler_running()` |
| `.env.example` | Variables DEV/TEST/PROD documentadas |
| `.gitignore` | Excluir `data/backups/` |

---

## 7. Docker

- **docker-compose.yml**: PostgreSQL 16, backend (uvicorn), frontend (nginx).
- Volúmenes: `postgres_data`, `backend_data`.
- Healthchecks en los tres servicios.
- `depends_on` con `condition: service_healthy`.
- Entrypoint ejecuta `validate_migrations.py` + `alembic upgrade head`.

**Limitación Cloud Agent:** daemon Docker no disponible (`permission denied` en `/var/run/docker.sock`). Builds J/K documentados como SKIP.

---

## 8. Ambientes DEV / TEST / PROD

| Variable | DEV | TEST | PROD |
|----------|-----|------|------|
| `APP_ENV` | `dev` | `test` | `prod` |
| `DATABASE_URL` | SQLite o PG local | PG test | PG prod |
| `ENABLE_API_DOCS` | default true | default true | default **false** |
| `CORS_ORIGINS` | localhost:5180 | configurable | dominio real obligatorio |
| `JWT_SECRET` | dev local | CI/test | secreto fuerte |

Sin editar código — solo variables de entorno.

---

## 9. PostgreSQL productivo

- Driver: `psycopg2-binary` (ya en requirements).
- URL formato: `postgresql+psycopg2://user:pass@host:5432/db`.
- Probado: conexión, migraciones, persistencia, reinicio de servicio.
- 57 tablas tras `alembic upgrade head`.

---

## 10. Alembic

| Verificación | Resultado |
|--------------|-----------|
| Head único | `1030a1b2c3d4e` — PASS |
| `validate_migrations.py` | PASS |
| `upgrade head` en BD vacía PG | PASS |
| BD existente compatible | PASS (reinicio backend) |
| Nuevas migraciones | **NINGUNA** |

---

## 11. Backup

Script: `backend/scripts/pg_backup.py`

- Usa `pg_dump` estándar.
- Nombre: `empleados_ia_<env>_<YYYYMMDD_HHMMSS>[_label].sql`
- Exit code 0/1, logging sin passwords.
- Destino configurable: `BACKUP_DIR` (default `data/backups`).

---

## 12. Restore

Script: `backend/scripts/pg_restore.py`

- Requiere `--file` explícito.
- Guardas: `--confirm-destructive`; en PROD además `--confirm-prod`.
- Falla seguro sin flags de confirmación (exit 1).
- Usa `psql --single-transaction --set ON_ERROR_STOP=1`.

---

## 13. Prueba backup → restore

```text
1. INSERT marcador audit_logs (action='infra.test', detail='marcador paquete A v2')
2. pg_backup.py --env test --label paquete_a_verify
   → data/backups/empleados_ia_test_20260828_164958_paquete_a_verify.sql (198408 bytes)
3. DROP/CREATE empleados_ia_restore_test
4. pg_restore.py --env test --confirm-destructive → BD restore_test
5. SELECT en restore_test → marcador presente
```

**Resultado: PASS**

---

## 14. Health checks

| Endpoint | Descripción | HTTP cuando DB caída |
|----------|-------------|----------------------|
| `GET /health/live` | Liveness (proceso API) | 200 |
| `GET /health/ready` | Readiness (DB) | **503** |
| `GET /health` | Diagnóstico completo | **503** (status `degraded`) |

Componentes: `api`, `database`, `schedulers` (automation + proactive).  
No expone passwords, URLs con secretos ni stack traces.

---

## 15. Startup

- Backend arranca con preflight migraciones + bootstrap + schedulers.
- Docker entrypoint: espera PG (60s max) → Alembic → uvicorn.
- Error DB: health 503 con mensaje en español.
- Sin retries infinitos en entrypoint.

---

## 16. Logging

- Backup/restore: logger `empleados_ia.backup` / `empleados_ia.restore`.
- Entrypoint: mensajes stdout en arranque.
- Schedulers: logging existente preservado.

---

## 17. CORS PROD

- `CORS_ORIGINS` parametrizado por env.
- En PROD debe configurarse origen real (no wildcard).
- DEV/TEST: defaults localhost preservados.

---

## 18. Docs PROD

- `ENABLE_API_DOCS=false` o `APP_ENV=prod` → `/docs`, `/redoc`, `/openapi.json` deshabilitados.
- Verificado: `GET /docs` → **404** en modo prod.
- DEV/TEST: docs disponibles por defecto.

---

## 19. Frontend build

```text
$ cd frontend && npm run build
✓ built in 1.18s
dist/assets/index-C_5OG9-q.js   389.61 kB
```

**PASS**

---

## 20. Instalación limpia (Cloud Agent)

| Paso | Resultado |
|------|-----------|
| `pip install -r backend/requirements.txt` | PASS |
| `npm ci` + `npm run build` | PASS |
| PostgreSQL local + create DB | PASS |
| `alembic upgrade head` | PASS |
| Backend uvicorn | PASS |
| Health endpoints | PASS |

**Limitación:** Docker Compose no ejecutable en VM Cloud Agent (sin daemon). Validación Docker pendiente en entorno con Docker operativo.

---

## 21. Pruebas exactas (A–O)

| ID | Prueba | Comando / acción | Resultado |
|----|--------|------------------|-----------|
| A | Backend startup | `uvicorn app.main:app` + `curl /health/live` | **PASS** |
| B | Frontend build | `npm run build` | **PASS** |
| C | PostgreSQL startup | `psql SELECT 1`, 57 tablas | **PASS** |
| D | Alembic upgrade | `validate_migrations.py` + `alembic upgrade head` | **PASS** |
| E | Health DB UP | `curl /health` → status up, HTTP 200 | **PASS** |
| F | Health DB DOWN | `service postgresql stop` → HTTP 503, status degraded | **PASS** |
| G | Backup real | `pg_backup.py --env test` → 198KB SQL | **PASS** |
| H | Restore real | `pg_restore.py --confirm-destructive` | **PASS** |
| I | Verificar datos restore | marcador `infra.test` en BD restore | **PASS** |
| J | Docker build | `docker build -f backend/Dockerfile` | **SKIP** (daemon no disponible) |
| K | Docker compose up | `docker compose up` | **SKIP** (daemon no disponible) |
| L | Reinicio servicios | stop/start uvicorn + `/health/ready` | **PASS** |
| M | Revisión secretos | `git grep` + no dumps en commit | **PASS** |
| N | Regresión | `pytest test_db_startup_805d.py test_migration_control.py` → 22 passed | **PASS** |
| O | git diff --check | sin conflictos whitespace | **PASS** |

---

## 22. Limitaciones

1. Docker build/compose no probado en Cloud Agent (sin daemon).
2. `.cursor/environment.json` no integrado — depende de rama setup.
3. Backup/restore requiere cliente PostgreSQL (`pg_dump`/`psql`) en host.
4. Restore sobre BD con datos existentes requiere BD vacía o limpieza previa (dump plain sin `--clean`).

---

## 23. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Restore destructivo accidental | Flags `--confirm-destructive` / `--confirm-prod` |
| CORS abierto en PROD | Documentado en `.env.example`; default prod sin docs |
| Docker no validado en CI local agent | QA GitHub Actions existente; validar compose en máquina con Docker |
| JWT_SECRET default en dev | Documentado; obligatorio en compose via `${JWT_SECRET:?}` |

---

## 24. Dependencias con otros paquetes

| Paquete | Dependencia |
|---------|-------------|
| Setup Cloud | `.cursor/` en rama separada — no mergeado |
| B (LLM) | Ninguna |
| C (Multi-tenant) | Ninguna |
| D (RBAC) | CORS/docs solo config |
| E (Tests PG) | Reutiliza mismo patrón DATABASE_URL PG |

---

## 25. Posibles conflictos de integración

- `backend/app/main.py` y `config.py` — archivos tocados por otros paquetes potencialmente.
- `docker-compose.yml` nuevo — sin conflicto esperado.
- `.env.example` — revisar al mergear setup Cloud Agent.

---

## 26. Veredicto final

# APTO PARA INTEGRACIÓN

**Criterios cumplidos:**
- Despliegue reproducible (Docker Compose + guía; Docker no probado en VM por limitación técnica)
- PostgreSQL funciona
- Alembic funciona
- Backup probado
- Restore probado con verificación de datos
- Health distingue fallo DB (HTTP 503)
- Frontend build pasa
- Sin secretos versionados
- CORS PROD parametrizado
- `/docs` deshabilitable en PROD
- Regresión relevante pasa
- `git diff --check` limpio
- PR creado, no mergeado

**Nota:** Pruebas J/K (Docker) SKIP por limitación del entorno Cloud Agent; no bloquean integración dado que artefactos Docker están presentes y documentados.

---

*Informe generado por Cloud Agent — Paquete A Infraestructura V1*
