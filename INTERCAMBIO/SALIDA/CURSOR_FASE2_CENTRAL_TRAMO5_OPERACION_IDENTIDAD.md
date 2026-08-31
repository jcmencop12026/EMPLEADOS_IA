# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 5 (OPERACIÓN, IDENTIDAD, INTEGRACIONES, CONTINUIDAD Y MI TRABAJO)

**Tipo:** Integración selectiva de vistas operativas y bandeja humana  
**Fecha:** 2026-08-29  
**Agente:** GENERAL  
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central antes** | `cda96774909576e589ee1fddcbabf08aeec65540` |
| **HEAD Tramo 5** | ver sección final |
| **Método** | Cherry-pick selectivo + extensiones puntuales |
| **main / V1** | NO modificados |

### Commits portados

| Orden | SHA central | Origen | Contenido |
|-------|-------------|--------|-----------|
| 1 | `01306f1` | `495fb1f` | APIs operativas integraciones + trazabilidad correlation_id |
| 2 | `764a42c` | `db02339` | UI integraciones, gobierno, continuidad, trazabilidad |
| 3 | `5ea3096` | `b3046cc` | UI identidad/seguridad 1300/1370/1380 + detalle usuario |
| 4 | `8ce8107` | `40e76bc` | Bandeja Mi Trabajo `/trabajo` |
| 5 | `98be0e5` | — | Fix conflicto AdminUsersPage |
| 6 | `3077281` | c045bd1 (manual) + extensión | Terminología integraciones + 1290 en Mi Trabajo |

**No portados:** Auditor B (`be761f6`, `3d066ae`, `1400a1b2c3d4e`), Mesa de Ayuda, Fábrica, CC-DT, demo, bloques 1390/1400.

**Corrección aprendizaje `a9ea000`:** **NO_APLICA** — `formatCalcLabel` ya presente desde Tramo 4; el commit eliminaría etiquetas de continuidad usadas en `ContinuidadPage`.

**Correcciones visuales `c045bd1`/`b96e683`:** aplicadas selectivamente (terminología integraciones); `uiTerms` ya portado en Tramo 4.

---

## 1. Alembic

| Campo | Valor |
|-------|-------|
| **Head antes** | `1340a1b2c3d4e` |
| **Migraciones nuevas** | **0** (solo vistas/servicios sobre tablas existentes) |
| **Head después** | `1340a1b2c3d4e` |
| **Cabezas** | **1** |

---

## 2. Componentes integrados

### Integraciones (1330 + vistas)

- `list_connectors_overview`, trazabilidad por `correlation_id`
- Rutas: `/integraciones`, `/integraciones/:id`, `/integraciones/trazabilidad?cid=...`
- Sin secretos en UI; backend real (no mocks)
- Tests: `test_integraciones_1330`, `test_wiring_1330_fase1`

### Gobierno de datos (1350)

- Vista mejorada `/gobernanza-datos` sobre dominio existente
- Multiempresa y RBAC preservados

### Continuidad (1360)

- Vista `/continuidad` con alertas, eventos `INTEGRACION_SALUD_RECUPERADA` y `RESTORE_BLOQUEADO_PRIVACIDAD`
- Terminología español en etiquetas

### Identidad y seguridad (1300/1370/1380)

- `/administracion/usuarios` y `/administracion/usuarios/:userId`
- MFA, SCIM, sesiones, roles/permisos vía backend central real
- Tests: `test_bloque_1300`, `test_scim_1380`

### Mi Trabajo

- `/trabajo` — `GET /api/trabajo/items`, `GET /api/trabajo/resumen`
- Fuentes: aprobaciones, ejecuciones fallidas, automatizaciones, oportunidades, continuidad, integraciones degradadas, FinOps, notificaciones 820
- **Extensión 1290:** recomendaciones `PENDIENTE_EJECUCION_HUMANA` (navegación, sin ejecutar desde bandeja)
- Deduplicación aprobación/notificación preservada
- Polling 60s en AppShell (sin aumento)
- Tests: `test_bandeja_trabajo_humano` (+ test 1290)

---

## 3. Preservaciones

| Control | Estado |
|---------|--------|
| Centro de Control sin cableado ejecutivo nuevo | PASS |
| No segundo motor integraciones/gobierno/continuidad | PASS |
| SUPERADMIN sin bypass nuevo | PASS |
| Secretos no expuestos | PASS |
| Semántica HECHO/INFERENCIA/RECOMENDACIÓN sin duplicar contrato | PASS |

---

## 4. Deudas conocidas

| Deuda | Severidad | Nota |
|-------|-----------|------|
| SCIM rate limit en memoria | P2 histórico | Sin regresión nueva; no rediseño en este tramo |
| Auditor → Mi Trabajo | Pendiente tramo posterior | `be761f6` no portado |

---

## 5. Validación diferencial

| Métrica | Antes (Tramo 4) | Después (Tramo 5) | Δ |
|---------|-----------------|-------------------|---|
| passed | 1061 | **1068** | +7 |
| skipped | 4 | **4** | 0 |
| failed | 0 | **0** | 0 |
| errors | 0 | **0** | 0 |

**FALLOS NUEVOS: 0**  
**ERRORES NUEVOS: 0**

### Focales ejecutados

| Suite | Resultado |
|-------|-----------|
| Integraciones 1330 + wiring | PASS |
| Mi Trabajo + 1290 + deduplicación | PASS |
| 1300, 1370, 1380 (SCIM) | PASS |
| Migration control | PASS |
| Frontend build | PASS |
| PostgreSQL | **PENDIENTE POR ENTORNO** |

| Severidad | Conteo |
|-----------|--------|
| P0 | **0** |
| P1 | **0** |
| P2 | **0** (SCIM rate limit = deuda histórica documentada) |

---

## 6. Recorrido visual preparado

| Paso | Ruta | Menú |
|------|------|------|
| Centro de Control | `/` | Inicio |
| Mi Trabajo | `/trabajo` | Operaciones → Mi trabajo |
| Integraciones | `/integraciones` | Análisis → Integraciones |
| Detalle integración | `/integraciones/:id` | Desde listado |
| Trazabilidad | `/integraciones/trazabilidad?cid=...` | Desde detalle/ejecución |
| Gobierno de datos | `/gobernanza-datos` | Análisis → Gobierno de datos |
| Continuidad | `/continuidad` | Análisis → Continuidad |
| Usuarios | `/administracion/usuarios` | Administración → Usuarios |
| Detalle usuario | `/administracion/usuarios/:userId` | Desde listado |

**RECORRIDO VISUAL: PREPARADO**

---

## 7. Veredicto

**TRAMO 5 APTO** — operación, identidad y Mi Trabajo integrados; regresión 0 failed; Alembic cabeza única; CC preservado.
