# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 6A (MESA DE AYUDA + INTEGRACIÓN MI TRABAJO)

**Tipo:** Integración selectiva MB-12 + delta soporte en Mi Trabajo
**Fecha:** 2026-08-29
**Agente:** GENERAL
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central certificada** | `e4ff40bf411fa5d91f69246e47e4805187a4d116` |
| **HEAD Tramo 6A** | `811a7b4a7b061703d193a4ff19fc584c7b4f26ba` |
| **Método** | Cherry-pick selectivo (sin merge completo de ramas) |
| **main / V1** | NO modificados |

### Commits portados

| Orden | SHA central | Origen | Contenido |
|-------|-------------|--------|-----------|
| 1 | `dffd294` | `bb72cc4` | Backend MB-12: modelos, servicios, router, RBAC, eventos, migración |
| 2 | `5adc7ef` | `45b0dcb` | Frontend `/soporte`, `/soporte/casos/:id`, menú Mesa de Ayuda |
| 3 | `1c8ef8b` | `68ff774` | Tests `test_mesa_ayuda_mb12.py` (14 casos) |
| 4 | `4536c7f` | — | Reparent migración `1391` sobre cabeza central `1340` |
| 5 | `de9579a` | `c319a00` | Delta `trabajo_service.py` + filtros router trabajo |
| 6 | `51a536e` | `307baee` | Tests integración Mi Trabajo (20 casos) |
| 7 | `2e5f8ae` | `632be4a` | UI Mi Trabajo: etiquetas origen Mesa de Ayuda |
| 8 | `b9f3b3b` | — | Fix viewer: `support.create` para abrir casos propios |
| 9 | `811a7b4` | — | Actualizar head SCIM test a `1391` |

**No portados:** `8aefc87` (bandeja Mi Trabajo completa — central es autoridad), MB-07, Auditor, Fábrica, MB-11, Conocimiento, CC-DT, bloques 1390/1400 funcionales, demo, main, V1.

### Archivos resueltos en conflictos

| Archivo | Resolución |
|---------|------------|
| `backend/app/main.py` | Routers `trabajo` + `soporte` coexisten |
| `backend/app/permissions.py` | Permisos centrales + `SUPPORT_PERMISSIONS`; viewer con `support.view` + `support.create` |
| `backend/alembic/migration_ledger.json` | Cadena 1260→…→1340→**1391** |
| `backend/scripts/schema_repair.py` | `HEAD_REVISION = 1391a1b2c3d4e` |
| `frontend/src/api.ts` | Bloque soporte añadido al final (sin mezclar tipos aprendizaje) |
| `frontend/src/auth/permissions.ts` | `/trabajo` preserva permisos amplios; `/soporte` requiere `support.create`/`support.view` |

---

## 1. Alembic y migración 1391

| Campo | Valor |
|-------|-------|
| **Head antes** | `1340a1b2c3d4e` |
| **Head después** | `1391a1b2c3d4e` |
| **down_revision** | `1340a1b2c3d4e` (reparentado; NO usar histórico `1330b1b2c3d4f`) |
| **Cabezas** | **1** |
| **Archivo** | `backend/alembic/versions/1391a1b2c3d4e_mesa_ayuda_soporte_mb12.py` |
| **Tablas nuevas** | `support_cases`, `support_case_history`, `support_case_comments`, `support_sla_policies` |

### Roundtrip SQLite

| Paso | Resultado |
|------|-----------|
| upgrade head | PASS (`test_migration_roundtrip_upgrade_downgrade_upgrade`) |
| downgrade -1 | PASS |
| re-upgrade | PASS |

**PostgreSQL:** PENDIENTE POR ENTORNO (sin instancia PG en VM).

---

## 2. Mesa de Ayuda (MB-12)

### Funcionalidad preservada

- Casos manuales y automáticos
- Historial y comentarios
- SLA (`compute_sla_estado`: vigente / riesgo / vencido)
- Asignación, prioridad, estados
- Deduplicación de casos automáticos equivalentes
- Eventos y notificaciones
- RBAC granular (`support.view`, `support.create`, `support.assign`, `support.update`, `support.resolve`, `support.close`, `support.admin`)
- Contrato Centro de Control: `GET /api/soporte/contrato/centro-control` (sin cablear CC ejecutivo)

### Rutas frontend

- `/soporte` — listado
- `/soporte/casos/:caseId` — detalle, historial, comentarios, SLA

### Tests MB-12

`tests/test_mesa_ayuda_mb12.py`: **14/14 PASS**

---

## 3. Integración Mi Trabajo (delta)

**Mi Trabajo central es autoridad** — NO se sustituyó bandeja (`40e76bc`/`d5acb37`). Solo delta en:

- `backend/app/services/trabajo_service.py` (+158 líneas)
- `backend/app/routers/trabajo.py` (filtros `modulo`, `case_id`)
- `frontend/src/pages/TrabajoPage.tsx` (etiquetas tipo/módulo soporte)

