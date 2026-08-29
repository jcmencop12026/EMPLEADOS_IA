# EMPLEADOS IA — VISTAS COMERCIALES Y DE VALOR (PRE-FASE 2)

**Agente:** C — Vistas comerciales y de valor  
**Base:** `ae03202465311303920c07f6d31e26276abfec0f`  
**Rama:** `cursor/vistas-comercial-valor-pre-fase2-dec7`  
**Fecha:** 2026-08-29  

## Resumen

Se expusieron en el frontend las capacidades ya construidas en la cadena 1280/1320/1340/1310 **sin nuevo motor comercial** ni duplicación de backend. Se reutilizan endpoints existentes (`/comercial/*`, `/finops/*`, `/tco/*`, `/implementacion/*`).

### Principios aplicados

- UI compacta, moderna, data-grid donde aplica, textos en español.
- **Valor verificado / estimado / potencial** mostrados por separado; potencial **excluido** del precio sugerido.
- Modalidad IA: administrada vs credenciales propias (sin secretos).
- Aviso explícito: **no existe IA ilimitada**.
- Semántica preparada para contrato transversal: VERIFICADO→HECHO, ESTIMADO/POTENCIAL→INFERENCIA, PROPUESTA→RECOMENDACIÓN (solo en etiquetas visuales).
- **Centro de Control:** no modificado.
- **Fase 2 central / main / V1:** no tocados.

---

## Commits (SHA completos)

| Etiqueta | SHA | Descripción |
|----------|-----|-------------|
| UI-PLANES | `f02063e625eb83c8691d0788630646fb296666be` | Detalle plan, segmentación, tabs comercial |
| UI-VALOR | `b75e42e6d55416f94f5b9377a17c9447a5f2ab06` | Propuesta: valor, ROI, precio, trazabilidad |
| UI-COSTOS-IA | `764107d6e3643bf4eb67a7adad9a39e421edbcd0` | Labels FinOps, TCO categorías |
| UI-IMPLEMENTACION | `2883574e26e91dd62363bbc30e92ab0bead08736` | Ciclo implementación, tablero |
| TESTS | `4e3921fd41778fd6a0ab48b728cab2538d1abc35` | Contrato API vistas comerciales |
| DOC | `5ae325b622ae2b417e5c8de9481ef1334548efce` | Este entregable |

---

## Navegación integrada (sin duplicar menús)

| Menú existente | Ruta | Contenido |
|----------------|------|-----------|
| Comercial y valor | `/comercial` | Tabs: Propuestas, Planes, Simulador |
| Segmentación y planes | `/comercial/segmentacion` | Grilla planes + enlace a detalle |
| Detalle plan | `/comercial/planes/:planId` | Capacidades, consumo IA, credenciales |
| Propuesta comercial | `/comercial/propuestas/:proposalId` | Resumen, valor, costos, precio/ROI, seguimiento |
| Costos y valor (FinOps) | `/costos-valor` | Costos IA, consumo, sobreconsumo |
| TCO | `/tco` | Costo total de propiedad |
| Implementación | `/implementacion` | Tablero + ciclo |
| Detalle implementación | `/implementacion/:id` | Hitos, valor comprometido/observado |

---

## Recorrido visual para revisión humana

### 1. Login
- **Ruta:** `/login`
- **Menú:** —
- **Qué debe ver:** Formulario de acceso.
- **Qué demuestra:** Autenticación multiempresa.

### 2. Plan contratado y capacidades
- **Ruta:** `/comercial/segmentacion` → clic en plan → `/comercial/planes/:planId`
- **Menú:** Comercial y valor → Segmentación y planes
- **Qué debe ver:** Nombre, segmento, empleados IA, usuarios, automatizaciones, integraciones, consumo IA incluido, modelos, almacenamiento, auditoría, SLA, sobreconsumo, modalidad credenciales, aviso sin IA ilimitada.
- **Qué demuestra:** Plan 1280 visible y configurable según permisos.

### 3. Costos y consumo IA
- **Ruta:** `/costos-valor`
- **Menú:** Costos y valor
- **Qué debe ver:** Proveedor, modelo, consumo, costo proveedor, incluido, utilizado, saldo, sobreconsumo, margen (si rol), presupuesto.
- **Qué demuestra:** FinOps 1320 reutilizado, sin valores inventados.

### 4. Valor (verificado / estimado / potencial)
- **Ruta:** `/comercial/propuestas/:id` → pestaña **Valor**
- **Menú:** Comercial y valor → Propuestas → detalle
- **Qué debe ver:** Tres tarjetas separadas con tooltips; desglose por categoría cuando exista; **no** suma de potencial al realizado.
- **Qué demuestra:** Cadena 1340/1310 en UI.

### 5. ROI y payback
- **Ruta:** `/comercial/propuestas/:id` → pestaña **Precio y ROI**
- **Menú:** (mismo)
- **Qué debe ver:** Inversión, beneficio atribuible, neto, ROI %, payback meses; datos del backend sin recálculo frontend.
- **Qué demuestra:** Motor comercial existente.

