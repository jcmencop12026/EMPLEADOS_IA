# 12 — Brechas restantes

## P0

Ninguno en alcance MB-11 EIAAX.

## P1

| Brecha | Nota |
|--------|------|
| SMTP/webhook real | Requiere credenciales y confirmación ENTREGADA |
| Aprobación previa envío externo | Frontera con Gobierno Operacional — no motor duplicado |
| Integración Centro de Negocios (B) | Contrato event bus preparado |
| Integración Gobierno Datos (A) | Hook en `validate_delivery_privacy` |

## P2

| Brecha | Nota |
|--------|------|
| UI gestión reglas avanzada | API completa; UI básica |
| Empleados IA NOTIFICAR/ENVIAR | Interfaz conceptual; RBAC obligatorio |
| PIIAX canales externos | Sin hardcode; intención EIAAX expresada |
| Reconciliación Alembic multi-rama | GENERAL integrará 1410/1420 con otras heads |

## Migración

`1420a1b2c3d4e` — depende de `1410a1b2c3d4e` (Inteligencia Resultados).
