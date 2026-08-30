# CERTIFICACIÓN VISUAL/UX — TRAMO 6B (Agente D)

| Campo | Valor |
|-------|-------|
| **SHA congelado** | `118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8` |
| **Commit** | `118cc2a` — docs(tramo6b): entregable Auditor, Fábrica y ciclo de mejora |
| **Rama certificación** | `cursor/cert-visual-tramo6b-d-9a85` |
| **Fecha** | 2026-08-30 (UTC) |
| **Entorno** | Frontend `http://127.0.0.1:5180` · Backend `http://127.0.0.1:8000` |
| **Usuario prueba** | `admin` (rol administrador) |
| **Resolución principal** | 1280×800 (escritorio) |
| **Central** | **NO MODIFICADA** |

## Alcance revisado

| Ruta | Vista | Resultado |
|------|-------|-----------|
| `/trabajo` | Mi Trabajo (bandeja unificada) | Revisada |
| `/empleados/auditoria` | Auditor de Empleados IA | Revisada |
| `/directorio` → `/empleados/:id` | Detalle Fábrica de Empleados IA (12 pestañas) | Revisada |
| `/optimizacion` | Optimización 1290 | Revisada |
| `/soporte` | Mesa de Ayuda | Revisada |
| `/soporte/casos/:id` | Detalle de caso (SUP-00001 creado en certificación) | Revisada |

**Evidencia:** recorrido grabado en `/opt/cursor/artifacts/certificacion_visual_tramo6b_recorrido.mp4` + verificación API (`POST /api/soporte/casos` → caso `SUP-00001` visible en UI y detalle navegable).

---

## Veredicto ejecutivo

| Dimensión | Estado |
|-----------|--------|
| Interfaz en español | **CONDICIONAL** — predominio español con fugas P1 en etiquetas técnicas |
| Navegación coherente | **PASS** |
| Mi Trabajo único | **PASS** |
| Fuentes/módulos identificables | **PASS** |
| Sin vistas duplicadas | **PASS** |
| Sin rutas muertas (alcance) | **PASS** |
| Layout compacto / consistencia | **PASS** |
| Errores y vacíos | **PASS** (con mejoras P2) |
| RBAC acciones | **PASS** (observado en código + UI) |

**Veredicto global:** **APTO CON OBSERVACIONES P1** — no bloqueantes funcionales en SHA congelado con backend activo; corregir etiquetas en inglés y UX de asignación en Mesa de Ayuda antes de certificación final de idioma.

---

## Hallazgos clasificados

### P0 — Bloqueo / idioma crítico / seguridad

*Ninguno confirmado en producto a SHA `118cc2a` con backend operativo.*

| ID | Hallazgo | Evidencia | Notas |
|----|----------|-----------|-------|
| — | — | — | Durante la certificación se observó un mensaje transitorio de conexión en `/soporte` al arrancar el entorno; **no reproducible** tras estabilizar backend. API `GET/POST /api/soporte/casos` responde 200 y el caso `SUP-00001` se crea y navega correctamente. Clasificado como **incidente de entorno**, no defecto de código. |

### P1 — Significativo (idioma, UX, coherencia)

| ID | Ruta / componente | Hallazgo | Evidencia |
|----|-------------------|----------|-----------|
| **P1-01** | `/trabajo` · `TrabajoPage.tsx` | Columna y panel usan **«Correlation» / «Correlation ID»** en lugar de español («ID de correlación»). Incumple criterio «interfaz completamente en español». | L25 `label: "Correlation"`; L401 `Correlation ID` |
| **P1-02** | `/soporte/casos/:id` · `SoporteCasoDetailPage.tsx` | Texto visible **«Correlation ID:»** en resumen del caso. | L49 |
| **P1-03** | `/optimizacion` · `OptimizacionPage.tsx` | Cabecera de tabla **«Correlation»** en listado 1290. | L149 |
| **P1-04** | `/empleados/:id` pestañas Modelo / Límites | Etiquetas visibles **«Fallback:»** y **«Timeout:»** (inglés) en detalle de empleado. | `EmployeeDetailPage.tsx` ~L446, L461 |
| **P1-05** | `/soporte/casos/:id` · Asignación | Campo **«ID responsable»** exige pegar UUID manual; sin selector de usuario/agente. Dificulta operación de Mesa de Ayuda y aumenta errores. | L57 placeholder `ID responsable` |
| **P1-06** | `/empleados/:id` (contexto Auditor) | Banner de contexto muestra prefijos técnicos en inglés: `finding:`, `run:`, `cid:`, `trace:` visibles al usuario. | `EmployeeDetailPage.tsx` ~L277-281 |

