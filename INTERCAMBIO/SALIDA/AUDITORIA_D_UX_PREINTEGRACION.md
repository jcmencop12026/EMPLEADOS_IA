# AUDITORÍA D — UX PRE-INTEGRACIÓN (V2 vs V1)

> **NOTIFICACIÓN VISIBLE (Agente D)**  
> **Estado:** Auditoría de solo lectura completada — **NO APTO para aplicar Norma Visual EIAAX todavía**.  
> **Alcance:** Identificación de deltas V2→V1, activos a proteger en convergencia y candidatas a Norma Transversal EIAAX.  
> **Regresiones:** P0=0 · P1=1 · P2=9  
> **Voz/TTS:** No disponible en este entorno Cloud Agent; notificación registrada únicamente en este documento.

---

## Metadatos

| Campo | Valor |
|-------|-------|
| Proyecto | EIAAX / EMPLEADOS_IA |
| Agente | D (visual / UX / español) |
| Modo | **SOLO LECTURA** — sin cambios de código |
| V1 (base) | `cursor/v1-integracion-final` @ `4c03cbe` |
| V2 (candidata Fase 2) | `cursor/convergencia-final-fase2-85e4` @ `dc1e6cd` |
| Fecha | 2026-08-31 (UTC) |
| Método | Diff estático (`AppShell`, `App.tsx`, `permissions.ts`, `styles.css`, 50+ páginas) + capturas Puppeteer 1280×900 y 1024×768 (`admin` / `Admin2026*`) |

---

## Resumen ejecutivo

V2 introduce una **expansión funcional y visual significativa** sobre V1: el home deja de ser un panel operativo simple (`DashboardPage`) y pasa a ser un **Centro de Control ejecutivo** con 6 pestañas; el menú lateral crece de **23 a 43 ítems** (+87%); se añaden **35 rutas** nuevas (70 vs 35); la identidad pasa de inglés comercial (“Enterprise AI OS”, “Test Lab”) a español empresarial (“Sistema empresarial de IA”, “Laboratorio de pruebas”); y aparecen patrones avanzados de bandeja (**Mi trabajo**), tablas con búsqueda/filtros/columnas persistentes y login ampliado (MFA/SSO).

**No se detectan regresiones P0.** Hay **1 P1** de convergencia (acceso al home condicionado por RBAC nuevo) y **9 P2** de consistencia/densidad/idioma residual. V2 corrige además varios hallazgos heredados de V1 (p. ej. `auth.login` crudo en auditoría del panel).

**Veredicto:** V2 es **APTA como base funcional de convergencia**, siempre que se **protejan** los activos listados en §6 y se planifique la Norma Transversal EIAAX sobre las pantallas de §7 **sin ejecutarla en este tramo**.

---

## 1. Sidebar

| Aspecto | V1 | V2 | Delta / riesgo |
|---------|----|----|----------------|
| Ítems visibles (admin) | 23 | 43 | +20 entradas; scroll vertical casi obligatorio en 1280px |
| Marca | `Enterprise AI OS` | `Sistema empresarial de IA` | Mejora idioma/identidad |
| Home | `Panel de control` → `/` | `Centro de Control` → `/` | Cambio semántico y de complejidad |
| Colapsable | Sí (`sidebar-collapsed`, `localStorage`) | Igual + persistencia secciones | **Proteger** mecanismo existente |
| Badge pendientes | Solo notificaciones (campana) | Campana + badge en **Mi trabajo** | Nuevo patrón V2 |
| Sección Análisis | 4 ítems | 18 ítems | Mayor carga cognitiva |
| Admin | 6 ítems | 7 (+ Identidad empresarial) | Extensión gobierno |

**Nuevas entradas V2 (20):** `/trabajo`, `/operaciones/solicitud`, `/empleados/auditoria`, `/lineas-base`, `/comercial`, `/tco`, `/implementacion`, `/comercial/segmentacion`, `/senales`, `/diagnosticos`, `/inteligencia-externa`, `/continuidad`, `/soporte`, `/integraciones`, `/aprendizaje`, `/optimizacion`, `/gobernanza-datos`, `/mi-seguridad`, `/comunicaciones`, `/administracion/identidad`.

**Renombres:** `Test Lab` → `Laboratorio de pruebas`; `Panel de control` → `Centro de Control`.

---

## 2. Navegación y rutas

