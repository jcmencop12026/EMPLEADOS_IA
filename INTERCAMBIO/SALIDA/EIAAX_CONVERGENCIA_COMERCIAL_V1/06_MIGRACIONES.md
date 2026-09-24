# Migraciones reconstruidas

## Punto de partida

- Base Lote 3 integrada: head `1770a1b2c3d4e`
- Sin portar revisiones literales colisionantes de A/B/C/D

## Cadena añadida

```
1770a1b2c3d4e
  └─ 1780a1b2c3d4e  flujo_comercial_v1
       └─ 1790a1b2c3d4e  presentacion_ejecutiva_v1
            └─ 1800a1b2c3d4e  espacio_externo_empresa
                 └─ 1810a1b2c3d4e  espacio_externo_cliente_v1b
                      └─ 1820a1b2c3d4e  espacio_externo_evidencias_v1c  ← HEAD
```

## Archivos

- `backend/alembic/versions/1780a1b2c3d4e_flujo_comercial_v1.py`
- `backend/alembic/versions/1790a1b2c3d4e_presentacion_ejecutiva_v1.py`
- `backend/alembic/versions/1800a1b2c3d4e_espacio_externo_empresa.py`
- `backend/alembic/versions/1810a1b2c3d4e_espacio_externo_cliente_v1b.py`
- `backend/alembic/versions/1820a1b2c3d4e_espacio_externo_evidencias_v1c.py`

## Ledger

```json
"baseline_head": "1820a1b2c3d4e"
```

## Verificación

```bash
cd backend && python scripts/validate_migrations.py
# Alembic head único: 1820a1b2c3d4e
```

Upgrade limpio desde candidato: `alembic upgrade head`
