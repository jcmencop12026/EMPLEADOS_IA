# 04 — Gráficos y semántica ANTES / PROYECTADO / REAL

## Semántica fija

```json
{
  "ANTES": "Línea base o situación previa documentada",
  "PROYECTADO": "Estimación o proyección — no es realizado",
  "REAL": "Medición o valor verificado con evidencia",
  "nota": "El proyectado nunca se presenta como realizado"
}
```

## Fuente de datos

- `evaluacion_service.get_impacto_resumen` por expediente activo
- Series por indicador/hallazgo con naturaleza explícita

## UI

- Barras con clases CSS: `.cc-bar-antes`, `.cc-bar-proyectado`, `.cc-bar-real`
- Tooltips en valores
- Nota "PROYECTADO ≠ REAL" cuando aplica

## Pendiente (P1)

- Exportación CSV/PNG de gráficos
- Drill-down temporal por periodo
- Agrupación configurable