| Aspecto | V1 | V2 |
|---------|----|----|
| Rutas `App.tsx` | ~35 | ~70 |
| Home `/` | `DashboardPage` (sin permiso) | `CentroControlPage` (**requiere** `control_center.view`) |
| Alias | — | `/centro-control` ≡ `/`; `/panel` → redirect `/` |
| `DashboardPage` | Activo en `/` | **Huérfano** (archivo existe, no enrutado) |
| RBAC menú | `filterMenuByPermissions` | Igual + `canAccessRoute` en badge trabajo |
| Redirect legacy | `/organizacion` → admin | Conservado |

**Duplicados conceptuales (no rutas idénticas):**

- **Costos y valor** (menú) ↔ pestaña **IA y costos** (CC).
- **Oportunidades / Comercial / TCO / Implementación** (menú) ↔ pestañas **Valor / Implementación** (CC).
- **Diagnóstico IPS** (Salud) vs **Diagnósticos** (Análisis) — módulos distintos, etiquetas parecidas.
- **Notificaciones** (menú) vs bandeja **Mi trabajo** (agrega aprobaciones, SLA, integraciones, etc.).

**Opciones sin función / placeholders:**

- V1: banner inferior en panel — *“Espacios reservados para integración futura: Automatizaciones y Notificaciones”* — **eliminado en V2** (mejora).
- V2 CC: múltiples KPI con *“Sin información disponible”* / *“Costo no disponible”* — estado vacío legítimo, no enlace roto.
- V2: `DashboardPage.tsx` residual — deuda técnica, no visible al usuario.

---

## 3. Headers y topbar

| Elemento | V1 | V2 |
|----------|----|----|
| Topbar | `EMPLEADOS_IA · Orquestador E2E · Workspace Salud` | `EMPLEADOS IA · Plataforma empresarial` |
| Campana | `/notificaciones` | Igual |
| Page headers | `page-header` estándar | + variantes `compact`, `compact-toolbar` en CC y módulos nuevos |
| Títulos ejecutivos | Panel simple | `Centro de Control ejecutivo` + subtítulo operativo |

---

## 4. Dashboards

| V1 — Panel de control | V2 — Centro de Control ejecutivo |
|-----------------------|----------------------------------|
| 6 tarjetas KPI (empleados, ejecuciones, aprobaciones) | 22+ indicadores en grid + secciones contextuales |
| Tabla actividad reciente (`event_type` API en inglés) | Pestañas: Resumen, Valor, Operación, IA y costos, Implementación, Salud |
| Tabla auditoría reciente (acciones API crudas) | Misma lógica en pestaña Salud con `formatAuditAction` |
| Placeholder integración futura | Selector periodo (MTD / 7d / 30d) + botón Actualizar |
| CSS `dashboard-grid` | CSS `metrics-grid`, `cc-metric-card`, `semantic-badge` |

**Hallazgo visual:** En V1, `OportunidadesPage` ya usaba clase `metrics-grid` pero **V1 `styles.css` no define `.metrics-grid`** → KPIs se renderizan como lista vertical. V2 incluye la regla CSS → tarjetas horizontales (mejora real).

**CC Salud:** estados API traducidos (`Operativa`); etiqueta **`Schedulers`** permanece en inglés (P2).

---

## 5. Tablas

| Capacidad | V1 | V2 |
|-----------|----|----|
| Clase base | `data-table`, `compact` | Igual + densidad variable por módulo |
| Búsqueda | Oportunidades, algunas admin | + Trabajo, Integraciones, Soporte, Líneas base, Optimización, Operaciones hub… |
| Filtros | Oportunidades (estado, dominio) | Múltiples módulos; Trabajo tiene 6 filtros + “Solo requiere acción” |
| Columnas show/hide | Oportunidades (`localStorage`) | + Trabajo, Usuarios admin, Integraciones |
| Orden ASC/DESC | Limitado | Trabajo (server-side), AdminUsers, Integraciones (client-side con ↑↓) |
| Paginación / registros por página | **No generalizado** | **No generalizado** (gap Norma EIAAX) |
| Columnas redimensionables | No | No |
| Persistencia | `oportunidades_cols`, sidebar | + `trabajo_cols_v1`, `integraciones_cols`, `admin_users_cols` |

---

## 6. Formularios

