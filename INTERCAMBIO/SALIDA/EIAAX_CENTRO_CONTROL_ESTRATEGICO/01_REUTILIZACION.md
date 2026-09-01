# 01 — Reutilización

## EXISTE (reutilizado sin duplicar)

| Componente | Ubicación | Uso V1 estratégico |
|------------|-----------|-------------------|
| Dossier transformación | `transformacion_service.get_dossier_completo` | Fuente única del dossier |
| Arquitecto expediente | `evaluacion_service` | Impacto ANTES/PROYECTADO/REAL, vista entidad |
| Adapters CC | `control_center_adapters.py` | Oportunidades, ValorRetorno, Comercial, TCO, Implementación, FinOps, Continuidad |
| Cadena ejecutiva | `control_center_service._cadena_ejecutiva` | Trazabilidad señal→oportunidad→ejecución |
| Integraciones overview | `integration_service.list_connectors_overview` | Lectura Sistemas (alto nivel) |
| MB-08 operacional | `/api/centro-control/operacional` | Enlace — no sustituido |
| Permisos publicación | `evaluacion.vista_entidad`, `visible_entidad` | Vista entidad y economía no publicable |
| UI patrones CC | `CentroControlPage.tsx`, estilos `.ops-page` | Base visual cockpit |

## NUEVO (capa lectura/orquestación)

| Archivo | Rol |
|---------|-----|
| `strategic_control_service.py` | Orquestador lecturas + gráficos + economía privada |
| `routers/strategic_control.py` | API `/api/centro-estrategico/*` |
| `CentroEstrategicoPage.tsx` | UI cockpit 5 lecturas + modo comité |
| `permissions.py` | `strategic_control.view`, `strategic_control.economia_privada` |

## EVITADO explícitamente

- Segundo MB-08 / segundo FinOps / segundo gobierno operacional
- Cuatro copias de datos por lectura
- Creación de dossier en lectura (`create=False` en cockpit)
- Sustitución de `/centro-control` operacional
- Migraciones nuevas (V1 es capa de lectura)

## Corrección colateral

- `ContinuidadAdapter`: `degradados` es lista — comparación con `len()` (bug preexistente expuesto por lectura Sistemas)
