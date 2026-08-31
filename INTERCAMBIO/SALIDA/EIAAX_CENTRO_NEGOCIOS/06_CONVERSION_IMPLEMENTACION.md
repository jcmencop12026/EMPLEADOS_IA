# 06 — Contratación y conversión a implementación

## Contratación (`POST .../contratar`)

Requiere versión presentada con PDF. Registra en `negocio_contract_records`:

- Versión aceptada y documento PDF
- Precio/modalidad contratada
- Fecha, responsable, condiciones
- Próximo paso

## Conversión (`POST .../convertir-implementacion`)

1. Contrata si no está `ACEPTADA` (usa última versión presentada)
2. Crea proyecto implementación 1340 con referencias:
   - evaluacion_id, opportunity_id, proposal_id, document_id
3. No solicita información ya conocida

## Salida

```json
{
  "proyecto_id": "...",
  "contract_id": "...",
  "referencias": {
    "evaluacion_id": "...",
    "opportunity_id": "...",
    "version_number": 2,
    "document_id": "..."
  }
}
```
