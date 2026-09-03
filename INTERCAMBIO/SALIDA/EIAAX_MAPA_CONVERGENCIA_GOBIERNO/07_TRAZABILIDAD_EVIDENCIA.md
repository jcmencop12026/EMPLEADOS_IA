# 07 — Trazabilidad y evidencia

---

## Cadena transversal deseada

```
organización (tenant)
    → expediente / proceso (evaluación, dossier, work_plan)
        → hallazgo / requerimiento / indicador
            → decisión (motor, analista, IA)
                → aprobación (ApprovalRequest / GobiernoAccionSolicitud)
                    → acción (ejecución, propuesta, comunicación)
                        → ejecución (task, FinOps, adapter externo)
                            → resultado (informe, métrica, entrega)
                                → comunicación / incidente (si aplica)
```

**Hilo conductor:** `correlation_id` (UUID) propagado en cada transición.

---

## Fuentes de traza por capa

| Capa | Tabla / API | correlation_id |
|------|-------------|----------------|
| Gobierno operacional | `GobiernoEvento`, `GobiernoAccionSolicitud` | Sí |
| Seguridad / evidencia | `EmpresaEvidenciaVinculo` | Sí |
| Visibilidad | `GobiernoVisibilidadLog` | Sí |
| Auditoría | `audit_log`, `GovAccessLog`, `SecurityEvent` | Parcial (detail JSON) |
| Aprobaciones | `ApprovalRequest.evidence_json` | Debe incluir |
| BP1 evaluación | `EvaluacionExpediente.correlation_id` | Sí |
| FinOps | `FinOpsRecord` via work_plan | Via plan/task |
| Partners | `PartnerAuditEvent` | Recomendado añadir |
| Comunicaciones | Entregas informe `f32c815` | Verificar en merge |
| Resultados | `af0e8cd` modelos | Verificar en merge |

---

## API canónica de lectura

```
GET /api/empresa-seguridad/trazabilidad/{correlation_id}
```

Agrega:
- Solicitudes gobierno
- Eventos gobierno
- Evidencias vinculadas
- Cambios visibilidad
- Aprobaciones (via evidence_json / filtros)
- Auditoría federada (subset)

---

## Conflictos — trazas aisladas o duplicadas

### T-01 — correlation_id no propagado en CN

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `fbfd6a2` aprobaciones negocio locales |
| **COMPONENTES** | `LocalNegocioApprovalAdapter`, propuestas |
| **AUTORIDAD** | `correlation_id` de propuesta o nuevo al crear solicitud gobierno |
| **CONSERVAR** | IDs propuesta |
| **ADAPTAR** | Adapter pasa correlation al gobierno |
| **RETIRAR** | Aprobación CN sin ID transversal |
| **RIESGO** | Cadena rota en Centro Confianza |

### T-02 — Fábrica sin correlation en approval

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `EmployeeFactoryApproval` |
| **COMPONENTES** | `employee_lifecycle_service`, `ApprovalRequest` |
| **AUTORIDAD** | `evidence_json` + evento gobierno |
| **CONSERVAR** | Patrón actual |
| **ADAPTAR** | Añadir `correlation_id` explícito en evidence |
| **RETIRAR** | — |
| **RIESGO** | Publicación empleado no enlazada a dossier |

### T-03 — BP2 acción externa traza separada

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `ee57fab` estados PIIAX |
| **COMPONENTES** | `evaluacion_siguiente_accion_service`, bridge |
| **AUTORIDAD** | Mismo `correlation_id` que expediente |
| **CONSERVAR** | Estados español |
| **ADAPTAR** | Cada transición PIIAX → `GobiernoEvento` |
| **RETIRAR** | Log solo en memoria/stub |
| **RIESGO** | Acción externa invisible en trazabilidad |

### T-04 — Múltiples audit sin federar

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Histórico incremental |
| **COMPONENTES** | `consultar_auditoria` vs lecturas directas |
| **AUTORIDAD** | `empresa_seguridad_service.consultar_auditoria` |
| **CONSERVAR** | Tablas fuente |
| **ADAPTAR** | UIs usan API federada |
| **RETIRAR** | Pantallas que lean solo `audit_log` |
| **RIESGO** | Evidencia incompleta en auditoría |

### T-05 — Evidencia duplicada

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Knowledge + hallazgo + evidencia transversal |
| **COMPONENTES** | `EmpresaEvidenciaVinculo`, knowledge center |
| **AUTORIDAD** | Vínculo transversal; contenido en dominio |
| **CONSERVAR** | `empresa_evidencia_vinculo` |
| **ADAPTAR** | Dominios registran vínculo, no copian blob |
| **RETIRAR** | Segunda tabla evidencia por dominio |
| **RIESGO** | Inconsistencia versión evidencia |

---

## Evidencia — modelo

| Campo | Uso |
|-------|-----|
| `objeto_tipo` + `objeto_id` | Qué se evidencia |
| `tipo_evidencia` | HALLAZGO, APROBACION, INFORME, etc. |
| `rol_vinculo` | SOPORTA, CONTRADICE, DERIVA |
| `correlation_id` | Hilo |
| `referencia_externa` | ID dominio (knowledge doc, archivo) |

---

## Checklist correlation_id (GENERAL)

Propagación obligatoria en:
- [ ] Crear expediente evaluación
- [ ] Crear hallazgo
- [ ] Solicitar aprobación (gobierno + legacy)
- [ ] Decidir aprobación
- [ ] Cambiar visibilidad/clasificación
- [ ] Publicar empleado IA
- [ ] Enviar comunicación / informe
- [ ] Ejecutar acción BP2 externa
- [ ] Registrar FinOps en misma acción

Test de aceptación: un `correlation_id` debe retornar ≥1 evento en cada etapa aplicable.
