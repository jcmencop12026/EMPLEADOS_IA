# 08 — Versionado y publicación

## Versionado

- `AIEmployee.version` incrementa en cambios sobre empleado ACTIVE/PUBLISHED con `force_new_version`
- `EmployeeVersion` conserva snapshot JSON completo de configuración
- Campos auditados: objetivo, instrucciones, herramientas, modelo, autonomía, políticas, conocimiento

Cada versión registra: quién (`created_by_id`), qué (`configuration_json`, `changed_fields_json`), cuándo (`created_at`), motivo (`change_reason`).

## Publicación controlada

```
GUARDAR (DRAFT/CONFIGURING)
  ↓
PROBAR (TESTING)
  ↓
CERTIFICAR (CERTIFIED)
  ↓
APROBAR si riesgo (PENDING_APPROVAL → decisión)
  ↓
PUBLICAR (PUBLISHED) — crea EmployeeVersion status=PUBLISHED
  ↓
ACTIVAR (ACTIVE)
```

## Validación pre-publicación

`validate_configuration` verifica:

- Capacidades asignadas
- Herramientas asignadas
- Instrucciones (rol/objetivo)
- Proveedor LLM configurado (si no es rule-engine)
- Pruebas PASS

`validate-provider` adicional para pruebas controladas sin ejecución productiva engañosa.

## Rollback

`POST /employees/{id}/rollback` restaura versión anterior con motivo auditado.
