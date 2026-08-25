# OPERACIONES-940 — Prioridad y Vencimiento Persistentes

**Estado:** `OPERACIONES-940 PRIORIDAD/VENCIMIENTO LISTO PARA REAUDITORÍA`  
**Rama:** `cursor/operations-center-940-12b6`  
**HEAD inicial:** `b73c396`  
**HEAD final:** `a8a1c2b`  
**NO MERGE**

---

## Commits

| SHA | Mensaje |
|-----|---------|
| `a8a1c2b` | `feat(940): migración Alembic prioridad/vencimiento WorkPlan` |
| `13a91c7` | `feat(940): prioridad y vencimiento persistentes en WorkPlan` |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/enums.py` | `WorkPlanPriority` (BAJA/MEDIA/ALTA/CRITICA) |
| `backend/app/orchestration_models.py` | columnas `prioridad`, `vencimiento` |
| `backend/alembic/versions/940a1b2c3d4e_workplan_priority_due_940.py` | migración |
| `backend/app/services/operations_labels.py` | etiquetas, `DUE_SOON_HOURS=48`, cálculo vencimiento |
| `backend/app/services/operations_center.py` | persistencia, filtros, summary overdue/due_soon |
| `backend/app/schemas_operations.py` | campos API + `due_soon` en summary |
| `backend/app/routers/operations.py` | filtros `vencimiento_filtro`, `orden`; PATCH vencimiento |
| `frontend/src/api.ts` | tipos + `updateOperation()` |
| `frontend/src/pages/OperationsHubPage.tsx` | columnas, filtros, indicador due_soon |
| `frontend/src/pages/OperationDetailPage.tsx` | edición prioridad/vencimiento |
| `frontend/src/styles.css` | badges prioridad y vencimiento |
| `tests/test_operations_940.py` | +12 regresiones |

---

## Modelo

- `prioridad`: `VARCHAR(20)`, default `MEDIA`, valores `BAJA|Media|ALTA|CRITICA`
- `vencimiento`: `DateTime(timezone=True)`, nullable
- Registros existentes: default `MEDIA`, sin vencimiento

## API

- `GET /api/operations/summary` → incluye `due_soon`
- `GET /api/operations/center` → filtros `prioridad`, `vencimiento_filtro`, `orden`, `bucket=overdue|due_soon`
- `PATCH /api/operations/center/{id}` → `prioridad`, `vencimiento`, `sin_vencimiento`
- Respuesta incluye `prioridad_codigo`, `vencimiento_estado`, `vencimiento_codigo`

## Estados temporales (backend)

| Código | Condición |
|--------|-----------|
| `sin_vencimiento` | sin fecha |
| `vencido` | vencimiento < now, plan abierto |
| `vence_hoy` | mismo día calendario |
| `proximo` | dentro de 48h (`DUE_SOON_HOURS`) |
| `vigente` | futuro > 48h o plan terminal |

## UI (español)

- Grilla: columnas Prioridad y Vencimiento con badges
- Filtros: estado, prioridad, vencimiento, orden
- Indicadores: Pendientes, En ejecución, Requieren aprobación, Próximos a vencer, Vencidos, Con error
- Detalle: edición prioridad + datetime-local vencimiento + checkbox sin vencimiento

---

## Tests

```bash
PYTHONPATH=backend:. pytest tests/test_operations_940.py -q
```

**22 passed**

Cobertura nueva: default Media, update prioridad, inválida 400, filtro, vencimiento futuro/pasado, due_soon, clear, viewer 403, cross-tenant 404, migración preserva MEDIA.

## Migración

```bash
DATABASE_URL=sqlite:////tmp/ops940_mig.db PYTHONPATH=. alembic upgrade head
DATABASE_URL=sqlite:////tmp/ops940_mig.db PYTHONPATH=. alembic downgrade 5b2eb2437398
DATABASE_URL=sqlite:////tmp/ops940_mig.db PYTHONPATH=. alembic upgrade head
```

**PASS** (upgrade → downgrade → upgrade)

## Suite completa / build

| Comando | Resultado |
|---------|-----------|
| `pytest` (rama 940) | **68 passed** |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |

## Pendientes reales

- Integrar con PostgreSQL en CI cuando rama 940 ejecute workflow QA
- Ordenamiento SQL nativo por prioridad (actual: sort en memoria para `orden=prioridad`)
- FINOPS, SALUD→WorkPlan: **fuera de alcance** (otro agente)

---

**OPERACIONES-940 PRIORIDAD/VENCIMIENTO LISTO PARA REAUDITORÍA — NO MERGE**
