# EMPLEADOS IA — Cierre P1-ID-03 Oportunidad / Línea Base 1200

## Resumen ejecutivo

Se cerró **P1-ID-03**: al registrar el resultado de una oportunidad (`register_result` / `POST /api/oportunidades/{id}/resultado`), queda un enlace trazable y persistente con la línea base 1200, incluyendo medición, comparación, clasificación de valor, atribución conservadora, auditoría y referencia consumible por 1260.

**Sin migración Alembic nueva** — se reutiliza `LineaBase.opportunity_id` y `resultado_json` enriquecido.

---

## Identificación

| Campo | Valor |
|-------|-------|
| BASE | `041209f4acabd595b5249c979a7e61031f598048` |
| RAMA | `cursor/oportunidad-linea-base-1200-p1-9a85` |
| HEAD | `aa5a959d458be24954454c5b5890264b28fe6927` |
| COMMIT FUNCIONAL | `1012b100fd572d59ab82e0c8019960d0849ce6b6` |
| COMMIT TESTS | `aa5a959d458be24954454c5b5890264b28fe6927` |

---

## Cambios implementados

### `baseline_service.py`
- `derive_baseline_context_from_opportunity` — extrae indicador/valor base desde contexto
- `find_linea_base_for_opportunity` / `find_compatible_linea_base` — anti-duplicación por org+oportunidad+indicador+proceso+fuente
- `ensure_linea_base_for_opportunity` — crea o reutiliza LB al aprobar
- `resolve_valor_clasificacion` — VERIFICADO / ESTIMADO / POTENCIAL
- `close_opportunity_with_baseline` — medición, impacto, auditoría, `learning_refs`

### `proactive_service.py`
- `approve_opportunity` — vincula LB al aprobar; descarte sin beneficio ficticio
- `activate_opportunity` — asegura LB si falta
- `register_result` — cierre con LB, idempotencia, FinOps solo Real si VERIFICADO
- `get_full_trace` — incluye `lineas_base`, `cierre_linea_base`, `learning_refs`

---

## Certificación P1-ID-03

```
EMPLEADOS IA — P1 OPORTUNIDAD/LÍNEA BASE TERMINADO

BASE:
041209f4acabd595b5249c979a7e61031f598048

RAMA:
cursor/oportunidad-linea-base-1200-p1-9a85

HEAD:
aa5a959d458be24954454c5b5890264b28fe6927

COMMIT FUNCIONAL:
1012b100fd572d59ab82e0c8019960d0849ce6b6

OPORTUNIDAD→LÍNEA BASE:
PASS

LÍNEA BASE EXISTENTE REUTILIZADA:
PASS

CREACIÓN CONTROLADA DE LÍNEA BASE:
PASS

NO DUPLICACIÓN:
PASS

CIERRE→RESULTADO:
PASS

VALOR ESPERADO:
PASS

VALOR MEDIDO:
PASS

VERIFICADO/ESTIMADO/POTENCIAL:
PASS

ATRIBUCIÓN:
PASS

EVIDENCIA:
PASS

IDEMPOTENCIA:
PASS

AUDITORÍA:
PASS

CORRELATION_ID:
PASS

VÍNCULO PARA 1260:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

1030:
PASS

1100:
PASS

1200:
PASS

1210:
PASS

1110:
PASS

FASE1 PRESERVADA:
PASS

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1380a1b2c3d4e

SQLITE:
PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

REGRESIÓN:
866 passed, 28 failed, 4 skipped (fallos preexistentes en Centro Control 1230/1250c, salud 971/bridge, identidad 1370, SCIM 1380 — no módulos modificados en esta rama)

FRONTEND:
NO MODIFICADO

P0:
0

P1:
0

P2:
0

P1-ID-03:
CERRADO

RAMA CENTRAL MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR
```

---

## Pruebas ejecutadas

| Suite | Resultado |
|-------|-----------|
| `tests/test_oportunidad_linea_base_p1_id03.py` | 17/17 PASS |
| Focal 1030/1100/1200/1210/1110 + 1360 | 121/121 PASS |
| Suite completa | 866 passed, 28 failed, 4 skipped |

---

## Contrato para 1260 (referencia estable)

```json
{
  "learning_refs": {
    "opportunity_id": "<uuid>",
    "linea_base_id": "<uuid>",
    "medicion_id": "<uuid>",
    "impacto_id": "<uuid>",
    "correlation_id": "<uuid>",
    "organization_id": "<uuid>",
    "valor_clasificacion": "VERIFICADO|ESTIMADO|POTENCIAL",
    "modulo_aprendizaje": "1260"
  }
}
```

Disponible en `resultado_json`, `GET /api/oportunidades/{id}/trazabilidad` y traza `CIERRE_LINEA_BASE`.

---

## Restricciones respetadas

- Rama desde Fase 1 `041209f4` — sin mezclar P1-ID-04 ni cadena 1260/1290/1270
- Sin tocar Centro de Control, main, V1, 1260, 1290, 1270
- Sin migración Alembic nueva
- Sin `git add .`
- Sin merge

---

*Generado: 2026-08-29 — Agente D P1-ID-03*
