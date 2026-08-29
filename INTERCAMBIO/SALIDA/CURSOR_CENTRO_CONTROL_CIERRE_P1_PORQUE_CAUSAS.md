# EMPLEADOS IA — Cierre P1-ID-01: Centro de Control «Por qué»

**Fecha:** 2026-08-29  
**Base:** `eef42759f9b16d1792d813213ed9f4d36c8bc658` (ensayo Fase 1)  
**Rama:** `cursor/centro-control-porque-causas-p1`

---

## Hallazgo cerrado

**P1-ID-01:** El Centro de Control no exponía suficientemente POR QUÉ, causas, evidencia y certeza.

**Solución:** Reutilizar motor 1220 vía `build_executive_explanations()` y adaptador `DiagnosticoExplicacionAdapter`, expuesto en `GET /api/centro-control/resumen-ejecutivo` como clave `explicacion`.

---

## Commits

| Pieza | SHA |
|-------|-----|
| BACKEND | `b86ed25ebcfc8a4f91e82d149e32868297a12f86` |
| FRONTEND | `0f735ea3fe9bac85cfbbe9791abde823e0b2e6d8` |
| PRUEBAS | `73c9d4307406663fa91262e34772f6049775c9e1` |

---

## Diseño técnico

### Backend (1220 → CC)

- `build_executive_explanations()` en `diagnostic_service.py`
- Mapeo certeza: `CONFIRMADA` → CAUSA DEMOSTRADA, `PROBABLE` → CAUSA PROBABLE, `HIPOTESIS` → HIPÓTESIS
- Correlaciones con `es_causal=False` → tipo `CORRELACION`, etiqueta «CORRELACIÓN (no causalidad)»
- `tipo_contenido`: HECHO / INFERENCIA / RECOMENDACIÓN
- `fuente_ambito`: INTERNA / EXTERNA / MIXTA (sin duplicar 1240)
- Evidencia estructurada: fuente, identificador, correlation_id, periodo, valor, comparación
- Degradación: try/except por adaptador → «NO DISPONIBLE» / «Diagnóstico no disponible»
- Filtros `proceso` y `estado` aplicados en adaptadores Diagnostico, Explicacion y Senales

### Frontend

- Sección compacta **¿Por qué está pasando?** en `CentroControlPage.tsx`
- Etiquetas accesibles (texto + tooltip, no solo color)
- Drill-down solo a `/diagnosticos/{id}` cuando existe enlace válido

### Sin alcance prohibido

- Sin endpoint nuevo
- Sin migración Alembic
- Sin segundo dashboard
- Sin motor diagnóstico duplicado
- Sin narrativa IA libre

---

## P1-ID-02 — PREPARADO PARCIALMENTE (no cerrado globalmente)

Superficies que ya distinguen HECHO / INFERENCIA / RECOMENDACIÓN en CC:

- Sección `explicacion` del Centro de Control

Superficies pendientes para adopción global tras bloque 1290:

- Atención requerida (alertas ejecutivas)
- Oportunidades y cadena ejecutiva
- Señales internas / Inteligencia externa (resúmenes)
- Notificaciones y recomendaciones operativas
- Paneles FinOps / valor (interpretaciones económicas)

---

## Pruebas

### Focal P1 (16)

```bash
BOOTSTRAP_ADMIN_PASSWORD='Admin2026*' PYTHONPATH=backend:. pytest tests/test_centro_control_porque_p1.py -q
```

**16 passed**

### Regresión SQLite

**898 passed, 2 skipped, 0 failed**

### Frontend

`npm run build` → **PASS**

### PostgreSQL

**PENDIENTE POR ENTORNO**

### Alembic

HEAD: `1380a1b2c3d4e` | HEADS: **1**

---

## Matriz de verificación

| Criterio | Resultado |
|----------|-----------|
| QUÉ | PASS |
| POR QUÉ | PASS |
| CAUSA DEMOSTRADA | PASS |
| CAUSA PROBABLE | PASS |
| HIPÓTESIS | PASS |
| EVIDENCIA | PASS |
| CORRELACIÓN ≠ CAUSALIDAD | PASS |
| HECHO/INFERENCIA EN CC | PASS |
| P1-ID-01 | **CERRADO** |
| P1-ID-02 | **PREPARADO PARCIALMENTE** |
| FILTRO PROCESO | PASS |
| FILTRO ESTADO | PASS |
| MULTIEMPRESA | PASS |
| RBAC | PASS |
| SUPERADMIN | PASS |
| DEGRADACIÓN | PASS |
| 1230 / 1240 / 1300–1380 | PASS (preservados) |
| P0 / P1 / P2 | 0 / 0 / 0 |

**VEREDICTO:** **APTO PARA PORTAR**

---

## Portabilidad

Cherry-pick recomendado sobre ensayo Fase 1 o convergencia:

1. `b86ed25ebcfc8a4f91e82d149e32868297a12f86`
2. `0f735ea3fe9bac85cfbbe9791abde823e0b2e6d8`
3. `73c9d4307406663fa91262e34772f6049775c9e1`
