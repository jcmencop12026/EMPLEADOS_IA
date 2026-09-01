# Aprobaciones — convergencia

## Arquitectura final

```
Dominio (negocio / operaciones)
    → puerto ApprovalPort
    → GobiernoNegocioApprovalAdapter / _mirror_decision_to_gobierno
    → Gobierno Operacional (crear_solicitud + decidir_solicitud)
    → registro local NegocioApprovalRecord (UI/estado negocio)
```

## Cambios

- `get_approval_adapter()` retorna `GobiernoNegocioApprovalAdapter` (no `LocalNegocioApprovalAdapter` como autoridad)
- `LocalNegocioApprovalAdapter` permanece como motor de registros locales únicamente
- `coordinator.decide_approval` registra decisión en Gobierno vía `_mirror_decision_to_gobierno`

## Contratos preservados

- `ApprovalPort` sin cambio de firma
- Endpoints `/api/centro-negocios/propuestas/{id}/aprobaciones` intactos
- Tests `test_centro_negocios_1710` PASS