### Estados accionables en bandeja

Incluidos: `NUEVO`, `ASIGNADO`, `EN_PROCESO`, `PENDIENTE_USUARIO`, `PENDIENTE_TERCERO`
Excluidos: `RESUELTO`, `CERRADO`, `CANCELADO`

### 1290 preservado

Extensión `PENDIENTE_EJECUCION_HUMANA` (optimización 1290) intacta en `trabajo_service.py`.
Tests: `test_optimizacion_1290.py` + `test_bandeja_trabajo_humano.py` — **PASS**

### Resumen y filtros

- `GET /api/trabajo/resumen` incluye fuente soporte sin romper fuentes existentes
- Filtros compatibles: `modulo=soporte`, `case_id`, `tipo`, `prioridad`/`estado` según contrato

### Navegación

Desde `/trabajo`, ítems soporte navegan a `/soporte/casos/:id` vía `enlace` (sin formulario duplicado en bandeja).

### Tests integración

`tests/test_mesa_ayuda_integracion_mi_trabajo.py`: **20/20 PASS**

---

## 4. Deduplicación 820

- Notificaciones `SUPPORT_*` / `support_case`: **INFORMA**
- Mi Trabajo casos accionables: **REQUIERE ACTUACIÓN**
- Si un caso ya genera ítem accionable, la notificación equivalente se omite (`pending_support_case_ids`, `pending_support_correlation_ids`)
- Tests dedup 820 en integración: **PASS**

---

## 5. Multiempresa, RBAC, SUPERADMIN, secretos

| Control | Resultado |
|---------|-----------|
| Multiempresa (manipulación IDs cross-org) | PASS |
| RBAC (ver ítem ≠ asignar/resolver/cerrar) | PASS |
| SUPERADMIN patrón central (sin bypass nuevo) | PASS |
| Secretos no expuestos en casos/comentarios/API/UI | PASS (`sanitize_text`) |

---

## 6. Frontend

| Verificación | Resultado |
|--------------|-----------|
| `npm run build` | **PASS** |
| Rutas `/trabajo`, `/soporte`, `/soporte/casos/:id` | Registradas |
| UI en español | PASS |

---

## 7. Regresión completa

| Métrica | Antes (base) | Después (Tramo 6A) |
|---------|--------------|---------------------|
| Passed | 1068 | **1102** |
| Skipped | 4 | 4 |
| Failed | 0 | **0** |
| Errors | 0 | 0 |
| Fallos nuevos | — | **0** |
| Errores nuevos | — | **0** |

Tests nuevos: +34 (14 MB-12 + 20 integración).
`test_migration_control.py`: 7/7 PASS.

---

## 8. Recorrido visual

**PREPARADO** — flujo documentado:

1. Login → Mi Trabajo → filtrar módulo Mesa de Ayuda → abrir caso → revisar SLA → asignar/actualizar según permisos → volver a Mi Trabajo → comprobar actualización
2. Mesa de Ayuda → listado → detalle → historial/comentarios → SLA

---

## 9. P0/P1/P2

**0 / 0 / 0**

---

## SALIDA FINAL

```
EMPLEADOS IA — FASE 2 CENTRAL TRAMO 6A TERMINADO

BASE:
e4ff40bf411fa5d91f69246e47e4805187a4d116

HEAD:
811a7b4a7b061703d193a4ff19fc584c7b4f26ba

MESA DE AYUDA:
PASS

CASOS:
PASS

SLA:
PASS

ASIGNACIÓN:
PASS

HISTORIAL:
PASS

COMENTARIOS:
PASS

MI TRABAJO:
PASS

SOPORTE EN MI TRABAJO:
PASS

1290 PRESERVADO:
PASS

DEDUPLICACIÓN 820:
PASS

DEDUPLICACIÓN CASOS:
PASS

RESUMEN:
PASS

FILTROS:
PASS

NAVEGACIÓN:
PASS

CONTRATO CC:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

SECRETOS:
PASS

REVISION 1391:
PASS

DOWN_REVISION:
1340a1b2c3d4e

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1391a1b2c3d4e

UPGRADE:
PASS

DOWNGRADE:
PASS

RE-UPGRADE:
PASS

REGRESIÓN ANTES:
1068 passed, 4 skipped, 0 failed

REGRESIÓN DESPUÉS:
1102 passed, 4 skipped, 0 failed

FALLOS NUEVOS:
0

ERRORES NUEVOS:
0

FRONTEND:
PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

PLATAFORMA EJECUTABLE:
SI

RECORRIDO VISUAL:
PREPARADO

P0/P1/P2:
0/0/0

MAIN:
NO

V1:
NO

MERGE MAIN:
NO

VEREDICTO:
TRAMO 6A APTO
```
