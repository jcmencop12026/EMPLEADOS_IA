# 02 — Modelo comercial

## Ciclo conceptual → estados 1280

| Ciclo EIAAX | Estado `CommercialProposal` |
|-------------|----------------------------|
| OPORTUNIDAD / EN_EVALUACIÓN / PROPUESTA_EN_PREPARACIÓN | `BORRADOR` |
| PROPUESTA_LISTA / REVISADA | `EN_REVISION` |
| APROBADA_INTERNA | `APROBADA` |
| PRESENTADA / NEGOCIACIÓN | `ENVIADA` |
| CONTRATADA | `ACEPTADA` |
| DESCARTADA / PERDIDA | `RECHAZADA` |
| SUSPENDIDA | `VENCIDA` |

## Transiciones permitidas (`PROPOSAL_TRANSITIONS`)

```
BORRADOR → EN_REVISION | RECHAZADA
EN_REVISION → BORRADOR | APROBADA | RECHAZADA
APROBADA → ENVIADA | BORRADOR
ENVIADA → ACEPTADA | RECHAZADA | VENCIDA
VENCIDA → BORRADOR
```

## Modelos comerciales configurables

`ModeloComercial` en `negocio_enums.py`:

- `IMPLEMENTACION_MENSUALIDAD`
- `PROYECTO_FIJO`
- `SUSCRIPCION`
- `VARIABLE_CONSUMO`
- `EXITO_RESULTADOS`
- `HIBRIDO` (default al crear desde expediente)

No se fijan valores universales; cada propuesta define su modalidad.

## Historial

- Transiciones comerciales: auditoría `negocio.propuesta.transicion`
- Estados de oportunidad vinculada: `OpportunityTransition` vía `proactive_service`
