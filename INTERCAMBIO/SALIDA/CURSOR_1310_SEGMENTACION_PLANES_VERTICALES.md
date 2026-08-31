# CURSOR 1310 — Segmentación de clientes + planes verticales + paquetes comerciales

**Fecha:** 2026-08-29  
**Rama:** `cursor/1310-segmentacion-planes-verticales`  
**Base:** `cursor/1280-modelo-comercial-valor-85e4` @ `9a61673b28ec194bbf561f76bd14a1f50bc8adbb`  
**Estado:** **BLOQUE 1310 TERMINADO**  
**NO MERGE**

---

## Base de desarrollo

| Campo | Valor |
|-------|-------|
| Rama base | `cursor/1280-modelo-comercial-valor-85e4` |
| SHA base | `9a61673b28ec194bbf561f76bd14a1f50bc8adbb` |
| Razón | Extensión directa del modelo comercial 1280 sin convergencias 1250/1290/1300 |

---

## Arquitectura

```
CommercialSector (configurable)
CommercialSegment (dimensiones JSON)
OrganizationCommercialProfile
        │
        ▼
CommercialPlan (1280 extendido: version, segment, lifecycle)
        │
        ▼
CommercialPackage (límites + capacidades estructuradas)
        │
        ▼
Motor recomendación determinista → plan/paquete + explicación
        │
        ▼
CommercialProposal (1280 + snapshot catálogo/perfil)
        │
        ▼
Motor precio 1280 (_compute_economics) — sin segundo motor
```

Motor **transversal**: sectores (salud, software, logística, etc.) son datos configurables, no lógica rígida. IPS/EPS/RIPS no están en el núcleo.

---

## Entidades

| Entidad | Descripción |
|---------|-------------|
| `CommercialSector` | Vertical/sector parametrizable |
| `CommercialSegment` | Segmento con dimensiones configurables |
| `OrganizationCommercialProfile` | Perfil comercial por organización |
| `CommercialCapability` | Catálogo de capacidades estructuradas |
| `CommercialPackage` | Paquete comercial con límites y capacidades |
| `CommercialPackageVersion` | Snapshot versionado |
| `CommercialPlanVersion` | Snapshot versionado de plan |
| `CommercialDiscount` | Descuento con trazabilidad y piso económico |

---

## Motor de recomendación

Scoring determinista por perfil vs límites del paquete:

- **INSUFICIENTE**: necesidades superan límites o presupuesto
- **EXCESIVO**: uso < 40% de capacidades y hay alternativa más ajustada
- **ADECUADO**: encaje razonable

Evita recomendar sistemáticamente el plan más caro (prefiere ADECUADO).

---

## API (`/api/segmentacion`)

| Método | Ruta | Permiso |
|--------|------|---------|
| GET/POST | `/sectores` | view / manage |
| GET/POST | `/segmentos` | view / manage |
| GET/PUT | `/perfil` | view / manage |
| GET/POST | `/paquetes` | planes.view / manage |
| POST | `/paquetes/{id}/activar` | planes.manage |
| POST | `/paquetes/{id}/versionar` | planes.manage |
| POST | `/paquetes/personalizado` | planes.manage |
| POST | `/comparar` | planes.view |
| GET | `/recomendar` | planes.recommend |
| POST | `/escalamiento` | planes.recommend |
| POST | `/descuentos` | planes.approve_discount |
| POST | `/paquetes/{id}/precio` | planes.view (motor 1280) |
| POST | `/planes/{id}/versionar` | planes.manage |

---

## RBAC

| Permiso | Descripción |
|---------|-------------|
| `segmentacion.view` | Consultar sectores, segmentos, perfil |
| `segmentacion.manage` | Administrar segmentación y perfil |
| `planes.view` | Consultar paquetes y comparar |
| `planes.manage` | CRUD paquetes, versionado, personalizado |
| `planes.recommend` | Recomendación y escalamiento |
| `planes.approve_discount` | Aprobar descuentos |

---

## UI (español)

| Vista | Ruta |
|-------|------|
| Segmentación, perfil, paquetes, comparador, recomendación | `/comercial/segmentacion` |

---

## Migración Alembic

- **Revision:** `1310a1b2c3d4e`
- **Down:** `1280b2c3d4e5f`
- Cabeza única en esta rama

---

## Archivos principales

| Archivo | Cambio |
|---------|--------|
| `backend/app/segmentation_enums.py` | Enumeraciones 1310 |
| `backend/app/segmentation_models.py` | Modelos segmentación/paquetes |
| `backend/app/services/segmentation_service.py` | Motor recomendación, comparación, descuentos |
| `backend/app/schemas_segmentation.py` | Schemas API |
| `backend/app/routers/segmentacion.py` | Router REST |
| `backend/app/commercial_models.py` | Campos plan/propuesta extendidos |
| `backend/app/services/commercial_service.py` | Snapshot propuesta con paquete |
| `frontend/src/pages/SegmentacionPage.tsx` | UI segmentación |
| `tests/test_segmentacion_1310.py` | 13 pruebas focales |

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| `pytest tests/test_segmentacion_1310.py` | **13/13 PASS** |
| Regresión 1280 + migraciones | **37 passed** |
| `npm run build` | **PASS** |

---

## Hallazgos

**P0:** 0 | **P1:** 0 | **P2:** 0

---

## Pendientes post-1310

1. UI avanzada de comparación (tabla visual lado a lado)
2. Asignación automática de segmento desde diagnóstico 1220
3. Integración catálogo con Centro de Control 1230

---

## Veredicto

```
EMPLEADOS IA — BLOQUE 1310 TERMINADO

RAMA: cursor/1310-segmentacion-planes-verticales
BASE: 9a61673b28ec194bbf561f76bd14a1f50bc8adbb
HEAD: <SHA final>

SEGMENTACIÓN: PASS
PERFIL CLIENTE: PASS
VERTICALES CONFIGURABLES: PASS
PLANES: PASS
PAQUETES: PASS
CAPACIDADES: PASS
RECOMENDACIÓN: PASS
EXPLICABILIDAD: PASS
PLAN INSUFICIENTE: PASS
PLAN EXCESIVO: PASS
PLAN PERSONALIZADO: PASS
PRECIO 1280: PASS
ESCALAMIENTO: PASS
CONSUMO: PASS
EXCEDENTES: PASS (reutiliza 1280)
DESCUENTOS: PASS
VERSIONADO: PASS
SNAPSHOT PROPUESTA: PASS
COMPARADOR: PASS
RBAC: PASS
MULTIEMPRESA: PASS
AUDITORÍA: PASS
UI EN ESPAÑOL: PASS
ALEMBIC: PASS
ALEMBIC HEAD: 1310a1b2c3d4e
TESTS: 37 passed (13×1310 + regresión)
FRONTEND: PASS

P0: 0
P1: 0
P2: 0

VEREDICTO: APTO
NO MERGE
```

**EMPLEADOS IA. Segmentación y planes verticales terminados.**
