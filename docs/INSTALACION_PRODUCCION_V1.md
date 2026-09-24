# Instalación y despliegue V1 — EMPLEADOS_IA

Guía operativa para infraestructura reproducible (Paquete A).

## Requisitos

| Componente | DEV local | PROD Docker |
|------------|-----------|-------------|
| Python | 3.12 | (incluido en imagen backend) |
| Node.js | 20 LTS | (incluido en build frontend) |
| PostgreSQL | opcional | 16 (servicio compose) |
| Docker | opcional | 24+ con Compose v2 |

## Ambientes

| Variable | DEV | TEST | PROD |
|----------|-----|------|------|
| `APP_ENV` | `dev` | `test` | `prod` |
| `DATABASE_URL` | SQLite o PG local | PostgreSQL test | PostgreSQL prod |
| `ENABLE_API_DOCS` | omitir (true) | omitir (true) | omitir (false) o `false` |
| `CORS_ORIGINS` | localhost:5180 | origen test | dominio real |
| `JWT_SECRET` | dev local | secreto CI | secreto fuerte |

## Instalación local (Windows / DEV)

1. Copiar `.env.example` → `.env`
2. `CREAR_ENTORNO.bat`
3. `ARRANCAR.bat`

API: http://127.0.0.1:8010 — Web: http://127.0.0.1:5180

## Instalación Docker (PROD)

```bash
cp .env.example .env
# Editar: POSTGRES_PASSWORD, JWT_SECRET, CORS_ORIGINS, APP_ENV=prod
docker compose up --build -d
docker compose ps
curl -s http://127.0.0.1:8010/health/ready
```

Web: http://127.0.0.1:5180 — API: http://127.0.0.1:8010

## Migraciones Alembic

```bash
cd backend
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. python scripts/validate_migrations.py
```

En Docker, el entrypoint ejecuta `alembic upgrade head` automáticamente al arrancar.

## Health checks

| Endpoint | Uso |
|----------|-----|
| `GET /health/live` | Liveness — proceso API activo |
| `GET /health/ready` | Readiness — PostgreSQL accesible |
| `GET /health` | Diagnóstico completo (API, DB, schedulers) |

Estados: `up`, `degraded`, `down`. Si la BD no responde, `/health` y `/health/ready` devuelven HTTP 503.

## Backup PostgreSQL

```bash
cd backend
PYTHONPATH=. python scripts/pg_backup.py --env test --database-url "$DATABASE_URL"
```

Requiere `pg_dump` en PATH. Salida: `data/backups/empleados_ia_<env>_<timestamp>.sql`

## Restore PostgreSQL

```bash
cd backend
PYTHONPATH=. python scripts/pg_restore.py \
  --env test \
  --file data/backups/empleados_ia_test_YYYYMMDD_HHMMSS.sql \
  --confirm-destructive
```

En PROD añadir `--confirm-prod`. Operación destructiva sobre la BD indicada.

## Reinicio de servicios

Docker:

```bash
docker compose restart backend frontend postgres
```

Local Windows: cerrar ventanas de `ARRANCAR.bat` y volver a ejecutar.

## Dependencia Cloud Agent

La configuración `.cursor/environment.json` y `.cursor/install.sh` proviene de una rama de setup separada y **no está integrada** en la base `dc51d5c`. Documentar al integrar setup + infra.

## Secretos

No versionar `.env`, dumps con datos reales ni contraseñas. Revisar antes de commit:

```bash
git diff --check
```
