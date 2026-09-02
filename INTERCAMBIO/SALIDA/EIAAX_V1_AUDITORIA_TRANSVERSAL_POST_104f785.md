# EIAAX — Auditoría transversal post-104f785 (solo lectura)

**Fecha:** 2026-09-02  
**Rama autoritativa:** `cursor/convergencia-comercial-v1-85e4`  
**SHA auditado:** `104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a`  
**Estado respaldo Agente A:** **PENDIENTE — NO PASS**

---

## B. Respaldo utilizado como punto de recuperación

| Verificación | Resultado |
|---|---|
| Artefacto `*104f785*` en `INTERCAMBIO/RESPALDOS/` | **No encontrado** |
| Manifiesto `PASS — RESPALDO 104f785 VERIFICADO Y RECUPERABLE` | **No encontrado** |
| Respaldos existentes | `EIAAX_LOTE_3`, `EIAAX_CONVERGENCIA`, `EIAAX_PREINTEGRACION` (anteriores) |

**Consecuencia:** Toda modificación de producto permanece **BLOQUEADA** hasta confirmación PASS del Agente A.

---

## A. SHA inicial

`104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a` — `docs: actualizar SHA certificación ac166dc`

**Integridad protegida:** `git diff 0014a4b -- scripts/windows/` → **0 líneas** (intacto).

---

## E. Vistas auditadas (inventario de capacidad)

### Centro de Control (`CentroControlPage.tsx`)

**Tabs reales (6):** Resumen · Valor · Operación · IA y costos · Implementación · Salud  
*(Difieren de la lista humana de 8 tabs; no existen tabs separados «Empleados IA», «Ejecuciones», «Requiere atención», «Aprobaciones» como pestañas propias — están embebidos en Resumen/Operación.)*

| Tab | Contenido | Clasificación demo vacío |
|---|---|---|
| Resumen | `CentroControlCockpit`: KPIs, gráficos valor/consumo, atención, operación, oportunidades, aprobaciones | FUNCIONAL — puede mostrar ceros/vacío si BD demo sin datos |
| Valor | Tarjetas naturaleza + valoración económica + comercial | DEPENDIENTE DE DATOS — estados «Sin información disponible» |
| Operación | Empleados, oportunidades, líneas base, diagnóstico, mi trabajo, ejecuciones, aprobaciones, actividad | FUNCIONAL CON ESTADO VACÍO ÚTIL parcial |
| IA y costos | FinOps, planificador, TCO, proveedores | DEPENDIENTE DE CONFIGURACIÓN / datos |
| Implementación | Proyectos e hitos | DEPENDIENTE DE DATOS |
| Salud | Componentes inline + enlaces | FUNCIONAL |

**Hallazgo transversal A:** Encabezado (título + descripción + toolbar contexto + banner) + fila tabs antes del primer contenido accionable → **superficie muerta en primer viewport**. El cockpit existe pero queda bajo el pliegue.

**Hallazgo transversal A2:** Con contexto empresa (`?expediente=`) se renderiza `CentroControlEmpresaPanel` **además** de «Vista global del periodo» → duplicación vertical.

### Centro de Operaciones (`OperationsHubPage.tsx`)

| Elemento | Estado |
|---|---|
| Accesos rápidos (9 enlaces) | FUNCIONAL |
| Filtros búsqueda/estado/prioridad/vencimiento | FUNCIONAL |
| 6 indicadores bucket | FUNCIONAL — **todos en 0** en demo vacío |
| Tabla operaciones | FUNCIONAL — **vacía** sin seed operativo |
| Convergencia con otros módulos | **NO** — no agrega señales de evaluaciones/ejecuciones/aprobaciones existentes |

**Clasificación B:** FUNCIONAL CON ESTADO VACÍO — falta densidad y datos demo coherentes.

### Cabina evaluación (`EvaluacionConsolePage.tsx`)

10 tabs: Empresa · Diagnóstico · Solución IA · Operación · Consumo · Valor · Resultados · Informes · Contrato · Vista Empresa

