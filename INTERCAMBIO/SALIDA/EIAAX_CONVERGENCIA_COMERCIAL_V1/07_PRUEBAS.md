# Pruebas acumulativas

## Bloque A+B+C+D (focal convergencia)

```bash
pytest tests/test_centro_estrategico_v1.py \
       tests/test_flujo_comercial_v1_1730.py \
       tests/test_presentacion_real_v1.py \
       tests/test_demo_comercial_ficticia.py \
       tests/test_espacio_externo_v1.py \
       tests/test_espacio_externo_evidencias_v1.py -q
```

**Resultado:** 67 passed (2026-09-01)

## Áreas cubiertas

| Área | Tests |
|------|-------|
| Centro Estratégico | cockpit, 5 lecturas, economía privada, MB-08 intacto, persistencia, privacidad |
| Flujo comercial | catálogo contextual, suficiencia, propuesta, instrumentos, POTENCIAL, recorrido demo |
| Presentación real | audiencias, PDF, fail-closed, protección contenido interno |
| Demo ficticia | semilla, aislamiento, PDF, gráficos |
| Espacio externo | portal prospecto, publicación, promoción cliente, privacidad |
| Evidencias | carga, versionado, descarga, validación, path traversal |

## Otras verificaciones

| Verificación | Estado |
|--------------|--------|
| `validate_migrations.py` | PASS — head único `1820` |
| `from app.main import app` | PASS |
| `npm run build` (frontend) | PASS |
| Alembic heads | 1 (`1820a1b2c3d4e`) |
| Windows arranque real | **PENDIENTE** |

## Nota SQLite tests

Usar BD limpia (`unset DATABASE_URL`) si esquema cambió entre iteraciones.
