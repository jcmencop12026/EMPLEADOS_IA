# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 1

**Tipo:** Integración incremental controlada
**Fecha:** 2026-08-29
**Agente:** GENERAL
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y genealogía

| Campo | Valor |
|-------|-------|
| **BASE certificada** | `041209f4acabd595b5249c979a7e61031f598048` |
| **HEAD Tramo 1** | `f6cde2cc2c603e68ff12a6bd4d4aac37038fcbf3` |
| **merge-base** | Correcto — BASE es ancestro directo |
| **main** | NO modificado |
| **V1** | NO modificada |
| **Alembic** | 1 cabeza — `1380a1b2c3d4e` (sin migraciones nuevas) |

---

## 1. Componentes integrados

### A. Corrección 1220 (deuda preexistente)

| Commit origen | SHA portado | Archivos |
|---------------|-------------|----------|
| FIX funcional | `84526d8` ← `8f09f6d` | `diagnostic_service.py` — severidad alineada con impacto sin umbral |
| TEST/fixture | `08c6777` ← `e28650f` | `test_diagnostico_transversal_1220.py` — tenant aislado test_08 |

### B. Centro de Control + 1240 + P1-ID-01

Referencia: `cursor/centro-control-porque-causas-p1` @ `700269b` — **cherry-pick selectivo** (sin merge bruto, sin docs).

| Orden | SHA portado | Origen | Contenido |
|-------|-------------|--------|-----------|
| 1 | `4aa1e7f` | `1028187` | Integración 1240 en adapters + service CC |
| 2 | `e107d07` | `aaf8881` | Gaps UI: finops_extendido, llm, auditoría, actividad |
| 3 | `ed40057` | `ec44052` | Tests 1240 + gaps UI + RBAC |
| 4 | `9b63416` | `b86ed25` | P1-ID-01 backend: QUÉ/POR QUÉ, causas, certeza, evidencia |
| 5 | `1aa6022` | `0f735ea` | P1-ID-01 UI: sección «¿Por qué está pasando?» |
| 6 | `f6cde2c` | `73c9d43` | Tests P1-ID-01: causas, certeza, filtros proceso/estado |

**NO incorporado en Tramo 1:**

- P1-ID-02 (semántica HECHO/INFERENCIA/RECOMENDACIÓN — agente A activo)
- Wiring 1330 (agente B)
- Cadena comercial (agente C)
- ID03 línea base (agente D en auditoría)
- Bloques 1260–1340 (excepto extensiones 1230/1240 certificadas)

**Regla causalidad preservada:** `es_causal=False`, nota «correlación ≠ causalidad», certezas CAUSA DEMOSTRADA / CAUSA PROBABLE / HIPÓTESIS.

---

## 2. Validación ejecutada

| Gate | Resultado |
|------|-----------|
| test_08 aislado × 5 | **5/5 PASS** |
| Archivo 1220 | **15/15 PASS** |
| CC 1240 + gaps + P1-ID-01 | **68 passed** (focales CC) |
| Núcleo inteligencia (1120→1230) | **114 passed** |
| RBAC + multitenant + SUPERADMIN + V1 | **109 passed, 2 skipped** |
| Regresión completa backend | **902 passed, 4 skipped, 0 failed** |
| Frontend `npm run build` | **PASS** |
| Alembic heads | **1** — `1380a1b2c3d4e` |
| PostgreSQL | **PENDIENTE POR ENTORNO** |
| Backend arranque `/health` | **200 OK** |

| Severidad | Conteo |
|-----------|--------|
| P0 | **0** |
| P1 | **0** |
| P2 | **0** |

---

## 3. Plataforma ejecutable — instrucciones de arranque

### 3.1 Requisitos

- Python 3.11+ (3.12 verificado)
- Node.js LTS + npm
- Puerto **8010** (API) y **5180** (web) libres

### 3.2 Primera instalación

**Windows (recomendado en `D:\EMPLEADOS_IA`):**

```bat
CREAR_ENTORNO.bat
```

**Linux / macOS / Cloud Agent:**

```bash
cd /ruta/a/EMPLEADOS_IA
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
mkdir -p data
cd backend && alembic upgrade head && cd ..
cd frontend && npm install && cd ..
```

### 3.3 Arranque diario

**Windows:**

```bat
ARRANCAR.bat
```

**Manual (dos terminales):**

```bash
# Terminal 1 — API
cd backend
source ../.venv/bin/activate   # Windows: ..\.venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

# Terminal 2 — Web
cd frontend
npm run dev
```

