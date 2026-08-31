# 01 — Reutilización

## Capacidades existentes reutilizadas (sin motores paralelos)

| Módulo | Uso en esta misión |
|--------|-------------------|
| **MB-11 (1341)** | `communications_models`, `communications_service`, router `/api/comunicaciones` |
| **Notificaciones 820** | Bandeja in-app independiente; no duplicada |
| **Scheduler 810C** | `process_scheduled_and_retries()` para programadas y reintentos |
| **Event bus** | Disparadores `RESULTADOS_INFORME_GENERADO`, `EVALUACION_INFO_FALTANTE` |
| **Inteligencia Resultados 1410** | Entrega de informes, evento al generar |
| **Evaluación 1405** | Origen de expedientes y solicitudes de información |
| **Experiencia transversal** | `EiaaxTable`, `ContextualHelp`, tokens, `AppShell` |
| **Mi Trabajo / Centro Control** | Contratos existentes `contrato_mi_trabajo`, `contrato_centro_control` |

## Evolución en 1420

- Tabla `comm_entregas_informe` — versión fijada al entregar
- Campos `referencias_json`, `prioridad` en `comm_messages`
- Integración formal informe → comunicación → historial

## No construido

- PIIAX, SMS, proveedores externos ficticios
- Centro de Negocios, Gobierno Operacional, Motor Económico, Fábrica IA
- Segundo scheduler ni segundo motor de notificaciones
