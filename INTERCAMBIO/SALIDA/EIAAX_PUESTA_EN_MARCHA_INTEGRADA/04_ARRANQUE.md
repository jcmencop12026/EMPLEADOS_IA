# Arranque real

## Estado verificado

| Componente | Estado |
|------------|--------|
| Backend `:8000` | UP — `/health` → 200 |
| Frontend `:5180` | UP — Vite dev |
| Login demo | PASS — `org_a_admin` |
| Alembic | head `1770a1b2c3d4e` |
| Routers Lote 3 | Registrados en `main.py` |

## Rutas frontend integradas

- `/centro-negocios`
- `/arquitecto-transformacion`
- `/resultados`
- `/soporte`, `/comunicaciones`, `/centro-confianza`

## Configuración

```bash
export DATABASE_URL=sqlite:////workspace/data/eiaax_integrado_demo.db
```

Backend debe arrancar desde `backend/` con PYTHONPATH implícito en uvicorn.
