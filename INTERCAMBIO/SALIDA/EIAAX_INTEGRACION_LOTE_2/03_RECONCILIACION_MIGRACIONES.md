# 03 — Reconciliación de migraciones

## Resultado obligatorio

**Un solo head Alembic:** `1600a1b2c3d4e`

Verificado:
```bash
cd backend && python3 -c "from alembic.script import ScriptDirectory; from alembic.config import Config; s=ScriptDirectory.from_config(Config('alembic.ini')); print(s.get_heads())"
# ['1600a1b2c3d4e'] — COUNT: 1
```

## Cadena lineal integrada

```
… → 1405a1b2c3d4e (expediente evaluación BP1)
  → 1410a1b2c3d4e (evaluación PIIAX prep — BP2)      ← canónico 1410
  → 1420a1b2c3d4e (motor siguiente acción — BP2)
  → 1411a1b2c3d4e (gobierno operacional)             ← renumerado desde colisión
  → 1412a1b2c3d4e (partners MB-03)                   ← renumerado desde colisión
  → 1600a1b2c3d4e (motor económico)
```

## Archivos de migración del lote

| Revisión | Archivo | Origen |
|----------|---------|--------|
| `1410a1b2c3d4e` | `1410a1b2c3d4e_evaluacion_piiax_prep_1410.py` | BP2 |
| `1420a1b2c3d4e` | `1420a1b2c3d4e_evaluacion_motor_siguiente_1420.py` | BP2 |
| `1411a1b2c3d4e` | `1411a1b2c3d4e_gobierno_operacional_eiaax.py` | Gobierno (renumerado) |
| `1412a1b2c3d4e` | `1412a1b2c3d4e_partners_mb03.py` | Partners (renumerado) |
| `1600a1b2c3d4e` | `1600a1b2c3d4e_motor_economico_eiaax.py` | Motor económico |

## Ledger y reparación

- `backend/alembic/migration_ledger.json` — `baseline_head`: `1600a1b2c3d4e`
- Revisiones protegidas incluyen 1410, 1420, 1411, 1412, 1600
- `backend/scripts/schema_repair.py` — head actualizado a `1600a1b2c3d4e`

## Verificación

| Prueba | Resultado |
|--------|-----------|
| `test_migration_control.py` | PASS |
| `alembic upgrade head` (SQLite aislado) | PASS en entorno dev |
| Estructura tablas gobierno/partners/motor | Creada por migraciones |

## Nota

No se eliminaron estructuras funcionales para resolver colisiones — solo reordenación de `down_revision` y renumeración de revisiones duplicadas.
