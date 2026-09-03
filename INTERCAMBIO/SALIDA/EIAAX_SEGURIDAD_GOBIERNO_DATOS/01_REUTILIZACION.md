# 01 — Reutilización de capacidades existentes

**SHA inicial:** `21e23308ce3d5ed39a969c8fb46217bdce73b0bc`  
**Rama origen:** `cursor/gobierno-operacional-eiaax-3e3d`  
**Rama trabajo:** `cursor/seguridad-gobierno-datos-eiaax-3e3d`

## Inventario auditado

| Capacidad | Ubicación | Reutilización |
|-----------|-----------|---------------|
| RBAC | `permissions.py`, `check_permission` | Extendido con permisos `gobierno.clasificacion.*`, `gobierno.trazabilidad.view`, etc. |
| AuditLog / write_audit | `audit.py`, `audit_logs` | Consulta federada + etiquetas español |
| Gobierno Operacional | `gobierno_operacional_*` | Visibilidad extendida, eventos, IA policies |
| Visibilidad BP1 | `evaluacion_service.set_visibilidad` | Dual-write preservado + niveles |
| Gobierno datos 1350 | `governance_models/service` | Clasificación PUBLICO/INTERNO/CONFIDENCIAL/RESTRINGIDO |
| Seguridad 1300 | `security_models`, `security_policy_service` | Evidencia en Centro de Confianza |
| ApprovalRequest | `orchestration_models` | Referenciado en trazabilidad (sin segundo flujo) |
| Centro de Confianza | `CentroConfianzaPage` | Evolucionado con grupos y estados |
| Knowledge | `knowledge_models` | Referencias de evidencia sin duplicar almacenamiento |
| Continuidad 1360 | `continuidad_models` | Control en Centro de Confianza si hay planes |

## Qué NO se duplicó

- Sin segundo RBAC
- Sin segundo gateway IA
- Sin segundo ApprovalRequest
- Sin generador de informes paralelo
- Sin motor de clasificación independiente del 1350

## Reservado para integración BP2 (P1)

- `coordinator.decide_approval` ↔ solicitudes gobierno
- `catalogo_proveedores_ref` en `gobierno_ia_policies` → catálogo cerrado GENERAL
