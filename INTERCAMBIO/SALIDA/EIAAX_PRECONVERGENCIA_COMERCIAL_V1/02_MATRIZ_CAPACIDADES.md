# 02 — Matriz de capacidades (A+B+C+D vs central)

Leyenda: **R** REUTILIZAR · **P** PORTAR · **K** CONECTAR (adapter) · **X** DESCARTAR · **?** REQUIERE DECISIÓN GENERAL

Base: central `75fc689`.

---

## Matriz por capacidad

| Capacidad | Central | A | B | C | D | Recomendación |
|-----------|---------|---|---|---|---|---------------|
| **Dossier / expediente** | `EvaluacionExpediente` | extiende info/validación | orquesta flujo | dossier transformación | demo seed | **R** central + **P** campos B/A |
| **Organización/empresa** | `Organization` + tenant | `EntidadEmpresa` externa | negocio/contrato | partners grant | demo entidad | **R** org + **K** EntidadEmpresa↔expediente |
| **Prospecto/cliente** | parcial (evaluación) | **autoridad** espacio externo | flujo comercial estados | — | demo prospecto | **P** A estados + **K** B promoción |
| **Publicación** | `evaluacion.visibility` | `EmpresaPublicacion` paquetes | propuesta presentar | cockpit lectura | `PresentacionPublicacion` | **?** → una autoridad (ver 03) |
| **Visibilidad 4 niveles gobierno** | modelos stub | **P** 1410/1420 completo | — | referencia | — | **P** A gobierno/seguridad |
| **Evidencias/adjuntos** | `evidencia_ref` texto | **autoridad** adjuntos versionados | — | — | — | **P** A + **K** `knowledge_storage` |
| **Economía privada** | FinOps + motor import | adapters sin filtrar | **P** motor 1600 | strategic_economy | — | **?** motor central único |
| **Precio / propuesta** | centro_negocios | — | **P** negocio+flujo | adapters comercial | — | **P** B sobre central |
| **Oportunidades** | `opportunity_models` | vista filtrada | clasificación comercial | mapa causas | resultados link | **R** + **K** B/C |
| **Propuesta comercial** | `CommercialProposal` | propuesta paquete | **P** instrumentos | — | — | **P** B |
| **Contratos** | `negocio_models` | contrato_ref | **P** instrumentos+continuidad | — | — | **P** B continuidad 1720 |
| **Resultados ANTES/PROY/REAL** | `resultados` router | adaptador estricto | continuidad port | gráficos estratégicos | **P** 1410 inteligencia | **R** central + **P** D |
| **Informes** | `communications` MB-11 | adapter portal externo | — | — | adapter comercial | **R** MB-11 + **K** A/D |
| **Gobierno/aprobaciones** | `governance` + gobierno stub | **P** gobierno operacional | negocio approval | — | — | **P** A |
| **Implementación** | `implementacion_service` | adapter externo | continuidad→1340 | enlace cockpit | — | **R** + **K** A |
| **Empleados IA** | `agent_factory` | adapter externo | — | MB-06 bridge | — | **R** + **K** A/C |
| **Soporte** | `support_service` | adapter portal | — | — | — | **R** + **K** A |
| **Auditoría** | `write_audit` | extensa espacio externo | flujo comercial | partners audit | demo audit | **R** central |
| **correlation_id** | expediente | entidad/entrega/adjunto | flujo comercial | dossier/partner | demo prefix | **R** + normalizar prefijos |
| **Centro Control MB-08** | `control_center` | — | **MOD** adapters | **MOD** service | — | **?** merge B∩C |
| **Centro Estratégico** | — | — | adapters en B | **autoridad** | lecturas demo | **P** C + **K** D |
| **Demo comercial** | — | — | — | — | **autoridad** | **P** D (aislado) |
| **Presentación ejecutiva** | — | vista entidad | `ComercialPresentacionEjecutiva` | selección cockpit | `PresentacionPublicacion` | **?** unificar |
| **Partners MB-03** | router stub | — | — | **P** completo | — | **P** C |
| **Arquitecto transformación** | transformacion router | — | — | **P** completo | — | **P** C |
| **Fábrica MB-06 puente** | agent_factory | — | — | **P** bridge | — | **P** C |
| **Espacio externo portal** | — | **autoridad** | — | — | — | **P** A |
| **UX/marca demo** | — | — | — | — | **P** brand/theme | **P** D (opcional lote) |

---

## Inventario resumido por candidato

### A — Espacio Externo + Evidencias (`f0d02bc`, 69 archivos)

