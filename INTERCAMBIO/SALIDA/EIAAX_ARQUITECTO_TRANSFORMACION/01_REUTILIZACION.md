# 01 — Reutilización obligatoria

## Motores NO duplicados

| Capacidad existente | Uso en Arquitecto |
|---------------------|-------------------|
| **BP1 Evaluaciones** (`evaluacion_service`, `evaluacion_models`) | Orquestador principal — expediente, información adaptativa, hallazgos |
| **Diagnósticos 1220** | FK `diagnostic_id` preparada; importación futura de findings |
| **Oportunidades 1030** | Puente vía `crear_oportunidad_desde_hallazgo` (expediente) |
| **Línea base 1200 / Valoración 1210** | Referenciados en impacto expediente |
| **Knowledge 930** | `evidencia_ref` + fuente `conocimiento` en dossier |
| **Coordinator / LLM** | `ask_eiaax` en consola evaluación |
| **Centro de Control** | Patrón adapter pendiente (P1) |
| **Mi Trabajo / Operaciones** | Ejecución posterior a iniciativas (P1) |

## Archivos extendidos (no paralelos)

- `backend/app/services/transformacion_service.py` — orquesta `evaluacion_service`
- `backend/app/transformacion_models.py` — dossier y artefactos de transformación
- `frontend/src/pages/ArquitectoTransformacionPage.tsx` — shell progresivo
- Expediente EIAAX sigue en `/evaluaciones` — no reemplazado

## Evitado explícitamente

PIIAX, Fábrica Empleados IA completa, BPMN, gestor de proyectos, formulario universal fijo, motor económico, marketplace.