| Área | V1 | V2 |
|------|----|----|
| Login | Usuario/contraseña | + MFA, descubrimiento SSO por código org, flujo OIDC |
| Título login | `Enterprise AI OS` | `Sistema empresarial de IA` |
| Wizards | Empleado, automatización, operaciones | + Integración, comunicaciones (plantillas/reglas) |
| Grids | `form-grid`, `assign-grid` | Igual + formularios densos en TCO, Gobernanza datos, Comercial |
| Validación/error | Español en mensajes | Consistente; algunos valores API sin mapear en tablas secundarias |

---

## 7. Modales

| V1 | V2 |
|----|----|
| Uso muy limitado / inline | `ComunicacionesPage`: `modal-backdrop` + `card modal` (detalle/envío) |
| — | Detalle lateral en Trabajo (panel, no modal clásico) |
| — | Varios módulos usan `<details>` para columnas en lugar de modal |

**Patrón a unificar bajo Norma EIAAX:** modal único reutilizable vs mezcla modal / details / paneles.

---

## 8. Pestañas

| Pantalla | V1 | V2 |
|----------|----|----|
| CC / Home | — | 6 pestañas ejecutivas (`tab-bar compact-tabs`) |
| Diagnóstico IPS | `salud-tabs` | Conservado |
| Comunicaciones | — | 6 pestañas (bandeja, plantillas, reglas, canales, programadas, historial) |
| Detalle oportunidad | Secciones | Secciones ampliadas (cadena operativa, valoración 1210) |
| Admin LLM / Seguridad | Parcial | Más sub-secciones |

---

## 9. Responsive

| Breakpoint | Comportamiento |
|------------|----------------|
| `≤768px` | Layout columna; sidebar ancho completo (V1 y V2) |
| `≤900px` | Split salud a 1 columna |
| `≤960px` | Reglas adicionales CC/compact (V2) |

**Observación 1024px:** sidebar + contenido CC denso → scroll vertical elevado; sin regresión P0/P1, pero **P2 densidad**.

---

## 10. Textos e idioma español

| Categoría | V1 | V2 | Clasificación |
|-----------|----|----|---------------|
| Marca / shell | Inglés (`Enterprise AI OS`, `Test Lab`) | Español | Mejora V2 |
| Auditoría acciones | `auth.login` visible | `Inicio de sesión` vía `formatAuditAction` | Mejora V2 |
| Acciones no mapeadas | `bootstrap.admin_created` | `bootstrap · admin created` (fallback) | P2 |
| Salud CC | — | `Schedulers` | P2 |
| Eventos panel V1 | `WORK_REQUESTED`, etc. en tabla actividad | CC no replica esa tabla | Mejora indirecta |
| Códigos módulo en UI | Menor exposición | `Valoraciones 1210`, códigos OPP, tipos API (`COMERCIAL`) | P2 |
| Proveedores IA | — | `Azure OpenAI (preparado)` — marca producto, aceptable | — |

**Capa de traducción V2 a proteger:** `frontend/src/lib/labels.ts` (`formatAuditAction`, `formatHealthStatus`, mapas de estado).

---

## 11. Estados (loading / error / vacío)

| Patrón | V1 | V2 |
|--------|----|----|
| Componentes compartidos | `AsyncState` (Loading, Error, Empty) | Igual, uso extendido |
| CC sin permiso | N/A | Mensaje: *“No tiene permiso para ver el Centro de Control.”* |
| KPIs sin dato | — | *“Sin información disponible”*, *“Costo no disponible”* |
| Trabajo vacío | N/A | `EmptyState` *“Sin elementos”* |

---

## 12. Componentes compartidos

| Componente | V1 | V2 |
|------------|----|----|
| `AppShell` | Base | + badge trabajo, fetch resumen |
| `AsyncState` | Sí | Sí |
| `labels.ts` | Parcial | Ampliado (salud, auditoría) |
| `optimizacion/*` | — | `EstadoBadge`, `SemanticBadge`, `HelpTooltip` |
| `comercial/*` | — | Badges, tooltips, barras ciclo |
| CSS global | 1008 líneas | 1377 líneas (+369; CC, compact, semantic badges) |

---

## 13. Scroll y densidad

- **Sidebar V2:** ~43 ítems → scroll frecuente; secciones colapsables mitigan pero no eliminan.
- **CC Resumen:** grid 22 tarjetas en viewport único → alta densidad informativa.
- **Oportunidades V2:** KPI en cards + tabla 12 columnas → horizontal scroll posible.
- **V1 panel:** menor densidad, más aire; pierde vista ejecutiva consolidada.

