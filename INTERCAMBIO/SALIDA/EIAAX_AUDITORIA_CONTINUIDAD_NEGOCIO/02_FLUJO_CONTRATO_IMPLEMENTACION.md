# 02 — Flujo contrato → implementación

**Base:** SHA `fbfd6a2`  
**Punto de partida:** Centro de Negocios — `contratar` y `convertir-implementacion`

## Diagrama de continuidad

```
Evaluación 1405 ──┐
                  ├──► CommercialProposal 1280 + NegocioProposalExtension 1700/1710
Oportunidad 1030 ─┘         │
                            ▼
                    Motor Económico 1600
                            │
              Presentar + PDF + Aprobaciones
                            │
                    POST /contratar
                            │
              negocio_contract_records + ACEPTADA
                            │
              POST /convertir-implementacion
                            │
                    impl_proyectos (1340)
                            │
         ext.implementacion_proyecto_id (back-link)
```

---

## 1. Contratación (`POST /api/centro-negocios/propuestas/{id}/contratar`)

**Evidencia:** `backend/app/routers/centro_negocios.py` L351, `negocio_service.contract_proposal`

### Precondiciones
- Última versión con `pdf_document_id` (422 si falta PDF).

### Objetos creados/actualizados

| Destino | Campos escritos |
|---------|-----------------|
| `negocio_contract_records` | `proposal_id`, `version_id`, `document_id`, `precio_contratado`, `modelo_comercial`, `condiciones`, `responsable_id` |
| `negocio_proposal_extensions` | `precio_contratado` |
| `negocio_price_phase_records` | fase `CONTRATADO` |
| `commercial_proposals` | `estado` → `ACEPTADA` |
| Auditoría | acción `negocio.contratacion` |

---

## 2. Conversión (`POST /api/centro-negocios/propuestas/{id}/convertir-implementacion`)

**Evidencia:** `negocio_service.convert_to_implementacion` L571-629

### Secuencia

1. Si `proposal.estado != ACEPTADA` → invoca `contract_proposal` automáticamente.
2. Si ya existe `ext.implementacion_proyecto_id` → retorna idempotente `ya_existia: true`.
3. Crea `ImplementacionProyecto` vía `impl_svc.create_proyecto`.
4. Escribe `ext.implementacion_proyecto_id = proyecto.id`.
5. Snapshot versión con trigger `CONTRATACION`.
6. Auditoría `negocio.convertir.implementacion`.

### Mapeo exacto a `impl_proyectos`

| Campo proyecto | Origen |
|----------------|--------|
| `titulo` | `proposal.titulo` |
| `proposal_id` | `proposal.id` (FK `commercial_proposals`) |
| `alcance` | `f"Implementación derivada de {proposal.codigo}"` — **plantilla**, no alcance real |
| `objetivos` | `ext.proximo_paso` (valor previo a sobrescritura) |
| `responsable_id` | `user.id` |
| `valor_compromiso_json` | `_snapshot_valor_compromiso(proposal_id)` |
| `codigo` | auto `IMPL-NNNN` |

### Snapshot económico (`valor_compromiso_json`)

**Evidencia:** `implementacion_service._snapshot_valor_compromiso` L112-128

```json
{
  "proposal_id", "codigo",
  "valor_total_esperado", "valor_atribuible_total",
  "precio_final", "precio_sugerido",
  "roi_pct", "payback_meses", "margen_pct",
  "supuestos"
}
```

### Respuesta API (referencias en respuesta, no persistidas en proyecto)

```json
{
  "proyecto_id": "...",
  "contract_id": "...",
  "referencias": {
    "evaluacion_id": "...",
    "opportunity_id": "...",
    "version_number": 2,
    "document_id": "..."
  }
}
```

---

## 3. Qué se conserva

| Dato | Dónde permanece | Acceso desde impl |
|------|-----------------|-------------------|
| Propuesta comercial completa | `commercial_proposals` + valores/escenarios | FK `proposal_id` |
| Extensión negocio | `negocio_proposal_extensions` | JOIN vía `proposal_id` |
| `opportunity_id` | `negocio_proposal_extensions.opportunity_id` | Indirecto (no en proyecto) |
| `evaluacion_id` | `negocio_proposal_extensions.evaluacion_id` | Indirecto |
| Contrato formal | `negocio_contract_records` | Por `proposal_id` |
| PDF contratado | `negocio_proposal_documents` vía `document_id` | Indirecto |
| Versiones / negociación / aprobaciones | Tablas `negocio_*` | Por `proposal_id` |
| Motor económico | `economic_recommendation_id`, `negocio_price_decisions` | Por `proposal_id` |
| Snapshot compromiso | `impl_proyectos.valor_compromiso_json` | **Directo** en proyecto |
| Enlace bidireccional | `implementacion_proyecto_id` en extensión | Directo |

