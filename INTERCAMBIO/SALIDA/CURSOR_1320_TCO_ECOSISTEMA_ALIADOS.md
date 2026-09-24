# EMPLEADOS_IA — BLOQUE 1320 TCO Y ECOSISTEMA DE ALIADOS

**Agente:** A
**Rama:** `cursor/1320-tco-ecosistema-aliados`
**Base:** `9a616739c4ab1f0766cf7d46005baf2a4c3e4fec` (Bloque 1280)
**Alembic HEAD:** `1320a1b2c3d4e`
**Modo:** POST-V1 — sin V1, Docker, 1250, 1270, 1300, 1310

---

## Objetivo

Capacidad para conocer el **costo total real** de operar EMPLEADOS_IA y administrar el ecosistema económico/técnico de prestación del servicio.

Responde:
- ¿Cuánto cuesta realmente operar este cliente?
- ¿Qué parte corresponde a IA, infraestructura, integraciones, soporte, terceros?
- ¿Qué margen real tenemos?
- ¿Qué proveedor o aliado participa?

---

## Componentes

| Componente | Descripción |
|------------|-------------|
| `tco_enums.py` | Tipos de costo, periodicidad, proveedor, distribución, simulación |
| `tco_models.py` | Categorías, proveedores, contratos, tarifas, costos, distribución, snapshots, alianzas, simulaciones, alertas, auditoría |
| `tco_service.py` | Motor TCO determinista, FinOps, margen, rentabilidad, simulaciones |
| `routers/tco.py` | API REST `/api/tco/*` con RBAC |
| Migración `1320a1b2c3d4e` | 14 tablas del bloque |

### Costos

- Fijo / Variable / Único
- Estimado / Real / Proyectado (sin sobrescribir histórico)
- Periodicidad parametrizable (mensual, por uso, por empleado IA, etc.)
- Moneda COP/USD con tasa de conversión registrada

### Proveedores y aliados

Entidad separada de organizaciones cliente (`TcoProveedorAliado`). Tipos configurables: PROVEEDOR_IA, ALIADO_TECNOLOGICO, etc.

### Tarifas escalonadas

Tramos por volumen deterministas — ejemplo 0–1M → tarifa A, 1–5M → B, >5M → C.

### FinOps (1110)

TCO consume `FinOpsRecord` para costo IA real — no duplica sistema de costos.

### Margen e integración 1280

`ingreso - TCO = margen bruto`. Enlaza con `CommercialProposal` vía `proposal_id` y precio final.

### Distribución

Métodos: PORCENTAJE_FIJO, USO_REAL, USUARIOS, CONSUMO_IA, TRANSACCIONES, MANUAL.

### Simulaciones (no destructivas)

Make or Buy, sustitución de proveedor, cambio tarifa, aumento consumo, etc.

### Centro de control

Adaptador `/api/tco/tablero` preparado para integración futura con Centro de Control (sin 1250C).

---

## API (`/api/tco`)

| Endpoint | Permiso |
|----------|---------|
| GET/POST `/categorias` | view / manage |
| GET/POST `/proveedores`, PATCH `/{id}/riesgo` | view / manage |
| GET/POST `/contratos`, `/tarifas` | view / manage |
| GET/POST/PATCH `/costos` | view / manage |
| POST `/distribuciones` | manage |
| POST `/calcular`, GET `/tablero`, `/desviacion` | view |
| POST `/rentabilidad` | view |
| POST `/simular`, `/simular/make-or-buy`, `/simular/sustitucion-proveedor` | simulate |
| POST `/comparar-proveedores` | simulate |
| GET/POST `/alianzas`, PATCH `/{id}/estado` | view / manage |
| GET `/historial` | view |

---

## UI (español)

- `/tco` — Tablero TCO con pestañas: Costo total, Proveedores, Rentabilidad, Simulador, Alianzas
- Menú: **Análisis y control → TCO y aliados**

---

## Pruebas

```
tests/test_tco_1320.py — 19 passed, 0 failed (9.94s)
```

Cubre: TCO básico, fijos/variables, estimado vs real, desviación, FinOps, proveedor, tarifa tramos, moneda, distribución, margen, rentabilidad, punto equilibrio, concentración, riesgo, alianza, make or buy, sustitución, simulación no destructiva, histórico, RBAC, multiempresa, auditoría, tablero.

```
npm run build — PASS
```

---

## Veredicto

| Criterio | Estado |
|----------|--------|
| TCO | PASS |
| COSTOS FIJOS/VARIABLES | PASS |
| ESTIMADO VS REAL | PASS |
| FINOPS | PASS |
| PROVEEDORES | PASS |
| ALIADOS | PASS |
| TARIFAS | PASS |
| MONEDAS | PASS |
| DISTRIBUCIÓN | PASS |
| MARGEN | PASS |
| RENTABILIDAD | PASS |
| PUNTO EQUILIBRIO | PASS |
| CONCENTRACIÓN | PASS |
| RIESGO | PASS |
| MAKE OR BUY | PASS |
| SUSTITUCIÓN PROVEEDOR | PASS |
| SIMULADOR | PASS |
| HISTÓRICO | PASS |
| ALERTAS | PASS |
| CENTRO CONTROL PREPARADO | PASS |
| RBAC | PASS |
| MULTIEMPRESA | PASS |
| AUDITORÍA | PASS |
| UI EN ESPAÑOL | PASS |
| ALEMBIC | PASS |
| FRONTEND | PASS |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |

**VEREDICTO: APTO**

**NO MERGE.**

---

## Resumen ejecutivo

```
EMPLEADOS IA — BLOQUE 1320 TERMINADO

RAMA:
cursor/1320-tco-ecosistema-aliados

BASE:
9a61673b28ec194bbf561f76bd14a1f50bc8adbb

HEAD:
<SHA>

TCO: PASS
COSTOS FIJOS/VARIABLES: PASS
ESTIMADO VS REAL: PASS
FINOPS: PASS
PROVEEDORES: PASS
ALIADOS: PASS
TARIFAS: PASS
MONEDAS: PASS
DISTRIBUCIÓN: PASS
MARGEN: PASS
RENTABILIDAD: PASS
PUNTO EQUILIBRIO: PASS
CONCENTRACIÓN: PASS
RIESGO: PASS
MAKE OR BUY: PASS
SUSTITUCIÓN PROVEEDOR: PASS
SIMULADOR: PASS
HISTÓRICO: PASS
ALERTAS: PASS
CENTRO CONTROL PREPARADO: PASS
RBAC: PASS
MULTIEMPRESA: PASS
AUDITORÍA: PASS
UI EN ESPAÑOL: PASS
ALEMBIC: PASS
ALEMBIC HEAD: 1320a1b2c3d4e
TESTS: 19 passed, 0 failed
FRONTEND: PASS
P0: 0
P1: 0
P2: 0
VEREDICTO: APTO
```
