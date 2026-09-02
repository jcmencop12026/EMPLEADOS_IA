# 05 — Evidencia

## Modelo

Tabla `empresa_evidencia_vinculo` — referencias sin duplicar almacenamiento documental.

| Campo | Uso |
|-------|-----|
| `tipo_evidencia` | documento, referencia, hallazgo, autorizacion, registro, enlace_externo |
| `referencia` | URI/ruta/ID (ej. `knowledge/doc-123`) |
| `rol_vinculo` | SOPORTE, HALLAZGO, DECISION, APROBACION, ACCION, RESULTADO, INFORME |
| `correlation_id` | Enlace trazabilidad |

## API

```
POST /api/empresa-seguridad/evidencias
GET  /api/empresa-seguridad/evidencias
GET  /api/empresa-seguridad/objetos/{tipo}/{id}  (vista consolidada)
```

## Reutilización

- Hallazgos BP1: campo `evidencia` existente
- Gobierno datos: `GovAuthorization.evidence_ref`
- Knowledge: referencia por ID sin copiar binarios
