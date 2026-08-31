# 09 — Duplicaciones y riesgos

**Base:** SHA `fbfd6a2`  
**Objetivo:** Identificar solapamientos, deuda técnica y riesgos de continuidad sin proponer reconstrucción

---

## 1. Duplicaciones vigentes

| # | Duplicación | Módulos | Evidencia | Riesgo | Acción |
|---|-------------|---------|-----------|--------|--------|
| D1 | Propuesta comercial dual UI | Comercial 1280 vs Centro Negocios 1700 | Misma `CommercialProposal`; `/comercial/propuestas` y `/centro-negocios/propuestas` | Usuario opera en superficie incorrecta; datos divergentes en `proximo_paso`/sync | INTEGRACIÓN — unificar entrada post-cierre negocio |
| D2 | FinOps vs Motor Económico | 950/1110 vs 1600 | `/api/finops` y `/api/motor-economico` | Doble lectura, confusión API | NO TOCAR — motor es facade; documentar ruta canónica |
| D3 | Incidentes soporte vs continuidad | MB-12 vs 1360 | `support_models` vs `continuidad_models` | Casos duplicados, SLA inconsistente | INTEGRACIÓN o reglas de enrutamiento |
| D4 | Aprobaciones comerciales vs gobierno | Negocio 1710 `LocalNegocioApprovalAdapter` vs Gobierno Operacional (Agente A) | `negocio_approval_adapter.py` | Dos sistemas aprobación si no se integra | INTEGRACIÓN — swap adapter (ya previsto P1) |
| D5 | Dashboard vs Centro Control | `DashboardPage.tsx` vs `CentroControlPage.tsx` | Dashboard no enrutado | Confusión mantenimiento | OBSOLETA — no revivir Dashboard |
| D6 | OrganizationPage vs AdminOrganization | Frontend legacy | `OrganizationPage.tsx` no enrutada | Código muerto | OBSOLETA — eliminar en lote limpieza |
| D7 | Valor en múltiples módulos | Comercial, valoración, motor, FinOps, éxito cliente | 5+ fuentes `valor_*` | Métricas inconsistentes si no se respeta semántica POTENCIAL | INTEGRACIÓN vistas; NO nuevo motor valor |

---

## 2. Riesgos de continuidad de negocio

### R1 — Conversión "datos reutilizados" sin validación
- **Evidencia:** `datos_reutilizados: True` hardcoded (`negocio_service.py` L622)
- **Impacto:** Falsa sensación de transferencia completa
- **Severidad:** Media
- **Tipo:** Integración

### R2 — Referencias no persistidas en proyecto
- **Evidencia:** `evaluacion_id`, `opportunity_id` solo en respuesta HTTP y extensión negocio
- **Impacto:** Vista implementación no resuelve origen sin JOIN
- **Severidad:** Media
- **Tipo:** Integración

### R3 — Alcance genérico en conversión
- **Evidencia:** `alcance = f"Implementación derivada de {codigo}"`
- **Impacto:** Pérdida semántica de compromiso comercial en impl
- **Severidad:** Alta (operativa)
- **Tipo:** Evolución conversión

### R4 — Contrato sin registro si ACEPTADA por transición
- **Evidencia:** `contract_id` puede ser `null` (`negocio_service.py` L585-591); test `test_centro_negocios_1700.py`
- **Impacto:** Conversión sin artefacto contractual
- **Severidad:** Media-Alta
- **Tipo:** Evolución flujo

### R5 — Router no pasa condiciones a conversión
- **Evidencia:** `centro_negocios.py` L416-426 vs servicio L571
- **Impacto:** Condiciones ignoradas en auto-contratación
- **Severidad:** Baja
- **Tipo:** Bug integración

### R6 — Documentación desalineada con código
- **Evidencia:** `06_CONVERSION_IMPLEMENTACION.md` afirma refs en proyecto; código solo `proposal_id`
- **Impacto:** Decisiones de integración basadas en doc incorrecta
- **Severidad:** Media
- **Tipo:** Documentación (corregida en esta auditoría)

