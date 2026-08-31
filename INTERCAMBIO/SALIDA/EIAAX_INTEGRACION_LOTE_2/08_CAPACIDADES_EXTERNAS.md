# 08 — Capacidades externas

## Separación conceptual

| Concepto | Implementación |
|----------|----------------|
| **Proveedor IA** | `llm_providers`, políticas IA gobierno, catálogo cerrado modelos |
| **Proveedor capacidad externa** | BP2 acciones externas, `PiiaxAdapter` |

## PIIAX

- Adaptador desacoplado; EIAAX autónomo sin PIIAX
- Sin simular éxito cuando no hay conexión real
- Sin contrato definitivo hardcodeado

## Recorrido 2 — Capacidad externa

```
expediente → necesidad externa → solicitud capacidad
  → proveedor no disponible → estado controlado → trazabilidad
```

Verificado en tests BP2:
- Estados controlados (no falso éxito)
- `PiiaxAdapter` retorna estado explícito

## Motor siguiente acción

Considera cuando corresponde: información, hallazgos, permisos, oportunidades, gobierno, aprobaciones, economía, capacidades externas — sin cadena de ifs duplicada por módulo.

## Preguntar a EIAAX (A–H)

Clasificación preservada: respuesta existente, información faltante, análisis IA, consulta externa, acción externa, aprobación humana, oportunidad, tarea/seguimiento. Gateways canónicos, sin acoplar OpenAI/PIIAX directamente.
