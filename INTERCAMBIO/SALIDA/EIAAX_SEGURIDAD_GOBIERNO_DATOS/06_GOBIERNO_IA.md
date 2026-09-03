# 06 — Gobierno IA

## Ampliación sin segundo gateway

Tabla `gobierno_ia_policies` extendida:

| Campo nuevo | Propósito |
|-------------|-----------|
| `trazabilidad_obligatoria` | Registro obligatorio de uso IA |
| `catalogo_proveedores_ref` | **Reservado BP2** — integración catálogo GENERAL |
| `registro_detalle_json` | Límites y metadatos de trazabilidad |

## Políticas existentes reutilizadas

- `proveedores_permitidos_json`, `modelos_permitidos_json`
- `acciones_permitidas_json`, `datos_permitidos_json`
- `requiere_aprobacion_humana_json`

## Verificación

`POST /api/gobierno-operacional/ia/verificar` — sin cambios de contrato.

## NO implementado (reservado integración)

- Catálogo cerrado de proveedores en runtime LLM
- Sincronización `gov_provider_policies` ↔ `gobierno_ia_policies`

Estado en Centro de Confianza: **PENDIENTE** con evidencia explícita.