| Tab | Capacidad | Brecha |
|---|---|---|
| Diagnóstico | Información adaptativa (texto) + hallazgos | **Sin upload de archivos** recibidos de IPS |
| Vista Empresa | `EspacioExternoAdminPanel` | Gestión entidad/publicación — **no carga documental** |
| Consumo | 3 campos + enlaces | Superficie mínima |
| Presentación | Enlaces a `/presentacion/:id` | Existe flujo |

### Configuración (`AdminConfigPage.tsx`)

8 tabs implementados (General, Identidad, Servicios, IA, Integraciones, Seguridad, Notificaciones, Experiencia).  
Identidad: `BrandMark level="corporativo"` sin CSS de contención + `EnterpriseLogoField` con límite 180 KB.

### Presentación (`PresentacionRealPage.tsx`)

Ruta `/presentacion/:expedienteId` — audiencias, PDF, `PresentacionView`.  
**No diferencia visualmente** «Presentar en reunión» vs «Publicar para consulta posterior» en la misma pantalla (publicación vive en Vista Empresa / espacio externo).

### Guía / instructivo

`GuiaRapidaPage` + `guiaRapidaHelp.ts` — 15 pasos con enlaces.  
**No existe** instructivo operativo V1 de 10 partes solicitado.

### Demo end-to-end

**No existe** entidad «CLÍNICA DEMO HORIZONTE» en seeds (`seed_lote3_demo.py` usa genérico «empresa demo»).

---

## F. Hallazgos transversales (priorizados)

### P0 — Usabilidad bloqueante

| ID | Área | Hallazgo | Evidencia |
|---|---|---|---|
| P0-1 | Logos | Límite frontend **180 KB** rechaza logos oficiales (~1–1.7 MB) | `EnterpriseLogoField.tsx` L3–27; backend permite 200 KB (`schemas_admin.py` L116) |
| P0-2 | Documentos IPS | Operador no tiene UX clara para cargar archivos recibidos en expediente | API adjuntos en `espacio_externo` (portal externo); `EspacioExternoAdminPanel` sin upload |
| P0-3 | E2E demo | Recorrido 28 pasos **no reproducible** — falta seed coherente Horizonte | Sin entidad en seeds |

### P1 — Experiencia grave

| ID | Área | Hallazgo |
|---|---|---|
| P1-1 | Menú | 50 ítems; Administración = 29. `.layout` usa `min-height:100vh` sin `height` fija → scroll de página en lugar de scroll lateral independiente en viewports reales |
| P1-2 | Centro Control | Marco vacío / baja densidad primer viewport |
| P1-3 | Centro Operaciones | Indicadores y tabla vacíos; no consola de dominio operativo |
| P1-4 | Tablas | Solo **6 pantallas** usan `EiaaxTable`; **KnowledgePage** expone checkboxes de columnas siempre visibles (panel permanente) |
| P1-5 | Identidad | `BrandMark corporativo` sin `max-height` CSS; imagen a resolución nativa en Config y sidebar |
| P1-6 | Presentación | Flujo operador → validación privacidad → reunión vs publicación **no evidente** en UI |

### P2 — Mejora / convergencia

| ID | Área | Hallazgo |
|---|---|---|
| P2-1 | Menú | Simplificación acordada pendiente: primarios vs Administración/Avanzado |
| P2-2 | CC tabs | Renombrar/agrupar para alinear con concepto maestro (8 dimensiones humanas) |
| P2-3 | Config | Compactar campos; reducir scroll |
| P2-4 | Instructivo | Ampliar guía 15 pasos → instructivo 10 partes con fuente mantenible |

---

## G. Opciones sin contenido (inventario menú — clasificación preliminar)

