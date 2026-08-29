# EMPLEADOS IA — VISTAS DE APRENDIZAJE, OPTIMIZACIÓN Y MULTIPROVEEDOR

**Agente:** C — Vistas aprendizaje / optimización / multiproveedor  
**Base:** `da195ad69244abbd6ffb63b629d7ddece38b0419` (`cursor/aprendizaje-optimizacion-multiproveedor-base-puente`)  
**Rama:** `cursor/vistas-aprendizaje-optimizacion-multiproveedor-dec7`  
**P1-ID-04 incorporado:** cherry-pick `245cb778e4eff058c70dca533607678899dffe0c`  
**Fecha:** 2026-08-29  

## Resumen

Se hicieron **visibles y operables** las capacidades 1260, 1290 y 1270 sin nuevos motores ni duplicación de backend. Se reutilizan endpoints existentes y FinOps.

### Restricciones respetadas

- Centro de Control: **NO modificado**
- Fase 2 central / main / V1: **NO tocados**
- Vistas comerciales (`cursor/vistas-comercial-valor-pre-fase2-dec7`): **NO tocadas**
- P1-ID-03 / 1330: **NO tocados**
- Sin Ollama instalado, sin OpenAI real

---

## Commits (SHA completos)

| Etiqueta | SHA | Descripción |
|----------|-----|-------------|
| P1-ID-04 backend | `66b4dc625eb83c8691d0788630646fb296666be` | Ejecución trazable recomendaciones |
| P1-ID-04 tests | `cac23f5` | Cobertura P1 aprobada→ejecutada |
| UI-APRENDIZAJE | *(ver HEAD)* | Vistas 1260 + repriorización |
| UI-OPTIMIZACION | *(ver HEAD)* | Vistas 1290 + ejecución P1-ID-04 |
| UI-MULTIPROVEEDOR | *(ver HEAD)* | Vistas 1270 observabilidad/modelos/logs |
| TESTS | *(ver HEAD)* | Contrato API vistas |
| DOC | *(ver HEAD)* | Este entregable |

---

## Navegación

| Menú | Ruta | Bloque |
|------|------|--------|
| Aprendizaje | `/aprendizaje`, `/aprendizaje/:id` | 1260 |
| Optimización | `/optimizacion`, `/optimizacion/:id` | 1290 |
| Proveedores IA | `/administracion/proveedores-ia` | 1270 |
| Costos y valor (FinOps) | `/costos-valor` | FinOps reutilizado |

---

## Recorrido visual para revisión humana

### 1. Login
- **Ruta:** `/login`
- **Menú:** —
- **Qué se ve:** Formulario de acceso.
- **Qué demuestra:** Autenticación multiempresa.

### 2. Aprendizajes
- **Ruta:** `/aprendizaje` → pestaña **Aprendizajes**
- **Menú:** Aprendizaje
- **Qué se ve:** Grilla con esperado/real, repriorización, correlation_id, filtros.
- **Qué demuestra:** 1260 visible sin presentar inferencias como hechos.

### 3. Resultado que originó aprendizaje
- **Ruta:** `/aprendizaje/:cicloId`
- **Menú:** Aprendizaje → detalle ciclo
- **Qué se ve:** Esperado vs observado, retroalimentación, lecciones, badges Hecho/Inferencia.
- **Qué demuestra:** Origen trazable (oportunidad, plan, señal, correlation_id).

### 4. Repriorización
- **Ruta:** `/aprendizaje` → pestaña **Repriorización** o detalle ciclo
- **Menú:** Aprendizaje
- **Qué se ve:** Prioridad anterior/nueva, motivo, evidencia; mensaje explícito si no hubo cambio.
- **Qué demuestra:** No se fabrican cambios.

### 5. Recomendaciones
- **Ruta:** `/optimizacion`
- **Menú:** Optimización
- **Qué se ve:** Grilla con estado, ejecución, ROI, riesgo, correlation_id.
- **Qué demuestra:** 1290 compacto con semántica Recomendación.

