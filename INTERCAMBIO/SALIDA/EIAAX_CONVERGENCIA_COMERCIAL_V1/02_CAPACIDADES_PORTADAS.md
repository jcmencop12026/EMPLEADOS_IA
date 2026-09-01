# Capacidades portadas

## C — Centro Estratégico (`25c79d5`)

- `backend/app/routers/strategic_control.py`
- `backend/app/services/strategic_control_service.py`
- `backend/app/services/strategic_economy_service.py`
- `backend/app/services/strategic_write_service.py`
- `frontend/src/pages/CentroEstrategicoPage.tsx`
- `tests/test_centro_estrategico_v1.py`
- Ruta frontend: `/centro-estrategico`
- API: `/api/centro-estrategico/*`
- Cinco lecturas (resumen, gerencia, operación, sistemas, financiero) sobre mismo dossier
- Economía privada vía `strategic_economy_service` (lectura; motor canónico `motor_economico`)

## B — Flujo Comercial V1 (`2bb3caa`)

- `backend/app/flujo_comercial_models.py`, `flujo_comercial_enums.py`
- `backend/app/routers/flujo_comercial.py`
- `backend/app/services/flujo_comercial_service.py`
- `backend/app/schemas_flujo_comercial.py`
- `tests/test_flujo_comercial_v1_1730.py`
- API: `/api/flujo-comercial/*`
- Catálogo contextual por sector, suficiencia, propuesta, instrumentos, garantías, recorrido demo
- Campo `sector` en `EvaluacionExpediente`; `origen_comercial` / `presentar_cliente` en `Opportunity`

## D — Demo + Presentación (`40b7c9b`)

- `backend/app/demo_comercial_constants.py`, `presentacion_models.py`
- Routers: `demo_comercial.py`, `presentacion.py`
- Services: demo, presentación, PDF, adapters publicación/informes
- Frontend: `DemoComercialPage`, `PresentacionEjecutivaPage`, `PresentacionRealPage`, `InformesPeriodicosDemoPage`, componentes `PresentacionView`, `DemoBanner`, `ContextualHelp`
- `tests/test_demo_comercial_ficticia.py`, `tests/test_presentacion_real_v1.py`
- Rutas: `/demo`, `/demo/presentacion/:id`, `/presentacion/:id`, `/demo/informes-periodicos`

## A — Espacio Externo + Evidencias (`f0d02bc`)

- `backend/app/espacio_externo_models.py`
- `backend/app/routers/espacio_externo.py`
- `backend/app/services/espacio_externo_service.py`, `espacio_externo_adapters.py`, `evidencia_entrega_service.py`
- Frontend: `EspacioExternoPortalPage`, `EspacioExternoAdminPanel`; `VistaEntidadPreview` extendido
- `tests/test_espacio_externo_v1.py`, `tests/test_espacio_externo_evidencias_v1.py`
- Ruta portal: `/mi-espacio`
- Rol sistema `external_prospect` con permisos portal/entregar
- Almacenamiento evidencias: `knowledge_storage.save_evidence_bytes`

## Integración transversal

- `main.py`: routers + imports modelos
- `permissions.py`: `STRATEGIC_CONTROL`, `FLUJO_COMERCIAL`, `ESPACIO_EXTERNO`
- `frontend/src/App.tsx`, `api.ts`, `evaluacionLabels.ts`
- `transformacion_service.py`: `create=False` en lecturas estratégicas (evita dossiers fantasma)
- `control_center_adapters.py`: compatibilidad `degradados` como lista
- `conftest.py`: imports modelos convergencia

## Arranque Windows preservado

- Scripts `d034566` intactos (`Resolve-EiaaxNpmCmdExecutable`, `call npm.cmd`)
- Tag y respaldo Lote3 **no alterados**