### 3.4 URLs y acceso

| Recurso | URL |
|---------|-----|
| **Frontend** | http://127.0.0.1:5180 |
| **API** | http://127.0.0.1:8010 |
| **Health** | http://127.0.0.1:8010/health |
| **Login** | http://127.0.0.1:5180/login |

**Usuario de prueba (bootstrap desarrollo, ya existente en seed):**

- Usuario: `admin`
- Contraseña: la configurada en desarrollo local (`Admin2026*` según README del proyecto — **solo entorno dev SQLite**)
- Rol: `superadmin` — acceso global a Centro de Control y módulos Tramo 1

> No se han creado credenciales nuevas ni modificado autenticación.

### 3.5 Base de datos

- **Desarrollo:** SQLite en `data/` (creada automáticamente en primer arranque tras `alembic upgrade head`)
- **HEAD migraciones:** `1380a1b2c3d4e`

---

## 4. Recorrido visual de revisión Tramo 1

| # | Ruta | Qué debe verse | Capacidad demostrada |
|---|------|----------------|----------------------|
| 1 | `/login` | Formulario en español, acceso con `admin` | Auth V1 preservada |
| 2 | `/` | «Centro de Control ejecutivo», selector periodo (MTD/7d/30d) | 1230 hub único |
| 3 | `/` → Resumen ejecutivo | Tarjetas KPI con enlaces (oportunidades, señales, etc.) | Agregación adapters |
| 4 | `/` → Atención requerida | Tabla priorizada o mensaje vacío controlado | Filtros estado PASS |
| 5 | `/` → **¿Por qué está pasando?** | Tabla con columnas Situación (QUÉ), Causa/acción (POR QUÉ), Certeza, Evidencia; nota causalidad | **P1-ID-01** |
| 6 | Misma sección | Tags `HECHO` / `INTERPRETACION` / `HIPOTESIS`; certezas CAUSA DEMOSTRADA / PROBABLE / HIPÓTESIS | Cadena 1220→CC sin afirmar causalidad |
| 7 | `/` → Diagnóstico (panel) | Conteos hallazgos/riesgos/oportunidades | 1220 integrado |
| 8 | `/diagnosticos` | Listado y detalle diagnósticos generados | 1220 operativo + fix test_08 |
| 9 | `/inteligencia-externa` | Fuentes, señales externas | **1240** preservado |
| 10 | `/` → Inteligencia externa (panel) | Fuentes activas, riesgos, recientes con enlaces | **1240 en CC** (Tramo 1) |
| 11 | `/` → Costos y FinOps + FinOps extendido | Costo, ROI, consumos, alertas presupuesto | finops_extendido gap cerrado |
| 12 | `/` → IA y proveedores | Tabla proveedores LLM | Panel llm gap cerrado |
| 13 | `/` → Actividad reciente | Eventos operativos con enlaces | actividad_reciente gap cerrado |
| 14 | `/` → Auditoría (si visible) | Eventos recientes de auditoría | auditoria_reciente gap cerrado |
| 15 | `/costos-valor` | Dashboard FinOps detallado | 1110 preservado |

**Datos para ver P1-ID-01 con contenido:** generar al menos un diagnóstico (`Diagnósticos` → generar) tras ingerir señales (`/senales` → ingesta). Sin datos, la sección muestra estado controlado «Diagnóstico no disponible» (degradación segura PASS).

---

## 5. Siguiente mecánica (Tramo 2+)

Integrar piezas certificadas de A/B/C/D cuando estén listas, manteniendo:

- Rama ejecutable
- 0 P0 / 0 P1 no controlados
- 1 cabeza Alembic
- Tests acumulativos + frontend compilando

---

## SALIDA FINAL

```
EMPLEADOS IA — FASE 2 CENTRAL TRAMO 1 TERMINADO

BASE:
041209f4acabd595b5249c979a7e61031f598048

RAMA:
cursor/fase2-central-integracion

HEAD:
f6cde2cc2c603e68ff12a6bd4d4aac37038fcbf3

1220 FIX:
PASS

P1-ID-01:
PASS

CENTRO CONTROL:
PASS

1240:
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
902 passed, 4 skipped, 0 failed

FRONTEND:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

P0:
0

P1:
0

P2:
0

PLATAFORMA EJECUTABLE:
SI

RECORRIDO VISUAL PREPARADO:
SI

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE MAIN:
NO

VEREDICTO:
TRAMO 1 APTO
```

---

*Rama lista para revisión visual humana y siguientes tramos incrementales.*
