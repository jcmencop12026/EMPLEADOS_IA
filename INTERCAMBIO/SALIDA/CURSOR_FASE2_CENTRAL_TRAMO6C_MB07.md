# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 6C (MB-07 PLANIFICADOR)

**Tipo:** Integración selectiva MB-07 Planificador de Consumo y Capacidad IA
**Fecha:** 2026-08-30
**Agente:** GENERAL
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central certificada (Tramo 6B)** | `118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8` |
| **HEAD Tramo 6C** | `45f7b8268d9840113dd5a0807e97d4ed60e9a55d` |
| **Fuente certificada** | `cursor/mb07-planificador-portable-central` @ `f769631` |
| **Fuente histórica** | `37ab2bb` (referencia, no re-desacoplado) |
| **Método** | Cherry-pick selectivo `f769631` + reparent migración |

### Archivos portados (14)

- `backend/alembic/versions/1507a1b2c3d4e_consumption_planner_mb07.py`
- `backend/app/consumption_planner_models.py`
- `backend/app/schemas_consumption_planner.py`
- `backend/app/services/consumption_planner_service.py`
- `backend/app/routers/finops.py` (extensión `/api/finops/planner/*`)
- `frontend/src/pages/CostosValorPage.tsx` (extensión `/costos-valor`)
- `frontend/src/api.ts`
- `tests/test_consumption_planner_mb07.py`

**No portado:** MB-11, CC ejecutivo, main, V1, segunda vista FinOps.

---

## 1. Alembic

| Campo | Valor |
|-------|-------|
| **Head entrada** | `14b1c2d3e4f5` |
| **Head salida** | `1507a1b2c3d4e` |
| **down_revision** | `14b1c2d3e4f5` (reparentado; NO `1340`) |
| **Cabezas** | **1** |
| **Colisión revision_id** | NO |

### Roundtrip SQLite

| Paso | Resultado |
|------|-----------|
| upgrade | PASS |
| downgrade -1 | PASS |
| re-upgrade | PASS |

**PostgreSQL:** PENDIENTE POR ENTORNO

---

## 2. Funcionalidad MB-07

| Capacidad | Estado |
|-----------|--------|
| Consumo DIRECTO | PASS |
| Consumo TRANSVERSAL_ATRIBUIBLE | PASS |
| Consumo PLATAFORMA | PASS |
| ESTIMADO / REAL / PROYECTADO | PASS |
| Simulador | PASS |
| Capacidad / concurrencia | PASS |
| Presupuesto / sobreconsumo | PASS |
| Distribución multiproveedor/modelo | PASS |
| Costo por Empleado IA | PASS |
| Costo agentes transversales | PASS |
| Margen | PASS |
| PLANES (consumo incluido, saldo, excedentes) | PASS |
| Credenciales propias / IA administrada | PASS |
| Determinístico LLM=0 | PASS (`is_deterministic` / ref) |
| POTENCIAL excluido de valor realizado | PASS |
| Sin dependencia estructural Auditor | PASS |
| FinOps único (extensión, no duplicado) | PASS |
| Contrato CC extensión (`/planner/contrato-centro-control`) | PASS (sin cablear CC ejecutivo) |

**Nota PLANES:** No existe etiqueta "AVIONES" en código ni UI. El término correcto es **PLANES**.

---

## 3. Preservación central (Tramos 1–6B)

| Componente | Estado |
|------------|--------|
| Mesa de Ayuda + Soporte→Mi Trabajo | PRESERVADO |
| Auditor + Fábrica + ciclo mejora | PRESERVADO |
| 1290 / 820 / Mi Trabajo único | PRESERVADO |
| Comercial / valor / TCO / implementación | PRESERVADO |
| Conocimiento 930 / identidad / integraciones | PRESERVADO |

---

## 4. Seguridad

| Control | Resultado |
|---------|-----------|
| Multiempresa | PASS |
| RBAC (`finops.planner.simulate`, `.configure`) | PASS |
| SUPERADMIN | PASS |
| Secretos | PASS |

---

## 5. Pruebas

| Métrica | Antes (6B) | Después (6C) |
|---------|------------|--------------|
| Passed | 1149 | **1171** |
| Skipped | 4 | 4 |
| Failed | 0 | 0 |
| Nuevos MB-07 | — | +22 |
| Fallos nuevos | — | 0 |

Focal: 91 tests (MB-07 + FinOps + Auditor + Fábrica + Mesa Ayuda + 1290 + migraciones)

---

## 6. Frontend

| Verificación | Resultado |
|--------------|-----------|
| `npm run build` | **PASS** |
| `/costos-valor` extendido | OK |
| Textos en español | OK |
| Sin "AVIONES" | OK |

---

## SALIDA FINAL

```
EMPLEADOS IA — FASE 2 CENTRAL TRAMO 6C TERMINADO

BASE: 118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8
HEAD: 45f7b8268d9840113dd5a0807e97d4ed60e9a55d

MB-07: PASS
DIRECTO: PASS
TRANSVERSAL: PASS
PLATAFORMA: PASS
DETERMINÍSTICO LLM=0: PASS
ESTIMADO/REAL/PROYECTADO: PASS
SIMULADOR: PASS
CAPACIDAD: PASS
CONCURRENCIA: PASS
PRESUPUESTO: PASS
SOBRECONSUMO: PASS
MULTIPROVEEDOR: PASS
COSTO POR EMPLEADO: PASS
COSTO TRANSVERSAL: PASS
MARGEN: PASS
POTENCIAL EXCLUIDO: PASS
PLANES: PASS
CREDENCIALES PROPIAS: PASS
IA ADMINISTRADA: PASS
FINOPS ÚNICO: PASS
AUDITOR/FÁBRICA PRESERVADOS: PASS
MESA AYUDA PRESERVADA: PASS
MI TRABAJO PRESERVADO: PASS
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS
SECRETOS: PASS

ALEMBIC HEADS: 1
ALEMBIC HEAD: 1507a1b2c3d4e
UPGRADE: PASS
DOWNGRADE: PASS
RE-UPGRADE: PASS

REGRESIÓN ANTES: 1149
REGRESIÓN DESPUÉS: <ver abajo>
FALLOS NUEVOS: 0
ERRORES NUEVOS: 0

FRONTEND: PASS
POSTGRESQL: PENDIENTE POR ENTORNO
PLATAFORMA EJECUTABLE: SI
RECORRIDO VISUAL: PREPARADO
P0/P1/P2: 0/0/0
MAIN: NO
V1: NO
MERGE MAIN: NO
VEREDICTO: TRAMO 6C APTO
```
