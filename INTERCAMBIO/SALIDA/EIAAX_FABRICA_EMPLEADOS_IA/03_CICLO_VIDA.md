# 03 — Ciclo de vida

## Estados canónicos (reutilizados)

| Estado | Fase | Descripción |
|--------|------|-------------|
| `DRAFT` | Diseño | Borrador inicial |
| `CONFIGURING` | Configuración | Tras primera edición |
| `TESTING` | Prueba | Ejecución de casos de prueba |
| `CERTIFIED` | Validación | Certificación aprobada |
| `PENDING_APPROVAL` | Aprobación | Esperando decisión humana |
| `PUBLISHED` | Publicación | Versión publicada |
| `ACTIVE` | Operación | En producción |
| `PAUSED` | Pausa | Suspendido temporalmente |
| `RETIRED` | Retiro | Fuera de operación (historial preservado) |
| `ERROR` | Error | Fallo operacional |

## Flujo objetivo

```
NECESIDAD → REQUERIMIENTO → DISEÑO → VALIDACIÓN → CONFIGURACIÓN → PRUEBA
→ APROBACIÓN → PUBLICACIÓN → ASIGNACIÓN → OPERACIÓN → MEDICIÓN → EVOLUCIÓN → PAUSA/RETIRO
```

## Separación crítica

| Acción | Endpoint | Efecto |
|--------|----------|--------|
| Guardar borrador | `PATCH /employees/{id}` | No activa |
| Probar | `POST /employees/{id}/test` | Solo TESTING |
| Certificar | `POST /employees/{id}/certify` | CERTIFIED |
| Solicitar aprobación | `POST /employees/{id}/request-approval` | PENDING_APPROVAL |
| Publicar | `POST /employees/{id}/publish` | PUBLISHED (requiere CERTIFIED + validación) |
| Activar | `POST /employees/{id}/activate` | ACTIVE |
| Pausar | `POST /employees/{id}/pause` | PAUSED |
| Retirar | `POST /employees/{id}/retire` | RETIRED |

## Guardas de publicación

`publish_with_guards` exige:

1. `validate_configuration` válida (capacidades, herramientas, instrucciones, proveedor)
2. Estado `CERTIFIED`
3. Aprobación humana si `requires_approval` (riesgo alto)
4. Pruebas PASS registradas

No se activa engañosamente con proveedor inexistente.
