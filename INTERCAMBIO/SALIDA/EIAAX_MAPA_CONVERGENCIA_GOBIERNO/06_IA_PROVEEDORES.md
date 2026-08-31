# 06 — IA y proveedores

**Distinción obligatoria:**

| Concepto | Qué es | Autoridad | NO es |
|----------|--------|-----------|-------|
| **Proveedor/modelo IA** | LLM para empleados IA (OpenAI, Anthropic, local) | `llm_model_catalog` + `/api/llm` gateway | PIIAX, RIPS, DocInt |
| **Proveedor capacidad externa** | Servicio fuera EIAAX (PIIAX evaluación, conectores) | `ProveedorExternoAdapter` | Modelo chat empleado |

---

## Inventario por rama

| Componente | SHA | Tipo | Estado |
|------------|-----|------|--------|
| `llm_model_catalog` + gateway `b950` | base | Modelo IA | **Canónico** |
| `gobierno_ia_policies` | `c433bac` | Política uso IA | **Canónico** |
| `EmployeeModelPolicy` | fábrica | Política por empleado | Adaptador → gateway |
| `validate_provider_for_test` | `2afd673` | Validación empleado | Debe usar catálogo LLM |
| `evaluacion_proveedor_externo_service` | `ee57fab` | Capacidad externa PIIAX | **Adapter** — no catálogo LLM |
| `catalogo_proveedores_ia` (Centro Confianza) | `c433bac` | Control reservado BP2 | P1 — no crear otro |
| `catalogo_proveedores_ref` | gobierno | Referencia futura BP2 | Pendiente integración |
| Integraciones 1330 | base | Conectores reales | Gov catalog wiring |
| FinOps `FinOpsRecord` | base | Costo por ejecución | Trazabilidad modelo |

---

## Arquitectura canónica

```
                    ┌─────────────────────────┐
                    │   gobierno_ia_policies   │
                    │   (qué permitido/org)    │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ llm_model_    │     │ /api/llm        │     │ ProveedorExterno │
│ catalog       │────▶│ gateway         │     │ Adapter (PIIAX)  │
└───────────────┘     └────────┬────────┘     └────────┬─────────┘
                               │                        │
                               ▼                        ▼
                    ┌─────────────────┐     ┌──────────────────┐
                    │ AIEmployee      │     │ BP2 acción       │
                    │ coordinator     │     │ externa eval     │
                    │ run_llm_for_task│     │ (no LLM employee)│
                    └─────────────────┘     └──────────────────┘
```

---

## Conflictos

### I-01 — validate-provider como catálogo paralelo

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `2afd673` `factory_bridge_service.validate_provider_for_test` |
| **COMPONENTES** | `agent_factory` router, `EmployeeModelPolicy` |
| **AUTORIDAD** | `llm_model_catalog` + `gobierno_ia_policies` |
| **CONSERVAR** | Endpoint validate como **test de conformidad** |
| **ADAPTAR** | Validar contra catálogo, no lista hardcoded |
| **RETIRAR** | Providers aceptados duplicados en bridge |
| **RIESGO** | Empleado publicado con modelo no gobernado |

### I-02 — Centro Confianza catalogo_proveedores_ia

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `c433bac` control agrupado pendiente BP2 |
| **COMPONENTES** | `empresa_seguridad_service` centro confianza |
| **AUTORIDAD** | Reflejo de `llm_model_catalog` + políticas — no fuente |
| **CONSERVAR** | UI control como indicador |
| **ADAPTAR** | P1: cablear `catalogo_proveedores_ref` |
| **RETIRAR** | Segundo CRUD de proveedores |
| **RIESGO** | Operador configura proveedor fuera de gateway |

### I-03 — BP2 PIIAX como proveedor IA

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `ee57fab` naming ambiguo |
| **COMPONENTES** | `evaluacion_proveedor_externo_service`, `piiax_bridge_service` |
| **AUTORIDAD** | Adapter capacidad externa |
| **CONSERVAR** | Stubs y estados español |
| **ADAPTAR** | Documentar en UI como "capacidad externa" |
| **RETIRAR** | Entrada en `llm_model_catalog` |
| **RIESGO** | FinOps mezcla costo PIIAX con tokens LLM |

### I-04 — Políticas IA por empleado vs org

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Fábrica `EmployeeModelPolicy` vs `GobiernoIaPolicy` |
| **COMPONENTES** | lifecycle, gobierno operacional |
| **AUTORIDAD** | Org: `gobierno_ia_policies`; empleado: subset permitido |
| **CONSERVAR** | Ambas capas |
| **ADAPTAR** | Empleado no puede exceder política org |
| **RETIRAR** | Política empleado que amplíe org |
| **RIESGO** | Bypass restricción modelo prohibido |

---

## Reglas GENERAL

1. **Un catálogo LLM** — `llm_model_catalog`. Ningún otro.
2. **Toda invocación LLM** pasa por gateway (coordinator / `run_llm_for_task`).
3. **PIIAX y conectores** solo vía `ProveedorExternoAdapter`.
4. **Centro Confianza** lee estado; no escribe catálogo hasta P1 BP2.
5. Tests: empleado con modelo fuera de catálogo → rechazo en publish.

---

## P1 reservado BP2

- Activar `catalogo_proveedores_ref` en gobierno
- Sincronizar control `catalogo_proveedores_ia` con gateway
- No implementar en esta convergencia