---

## 14. Consistencia global

| Dimensión | Evaluación |
|-----------|------------|
| Paleta / tipografía | Coherente entre V1 y V2 (herencia `styles.css`) |
| Patrones de tabla | Heterogéneos: unas con sort, otras no; sin paginación estándar |
| Nomenclatura menú vs título página | Alineada en español salvo residuos técnicos |
| Permisos vs visibilidad | Menú filtra; CC bloquea en página si falta permiso |
| Identidad EIAAX | Marca española en shell; falta logo/guión EIAAX explícito |

---

## 15. Qué proteger durante la convergencia

### Crítico (no revertir)

1. **`CentroControlPage`** como home + ruta `/centro-control` y redirect `/panel`.
2. **CSS `metrics-grid`** y variantes `compact-*` / `centro-control-page`.
3. **`lib/labels.ts`** — especialmente `formatAuditAction` y `formatHealthStatus`.
4. **Renombres español:** marca shell, Test Lab, topbar.
5. **`TrabajoPage`** + API resumen + badge sidebar + permisos compuestos `/trabajo`.
6. **Mapa RBAC ampliado** en `permissions.ts` (20 rutas nuevas).
7. **Persistencia UX:** `localStorage` sidebar, columnas visibles, secciones menú.
8. **Login MFA/SSO** (flujos y copy español).
9. **37 páginas nuevas** y rutas asociadas (lista en diff `App.tsx`).
10. **Correcciones post-6E ya certificadas:** KPI CC legibles, `Operativa`, `Inicio de sesión`.

### Vigilar (riesgo de regresión en merge)

1. **Fallback home** para usuarios sin `control_center.view` (ver P1).
2. **No reintroducir** `Enterprise AI OS` / `Test Lab` en labels visibles.
3. **No eliminar** alias `/centro-control`.
4. **Evitar duplicar** lógica CC en `DashboardPage` huérfano — decidir en convergencia (eliminar o redirigir).
5. **Mantener** mejoras Oportunidades (cards KPI con CSS presente).

---

## 16. Candidatas a Norma Transversal EIAAX (solo identificación)

Leyenda de madurez actual vs norma: ✅ parcial · ⬜ pendiente

