# 08 — Pruebas y runtime

## Tests automatizados

Archivo: `tests/test_centro_negocios_1700.py`

| Test | Cobertura |
|------|-----------|
| `test_centro_negocios_recorrido_completo` | Evaluación → oportunidad → propuesta → economía → precio → transiciones → negociación → contrato → implementación |
| `test_centro_negocios_aislamiento_tenant` | Multiempresa A/B |
| `test_centro_negocios_sin_permiso` | RBAC viewer |
| `test_version_snapshot_inmutable` | Versionamiento post-presentación |

**Resultado:** 4 PASS

## Migraciones

```bash
cd backend && python3 scripts/validate_migrations.py
# Alembic head único: 1700a1b2c3d4e
```

## Frontend

```bash
cd frontend && npm run build
# ✓ build exitoso
```

## API endpoints

| Método | Ruta |
|--------|------|
| GET | `/api/centro-negocios/dashboard` |
| GET | `/api/centro-negocios/pipeline` |
| POST | `/api/centro-negocios/propuestas/desde-expediente` |
| GET | `/api/centro-negocios/propuestas/{id}` |
| POST | `/api/centro-negocios/propuestas/{id}/enriquecer` |
| POST | `/api/centro-negocios/propuestas/{id}/transicion` |
| POST | `/api/centro-negocios/propuestas/{id}/precio` |
| POST | `/api/centro-negocios/propuestas/{id}/negociacion` |
| GET | `/api/centro-negocios/propuestas/{id}/versiones` |
| GET | `/api/centro-negocios/propuestas/{id}/negociaciones` |
| PUT | `/api/centro-negocios/propuestas/{id}/ia-consumo` |
| PUT | `/api/centro-negocios/propuestas/{id}/perspectivas` |
| POST | `/api/centro-negocios/propuestas/{id}/convertir-implementacion` |
