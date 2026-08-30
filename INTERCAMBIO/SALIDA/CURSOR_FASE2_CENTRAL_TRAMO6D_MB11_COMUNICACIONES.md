# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 6D (MB-11 COMUNICACIONES + MI TRABAJO)

**Tipo:** Integración selectiva MB-11 Centro de Información y Comunicaciones + delta Mi Trabajo  
**Fecha:** 2026-08-30  
**Agente:** GENERAL  
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central certificada (Tramo 6C)** | `82c1ec273f920c33fe2ea8b073d7f9c9d30e8b8` |
| **HEAD Tramo 6D** | `31c1991f` (docs + fix App.tsx) |
| **Fuente MB-11** | `cursor/mb11-centro-informacion-comunicaciones` @ `9d697f0c1755d4e836adc7219e43092ddd2aee37` (commit funcional `e3fb206`) |
| **Fuente Mi Trabajo** | `cursor/mb11-integracion-mi-trabajo` @ `c0fe2549990fe4c8aa63ab898bb0a22ca9395039` |
| **Método** | Cherry-pick selectivo + reparent migración `1341` sobre `1507`; delta Mi Trabajo aplicado manualmente sobre `trabajo_service` central |

### Commits Tramo 6D

| SHA | Mensaje |
|-----|---------|
| `bf713ea` | feat(mb-11): centro de información y comunicaciones reparentado sobre 1507 |
| `1795d8e` | feat(mb-11): integración Mi Trabajo sobre bandeja central |
| `a2e5425` | fix(frontend): eliminar duplicados Mi Trabajo en api.ts |
| `31c1991` | docs(tramo6d): entregable MB-11 comunicaciones + Mi Trabajo |

### Archivos portados (26 archivos, +3552 líneas netas)

**Backend MB-11:**
- `backend/alembic/versions/1341a1b2c3d4e_centro_comunicaciones_mb11.py`
- `backend/app/communications_enums.py`, `communications_models.py`, `schemas_communications.py`
- `backend/app/services/communications_service.py`
- `backend/app/routers/comunicaciones.py`
- Wiring: `main.py`, `permissions.py`, `notifications.py`, `automation_scheduler.py`
- `backend/alembic/migration_ledger.json`, `backend/scripts/schema_repair.py`

**Delta Mi Trabajo:**
- `backend/app/services/trabajo_service.py` — fuente `comunicaciones`, dedup 820
- `backend/app/routers/trabajo.py` — filtro `communication_id`
- `frontend/src/pages/TrabajoPage.tsx` — etiquetas tipos accionables

**Frontend MB-11:**
- `frontend/src/pages/ComunicacionesPage.tsx`
- `frontend/src/api.ts` (bloque Comunicaciones)
- `frontend/src/App.tsx`, `AppShell.tsx`, `auth/permissions.ts`

**Tests:**
- `tests/test_mb11_comunicaciones.py` (+15 tests)
- `tests/test_mb11_integracion_mi_trabajo.py` (+15 tests)
- `tests/test_scim_1380.py` (head → 1341)

**No portado:** Centro de Control ejecutivo, segunda bandeja, segundo motor 820/810C, reconstrucción MB-11, main/V1.

---

## 1. Alembic

| Campo | Valor |
|-------|-------|
| **Head entrada** | `1507a1b2c3d4e` |
| **Head salida** | `1341a1b2c3d4e` |
| **down_revision** | `1507a1b2c3d4e` (reparentado; NO `1340`) |
| **Colisión revision_id 1341** | NO (verificado antes de reparent) |
| **Cabezas** | **1** |
| **Merge migration** | NO necesaria |

### Cadena relevante

`14b1` → `1507` (MB-07) → `1341` (MB-11)

### Roundtrip SQLite (limpio)

| Paso | Resultado |
|------|-----------|
| upgrade head | PASS |
| downgrade -1 | PASS |
| re-upgrade head | PASS |
| `alembic_version` final | `1341a1b2c3d4e` |