| Ruta | Clasificación preliminar | Notas |
|---|---|---|
| `/` | FUNCIONAL CON DATOS / VACÍO según BD | |
| `/ayuda/guia` | FUNCIONAL | 15 pasos, no instructivo completo |
| `/trabajo` | DEPENDIENTE DE DATOS | |
| `/operaciones` | FUNCIONAL CON ESTADO VACÍO | |
| `/operaciones/solicitud` | FUNCIONAL | |
| `/ejecuciones` | DEPENDIENTE DE DATOS | |
| `/aprobaciones` | DEPENDIENTE DE DATOS | |
| `/automatizaciones` | DEPENDIENTE DE DATOS | |
| `/empresas` | FUNCIONAL | |
| `/oportunidades` | DEPENDIENTE DE DATOS | |
| `/evaluaciones` | FUNCIONAL | |
| `/directorio` | DEPENDIENTE DE DATOS | |
| `/empleados/auditoria` | DEPENDIENTE DE CONFIGURACIÓN | |
| `/capacidades` | FUNCIONAL | |
| `/herramientas` | FUNCIONAL | |
| `/conocimiento` | FUNCIONAL | Upload global, no contextual expediente |
| `/test-lab` | SOLO DEMO / POST-V1 | Laboratorio técnico |
| `/resultados` | DEPENDIENTE DE DATOS | |
| `/costos-valor` | DEPENDIENTE DE DATOS | |
| `/comunicaciones` | DEPENDIENTE DE DATOS | |
| `/centro-confianza` | FUNCIONAL | |
| `/lineas-base` | DEPENDIENTE DE DATOS | |
| `/comercial` | DEPENDIENTE DE DATOS | |
| `/centro-negocios` | POST-V1 / ARQUITECTURA | Usuario cotidiano |
| `/arquitecto-transformacion` | POST-V1 / ARQUITECTURA | |
| `/tco` | ADMINISTRACIÓN | |
| `/implementacion` | DEPENDIENTE DE DATOS | |
| `/comercial/segmentacion` | ADMINISTRACIÓN | |
| `/partners` | DEPENDIENTE DE DATOS | |
| `/senales` | ADMINISTRACIÓN / AVANZADO | |
| `/diagnosticos` | DEPENDIENTE DE DATOS | |
| `/inteligencia-externa` | AVANZADO | |
| `/continuidad` | AVANZADO | |
| `/soporte` | FUNCIONAL | |
| `/integraciones` | DEPENDIENTE DE CONFIGURACIÓN | |
| `/aprendizaje` | AVANZADO | |
| `/optimizacion` | AVANZADO | |
| `/gobernanza-datos` | AVANZADO | |
| `/mi-seguridad` | FUNCIONAL | |
| `/notificaciones` | FUNCIONAL | |
| `/auditoria` | ADMINISTRACIÓN | |
| `/salud/diagnostico` | VERTICAL IPS | No menú cotidiano |
| `/administracion/*` | ADMINISTRACIÓN | 8 rutas |

---

## H–N. Detalle por bloque humano

### C. Menú / scroll (J)

- `AppShell.tsx`: secciones colapsables con persistencia `localStorage` (`eaios_menu_sections`, `eaios_menu_collapsed`) ✓
- `nav-hierarchical`: `flex:1; overflow-y:auto` ✓ en CSS
- **Problema:** `.layout { min-height: 100vh }` — sidebar crece con contenido → **scroll global** en 1366×768 con Administración expandida
- **Corrección planificada:** `height: 100vh; overflow: hidden` en layout; sidebar `position: sticky`; `scroll-margin` en ítem activo

### D. Tablas / columnas (J)

- `EiaaxTable`: botón «Columnas» con popover (`showCols` toggle) — **patrón correcto**
- Adopción: EvaluacionConsole, CentroConfianza, Oportunidades, Directory, ResultadosInteligencia (+ componente)
- **Anti-patrón confirmado:** `KnowledgePage.tsx` L173–194 — panel «Columnas:» con 8 checkboxes siempre visible
- Mayoría de pantallas: `data-table` directo sin estándar unificado

### E. Logos / identidad (K)

