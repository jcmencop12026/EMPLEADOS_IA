# 06 — Conversión a implementación

## Punto de continuación

`POST /api/centro-negocios/propuestas/{id}/convertir-implementacion`

Permiso: `negocio.contract`

## Comportamiento

1. Si la propuesta no está `ACEPTADA`, la marca como contratada
2. Crea `ImplementacionProyecto` vía `implementacion_service.create_proyecto`
3. Vincula `implementacion_proyecto_id` en extensión
4. Genera snapshot de versión con trigger `CONTRATACION`
5. Idempotente: si ya existe proyecto, retorna `ya_existia: true`

## Datos reutilizados

- Título de propuesta → título del proyecto
- `proposal_id` → enlace directo
- Valor compromiso snapshot desde propuesta (1340)
- Trazabilidad evaluación/oportunidad en extensión

## Flujo conceptual

```
PROSPECTO → DIAGNÓSTICO → PROPUESTA → NEGOCIACIÓN → CONTRATADO → LEVANTAMIENTO / IMPLEMENTACIÓN
```

**No** se construye el módulo completo de implementación — solo el contrato de transferencia y proyecto inicial.
