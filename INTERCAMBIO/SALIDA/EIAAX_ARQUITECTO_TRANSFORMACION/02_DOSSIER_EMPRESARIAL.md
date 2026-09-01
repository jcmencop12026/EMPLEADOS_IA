# 02 — Dossier empresarial persistente

## Modelo

Tabla `dossier_empresarial` — **una instancia por organización** (`uq_dossier_org`).

## Ciclo de vida

`PROSPECTO` → `EVALUACION` → `DIAGNOSTICO` → `OPORTUNIDADES` → `PROPUESTA` → `CLIENTE` → `IMPLEMENTACION` → `OPERACION` → `MEDICION`

## Conocimiento reutilizable

`dossier_conocimiento_items` almacena respuestas válidas con:

- procedencia (`fuente`: expediente, captura_guiada, documento, etc.)
- calidad (`ALTA` / `MEDIA` / `BAJA`)
- vigencia (`vigente`)

`prefill_from_dossier()` rellena expedientes nuevos — **no repregunta** información conocida.

## Vínculo expediente

`expediente_activo_id` apunta al expediente EIAAX en curso. Cada necesidad crea expediente pero absorbe conocimiento al dossier.