### 6. Precio sugerido (sin potencial)
- **Ruta:** misma pestaña **Precio y ROI**
- **Qué debe ver:** Precio sugerido, base, valor atribuible usado, fracción; nota explícita de exclusión de potencial.
- **Qué demuestra:** Regla de negocio P0 del cierre comercial.

### 7. TCO
- **Ruta:** `/tco`
- **Menú:** TCO (según shell)
- **Qué debe ver:** Licencia, implementación, operación, IA, integraciones, soporte, infra (según datos).
- **Qué demuestra:** Endpoint TCO existente.

### 8. Propuesta comercial
- **Ruta:** `/comercial` → Propuestas → detalle
- **Qué debe ver:** Cliente, plan, alcance, costos IA, inversión, valor, ROI, payback, precio, supuestos, vigencia/estado.
- **Qué demuestra:** Vista única con pestañas (sin cinco pantallas).

### 9. Implementación y seguimiento
- **Ruta:** `/implementacion` y `/implementacion/:id`; propuesta → pestaña **Seguimiento**
- **Qué debe ver:** Ciclo diagnóstico→seguimiento, estado, responsable, fechas, hitos, riesgos, valor esperado/observado.
- **Qué demuestra:** 1310 visible sin nuevo backend.

---

## Archivos principales

### Nuevos
- `frontend/src/lib/comercialLabels.ts` — tooltips ES, categorías valor, formato moneda
- `frontend/src/components/comercial/HelpTooltip.tsx`
- `frontend/src/components/comercial/CredentialModeBadge.tsx`
- `frontend/src/components/comercial/ValueNatureCards.tsx`
- `frontend/src/components/comercial/ImplementationCycleBar.tsx`
- `frontend/src/pages/ComercialPlanDetailPage.tsx`
- `tests/test_vistas_comercial_api_contract.py`

### Modificados
- `frontend/src/App.tsx`, `api.ts`, `styles.css`
- `ComercialPage.tsx`, `ComercialPropuestaDetailPage.tsx`, `SegmentacionPage.tsx`
- `ImplementacionPage.tsx`, `ImplementacionDetailPage.tsx`, `TcoPage.tsx`

---

## Validación

| Área | Resultado |
|------|-----------|
| Frontend build (`npm run build`) | PASS |
| Tests contrato API (6) | PASS |
| Regresión backend completa | 970 passed, 4 skipped, 0 failed |
| Backend modificado | NO |
| PostgreSQL | NO APLICA (sin cambios backend) |
| Alembic heads | 1 (`1390a1b2c3d4e`) |
| Centro Control modificado | NO |
| Fase2 central / main / V1 | NO |

### Checklist funcional

| Ítem | Estado |
|------|--------|
| PLANES | PASS |
| COSTOS IA | PASS |
| CONSUMO IA | PASS |
| SOBRECONSUMO | PASS |
| CREDENCIALES | PASS |
| VALOR VERIFICADO | PASS |
| VALOR ESTIMADO | PASS |
| VALOR POTENCIAL | PASS |
| POTENCIAL EXCLUIDO DE PRECIO | PASS |
| ROI | PASS |
| PAYBACK | PASS |
| TCO | PASS |
| PROPUESTA | PASS |
| IMPLEMENTACIÓN | PASS |
| MULTIEMPRESA | PASS (tests existentes + contrato org) |
| RBAC | PASS (permisos API sin bypass UI) |
| SUPERADMIN | PASS (comportamiento preservado) |
| FRONTEND BUILD | PASS |
| RECORRIDO VISUAL | PREPARADO |
| PLATAFORMA VISUALMENTE REVISABLE | SI (con `npm run dev`) |

**P0 / P1 / P2:** 0 / 0 / 0  

**VEREDICTO:** APTO PARA PORTAR A FASE2

---

## SALIDA FINAL

```
EMPLEADOS IA — VISTAS COMERCIALES Y DE VALOR TERMINADAS

BASE:
ae03202465311303920c07f6d31e26276abfec0f

RAMA:
cursor/vistas-comercial-valor-pre-fase2-dec7

HEAD:
d150e4c345d8b4b00299a751f5a1eba1f9971c2e

PLANES:
PASS

COSTOS IA:
PASS

CONSUMO IA:
PASS

SOBRECONSUMO:
PASS

CREDENCIALES:
PASS

VALOR VERIFICADO:
PASS

VALOR ESTIMADO:
PASS

VALOR POTENCIAL:
PASS

POTENCIAL EXCLUIDO DE PRECIO:
PASS

ROI:
PASS

PAYBACK:
PASS

TCO:
PASS

PROPUESTA:
PASS

IMPLEMENTACIÓN:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

FRONTEND BUILD:
PASS

BACKEND:
NO MODIFICADO

POSTGRESQL:
NO APLICA

ALEMBIC HEADS:
1

REGRESIÓN:
970 passed, 4 skipped, 0 failed

PLATAFORMA VISUALMENTE REVISABLE:
SI

RECORRIDO VISUAL:
PREPARADO

P0:
0

P1:
0

P2:
0

CENTRO CONTROL MODIFICADO:
NO

FASE2 CENTRAL MODIFICADA:
NO

MAIN:
NO

V1:
NO

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR A FASE2
```