### P2 — Pulido / accesibilidad / consistencia menor

| ID | Ruta / componente | Hallazgo | Evidencia |
|----|-------------------|----------|-----------|
| **P2-01** | `/empleados/:id` · Resumen | **9 botones de acción** simultáneos (Validar, Ejecutar pruebas, Certificar, Solicitar aprobación, Publicar, Activar, Capacitar, Retirar, Editar). Layout funcional pero denso; riesgo de fatiga/decisión. | Barra de acciones en pestaña Resumen |
| **P2-02** | `/optimizacion` | `HelpTooltip` renderiza **«?»** como único indicador visual; la ayuda existe en `title` pero no es obvia sin hover. | `HelpTooltip.tsx` default `label="?"` |
| **P2-03** | `/soporte/casos/:id` · Historial | Columna **Detalle** muestra `JSON.stringify(detalle)` — legibilidad pobre para operadores. | L110 |
| **P2-04** | `/trabajo` · panel detalle | Valores crudos de dominio (`health_status`, `semantic_kind`, `estado_dominio`) sin mapa de etiquetas españolas en todos los casos. | Metadatos auditor en panel lateral |
| **P2-05** | `/soporte` | Tipos/estados en **MAYÚSCULAS técnicas** (`SOLICITUD`, `NUEVO`) en tabla; comprensible pero poco amigable frente al resto de la plataforma. | Tabla listado casos |
| **P2-06** | Global | Certificación realizada principalmente a **1280×800**; no se validó exhaustivamente 1024×768 ni viewports estrechos. | Observación de proceso |
| **P2-07** | Menú Operaciones | Coexisten **«Mi trabajo»** y **«Aprobaciones»** como entradas separadas. No es duplicación de vista (bandeja vs módulo operativo), pero conviene documentar en capacitación para evitar confusión. | `AppShell.tsx` |

---

## Checklist de verificación

### Interfaz en español
- **PASS** en títulos, menús, botones principales, formularios y mensajes de error/vacío.
- **P1** por fugas «Correlation», «Fallback», «Timeout» y prefijos técnicos en contexto Auditor (ver P1-01 a P1-06).

### Navegación coherente
- **PASS:** menú lateral por secciones (Inicio, Operaciones, Empleados IA, Análisis…).
- **PASS:** breadcrumbs «← Directorio», «← Volver a Mesa de Ayuda», «← Optimización».
- **PASS:** sin 404 en rutas del alcance; login redirige correctamente.

### Mi Trabajo único
- **PASS:** una sola ruta `/trabajo` y una entrada de menú «Mi trabajo».
- **PASS:** agrega ítems de soporte (`soporte_caso`, SLA) y auditor (`auditor_empleado_*`) con `MODULO_LABELS` («Mesa de Ayuda», «Auditor de Empleados IA»).
- **PASS:** no existe segunda bandeja paralela; `/aprobaciones` es módulo operativo específico (complementario, no duplicado).

### Fuentes claramente identificables
- **PASS:** columnas Módulo/Tipo en Mi Trabajo con etiquetas españolas.
- **PASS:** Auditor y Mesa de Ayuda con títulos y subtítulos descriptivos en español.

### Auditor (`/empleados/auditoria`)
- **PASS:** salud por empleado, hallazgos, acciones Auditar/Detalle.
- **PASS:** estados vacíos («Sin hallazgos»).
- **PASS:** RBAC — botón masivo «Auditar empleados activos» solo con `auditor_empleados.execute`.

### Mesa de Ayuda (`/soporte`, `/soporte/casos/:id`)
- **PASS:** listado, filtros, formulario «Nuevo caso», estados vacíos.
- **PASS:** detalle con secciones Resumen, Asignación, Resolver, Comentarios, Historial.
- **PASS:** RBAC — crear/asignar/resolver según permisos `support.*`.
- **P1:** asignación por UUID (P1-05).

