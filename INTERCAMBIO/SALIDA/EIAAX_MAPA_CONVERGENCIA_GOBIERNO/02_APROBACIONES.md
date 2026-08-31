# 02 — Arquitectura de aprobaciones (propuesta, sin implementar)

**Referencia:** `c433bac` + análisis ramas `ee57fab`, `fbfd6a2`, `2afd673`

---

## Estado actual por componente

| Componente | Rama | Rol actual |
|------------|------|------------|
| `ApprovalRequest` | Todas | Tabla legacy universal; work_plan / task |
| `coordinator.decide_approval` | Todas | **Único motor de decisión** con guards fábrica |
| `GobiernoAccionSolicitud` | `c433bac` | Solicitudes transversales PROPUESTA/EJECUCIÓN |
| `gobierno_operacional_service` | `c433bac` | Crear/listar/decidir solicitudes gobierno |
| `EmployeeFactoryApproval` | Todas (fábrica) | Extensión dominio → enlaza a `ApprovalRequest` |
| `employee_lifecycle_service` | Todas | Crea approval fábrica; `sync_factory_approval_on_decide` |
| `ApprovalPort` | `fbfd6a2` | Contrato CN para gobierno futuro |
| `LocalNegocioApprovalAdapter` | `fbfd6a2` | **Implementación local CN** — niveles por propuesta |
| `NegocioApprovalRecord` | `fbfd6a2` | Registros por nivel (COMERCIAL, LEGAL, etc.) |
| BP2 motor acción | `ee57fab` | Aprobación humana vía evaluación / PIIAX estados |

---

## Arquitectura final propuesta (UNA sola)

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE SOLICITUD                         │
│  GobiernoAccionSolicitud  │  EmployeeFactoryApproval        │
│  (transversal dominio)    │  (extensión ciclo vida IA)       │
│  NegocioProposalApproval  │  BP2 AccionExterna pendiente    │
│  (adaptador CN)           │                                  │
└───────────────┬─────────────────────────────────────────────┘
                │ crea / vincula
                ▼
┌─────────────────────────────────────────────────────────────┐
│              ApprovalRequest (registro único)                │
└───────────────┬─────────────────────────────────────────────┘
                │ decide
                ▼
┌─────────────────────────────────────────────────────────────┐
│           coordinator.decide_approval (motor único)        │
│  + assert_factory_approval_decision_allowed                  │
│  + sync_factory_approval_on_decide                           │
│  + hooks futuros: gobierno, negocio, bp2                     │
└───────────────┬─────────────────────────────────────────────┘
                │ emite
                ▼