| Tipo | Artefactos clave |
|------|------------------|
| Modelos nuevos | `espacio_externo_models`, ext. `evaluacion_models`, `gobierno_operacional_models`, `empresa_seguridad_models` |
| Migraciones NEW | `1410` gobierno, `1420` seguridad, `1430-1432` espacio externo |
| Routers NEW | `espacio_externo`, ext. `gobierno_operacional`, `empresa_seguridad`, `audit` |
| Servicios NEW | `espacio_externo_service`, `espacio_externo_adapters`, `evidencia_entrega_service`, `gobierno_operacional_service`, `empresa_seguridad_service` |
| Adapters | implementación, agent_factory, communications, support |
| Frontend | `EspacioExternoPortalPage`, `VistaEntidadPreview`, `CentroConfianzaPage`, admin panel |
| Permisos | `espacio_externo.*`, `gobierno.*` |
| Tests | 3 suites espacio externo + gobierno + seguridad (28 tests evidencias+externo) |

### B — Flujo Comercial (`2bb3caa`, 93 archivos)

| Tipo | Artefactos clave |
|------|------------------|
| Modelos NEW/MOD | `flujo_comercial_models`, `economic_motor_models` (NEW vs central), `continuidad_comercial_models`, ext. `negocio/opportunity/implementacion/evaluacion` |
| Migraciones | MOD `1600-1720`, NEW `1730` flujo comercial |
| Routers NEW | `flujo_comercial`; ext. `centro_negocios`, `motor_economico`, `continuidad_comercial`, `implementacion`, `evaluaciones` |
| Servicios | `flujo_comercial_service`, `economic_motor_service`, `negocio_*`, `continuidad_*`, `control_center_*` (MOD) |
| Frontend | `CentroNegocios*`, `ComercialPropuestaDetailPage`, `ContinuidadVistaPanel` |
| Permisos | `flujo_comercial.*`, `negocio.*`, `continuidad_comercial.*`, `finops.economy.*` |
| Tests | 5 suites (1600, 1700, 1710, 1720, 1730) |

### C — Centro Control Estratégico (`25c79d5`, 108 archivos)

| Tipo | Artefactos clave |
|------|------------------|
| Modelos NEW | ext. `partner_models`, `transformacion_models`, `orchestration_models` |
| Migraciones NEW | `1410` partners, `1420` arquitecto, `1430` fábrica bridge |
| Routers NEW | `strategic_control`; ext. `partners`, `transformacion`, `control_center`, `agent_factory` |
| Servicios NEW | `strategic_control_service`, `strategic_write_service`, `strategic_economy_service`, `transformacion_service`, `partner_service`, `factory_bridge_service`, `operational_control_service` |
| Frontend | `CentroEstrategicoPage`, `ArquitectoTransformacionPage`, `PartnersPage` |
| Permisos | `strategic_control.*`, `transformacion.*`, `partners.*` |
| Tests | 5 suites (MB-03, arquitecto, estratégico, MB-08, fábrica) |

### D — Demo + Presentación (`40b7c9b`, 107 archivos)

| Tipo | Artefactos clave |
|------|------------------|
| Modelos NEW | `presentacion_models`, ext. `resultados_models`, `communications_models` |
| Migraciones NEW | `1410` resultados, `1420` MB-11 entregas, `1430` presentación |
| Routers NEW | `presentacion`, `demo_comercial`; ext. `resultados`, `comunicaciones` |
| Servicios NEW | `presentacion_service`, `presentacion_publicacion_adapter`, `presentacion_pdf_service`, `demo_comercial_service`, `informes_comerciales_adapter`, `resultados_service` |
| Frontend | demo UX, `PresentacionView`, charts, brand/theme, help contextual |
| Permisos | `resultados.*` |
| Tests | 4 suites (demo, presentación, resultados, MB-11) |

---

## Archivos tocados por ≥2 candidatos (producto)

| Archivo | Ramas | Riesgo |
|---------|-------|--------|
| `main.py` | A,B,C,D | ALTO |
| `permissions.py` | A,B,C,D | ALTO |
| `api.ts`, `App.tsx`, `menu.ts` | A,B,C,D | ALTO |
| `evaluacion_service.py` | A,B,D | ALTO |
| `evaluacion_models.py` | A,B | MEDIO |
| `control_center_service.py` | B,C | ALTO |
| `control_center_adapters.py` | B,C | ALTO |
| `EvaluacionConsolePage.tsx` | A,B,D | MEDIO |
| `VistaEntidadPreview.tsx` | A,D | MEDIO |
| `evaluacionLabels.ts` | A,D | BAJO |
| `migration_ledger.json` | B,C,D | MEDIO |
| `styles.css` | C,D | BAJO |