**PostgreSQL:** PENDIENTE POR ENTORNO (`pg_isready` no disponible)

---

## 2. Funcionalidad MB-11

| Capacidad | Estado |
|-----------|--------|
| Bandeja | PASS |
| Plantillas | PASS |
| Versionado plantillas | PASS |
| Reglas | PASS |
| Canales | PASS |
| Correo (PREPARADO cuando aplica) | PASS |
| Comunicación interna | PASS |
| Destinatarios | PASS |
| Programación | PASS |
| Idempotencia (`org + event_id + rule_id + destinatario + channel_id`) | PASS |
| Deduplicación (`comm_dedup`) | PASS |
| Reintentos (810C) | PASS |
| Preferencias | PASS |
| Multiidioma | PASS |
| Auditoría | PASS |
| Webhook PREPARADO (sin fingir productivo) | PASS |
| Contratos CC (sin cablear CC ejecutivo) | PASS |

---

## 3. 820 y 810C

| Control | Estado |
|---------|--------|
| Reutiliza 820 existente (no duplicado) | PASS |
| Reutiliza 810C programación/reintentos | PASS |
| Sin segunda notificación redundante por evento | PASS |
| Dedup conjunta 820 + comm_dedup + Mi Trabajo | PASS |
| Reintento automático activo → NO Mi Trabajo | PASS |

---

## 4. MB-11 → Mi Trabajo

| Campo | Valor |
|-------|-------|
| **Fuente** | `comunicaciones` |
| **Etiqueta visible** | Centro de Información y Comunicaciones |
| **Navegación** | `/comunicaciones?mensaje={id}` |
| **trabajo_service** | Extendido (NO reemplazado) |

### Tipos accionables certificados

| Tipo | Condición |
|------|-----------|
| `comunicacion_envio_critico` | FALLIDA + reintentos agotados + sin reintento futuro |
| `comunicacion_canal_bloqueado` | Canal ERROR/DEGRADADO con fallo real |
| `comunicacion_configuracion_requerida` | Config obligatoria ausente con fallo terminal |

### Excluidos (automatización primero)

- ENVIADA / entregada
- PROGRAMADA normal
- PENDIENTE_ENVIO con reintento futuro
- Fallo recuperable / reintento automático activo
- Correo/webhook PREPARADO sin uso/fallo real
- Resuelto → desaparece de pendientes

---

## 5. Preservación central (Tramos 1–6C)

| Componente | Estado |
|------------|--------|
| Mesa de Ayuda + Soporte→Mi Trabajo | PRESERVADO |
| Auditor + Fábrica + ciclo mejora | PRESERVADO |
| MB-07 Planificador + FinOps único | PRESERVADO |
| 1290 / optimización | PRESERVADO |
| 820 notificaciones único | PRESERVADO |
| Mi Trabajo único (1290+soporte+auditor+comunicaciones) | PRESERVADO |
| Comercial / valor / TCO / implementación | PRESERVADO |
| Conocimiento 930 / identidad / MFA / SCIM | PRESERVADO |

---

## 6. Seguridad

| Control | Resultado |
|---------|-----------|
| Multiempresa | PASS |
| RBAC (`communications.view`, `.configure`, `.send`) | PASS |
| SUPERADMIN | PASS |
| Secretos no expuestos al frontend (`secret_configured`) | PASS |
| Aislamiento organizacional comunicaciones/trabajo | PASS |

---

## 7. Fechas (UTC/timezone)

| Área | Resultado |
|------|-----------|
| Programación | PASS (aware UTC) |
| Reintentos / próxima ejecución | PASS |
| Comparación naive/aware en servicio | PASS |

---

## 8. Pruebas