┌─────────────────────────────────────────────────────────────┐
│  GobiernoEvento + write_audit + correlation_id               │
└─────────────────────────────────────────────────────────────┘
```

### Reglas

1. **Ningún dominio implementa su propio `approve/reject` final** salvo como UI que llama al motor único.
2. **Aprobaciones multinivel CN** se modelan como múltiples `GobiernoAccionSolicitud` o subtareas vinculadas, no como segundo motor.
3. **Fábrica** mantiene `EmployeeFactoryApproval` como metadatos de dominio (`approval_kind`, `target_version`); la decisión siempre pasa por `decide_approval`.
4. **BP2** estados `ESPERANDO APROBACION` deben mapear a solicitud gobierno + `ApprovalRequest`, no a tabla paralela.

---

## Matriz de adaptadores

| Adaptador / componente | Disposición | Acción GENERAL |
|------------------------|-------------|----------------|
| `coordinator.decide_approval` | **CONSERVAR** | Motor canónico; añadir hooks gobierno/negocio |
| `ApprovalRequest` | **CONSERVAR** | Tabla única de instancias |
| `GobiernoAccionSolicitud` | **CONSERVAR** | Fuente solicitudes transversales |
| `EmployeeFactoryApproval` | **CONSERVAR COMO ADAPTADOR** | Extensión fábrica; no duplicar decisión |
| `ApprovalPort` | **CONSERVAR COMO ADAPTADOR** | Contrato estable CN ↔ gobierno |
| `LocalNegocioApprovalAdapter` | **REEMPLAZAR** | Por adaptador que cree `GobiernoAccionSolicitud` |
| `NegocioApprovalRecord` | **MIGRAR** | Historial CN; dejar de ser autoridad de `can_present` |
| `NegocioApprovalPolicy` | **ADAPTAR** | Config local que alimenta políticas gobierno |
| BP2 boundaries/stubs PIIAX | **CONSERVAR COMO ADAPTADOR** | `ProveedorExternoAdapter`; aprobación vía gobierno |
| `/api/operations/approvals/*` | **ADAPTAR** | Delegar a motor único + federar listados |
| `gobierno_operacional_service` decide | **ADAPTAR** | Debe llamar `decide_approval` o unificar código |

---

## Conflictos detallados

### A-01 — CN LocalNegocio vs Gobierno

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `fbfd6a2` — comentario explícito "reemplazable por Gobierno Operacional" |
| **COMPONENTES** | `LocalNegocioApprovalAdapter`, `NegocioApprovalRecord`, `GobiernoAccionSolicitud` |
| **AUTORIDAD** | `GobiernoAccionSolicitud` + `decide_approval` |
| **CONSERVAR** | `ApprovalPort`, políticas CN, UI negociación |
| **ADAPTAR** | Adapter implementa `ApprovalPort` llamando gobierno |
| **RETIRAR** | `can_present` autónomo sin consultar gobierno |
| **RIESGO** | Propuesta presentada sin aprobaciones reales |

### A-02 — Fábrica EmployeeFactoryApproval

| Campo | Valor |
|-------|-------|
| **ORIGEN** | MB-06 / gate post6d |
| **COMPONENTES** | `EmployeeFactoryApproval`, `employee_lifecycle_service`, `decide_approval` |
| **AUTORIDAD** | `decide_approval` (ya integrado) |
| **CONSERVAR** | Patrón actual — **correcto** |
| **ADAPTAR** | Registrar `correlation_id` en solicitud gobierno al publicar |
| **RETIRAR** | Nada |
| **RIESGO** | Bajo si se mantiene patrón |

### A-03 — Gobierno decide sin coordinator

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `gobierno_operacional_service` puede decidir solicitudes propias |
| **COMPONENTES** | `gobierno_operacional_service`, `coordinator` |
| **AUTORIDAD** | Unificar en `decide_approval` o extraer `approval_engine` compartido |
| **CONSERVAR** | API `/api/gobierno-operacional/solicitudes/{id}/decidir` |
| **ADAPTAR** | Implementación interna delega a motor único |
| **RETIRAR** | Lógica duplicada de transición APPROVED/REJECTED |
| **RIESGO** | Reglas de segregación distintas entre operaciones y gobierno |

### A-04 — BP2 aprobación PIIAX

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `ee57fab` — estados capacidad externa |
| **COMPONENTES** | `evaluacion_proveedor_externo_service`, `evaluacion_siguiente_accion_service` |
| **AUTORIDAD** | Gobierno para humana; adapter para ejecución externa |
| **CONSERVAR** | `ProveedorExternoAdapter`, stubs |
| **ADAPTAR** | `ESPERANDO APROBACION` → `GobiernoAccionSolicitud` |
| **RETIRAR** | Aprobación solo en estado JSON sin `ApprovalRequest` |
| **RIESGO** | Acción externa ejecutada sin auditoría EIAAX |

---

## Secuencia de convergencia sugerida (GENERAL)

1. Extraer `approval_engine` desde `decide_approval` (refactor interno).
2. Cablear `gobierno_operacional_service` → engine.
3. Implementar `GobiernoNegocioApprovalAdapter` reemplazando local CN.
4. BP2: hook solicitud al crear acción externa pendiente.
5. Deprecar endpoints que decidan fuera del engine (lista en auditoría P0).
