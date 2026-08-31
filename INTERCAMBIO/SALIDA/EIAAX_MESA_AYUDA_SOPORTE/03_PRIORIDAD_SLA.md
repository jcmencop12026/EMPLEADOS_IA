# 03 — Prioridad y SLA

## Prioridad
Función `suggest_priority(impacto, urgencia)` — matriz que evita que todo sea urgente.

- Endpoint: `POST /api/soporte/prioridad/sugerir`
- Ajuste autorizado: `POST /api/soporte/casos/{id}/prioridad` con `motivo` registrado en historial.

## SLA (`SupportSlaPolicy`)
Configurable por organización, prioridad, tipo de caso y servicio.

Campos:
- `minutos_primera_respuesta`
- `minutos_resolucion`

Estados calculados (`compute_sla_estado`):
- `DENTRO` → En tiempo
- `PROXIMO` → Próximo a vencer (≤60 min)
- `VENCIDO` → Vencido
- `NO_APLICA` → Sin SLA configurado

## Alertas
`POST /api/soporte/sla/verificar-alertas` emite `SUPPORT_SLA_WARNING` (notificación + bus MB-11).

## APIs
- `GET/POST /api/soporte/sla` — listar/crear políticas
- Filtro lista casos: `sla_estado=PROXIMO|VENCIDO`
