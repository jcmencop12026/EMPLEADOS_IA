# 07 — Centro de Confianza evolucionado

## Endpoint

`GET /api/empresa-seguridad/confianza`

## Grupos

Acceso · Datos · IA · Aprobaciones · Auditoría · Trazabilidad · Privacidad · Continuidad

## Estados

| Estado | Significado |
|--------|-------------|
| IMPLEMENTADO | Control activo con evidencia numérica |
| CONFIGURADO | Módulo disponible, sin uso registrado aún |
| PENDIENTE | Reservado integración (ej. catálogo proveedores BP2) |
| NO_DISPONIBLE | Módulo no accesible |

## UI

`/centro-confianza` — agrupación por dominio, etiquetas en español.

## Principio

Solo controles verificables. El catálogo cerrado de proveedores IA aparece como **PENDIENTE**, no como certificado.
