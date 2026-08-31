# 06 — Compromiso → Resultado (B09)

## Vista continuidad

`GET /api/continuidad-comercial/propuestas/{id}/vista`  
`GET /api/continuidad-comercial/contratos/{id}/vista`  
`GET /api/continuidad-comercial/proyectos/{id}/vista`

Cadena expuesta:

1. **Diagnosticado** — evaluación origen
2. **Prometido** — propuesta y documento cliente
3. **Contratado** — snapshot compromiso
4. **Implementado** — proyecto, alcance, go-live
5. **Operando** — FinOps vinculado
6. **Proyectado** — valor/ROI de propuesta (referencia)
7. **Resultado real** — adaptador reemplazable

## Adaptador

`continuidad_resultado_port.py` → `LocalResultadoContinuidadAdapter`

- Boundary clara para sustituir por Inteligencia de Resultados
- No recalcula indicadores; lee mediciones existentes de éxito del cliente

## UI

Pestaña **Continuidad** en Centro de Negocios e Implementación (`ContinuidadVistaPanel`).

## Brecha cerrada

**B09** — Vista compromiso→resultado sin módulo paralelo.
