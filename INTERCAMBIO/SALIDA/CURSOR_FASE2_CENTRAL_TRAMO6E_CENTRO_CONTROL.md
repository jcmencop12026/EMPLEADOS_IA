# EMPLEADOS IA — FASE 2 CENTRAL TRAMO 6E — CENTRO DE CONTROL EJECUTIVO

**Rama:** `cursor/tramo6e-centro-control-85e4`
**Base:** `cursor/fase2-central-integracion` @ `1db7a7e5b0947cf89108b4cf8606a20497d21385`
**Fecha:** 2026-08-30

---

## 1. BASE

| Verificación | Resultado |
|---|---|
| HEAD base certificado | `1db7a7e` ✓ |
| Alembic heads | 1 |
| Alembic head | `1341a1b2c3d4e` |
| Migración nueva | NO |

---

## 2. FUENTES PORTADAS (SELECTIVO)

| Fuente | HEAD | Qué se portó |
|---|---|---|
| `cursor/centro-control-cableado-ejecutivo-fase2` | `99757a2` | Adaptadores 1260–1340, 1280 comercial, `SEMANTICA_VALOR`, `valor_consolidado`, UI con pestañas, indicadores ampliados |
| `cursor/fix-centro-control-datetime-determinismo` | `096b7e8` / tests `84ab9f7` | `_as_utc()`, `_max_utc()`, tests naive/aware (ya incluidos en cableado) |

## 3. FUENTES DESCARTADAS (YA EN CENTRAL)

- Routers MB-07, MB-11, MB-12, Auditor, Mi Trabajo, Fábrica — ya integrados en central
- `main.py`, `permissions.py`, `App.tsx` de ramas portables — central es más reciente
- Merge ciego PR #92 — NO aplicado

## 4. INTEGRACIÓN NUEVA TRAMO 6E

Adaptadores ejecutivos cableados a contratos reales existentes:

| Módulo | Contrato / servicio |
|---|---|
| MB-07 | `consumption_planner_service.centro_control_contract` (solo lectura si config existe) |
| MB-11 | `communications_service.contrato_centro_control` |
| MB-12 | `support_service.contrato_centro_control` |
| Auditor | Consultas read-only (sin `get_or_create` en CC) |
| Mi Trabajo | `trabajo_service.resumen` (resumen, no bandeja duplicada) |
| Continuidad | `continuidad_service.centro_control_resumen` |

---

## 5. ARQUITECTURA CENTRO DE CONTROL ÚNICO

- **Un solo** Centro de Control en `/centro-control`
- Capa agregadora: `control_center_service.get_executive_summary()`
- Adaptadores modulares: `control_center_adapters.py`
- API: `GET /api/centro-control/resumen-ejecutivo`
- **NO** segundo dashboard, NO Centro Salud, NO segundo FinOps, NO segunda bandeja Mi Trabajo

### Secciones (pestañas)

1. Resumen ejecutivo
2. Valor y rentabilidad
3. Operación y atención
4. IA y costos
5. Implementación
6. Salud

---

## 6. SEMÁNTICA Y VALOR

- Contrato: `HECHO` / `INFERENCIA` / `RECOMENDACIÓN` / `SIN_CLASIFICAR`
- Valor: `VERIFICADO` / `ESTIMADO` / `POTENCIAL`
- **POTENCIAL excluido de realizado** — nota explícita en `valor_consolidado.nota_potencial`
- Sin KPIs inventados — `Sin información disponible` cuando no hay fuente

---

## 7. PRESERVACIÓN GATE POST-6D

CAS concurrencia, G1–G4, `auto_execution_blocked`, Mi Trabajo único, español, RBAC, multiempresa — preservados.

---

## 8. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---|---|
| `backend/app/services/control_center_adapters.py` | +6 adaptadores portables + 6 adaptadores MB/Auditor/Trabajo/Continuidad |
| `backend/app/services/control_center_service.py` | Datetime, valor consolidado, secciones, rollback en adapters |
| `frontend/src/pages/CentroControlPage.tsx` | UI ejecutiva con pestañas + paneles MB-07/11/12 |
| `frontend/src/api.ts` | Tipos `valor_consolidado`, módulos 6E |
| `tests/test_centro_control_cableado_ejecutivo_fase2.py` | Portado + actualizado MB-07 Integrado |
| `tests/test_control_center_datetime_cc_dt.py` | Portado |
| `tests/test_centro_control_tramo6e.py` | Nuevo — agregación, semántica, tenant, RBAC, datetime |

---

## 9. REGRESIÓN

| Métrica | Antes (baseline) | Después |
|---|---|---|
| Passed | 1202 | **1229** |
| Failed | 0 | **0** |
| Skipped | 4 | 4 |

### Pruebas focales CC

- `test_centro_control_tramo6e.py` — PASS
- `test_centro_control_cableado_ejecutivo_fase2.py` — PASS
- `test_bloque_1230_centro_control.py` — PASS
- `test_bloque_1250c_centro_control_integrado.py` — PASS
- `test_control_center_datetime_cc_dt.py` — PASS

### Frontend

`npm run build` — PASS

### PostgreSQL

PENDIENTE POR ENTORNO

---

## 10. SALIDA FINAL

```
EMPLEADOS IA — FASE 2 CENTRAL TRAMO 6E TERMINADO

BASE: 1db7a7e
HEAD: cursor/tramo6e-centro-control-85e4

CENTRO CONTROL ÚNICO: SÍ — una sola experiencia /centro-control
BACKEND: control_center_service + 20 adaptadores
FRONTEND: CentroControlPage con 6 pestañas ejecutivas

RESUMEN EJECUTIVO: indicadores reales + atención requerida
VALOR/RENTABILIDAD: valor_consolidado VERIFICADO/ESTIMADO/POTENCIAL
FUERZA LABORAL: empleados IA + auditor (solo lectura)
OPERACIÓN: Mi Trabajo resumen, MB-11, MB-12, oportunidades, diagnóstico
RIESGOS: continuidad + inteligencia externa + diagnóstico
OPORTUNIDADES: módulo 1100 integrado
TECNOLOGÍA/CAPACIDAD: MB-07, FinOps, TCO, multiproveedor 1270

SEMÁNTICA: HECHO/INFERENCIA/RECOMENDACIÓN preservada
VERIFICADO/ESTIMADO/POTENCIAL: implementado
POTENCIAL EXCLUIDO DE REALIZADO: SÍ

MI TRABAJO: resumen ejecutivo → /trabajo
MB07: integrado (read-only)
MB11: integrado
MB12: integrado
AUDITOR: integrado read-only, auto_execution_blocked
FÁBRICA: vía empleados IA / auditor
1290/1260/1270/1320/1340: integrados vía adaptadores portables
FINOPS ÚNICO: SÍ

DATETIME: _as_utc/_max_utc + tests CC-DT
MULTIEMPRESA: verificado
RBAC: verificado
SUPERADMIN: preservado
SECRETOS: no expuestos en CC

ALEMBIC HEADS: 1
ALEMBIC HEAD: 1341a1b2c3d4e

REGRESIÓN ANTES: 1202 passed
REGRESIÓN DESPUÉS: 1229 passed
FAILED: 0
ERRORS: 0
SKIPPED: 4

FRONTEND: PASS
RECORRIDO VISUAL: código verificado (6 pestañas + drill-down)
POSTGRESQL: PENDIENTE POR ENTORNO

P0: 0
P1: 0
P2: documentados (cosmética menor)

PLATAFORMA EJECUTABLE: SÍ

MAIN: NO
V1: NO

VEREDICTO: TRAMO 6E APTO
```