| Métrica | Antes (6C) | Después (6D) |
|---------|------------|--------------|
| Passed | 1171 | **1186** |
| Skipped | 4 | 4 |
| Failed | 0 | 0 |
| Nuevos MB-11 | — | +30 (15 core + 15 Mi Trabajo) |
| Fallos nuevos | — | 0 |
| Errores nuevos | — | 0 |

### Focal ejecutado

- `test_mb11_comunicaciones.py` — 15 PASS
- `test_mb11_integracion_mi_trabajo.py` — 15 PASS
- `test_consumption_planner_mb07.py` — PASS (MB-07 preservado)
- Regresión completa `tests/` — 1186 passed, 4 skipped

### Validaciones explícitas

| Caso | Resultado |
|------|-----------|
| Recuperable → NO Mi Trabajo | PASS |
| Reintentos agotados → SÍ Mi Trabajo | PASS |
| Resuelto → no accionable | PASS |
| Deduplicación conjunta | PASS |

---

## 9. Frontend

| Verificación | Resultado |
|--------------|-----------|
| `npm run build` | **PASS** |
| `/comunicaciones` (6 pestañas) | OK |
| `/trabajo` etiqueta Centro de Información y Comunicaciones | OK |
| Coexistencia `/soporte`, `/empleados/auditoria`, `/costos-valor` | OK |
| Textos en español | OK |

### Recorrido visual

- `/comunicaciones`: Bandeja, Plantillas, Reglas, Canales, Programadas, Historial — OK
- `/trabajo`: filtros y módulo comunicaciones — OK
- `/soporte`, `/empleados/auditoria`, `/costos-valor` — OK

---

## 10. Deuda / P0-P1-P2

| ID | Severidad | Descripción |
|----|-----------|-------------|
| — | — | Sin P0/P1/P2 abiertos en Tramo 6D |

**PostgreSQL real:** PENDIENTE POR ENTORNO (no simulado PASS).

---

## SALIDA FINAL

```
EMPLEADOS IA — FASE 2 CENTRAL TRAMO 6D TERMINADO

BASE: 82c1ec273f920c33fe2ea8b073d7f9c9d30e8b8
HEAD: 31c1991f

MB-11: PASS
BANDEJA: PASS
PLANTILLAS: PASS
REGLAS: PASS
CANALES: PASS
PROGRAMACIÓN: PASS
IDEMPOTENCIA: PASS
DEDUPLICACIÓN: PASS
REINTENTOS: PASS
820: PASS (reutilizado, no duplicado)
810C: PASS (reutilizado, no duplicado)
MI TRABAJO: PASS (único, extendido)
COMUNICACIONES → MI TRABAJO: PASS
RECUPERABLES EXCLUIDOS: PASS
REINTENTOS AGOTADOS: PASS
RESUELTOS EXCLUIDOS: PASS
ASIGNACIÓN: PASS (sin hardcode usuarios)
MB-07 PRESERVADO: PASS
AUDITOR/FÁBRICA PRESERVADOS: PASS
MESA AYUDA PRESERVADA: PASS
1290 PRESERVADO: PASS
FINOPS ÚNICO: PASS
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS
SECRETOS: PASS
FECHAS: PASS

ALEMBIC HEADS: 1
ALEMBIC HEAD: 1341a1b2c3d4e
UPGRADE: PASS
DOWNGRADE: PASS
RE-UPGRADE: PASS

REGRESIÓN ANTES: 1171 passed, 4 skipped, 0 failed
REGRESIÓN DESPUÉS: 1186 passed, 4 skipped, 0 failed
FALLOS NUEVOS: 0
ERRORES NUEVOS: 0

FRONTEND: PASS
POSTGRESQL: PENDIENTE POR ENTORNO
PLATAFORMA EJECUTABLE: SI
RECORRIDO VISUAL: PASS
P0/P1/P2: 0/0/0
MAIN: NO
V1: NO
MERGE MAIN: NO
VEREDICTO: TRAMO 6D APTO
```
