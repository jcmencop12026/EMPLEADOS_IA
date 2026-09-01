# 05 — Separación MB-08 operacional

## Dos conceptos complementarios

| Centro | Ruta | Alcance |
|--------|------|---------|
| **Operacional MB-08** | `/centro-control`, `/api/centro-control/operacional` | Empleados IA, ejecuciones, capacidad, costos operativos, alertas, aprobaciones |
| **Estratégico V1** | `/centro-estrategico`, `/api/centro-estrategico/cockpit` | Dossier comercial/estratégico prospecto/cliente |

## Frontera en código

- Estratégico **no incluye** `fuerza_laboral`, ejecuciones ni bandeja operacional
- Lectura operación estratégica enlaza a MB-08: `enlace_operacional_mb08.ruta = /centro-control`
- `test_mb08_no_sustituido` verifica ambos endpoints activos

## No crear segundo MB-08

- Sin adapters operacionales duplicados (Fábrica, Conocimiento operacional)
- Reutiliza adapters de valor/comercial ya existentes en CC
