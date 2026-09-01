# Continuación V1 — Presentación real, PDF, informes y gráficos

**Rama:** `cursor/demo-comercial-ficticia-9a85`  
**SHA inicial:** `72dd6438e964b0e3ad497763db2d5f9c9d044a03`

## Reutilizado (sin duplicar)

- Vista Entidad (`get_vista_entidad`) — hallazgos/oportunidades publicables
- Inteligencia Resultados (`build_antes_proyectado_real`) — gráficos ANTES/PROY/REAL
- Informes impacto (`visibilidad` INTERNO / VISIBLE_ENTIDAD)
- Centro Información MB-11 — contrato `INFORME_COMERCIAL_PERIODICO` vía adapter
- Demo comercial existente — ruta `/demo/presentacion` con 403 para no-DEMO

## Construido

- `presentacion_models.py` — estados publicación + config informes comerciales
- `presentacion_publicacion_adapter.py` — PRIVADO → PREPARADO → PUBLICADO (fail-closed)
- `presentacion_service.py` — núcleo compartido DEMO/REAL + PDF
- `presentacion_pdf_service.py` — PDF ejecutivo sin dependencias externas
- `informes_comerciales_adapter.py` — persistencia config + integración MB-11
- Router `/api/presentacion/*` — presentación real, PDF, publicación, informes
- Frontend `/presentacion/:expedienteId` — 4 audiencias, gráficos, PDF
- Componentes `PresentacionView`, `PresentacionIndicadoresChart`

## Adapter de integración

| Área | Contrato | Estado |
|------|----------|--------|
| Publicación definitiva | `presentacion_publicacion_v1` | Adapter local fail-closed |
| Scheduler informes | `INFORME_COMERCIAL_PERIODICO` + `comm_rule_id` | PENDIENTE_INTEGRACION |
| Gráficos Centro Control | `reutiliza_datos_resultados_v1` | DEPENDENCIA CENTRO CONTROL |

## Criterios de cierre

| Criterio | Resultado |
|----------|-----------|
| Presentación DEMO | PASS |
| Presentación REAL | PASS |
| Publicación | PASS (adapter v1) |
| Cuatro audiencias | PASS |
| PDF | PASS |
| Informes periódicos | PASS (config) / DEPENDENCIA INTEGRACIÓN (scheduler) |
| Gráficos | PASS / DEPENDENCIA CENTRO CONTROL |
| CTA demo→evaluación | PASS |
| Separación demo/real | PASS |
| Tests backend | 16 passed |
| Frontend build | PASS |

## P0/P1/P2

- **P0:** Presentación real autorizada, PDF, aislamiento demo — cerrados
- **P1:** Scheduler envío real informes — adapter listo, cableado MB-11 pendiente
- **P1:** Gráficos avanzados Centro Control — componente presentación reutiliza APR
- **P2:** Integración autoridad publicación definitiva de otro agente
