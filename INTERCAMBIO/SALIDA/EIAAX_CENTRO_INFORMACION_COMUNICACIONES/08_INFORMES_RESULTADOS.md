# 08 — Informes y resultados

## Flujo integrado

1. Generar informe (`POST /api/resultados/informes/generar`)
2. Evento `RESULTADOS_INFORME_GENERADO`
3. Seleccionar destinatario autorizado + canal
4. `deliver_informe_impacto()` — verifica visibilidad
5. Registro en `comm_entregas_informe` + historial de mensajes

## Frontend

- `InformeImpactoPage` — panel «Entregar informe»
- Historial de entregas por versión

## Distinción PROYECTADO/REAL

El contenido narrativo del informe mantiene semántica 1410; la entrega no altera valores medidos.
