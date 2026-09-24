# 02 — Decisiones de arquitectura

## Principio rector

Integración selectiva sobre BP1 — una sola arquitectura coherente. Sin cherry-pick ciego ni sistemas paralelos.

## Decisiones canónicas

### 1. Gobierno operacional = autoridad de políticas/aprobaciones
- BP2 conserva `evaluacion_integracion_gobierno.py` como **frontera delgada**, no como motor.
- Flujo: acción/intención → `evaluar_accion` / `crear_solicitud` → decisión humana → continuación.
- Modelo de acciones: LECTURA, ANÁLISIS, PROPUESTA, EJECUCIÓN.
- `coordinator.decide_approval` no duplicado; gobierno es transversal cuando corresponde.

### 2. Motor económico = capa FinOps real para BP2
- `evaluacion_integracion_finops.py` delega en `economic_motor_service`.
- Reutiliza `finops_service`, `consumption_planner_service`, valoración 1210.
- Clasificaciones preservadas: DIRECTO / TRANSVERSAL_ATRIBUIBLE / PLATAFORMA; ESTIMADO / REAL; VERIFICADO / ESTIMADO / POTENCIAL.
- **POTENCIAL nunca se convierte silenciosamente en realizado.**

### 3. Economía privada
- Permiso `finops.economy.private.view` restringido (admin/superadmin).
- Vista Entidad y integración evaluación usan `entity_view_summary` sin economía privada.
- `economia_privada_expuesta: false` en contrato de integración.

### 4. Proveedor IA ≠ proveedor capacidad externa
- Catálogo IA (`gobierno_operacional` políticas IA, `llm_providers`) para modelos.
- Capacidades externas BP2 / PIIAX vía `PiiaxAdapter` desacoplado.
- Sin simular éxito sin conexión real.

### 5. PIIAX
- EIAAX funciona sin PIIAX; adaptador desacoplado.
- Sin hardcodear contrato definitivo inexistente.

### 6. Partners MB-03
- Aislamiento por grant explícito; revocación efectiva en backend.
- No bypass de RBAC multiempresa.

### 7. Migración 1410
- **Canónico BP2** (`1410a1b2c3d4e` evaluación).
- Gobierno renumerado `1411a1b2c3d4e` (down: 1420).
- Partners renumerado `1412a1b2c3d4e` (down: 1411).
- Motor económico `1600a1b2c3d4e` (down: 1412).

### 8. Experiencia transversal vs BP2
- Una sola experiencia: ThemeProvider global, BrandMark en AppShell.
- Evaluaciones: consola BP2 + componentes transversales (tabla, ayuda, vista entidad).
- Conflictos de densidad/scroll resueltos priorizando coherencia BP2 + tokens semánticos.

## Conflictos encontrados y resolución

| Conflicto | Resolución |
|-----------|------------|
| Tres ramas con revisión `1410` | Cadena lineal; gobierno/partners renumerados |
| Stubs gobierno/finops en BP2 | Convertidos en delegación a servicios reales |
| `/partners` vs proveedores IA | Rutas separadas; menú distingue MB-03 vs admin LLM |
| Permisos nuevos no en sesión admin existente | `bootstrap_permissions` en arranque añade vínculos faltantes |
| Servidor uvicorn obsoleto en runtime | Reinicio requerido tras integración para exponer routers |