### Optimización 1290 (`/optimizacion`)
- **PASS:** simulador, filtros, tabla recomendaciones, vacío «Sin recomendaciones».
- **PASS:** badges semánticos RECOMENDACIÓN + tooltip.
- **P1/P2:** columna Correlation (P1-03); tooltip «?» (P2-02).

### Fábrica — pestañas detalle empleado
Las **12 pestañas** requeridas están presentes y navegables:

| Pestaña | Estado |
|---------|--------|
| Resumen | PASS |
| Configuración | PASS |
| Conocimiento | PASS |
| Herramientas | PASS |
| Modelo | PASS (P1-04 Fallback) |
| Automatizaciones | PASS |
| Límites | PASS (P1-04 Timeout) |
| Versiones | PASS |
| Pruebas | PASS |
| Aprobación | PASS |
| Publicación | PASS |
| Historial | PASS |

### Aprobación, capacitación, versiones, pruebas
- **PASS:** pestañas dedicadas Aprobación, Pruebas, Versiones.
- **PASS:** acciones Capacitar, Solicitar aprobación, Ejecutar pruebas en Resumen con guardas de ciclo de vida.
- **PASS:** integración Auditor → Fábrica vía query `finding_id` / `trace_id` con acciones «Capacitar (autorizado)», reauditar.

### Acciones según permisos
- **PASS:** `usePermissions` / `RequirePermission` en rutas y botones críticos (auditor execute, support.create/assign/resolve, employee.approve/edit/train).

### Sin botones/vistas duplicadas
- **PASS:** no se detectaron dos pantallas equivalentes para Mi Trabajo, Auditor o Mesa de Ayuda.

### Sin rutas muertas (alcance)
- **PASS:** todas las rutas del alcance responden con contenido o estado vacío legítimo.

### Layout compacto y consistencia
- **PASS:** `ops-page`, `compact-table`, `panel`, `page-header` alineados con resto de plataforma Tramo 6B.

### Errores visibles
- **PASS:** `role="alert"` / `.error` / `ErrorState` en Mi Trabajo y Auditor.
- **PASS:** mensajes en español.

### Estados vacíos
- **PASS:** «Sin elementos», «No hay casos», «Sin recomendaciones», «Sin hallazgos», etc.

### Tooltips / ayuda
- **PASS:** tooltips en Optimización (1290) y badges semánticos.
- **P2:** icono «?» poco descubrible sin hover (P2-02).

### Resoluciones razonables
- **PASS** a 1280×800.
- **P2:** validación adicional en 1024×768 pendiente (P2-06).

---

## Resumen de severidades

| Severidad | Cantidad | Bloquea certificación |
|-----------|----------|------------------------|
| **P0** | 0 | No |
| **P1** | 6 | No (idioma/UX; corregir antes de sign-off idioma) |
| **P2** | 7 | No |

---

## Recomendaciones para General (sin rediseño)

1. **P1-01..03:** Renombrar «Correlation» → «ID de correlación» en Mi Trabajo, Soporte y Optimización.
2. **P1-04:** Traducir «Fallback» → «Reserva» / «Modelo de respaldo»; «Timeout» → «Tiempo de espera».
3. **P1-05:** Sustituir input UUID por selector de usuario/agente en asignación de casos.
4. **P1-06:** Etiquetas de contexto Auditor en español («Hallazgo», «Ejecución», «Correlación», «Trazabilidad»).
5. **P2-01:** Agrupar acciones de ciclo de vida en menú desplegable o jerarquía primaria/secundaria.
6. **P2-03:** Renderizar historial de caso con plantilla legible, no JSON crudo.

---

## Restricciones respetadas

- **NO** se modificó `cursor/fase2-central-integracion` ni rama central.
- **NO** se rediseñó la plataforma.
- **NO** se corrigió código de producto; solo evidencia y este informe.
- SHA de revisión: **`118cc2a573f920c33fe2ea8b073d7f9c9d30e8b8`**.

---

## Notificación

**EMPLEADOS IA — Certificación visual/UX Tramo 6B (Agente D) terminada.**

Entregable: `INTERCAMBIO/SALIDA/CERTIFICACION_VISUAL_TRAMO6B_D.md`