**Nada se elimina** en la conversión; la pérdida es de **denormalización**, no de datos.

---

## 4. Qué se pierde (para consumidores solo-impl)

Datos que **no se copian** al proyecto y requieren navegar al grafo comercial:

| Categoría | Contenido no transferido |
|-----------|--------------------------|
| Origen | `opportunity_id`, `evaluacion_id` como columnas del proyecto |
| Contrato | `condiciones`, `modelo_comercial` contratado, `contract_id` |
| Contenido rico | `perspectivas_json`, `documento_cliente_json`, `documento_interno_json`, `ia_consumo_json` |
| Líneas de valor | `commercial_proposal_values`, escenarios, costos detallados |
| Negociación | `negocio_negotiation_entries`, `negocio_approval_records` |
| Historial precio | `negocio_price_phase_records` completo |
| Economía operador | Margen/costo real del motor privado |
| Campos omitidos del snapshot | `beneficio_neto_cliente`, `riesgos_json`, `traceability_json`, items de valor |
| Semántica alcance | `alcance` es string genérico, no perspectivas/supuestos |

---

## 5. Qué debe reintroducirse manualmente

| Elemento | Motivo |
|----------|--------|
| Plan de trabajo detallado | Conversión no genera fases/hitos automáticos |
| Responsables por fase/hito | Solo `responsable_id` del proyecto (= usuario que convierte) |
| Requisitos técnicos | No se extraen de evaluación |
| Empleados IA a desplegar | No hay auto-provisión desde `ia_consumo_json` |
| Vínculo explícito a oportunidad en impl | No hay FK; UI debe resolver vía negocio |
| Condiciones contractuales en impl | No copiadas; operador debe consultar contrato |

---

## 6. Objeto que recibe la implementación

**Entidad primaria:** `ImplementacionProyecto` (`impl_proyectos`)

**Estado inicial:** `PLANIFICACION` (default enum)

**Referencias permanentes:**
- `proposal_id` → `commercial_proposals.id`
- `negocio_proposal_extensions.implementacion_proyecto_id` → `impl_proyectos.id`

**Puente de trazabilidad en tablero:**

```741:747:backend/app/services/implementacion_service.py
        "trazabilidad": {
            "que_vendimos": _parse(proj.valor_compromiso_json),
            "que_prometimos": proj.objetivos,
            "que_implementamos": proj.alcance,
            "fase_actual": proj.estado,
            "go_live": proj.go_live_aprobado,
        },
```

---

## 7. Brechas documentación vs código

| Documento | Afirmación | Realidad código |
|-----------|------------|-----------------|
| `06_CONVERSION_IMPLEMENTACION.md` | Referencias almacenadas en proyecto | Solo en respuesta HTTP `referencias`; proyecto solo tiene `proposal_id` |
| `convert_to_implementacion` | `datos_reutilizados: true` | Hardcoded; no valida completitud |
| Router `convertir-implementacion` | Acepta condiciones | Servicio acepta `condiciones` pero router no las pasa (L416-426 `centro_negocios.py`) |
| Aceptación sin `/contratar` | — | `contract_id` puede ser `null` si propuesta llegó a `ACEPTADA` solo por transición |

---

## 8. Clasificación del flujo

| Aspecto | Clasificación |
|---------|---------------|
| Endpoint contratar | OPERATIVA |
| Endpoint convertir | OPERATIVA |
| Idempotencia conversión | OPERATIVA |
| Puente `proposal_id` | OPERATIVA |
| Transferencia datos ricos | PARCIAL |
| Auto-generación plan impl | AUSENTE |
| Trazabilidad multi-objeto en impl | PARCIAL |

---

## 9. Matriz de decisión

| | YA EXISTE Y NO TOCAR | EXISTE PERO REQUIERE INTEGRACIÓN | EXISTE PARCIAL Y REQUIERE EVOLUCIÓN | REALMENTE AUSENTE |
|--|---------------------|----------------------------------|-------------------------------------|-------------------|
| Flujo contratar→convertir | ✓ endpoints y servicios | Enlace oportunidad/evaluación en vista impl | Copia selectiva de alcance/condiciones | Auto-plan desde contrato |
| Registro contractual | ✓ `negocio_contract_records` | Mostrar contrato en detalle impl | Pasar `condiciones` desde router | — |
| Snapshot valor | ✓ `valor_compromiso_json` | Enlazar líneas de valor comercial | Ampliar campos del snapshot | — |
