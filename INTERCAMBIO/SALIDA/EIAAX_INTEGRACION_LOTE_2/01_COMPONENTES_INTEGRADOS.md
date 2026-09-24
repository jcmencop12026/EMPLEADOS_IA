# 01 — Componentes integrados (Lote 2)

## Rama y SHAs

| Concepto | Valor |
|----------|-------|
| **Base BP1 certificada** | `7e9abba11f4c4f216142c6c70d662229ffc585bb` |
| **Rama integración** | `cursor/integracion-lote-2-85e4` |
| **SHA candidato integrado** | `e34c778790440b448e916ac1747b2a262ae762ed` |

## Orígenes incorporados (congelados en este lote)

| Componente | Rama | SHA origen |
|------------|------|------------|
| BP2 — Producto Bloque 2 | `cursor/producto-bloque-2-piiax-prep-85e4` | `ee57fab` |
| Experiencia transversal | `cursor/eiaax-experiencia-transversal-9a85` | `7f2e3ce` |
| Gobierno operacional | `cursor/gobierno-operacional-eiaax-3e3d` | `21e2330` |
| Motor económico | `cursor/motor-economico-eiaax-3581` | `1c74dc7602b09257a162f487d3a2b7423b3c068f` |
| Partners / aliados MB-03 | `cursor/mb03-partners-aliados-dec7` | `fe646d4` |

## Backend integrado

### Modelos y servicios nuevos
- `gobierno_operacional_models.py`, `gobierno_operacional_service.py`
- `partner_models.py`, `partner_service.py`
- `economic_motor_models.py`, `economic_motor_enums.py`, `economic_motor_service.py`

### Routers API
- `/api/gobierno-operacional/*` — políticas, solicitudes, aprobaciones, centro de confianza, IA
- `/api/partners/*` — partners, grants, membresías, auditoría
- `/api/motor-economico/*` — valoración, costos, vista entidad segura

### BP2 — wiring a servicios reales
- `evaluacion_integracion_gobierno.py` → delega en `gobierno_operacional_service`
- `evaluacion_integracion_finops.py` → delega en `economic_motor_service`
- `evaluacion_siguiente_accion_service.py` — política con contexto org/db
- `evaluacion_accion_service.py` — solicitud gobierno al crear acciones sensibles
- `control_center_adapters.py` — `MotorEconomicoAdapter`

### Preservado de BP1 y bloques previos
- Expediente evaluación (1405), oportunidades, centro de control, FinOps base, RBAC, multiempresa, auditoría, AppShell, knowledge, analytics.

## Frontend integrado

### Experiencia transversal (selectivo)
- `hooks/useTheme.tsx`, `ThemeProvider`, `ThemeToggle`
- `components/identity/BrandMark.tsx`
- `lib/brand.ts`, `identityAssets.ts` (HERO, CORPORATIVO, EX08, MICRO)
- `components/EiaaxTable.tsx`, `ContextualHelp.tsx`
- `components/evaluacion/VistaEntidadPreview.tsx`
- `lib/evaluacionHelp.ts`, labels español

### Rutas nuevas
- `/centro-confianza` — `CentroConfianzaPage`
- `/partners`, `/partners/:partnerId` — MB-03 Partners (distinto de `/administracion/proveedores-ia`)

### Navegación
- Menú: Centro de Confianza, Partners y aliados (sección Análisis y control)
- Permisos de ruta en `auth/permissions.ts`

## NO integrado (siguiente lote)

- Seguridad / Gobierno de datos ampliado (nuevas misiones)
- Centro de Negocios
- Arquitecto de Transformación
- Inteligencia de Resultados
- BP3
- Nuevas misiones en curso de A/B/C/D
