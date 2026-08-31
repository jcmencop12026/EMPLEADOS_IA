# 05 — Economía privada

**Principio:** costos internos, margen, precio recomendado no aprobado y notas privadas **nunca** salen en vista entidad, partner ni comunicación externa sin permiso explícito.

---

## Superficies por rama

| Superficie | SHA | Datos sensibles | Protección actual |
|------------|-----|-----------------|-------------------|
| Motor Económico | `fbfd6a2` | `EconomicPrivateEconomy`, simulación costos | `get_private_economy` + permiso |
| Centro Negocios | `fbfd6a2` | Propuesta, márgenes, precio recomendado | `negocio.economy.private`; PDF strip |
| BP2 Vista Entidad | `ee57fab` | Impacto sin costos | Debe filtrar `INTERNO_EIAAX` |
| Partners | `2afd673` | No debe ver economía | Scopes sin economy |
| Resultados | `af0e8cd` | ROI, antes/después costos | Visibilidad + RBAC |
| Comunicaciones | `f32c815` | Informes con anexos económicos | Entrega debe validar clasificación |
| FinOps | base | `FinOpsRecord`, trazabilidad 1110 | `finops.economy.private` |
| Evaluación BP1 | base | Notas analista | `visible_entidad` / visibilidad |

---

## Campos de alto riesgo

| Campo / concepto | Ubicación | Riesgo |
|------------------|-----------|--------|
| `costo_estimado_historico` | Motor económico dashboard | Exposición a cliente |
| `costo_total` / `costos_por_clase` | Simulación planner | Exposición en propuesta |
| Precio recomendado (fórmula 40% valor) | `economic_motor_service` | Publicación no aprobada |
| `notas_internas` | Partner, propuesta | Fuga en vista partner |
| `margen` / `factor_ajuste` | CN extensión propuesta | Competencia |
| Economía otro tenant | Cualquier API sin `organization_id` | Crítico |

---

## Conflictos

### E-01 — PDF propuesta CN sin strip

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `fbfd6a2` generación PDF |
| **COMPONENTES** | `negocio_service`, motor económico, PDF renderer |
| **AUTORIDAD** | `economic_motor_service` + visibilidad `VISIBLE_ENTIDAD` |
| **CONSERVAR** | Vista interna completa con permiso |
| **ADAPTAR** | PDF cliente = subset campos aprobados |
| **RETIRAR** | Inclusión automática `costos_motor` en PDF externo |
| **RIESGO** | Cliente ve margen EIAAX |

### E-02 — Vista entidad BP2 con impacto económico

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `ee57fab` `ImpactoGrafico`, integración FinOps |
| **COMPONENTES** | `evaluacion_integracion_finops`, `VistaEntidadView` |
| **AUTORIDAD** | Solo métricas de impacto aprobadas y visibles |
| **CONSERVAR** | Gráficos cualitativos / % mejora aprobados |
| **ADAPTAR** | Filtrar series con `INTERNO_EIAAX` |
| **RETIRAR** | Endpoints vista-entidad con costos raw |
| **RIESGO** | Entidad evaluada ve costo interno IA |

### E-03 — Informe resultados con ROI detallado

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `af0e8cd` / `f32c815` |
| **COMPONENTES** | Informes impacto, entregas MB-11 |
| **AUTORIDAD** | Clasificación + visibilidad antes de entrega |
| **CONSERVAR** | Modelo indicadores |
| **ADAPTAR** | Plantilla informe: versión interna vs entidad |
| **RETIRAR** | Envío automático al publicar |
| **RIESGO** | Email con ROI y costos FinOps |

### E-04 — Private economy API sin permiso

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Motor 1600 |
| **COMPONENTES** | Routers motor económico |
| **AUTORIDAD** | `negocio.economy.private` / `finops.economy.private` |
| **CONSERVAR** | Endpoints separados private vs public |
| **ADAPTAR** | Tests adversarial en merge |
| **RETIRAR** | Campos private en DTO público |
| **RIESGO** | API leak cross-role |

### E-05 — Partner scope amplio a propuestas

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Integración CN + partners futura |
| **COMPONENTES** | `partner_organization_grants`, CN |
| **AUTORIDAD** | Grant sin economía; RBAC LECTOR |
| **CONSERVAR** | `evaluacion.view` limitado |
| **ADAPTAR** | Vista partner sin extensión económica |
| **RETIRAR** | Reutilizar DTO interno CN |
| **RIESGO** | Consultor ve precio recomendado no cerrado |

---

## Reglas de exposición (GENERAL)

1. **Dos DTOs:** `*Internal` (private economy) y `*Entity` (público aprobado).
2. **Aprobación comercial** obligatoria antes de incluir precio en `*Entity`.
3. **Vista entidad** nunca llama endpoints `private_economy`.
4. **Comunicaciones** adjunta solo objetos con visibilidad ≥ `VISIBLE_ENTIDAD` y sin campos strip pendientes.
5. **Auditoría:** `economic_motor.private_economy.saved` ya existe — extender a lecturas.

---

## Checklist pre-merge

- [ ] grep `costo_` en routers públicos / vista-entidad
- [ ] grep `private_economy` sin `check_permission`
- [ ] PDF/propuesta tests con rol LECTOR sin economía
- [ ] Partner grant test sin campos margen