### R7 — Sub-entidades impl sin ciclo de vida
- **Evidencia:** tareas/bloqueadores/requisitos create-only
- **Impacto:** Datos huérfanos; go-live gates pueden quedar bloqueados sin API resolver
- **Severidad:** Alta (operativa)
- **Tipo:** Evolución 1340

### R8 — Dependencias JSON no validadas
- **Evidencia:** `dependencias_json` en fases/hitos; test crea pero no valida
- **Impacto:** Avance incoherente
- **Severidad:** Baja-Media
- **Tipo:** Estructural

### R9 — Economía contractual desconectada de FinOps
- **Evidencia:** sin budget auto desde `precio_contratado`
- **Impacto:** Desviación consumo sin alerta relativa al contrato
- **Severidad:** Alta (negocio)
- **Tipo:** Integración

### R10 — Renovación/expansión sin salida comercial
- **Evidencia:** API create-only; sin UI ni oportunidad
- **Impacto:** Renovaciones perdidas en registro muerto
- **Severidad:** Media
- **Tipo:** Integración

### R11 — Knowledge no en Centro de Control
- **Evidencia:** CC marca CONOCIMIENTO_930 pendiente
- **Impacto:** Visión ejecutiva incompleta
- **Severidad:** Baja
- **Tipo:** Integración

### R12 — Semántica POTENCIAL mal usada
- **Evidencia:** múltiples módulos; regla documentada pero dispersa
- **Impacto:** ROI inflado en reportes
- **Severidad:** Alta (gobierno datos)
- **Tipo:** Integración / capacitación

### R13 — UI impl orientada demo
- **Evidencia:** go-live checklist pre-marcado en frontend
- **Impacto:** Aprobaciones formales sin rigor en demo
- **Severidad:** Media (gobierno)
- **Tipo:** Evolución UI

### R14 — Sin offboarding contractual
- **Evidencia:** ausencia registro fin contrato
- **Impacto:** Historial incompleto
- **Severidad:** Media
- **Tipo:** Evolución

---

## 3. Riesgos de re-construcción (misión explícita: evitar)

| Riesgo si se ignora auditoría | Consecuencia |
|-------------------------------|--------------|
| Construir "módulo implementación" nuevo | Duplica 1340 (21 tablas, 27 endpoints, 18 tests) |
| Construir CRM para renovación | Duplica oportunidades 1030 + negocio 1700 |
| Construir Inteligencia de Resultados | Duplica valoración, línea base, éxito cliente, CC |
| Construir facturación completa | Fuera alcance; FinOps ya cubre consumo |
| Modificar Motor Económico | Violación restricción; integrar en lugar de reescribir |

---

## 4. Deuda técnica transversal

| Item | Clasificación |
|------|---------------|
| Migración head única 1710 | OK en rama centro-negocios |
| Adapter aprobaciones local | PARCIAL — pendiente Gobierno Operacional |
| Tests E2E convergencia | Existen (`test_convergencia_*.py`) — validar post-integración ramas |
| Ledger migraciones | `migration_ledger.json` — mantener single head al integrar |

---

## 5. Mapa riesgo × matriz final

| Riesgo | YA EXISTE NO TOCAR | REQUIERE INTEGRACIÓN | PARCIAL EVOLUCIÓN | AUSENTE |
|--------|-------------------|---------------------|-------------------|---------|
| R1-R2 Referencias | ✓ flujo base | ✓ | — | — |
| R3 Alcance | — | — | ✓ | — |
| R4 Contrato | — | — | ✓ | — |
| R7 Ciclo vida impl | ✓ hitos/go-live | — | ✓ sub-entidades | — |
| R9 Economía | ✓ motor/finops | ✓ contrato→budget | — | facturación |
| R10 Renovación | ✓ modelos | ✓ pipeline | ✓ workflow | — |
| R14 Offboarding | ✓ retiro IA | — | ✓ cierre impl | cierre contrato |

---

## Conclusión

Los riesgos principales son de **integración y completitud de ciclo de vida**, no de ausencia de plataforma. Priorizar cableado sobre construcción; tratar duplicaciones D1, D3, D4 como deuda de integración, no como invitación a nuevos módulos.