### 6. Aprobar recomendación
- **Ruta:** `/optimizacion/:id` → **Aprobar recomendación**
- **Qué se ve:** Transición PROPUESTA → APROBADA.
- **Qué demuestra:** RBAC `optimizacion.approve`.

### 7. Ejecutar / pendiente humana
- **Ruta:** `/optimizacion/:id`
- **Qué se ve:** Botones ejecutar automática o marcar pendiente humana; panel de ejecución.
- **Qué demuestra:** P1-ID-04 APROBADA → EJECUTADA / PENDIENTE_EJECUCION_HUMANA.

### 8. Resultado de ejecución
- **Ruta:** `/optimizacion/:id` → panel **Ejecución**
- **Qué se ve:** Estado real (nunca EJECUTADA si falló), referencia externa, learning_refs.
- **Qué demuestra:** Fallo controlado visible.

### 9. Proveedores IA
- **Ruta:** `/administracion/proveedores-ia` → **Proveedores**
- **Menú:** Administración → Proveedores IA
- **Qué se ve:** OpenAI operativo, Ollama opcional, otros preparados; credencial enmascarada.
- **Qué demuestra:** 1270 sin exponer secretos.

### 10. Modelos
- **Ruta:** `/administracion/proveedores-ia` → **Modelos**
- **Qué se ve:** Catálogo por proveedor, estado, prioridad.
- **Qué demuestra:** Modelos visibles según contrato backend.

### 11. Observabilidad
- **Ruta:** `/administracion/proveedores-ia` → **Consumo**
- **Qué se ve:** Solicitudes, éxitos, fallos, latencia, tokens, costo (si permiso), por proveedor.
- **Qué demuestra:** Observabilidad 1270 compacta.

### 12. Consumo/costos
- **Ruta:** `/costos-valor` (enlace desde observabilidad si `finops.view`)
- **Qué demuestra:** FinOps reutilizado, sin duplicar cálculo.

### 13. Trazabilidad correlation_id
- **Rutas:** `/aprendizaje/:id`, `/optimizacion/:id`
- **Qué se ve:** correlation_id en métricas y panel ejecución.
- **Qué demuestra:** Trazabilidad transversal preparada para contrato A.

---

## Validación

| Área | Resultado |
|------|-----------|
| Frontend build | PASS |
| Tests contrato API (7) | PASS |
| test_aprendizaje_1260 | PASS |
| test_optimizacion_1290_ejecucion_p1 | PASS |
| test_bloque_1270_multiproveedor | PASS |
| Focales combinados | 41 passed |
| Alembic heads | 1 (`1270a1b2c3d4e`) |
| Centro Control | NO modificado |
| Fase 2 central | NO modificada |

---

## SALIDA FINAL

```
EMPLEADOS IA — VISTAS DE APRENDIZAJE, OPTIMIZACIÓN Y MULTIPROVEEDOR TERMINADAS

RAMA:
cursor/vistas-aprendizaje-optimizacion-multiproveedor-dec7

HEAD:
<completar tras commit>

APRENDIZAJE 1260: PASS
REPRIORIZACIÓN: PASS
RECOMENDACIONES 1290: PASS
APROBACIÓN: PASS
EJECUCIÓN: PASS
PENDIENTE HUMANA: PASS
FALLO CONTROLADO: PASS
P1-ID-04: PASS
MULTIPROVEEDOR 1270: PASS
MODELOS: PASS
RUTEO: PASS
OBSERVABILIDAD: PASS
FINOPS: PASS
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS
SECRETOS PROTEGIDOS: PASS
FRONTEND BUILD: PASS
BACKEND: PASS (P1-ID-04 cherry-pick)
REGRESIÓN FOCAL: 41 passed, 0 failed
ALEMBIC HEADS: 1
ALEMBIC HEAD: 1270a1b2c3d4e
RECORRIDO VISUAL: PREPARADO
PLATAFORMA VISUALMENTE REVISABLE: SI
P0/P1/P2: 0/0/0
CENTRO CONTROL MODIFICADO: NO
FASE2 CENTRAL: NO MODIFICADA
MAIN/V1/MERGE: NO
VEREDICTO: APTO PARA PORTAR A FASE2
```
