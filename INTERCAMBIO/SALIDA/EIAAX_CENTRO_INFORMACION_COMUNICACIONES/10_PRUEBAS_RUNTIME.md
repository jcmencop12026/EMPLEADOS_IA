# 10 — Pruebas y runtime

## Pruebas

| Archivo | Casos |
|---------|-------|
| `test_mb11_comunicaciones.py` | 8 — core MB-11 |
| `test_mb11_eiaax_centro_informacion.py` | 7 — 5 casos runtime + versión + regresión 1410 |
| `test_mb11_integracion_mi_trabajo.py` | integración Mi Trabajo |

**Total MB-11 EIAAX: 7/7 PASS** (+ 22 regresión combinada)

## Casos runtime demostrados

1. Informe → entregar → historial
2. Info faltante → SOLICITUD
3. Webhook roto → FALLIDA (sin ENTREGADA falsa)
4. Informe INTERNO → rechazo visible entidad
5. Multitenant aislamiento

## Runtime

```bash
alembic upgrade head  # head: 1420a1b2c3d4e
python scripts/centro-informacion-demo.py
```

Backend `:8012`, frontend `:5187` (ver capturas).

## Frontend

`npm run build` — PASS
