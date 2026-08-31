# 06 — Conocimiento y capacidades

## Conocimiento (reutilizado)

- `EmployeeKnowledgeSource` asocia fuentes autorizadas por organización
- `KnowledgeSource` como catálogo backend
- Validación en `validate_configuration`: advertencia si sin fuentes
- El empleado solo consulta conocimiento de su `organization_id`

**No** se reconstruyó Knowledge.

## Herramientas técnicas vs capacidades empresariales

| Capa | Modelo | Uso |
|------|--------|-----|
| Técnica | `Tool`, `EmployeeToolGrant` | Ejecución real (docint, rips, etc.) |
| Empresarial | `EmployeeBusinessCapability` | Declaración de necesidad (CONSULTAR_DATOS, etc.) |

El Empleado IA **no** declara conectores concretos en definición de negocio.

## Mapeo desde Arquitecto

`factory_bridge_service` traduce `herramientas_json` del requerimiento a capacidades empresariales con defaults:

- conocimiento → CONSULTAR_DATOS (LECTURA)
- operaciones → EJECUTAR_PROCESO (EJECUCION)
- notificaciones → NOTIFICAR (PROPUESTA)
- documentos → OBTENER_DOCUMENTO (LECTURA)

## Contrato para capacidades externas (GENERAL)

```python
{
  "code": "CONSULTAR_DATOS",
  "label": "Consultar datos autorizados",
  "operation_class": "LECTURA",
  "organization_id": "<tenant>",
  "employee_id": "<empleado>"
}
```

Resolución a conector real: responsabilidad de capa GENERAL/PIIAX (no construida aquí).
