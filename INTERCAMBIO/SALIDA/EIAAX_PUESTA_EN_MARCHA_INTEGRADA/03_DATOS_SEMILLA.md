# Datos semilla demostrativos

Script: `backend/scripts/seed_lote3_demo.py`
BD: `sqlite:////workspace/data/eiaax_integrado_demo.db`

## Organización A — Empresa Demo A

| Entidad | Descripción |
|---------|-------------|
| Expediente | EVA-2026-0001 con hallazgo y oportunidad |
| Propuesta | Centro Negocios con extensión |
| Dossier | Arquitecto de Transformación |
| Indicadores | ANTES / PROYECTADO / REAL (con evidencia) |
| Soporte | Caso demo |
| Comunicaciones | Bootstrap defaults |
| Gobierno | Solicitud PENDIENTE |

Usuarios: `org_a_admin` (admin), `org_a_viewer` (viewer)

## Organización B — Empresa Demo B

Solo org + admin (`org_b_admin`) para pruebas de aislamiento.

## Ejecución

```bash
cd backend
DATABASE_URL=sqlite:////workspace/data/eiaax_integrado_demo.db python3 scripts/seed_lote3_demo.py
```

Salida JSON con IDs de entidades para pruebas API.
