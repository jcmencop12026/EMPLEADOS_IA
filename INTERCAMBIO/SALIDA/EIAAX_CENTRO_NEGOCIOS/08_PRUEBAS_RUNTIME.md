# 08 — Pruebas y runtime (cierre integral)

## Tests — 14 PASS

| Archivo | Tests |
|---------|-------|
| `test_centro_negocios_1700.py` | 4 (E2E, multiempresa, RBAC, versionamiento) |
| `test_centro_negocios_1710.py` | 10 (PDF, aprobaciones, precio, sync, contrato, privacidad) |

## Cobertura focal 1710

- Presentación rechazada sin aprobaciones
- PDF generado (`%PDF`) sin datos internos
- Fases precio RECOMENDADO/APROBADO/PRESENTADO/CONTRATADO
- Economía privada 403 viewer
- Sincronización oportunidad + sync_log
- Contratación requiere versión presentada
- Negociación reset aprobaciones
- POTENCIAL en nota, no en inversión
- Aislamiento tenant detalle
- Política aprobación configurable

## Regresión Motor Económico

`test_economic_motor_1600.py` — PASS

## Migración

Head: `1710a1b2c3d4e`

## Frontend

`npm run build` — OK

## Vista detalle

`/centro-negocios/propuestas/{id}` — pestañas: Resumen, Economía, Versiones, Aprobaciones, Negociación, Trazabilidad

## APIs nuevas 1710

- `GET .../detalle`
- `POST .../aprobaciones`
- `POST .../pdf`
- `GET /documentos/{id}/pdf`
- `POST .../contratar`
- `POST .../sincronizar`
- `PUT /politica-aprobacion`
