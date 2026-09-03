# 11 — Riesgos de integración

**Prioridad:** P0 = bloqueante convergencia | P1 = alto antes producción | P2 = seguimiento

---

## Matriz de riesgos

| ID | Riesgo | Prob. | Impacto | P | Mitigación |
|----|--------|-------|---------|---|------------|
| R-01 | Merge Alembic con revision duplicada | Alta | Crítico | P0 | Renumerar según doc 10; nunca merge naive |
| R-02 | Dos sistemas aprobación operativos | Alta | Alto | P0 | Motor único `decide_approval`; CN adapter |
| R-03 | Bypass visibilidad en API | Media | Crítico | P0 | Gate `set_visibilidad_nivel`; tests adversarial |
| R-04 | Exposición economía privada | Media | Crítico | P0 | DTOs separados; strip PDF; permisos |
| R-05 | Partner cross-tenant | Media | Crítico | P0 | Grant + membership + RBAC AND |
| R-06 | Modelo IA no gobernado | Media | Alto | P1 | Catálogo único; validate-provider |
| R-07 | Trazabilidad rota | Alta | Alto | P1 | correlation_id obligatorio |
| R-08 | Clasificación contradictoria | Media | Alto | P1 | `asignar_clasificacion` único |
| R-09 | Comunicación externa sin aprobación | Media | Alto | P1 | Gate pre-envío |
| R-10 | Permisos frontend/backend desync | Alta | Medio | P1 | Merge permissions.py primero |
| R-11 | PIIAX confundido con LLM | Media | Medio | P2 | Documentación + UI labels |
| R-12 | Evidencia duplicada | Baja | Medio | P2 | Vínculo transversal único |

---

## Riesgos por conflicto no resuelto

### Si NO se resuelve 1410/1420 (R-01)

- `alembic upgrade head` falla o aplica esquema incorrecto
- Tablas gobierno ausentes mientras código las exige
- Rollback imposible sin intervención manual
- **Acción:** detener merge hasta renumeración

### Si NO se unifican aprobaciones (R-02)

- Usuario aprueba en CN sin registro gobierno
- Bandeja operaciones vs bandeja gobierno divergentes
- BP2 ejecuta acción externa sin `ApprovalRequest`
- **Acción:** feature flag CN presentación hasta adapter listo

### Si NO se unifica visibilidad (R-03)

- Vista entidad muestra hallazgo INTERNO
- Informe resultados visible sin log
- Centro Confianza incompleto
- **Acción:** bloquear vista entidad en merge hasta dual-write verificado

### Si NO se protege economía (R-04)

- PDF propuesta con margen
- Partner ve precio recomendado
- FinOps en respuesta JSON pública
- **Acción:** tests P0 en CI convergencia

### Si grant sustituye RBAC (R-05)

- Partner accede org sin membresía válida
- Datos tenant A desde sesión tenant B
- **Acción:** middleware partner obligatorio

---

## Riesgos de orden de integración incorrecto

| Orden incorrecto | Consecuencia |
|------------------|--------------|
| BP2 antes de seguridad | Sin dual-write visibilidad |
| CN antes de gobierno | LocalNegocio queda canónico |
| Comunicaciones antes resultados | Entregas sin tablas informe |
| Fábrica antes arquitecto | Bridge sin requerimientos |
| Cualquiera antes 1410 gobierno | Sin políticas acción transversales |

**Orden seguro:** Gobierno+Seguridad → Partners/Arquitecto/Fábrica → Resultados/Com → BP2 → CN

---

## Regresiones conocidas en hotspots

| Archivo | Riesgo merge |
|---------|--------------|
| `evaluacion_service.py` | Pérdida dual-write |
| `permissions.py` | Permisos nuevos omitidos |
| `main.py` | Routers duplicados o ausentes |
| `conftest.py` | Tests pasan con esquema parcial |

---

## Criterios de aceptación convergencia (GENERAL)

- [ ] Una sola head Alembic
- [ ] 29+ tests seguridad PASS
- [ ] 18+ tests gobierno PASS
- [ ] Test adversarial visibilidad vista entidad
- [ ] Test partner sin grant → 403
- [ ] Test PDF CN sin costos para rol LECTOR
- [ ] `correlation_id` end-to-end en expediente→informe
- [ ] Un solo listado aprobaciones pendientes federado (o documentado)

---

## Deuda explícita aceptada (P1 post-convergencia)

- `catalogo_proveedores_ref` BP2
- Hook completo gobierno↔coordinator para todas las acciones
- Federación UI bandeja aprobaciones única
- Partner scopes adicionales (evaluación limitada)

No bloquean merge si documentado y con guards temporales.
