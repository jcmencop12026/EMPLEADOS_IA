# 08 — Offboarding

**Alcance:** Finalización de relación cliente, retiro recursos, evidencia histórica  
**Base:** SHA `fbfd6a2`

---

## Respuesta directa

EIAAX tiene soporte **parcial y desigual** para offboarding: maduro para retiro de Empleados IA; limitado para cierre de proyecto implementación; **ausente** para offboarding organizacional y cierre contractual guiado.

---

## Capacidades por dimensión

### 1. Finalización de proyecto / servicio

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| Estado terminal proyecto | PARCIAL | `EstadoImplementacion.CERRADO` en enum |
| Workflow cierre impl | AUSENTE | Sin endpoint dedicado cierre con checklist |
| Cierre oportunidad | OPERATIVA | `register_result` — `oportunidades.py` L306 |
| Cierre caso soporte | OPERATIVA | Estados en `SupportCase` |

### 2. Retiro de accesos

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Usuarios org | PARCIAL | Admin desactiva usuarios — `admin.py` |
| SSO/SCIM desaprovisionamiento | OPERATIVA | `scim.py`, migración 1380 |
| Identidad empresarial | OPERATIVA | `identidad.py` — SAML/OIDC |
| Revocación grants empleado | PARCIAL | Retiro empleado desactiva; grants explícitos no siempre limpiados |
| Accesos integración | PARCIAL | `integraciones.py` — credenciales por conector |

### 3. Pausa / retiro Empleados IA

| Operación | Estado | Evidencia |
|-----------|--------|-----------|
| Retiro definitivo | OPERATIVA | `retire_employee` — `lifecycle_status=RETIRED`, `is_active=False` |
| API | OPERATIVA | `POST /api/agent-factory/employees/{id}/retire` |
| Permiso | OPERATIVA | `employee.retire` |
| Auditoría | OPERATIVA | `write_audit` action `employee.retired` |
| Evento | OPERATIVA | `EmployeeEventType.EMPLOYEE_RETIRED` |
| Retiro por hallazgo auditor | OPERATIVA | `auditor_factory_bridge.py` L639 |
| Pausa temporal | PARCIAL | Desactivar vs retirar; sin estado PAUSED formal en todos paths |
| UI | OPERATIVA | `EmployeeDetailPage.tsx` |

**Test:** `test_retire_employee` en `test_employee_lifecycle_factory_mb06.py`

### 4. Retención de evidencia

| Tipo evidencia | Retención | Evidencia |
|----------------|-----------|-----------|
| Auditoría plataforma | OPERATIVA | `audit.py` — logs inmutables |
| Auditoría implementación | OPERATIVA | `impl_auditoria` |
| Versiones propuesta/PDF | OPERATIVA | `negocio_proposal_versions`, `negocio_proposal_documents` |
| Contratos | OPERATIVA | `negocio_contract_records` |
| Ejecuciones empleado | OPERATIVA | `WorkPlan`, `WorkEvent` históricos |
| Knowledge | OPERATIVA | Documentos persistidos |
| Gobierno datos | OPERATIVA | Políticas retención 1350 — `governance.py` |

### 5. Exportación

| Tipo | Estado | Evidencia |
|------|--------|-----------|
| Export PDF propuesta | OPERATIVA | `negocio_pdf_service.py` |
| Export datos org (GDPR pack) | PARCIAL | Gobierno datos; sin "export pack contractual" unificado |
| Export ejecuciones | PARCIAL | APIs lectura; sin export masivo UI |

### 6. Cierre contractual

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| Registro contratación | OPERATIVA | `negocio_contract_records` |
| Registro fin contrato | **AUSENTE** | Sin `negocio_contract_closure` o equivalente |
| Renovación NO_RENOVADO | PARCIAL | Enum `EstadoRenovacion`; sin workflow |
| Offboarding checklist cliente | **AUSENTE** | — |

### 7. Trazabilidad histórica

| Enlace | Persistencia |
|--------|--------------|
| Oportunidad → propuesta → contrato → impl | FKs y extensiones — **conservado** |
| Empleado retirado | Registro permanece con `RETIRED` |
| Org eliminada | **AUSENTE** — soft-delete org no estándar |

---

## Offboarding organización (tenant)

| Capacidad | Estado |
|-----------|--------|
| Crear org | OPERATIVA — `POST /api/platform/organizations` |
| Eliminar/archivar org | **AUSENTE** |
| Export completo tenant | **AUSENTE** |
| Cascada retiro empleados al cerrar org | **AUSENTE** |

---

## Automatizaciones en offboarding

| Aspecto | Estado |
|---------|--------|
| Desactivar automatizaciones al cierre | PARCIAL — manual |
| Scheduler cleanup | No evidenciado en auditoría |

---

## Matriz offboarding

| | YA EXISTE Y NO TOCAR | EXISTE PERO REQUIERE INTEGRACIÓN | EXISTE PARCIAL Y REQUIERE EVOLUCIÓN | REALMENTE AUSENTE |
|--|---------------------|----------------------------------|-------------------------------------|-------------------|
| Retiro Empleado IA | ✓ | Checklist retiro masivo por proyecto | Pausa formal | — |
| Evidencia histórica | ✓ | Pack export contractual | — | — |
| Cierre oportunidad/soporte | ✓ | — | — | — |
| Cierre proyecto impl | — | — | ✓ estado CERRADO | Workflow checklist |
| Cierre contractual | — | — | — | ✓ registro fin contrato |
| Offboarding org | — | — | — | ✓ |

---

## Conclusión

Para offboarding operativo de IA, EIAAX está **listo**. Para offboarding de relación comercial completa (cierre contrato, retiro coordinado de empleados/automatizaciones, export evidencia), requiere **integración y workflow** sobre piezas existentes — no un módulo nuevo desde cero.
