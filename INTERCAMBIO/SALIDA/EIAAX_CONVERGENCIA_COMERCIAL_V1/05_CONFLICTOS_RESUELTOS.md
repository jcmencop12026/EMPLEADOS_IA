# Conflictos resueltos en convergencia

| Conflicto | Resolución |
|-----------|------------|
| Colisión IDs migración A/B/C/D | Cadena única `1780`–`1820` desde `1770a1b2c3d4e` |
| `migration_ledger` desactualizado | `baseline_head` → `1820a1b2c3d4e`; revisiones certificadas |
| `get_dossier_completo(create=True)` en lecturas | `create=False` en Centro Estratégico; evita 5 dossiers por sesión SQLite |
| `EvaluacionExpediente.sector` ausente | Campo + migración `1780` + API evaluaciones |
| `Opportunity.origen_comercial` ausente | Campo + migración `1780` |
| `estado_validacion` en información | Campos espacio externo en modelo + migración `1800` |
| `knowledge_storage.save_evidence_bytes` ausente | Portado desde rama A |
| `external_prospect` sin permisos | Rol sistema + `espacio_externo.portal/entregar` |
| `ContinuidadAdapter.degradados` tipo lista | Comparación `len()` compatible |
| `strategic_control_service` `create=False` | Alineado con API `transformacion_service` extendida |
| `CentroConfianzaPage` rama A | **No portado** — conflicto API |
| `api.ts` truncado en portado | Restaurado y extendido con endpoints C/D/A |
| `evaluacionLabels.ts` | Restaurado base + wrappers portados |
