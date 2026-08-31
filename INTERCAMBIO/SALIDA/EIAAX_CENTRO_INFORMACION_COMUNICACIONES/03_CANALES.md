# 03 — Canales

## Implementados

| Canal | Comportamiento |
|-------|----------------|
| `INTERNO_PLATAFORMA` | Bandeja EIAAX — estado ENVIADA |
| `CORREO_ELECTRONICO` | Adaptador con `secret_ref`; simulado sin SMTP |
| `WEBHOOK` | Validación SSRF; sin HTTP real en esta fase |

## Extensibilidad preparada

Enum documenta SMS, mensajería, etc. — no implementados sin proveedor real.

## Regla ENTREGADA

`ENTREGADA` solo con confirmación real; actualmente canales externos reportan `ENVIADA` con nota explícita de no verificación.