| Pantalla / ruta | Menú colapsable | Vista compacta | Pestañas | Búsqueda | Filtros | Paginación | Reg./página | Col. redim. | Mostrar/ocultar | ASC/DESC | Persistencia | Mín. scroll | Identidad EIAAX |
|-----------------|-----------------|----------------|----------|----------|---------|------------|-------------|-------------|-----------------|----------|--------------|-------------|-----------------|
| **AppShell** (global) | ✅ | ⬜ | — | — | — | — | — | — | — | — | ✅ sidebar | ⬜ | ⬜ |
| **/** Centro de Control | — | ✅ | ✅ | ⬜ | ✅ periodo | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ periodo UI | ⬜ | ⬜ |
| `/trabajo` | ✅ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ✅ | ✅ cols | ⬜ | ⬜ |
| `/oportunidades` | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ cols | ⬜ | ⬜ |
| `/integraciones` | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ✅ | ✅ cols | ⬜ | ⬜ |
| `/administracion/usuarios` | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ✅ | ✅ cols | ⬜ | ⬜ |
| `/comunicaciones` | ✅ | ⬜ | ✅ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/auditoria` | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/ejecuciones` | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/directorio` | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/lineas-base` | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/senales`, `/diagnosticos` | ✅ | ⬜ | ⬜ | parcial | parcial | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/soporte` | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/aprendizaje`, `/optimizacion` | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/costos-valor`, `/gobernanza-datos` | ✅ | ⬜ | ⬜ | parcial | parcial | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| `/salud/diagnostico` (IPS) | ✅ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Módulos admin (roles, LLM, seguridad, identidad) | ✅ | ⬜ | parcial | parcial | parcial | ⬜ | ⬜ | ⬜ | parcial | parcial | parcial | ⬜ | ⬜ |
| Detalles (`*:id`) — 20+ rutas | ✅ | ⬜ | parcial | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

**Prioridad sugerida para Norma EIAAX (post-convergencia):** AppShell → CC → Mi trabajo → Oportunidades → Integraciones → Auditoría → resto de listados.

---

## 17. Regresiones clasificadas (P0 / P1 / P2)

### P0 — Bloqueantes
*Ninguna detectada.* Login, navegación principal y módulos core operan en V2 con credenciales demo.

### P1 — Altas (corregir antes o durante convergencia)

| ID | Hallazgo | V1 | V2 | Acción convergencia |
|----|----------|----|----|---------------------|
| **P1-D-UX-01** | Home `/` exige `control_center.view`; usuarios sin permiso pierden landing (V1 era abierto a todos los autenticados) | Abierto | Restringido | Definir fallback (`/trabajo` o panel reducido) o rol por defecto |

### P2 — Medias / cosméticas / deuda

| ID | Hallazgo | Notas |
|----|----------|-------|
| **P2-D-UX-01** | Etiqueta inglesa `Schedulers` en CC pestaña Salud | `CentroControlPage.tsx` ~L602 |
| **P2-D-UX-02** | `bootstrap.admin_created` sin entrada en `AUDIT_ACTION` | Fallback inglés en `/auditoria` |
| **P2-D-UX-03** | Sidebar 43 ítems — scroll y truncado (`Centro de oportunidad…` en V1; riesgo mayor en V2) | Densidad navegación |
| **P2-D-UX-04** | Duplicidad menú ↔ pestañas CC (costos, valor, implementación) | Riesgo desorientación |
| **P2-D-UX-05** | KPI `Valor potencial` en CC sin formato moneda (`7300000` vs `$ 7.300.000` en Oportunidades) | Consistencia numérica |
| **P2-D-UX-06** | Códigos de módulo visibles (`1210`, tipos `COMERCIAL`, `AUTOMATIZACION`) | Identidad ejecutiva |
| **P2-D-UX-07** | Sin paginación estándar ni “registros por página” en tablas largas | Gap Norma EIAAX |
| **P2-D-UX-08** | `DashboardPage.tsx` huérfano en V2 | Deuda / confusión mantenimiento |
| **P2-D-UX-09** | V1: clase `metrics-grid` en Oportunidades sin CSS (KPIs apilados) — **corregido en V2** | No reintroducir al merge |

### Mejoras V2 sobre V1 (no regresiones — proteger)

- Traducción shell y Test Lab.
- `formatAuditAction` / `formatHealthStatus`.
- Tarjetas KPI Oportunidades con CSS.
- Bandeja Mi trabajo unificada.
- Eliminación placeholder “integración futura” del panel.
- Login MFA/SSO con copy español.

---

## 18. Evidencia visual

| Archivo | Descripción |
|---------|-------------|
| `v1_home.png` | Panel de control V1 — 6 KPI + actividad/auditoría |
| `v2_home.png` | Centro de Control V2 — pestaña Resumen, 22 indicadores |
| `v1_test-lab.png` / `v2_test-lab.png` | Renombre Test Lab → Laboratorio de pruebas |
| `v1_auditoria.png` / `v2_auditoria.png` | `auth.login` crudo vs `Inicio de sesión` |
| `v1_oportunidades.png` / `v2_oportunidades.png` | KPI lista vs cards |
| `v2_trabajo.png` | Nueva bandeja con filtros y columnas |
| `v2_cc_salud.png` | Pestaña Salud — `Schedulers` en inglés |
| `v2_home_1024.png` | Vista responsive 1024px |

Ruta artefactos: `/opt/cursor/artifacts/screenshots/`

---

## 19. Veredicto Agente D

| Criterio | Resultado |
|----------|-----------|
| ¿V2 lista para convergencia técnica? | **SÍ**, con protección de activos §15 |
| ¿Aplicar Norma Visual EIAAX ahora? | **NO** — solo identificación §16 |
| P0 / P1 / P2 | **0 / 1 / 9** |
| Aptitud pre-integración UX | **APTA CON CONDICIONES** (resolver P1-D-UX-01 en diseño de convergencia) |

---

## 20. Próximos pasos recomendados (fuera de este pedido)

1. Decidir política de landing para roles sin `control_center.view`.
2. Congelar checklist de protección §15 en plan de merge.
3. Priorizar candidatas §16 para oleada Norma Transversal EIAAX.
4. Cerrar P2 idioma (`Schedulers`, `bootstrap.admin_created`) en sprint de pulido post-convergencia.

---

*Documento generado por Agente D — modo solo lectura. Sin modificaciones al repositorio de aplicación.*