| Capa | Estado |
|---|---|
| Backend | `max_length=200000` para data URLs |
| Frontend upload | `MAX_BYTES = 180_000` — **inconsistencia** |
| Preview tenant | `max-height: 48px` ✓ |
| Marca madre Config | `BrandMark corporativo` — **sin CSS** `brand-mark--*` en styles.css; imagen a tamaño completo |
| Separación madre/tenant | Texto explicativo existe; visualmente marca madre domina |

### G. Carga documental (L)

**Capacidad existente (reutilizable):**

| Capacidad | Ubicación |
|---|---|
| Adjuntos versionados | `evaluacion_entrega_adjuntos`, migración `1820` |
| Upload portal externo | `POST /api/espacio-externo/mi-espacio/adjuntos` |
| Listado interno | `GET .../entregas/{id}/adjuntos` |
| Conocimiento global | `/conocimiento`, `KnowledgePage` |
| Información adaptativa | Texto en tab Diagnóstico |

**Gap UX:** Operador interno necesita flujo  
`Empresa → Evaluación → Información y documentos / Evidencias recibidas`  
con upload, categoría, confidencialidad, asociación expediente — **no expuesto**.

### M. Centro Control (M)

Revalidación concepto maestro: estructura por tabs + cockpit parcialmente alineada; falta **priorización inmediata** (cartera, siguiente acción global) en primer viewport sin scroll.

### N. Centro Operaciones (N)

Paradigma «consola operativa» declarado pero implementación = filtros + tabla genérica sin convergencia de señales.

---

## O–S. Ejercicio demo, E2E, presentación, instructivo

| Requisito | Estado |
|---|---|
| CLÍNICA DEMO HORIZONTE | **No existe** |
| Recorrido 28 pasos UI | **No verificable** |
| Modo Presentación | Ruta existe; flujo operador no evidente |
| Vista Empresa | Tab + espacio externo |
| Instructivo 10 partes | **No existe** (solo guía 15 pasos) |

---

## Plan de corrección (post-respaldo PASS)

Orden propuesto:

1. **Logos P0** — alinear límite con backend; resize client-side; CSS `brand-mark`; preview compacto madre
2. **Menú P1** — scroll lateral fijo; reagrupar primarios (≤15 visibles cotidianos)
3. **Documentos P0** — panel «Evidencias recibidas» en cabina Diagnóstico reutilizando API adjuntos interna (+ upload operador si falta endpoint)
4. **Seed Horizonte P0** — `seed_demo_horizonte.py` coherente end-to-end
5. **CC + Ops P1** — densificar viewport; estados vacío demo; convergencia datos
6. **Tablas P1** — migrar KnowledgePage + tablas críticas a patrón compacto
7. **Presentación P1** — wizard preparar → presentar → publicar
8. **Instructivo** — extender `guiaRapidaHelp.ts` como fuente única (10 partes)
9. Ciclo: pruebas → auditoría visual → E2E → persistencia → login

---

## T–AC. Pendiente de ejecución

| Sección | Estado |
|---|---|
| C. SHA final | Pendiente (sin cambios) |
| D. Rama trabajo | Pendiente creación post-respaldo |
| T. Pruebas funcionales | No iniciadas (bloqueo) |
| U. Regresión | No iniciada |
| V. Login preservado | Verificado intacto |
| W. scripts/windows | Verificado intacto |
| X. Persistencia/reinicio | Pendiente |
| AB. Evidencia visual | Pendiente post-corrección |
| AC. Comando Windows revisión humana | Existente en `GUIA_WINDOWS_PRUEBA_HUMANA.md` |

---

## Notificación

**AUDITORÍA SOLO LECTURA COMPLETADA — PRODUCTO NO MODIFICADO**

**BLOQUEO ACTIVO:** Esperando `PASS — RESPALDO 104f785 VERIFICADO Y RECUPERABLE` del Agente A.

Cuando el respaldo confirme PASS, retomar integración en el orden del plan anterior.
