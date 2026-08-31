# 05 — Alertas y excepciones

## Centralización visual (sin motor paralelo)

`requiere_atencion` agrega desde:

- Ejecuciones fallidas (`WorkPlan.FAILED`)
- Aprobaciones operaciones y fábrica
- Automatizaciones fallidas
- Presupuestos FinOps en riesgo
- Oportunidades críticas
- Notificaciones HIGH/CRITICAL
- Empleados `FAILED_TEST`
- Proveedor no disponible

## Priorización

Puntuación por: impacto (severidad), urgencia, tipo, antigüedad. **No todo es crítica.**

## Actualización

`modo_actualizacion: bajo_demanda` — botón Actualizar en UI. No polling agresivo. `ultima_actualizacion` visible.
