# 05 — Versionamiento y negociación

## Versiones inmutables

Al presentar (`ENVIADA`) o en negociación/contratación se crea `NegocioProposalVersion`:

- `snapshot_json` — estado completo de la propuesta
- `documento_cliente_json` — copia del documento visible al cliente
- `trigger` — `PRESENTACION` | `NEGOCIACION` | `CONTRATACION` | `REVISION_INTERNA`

**Regla:** modificar perspectivas o datos internos **no altera** versiones ya presentadas.

## Estados de propuesta (evolución)

```
BORRADOR → EN_REVISION → APROBADA → ENVIADA
```

Tras negociación con `crear_nueva_version: true` → vuelve a `BORRADOR` para nueva iteración.

## Negociación ligera

`negocio_negotiation_entries` registra:

- Versión presentada, fecha, interlocutor
- Observaciones, cambios solicitados
- Próximo paso, estado (`ABIERTA` / cerrada)
- Referencia a nueva versión si aplica

No es CRM completo — solo trazabilidad del ciclo EIAAX.

## APIs

- `POST .../negociacion` — registrar ronda
- `GET .../negociaciones` — historial
- `GET .../versiones` — snapshots
