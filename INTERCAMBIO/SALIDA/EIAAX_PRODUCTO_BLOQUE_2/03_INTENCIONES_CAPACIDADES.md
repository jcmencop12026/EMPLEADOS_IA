# 03 — Intenciones y capacidades

## Intenciones agente (A–H)

| Código | Significado |
|--------|-------------|
| A | Información existente |
| B | Información adicional |
| C | Análisis IA |
| D | Consulta fuente externa |
| E | Acción externa |
| F | Aprobación humana |
| G | Oportunidad de mejora |
| H | Tarea / seguimiento |

**Servicio:** `evaluacion_intent_service.py`  
**Panel:** `EiaaxAskPanel.tsx` — sin ejecución externa automática.

## Capacidades (no conectores)

`consultar_datos`, `validar_registros`, `obtener_documento`, `sincronizar`, `transformar`, `enviar_informacion`, `notificar`, `ejecutar_proceso`, `consultar_estado`

EIAAX expresa **qué necesita**; el proveedor (PIIAX preferente) resuelve **cómo**.

## Estados capacidad externa (español)

`NO DISPONIBLE`, `DISPONIBLE`, `PENDIENTE`, `EN COLA`, `EJECUTANDO`, `ESPERANDO APROBACION`, `COMPLETADO`, `FALLIDO`, `CANCELADO`

Mapeo desde estados internos vía `evaluacion_proveedor_externo_service.estado_capacidad_es()`.
