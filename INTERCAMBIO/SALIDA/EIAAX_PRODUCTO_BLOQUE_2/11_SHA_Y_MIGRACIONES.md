# 11 — SHA, migraciones y permisos

## SHA

| Etapa | Commit |
|-------|--------|
| Base certificada BP1 | `7e9abba11f4c4f216142c6c70d662229ffc585bb` |
| Final BP2 | `19bda9f` |

## Migración

**Revisión:** `1410a1b2c3d4e`  
**Archivo:** `backend/alembic/versions/1410a1b2c3d4e_evaluacion_piiax_prep_1410.py`

Tablas nuevas:

- `evaluaciones_acciones_externas`
- `evaluaciones_accion_eventos`
- `evaluaciones_indicadores`

Ledger y `schema_repair.py` actualizados a head `1410a1b2c3d4e`.

## Permisos nuevos

| Código | Descripción |
|--------|-------------|
| `evaluacion.accion.request` | Solicitar capacidades externas |
| `evaluacion.accion.approve` | Aprobar acciones de ejecución |
| `evaluacion.indicadores.manage` | Gestionar indicadores de impacto |

Asignados a rol admin en `permissions.py`.

## Configuración opcional

- `PIIAX_BRIDGE_ENABLED` (env)
- `PIIAX_BRIDGE_URL` (env, reservado)
- `organization.config_json.piiax` (`enabled`, `detalle_url`)
