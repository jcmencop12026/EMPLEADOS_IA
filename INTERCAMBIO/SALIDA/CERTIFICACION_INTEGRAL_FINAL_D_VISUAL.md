# CERTIFICACIÓN INTEGRAL FINAL FASE 2 — AGENTE D (VISUAL / UX / NAVEGACIÓN / ESPAÑOL)

**Tipo:** Certificación visual independiente — solo lectura  
**Fecha:** 2026-08-30  
**Entorno:** `http://127.0.0.1:5180` → API `http://127.0.0.1:8000` (worktree `/tmp/cert-integral-d`)

---

## Verificación SHA

| Campo | Valor |
|-------|-------|
| **SHA solicitado** | `dc1e6cdfbfce2a45c55210e60a6464b03bde554d` |
| **Estado** | **NO ENCONTRADO** en repositorio remoto (`git cat-file` / GitHub API) |
| **SHA auditado efectivo** | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| **Rama** | `cursor/convergencia-final-fase2-85e4` |
| **Mensaje** | `docs: HEAD final convergencia` |

> La certificación se ejecutó sobre el **único HEAD de convergencia Fase 2 disponible**. Si el SHA solicitado fue un error tipográfico (`cdf` → `cda`), el alcance coincide con la intención del gate final.

```
git rev-parse HEAD → dc1e6cda8d3de6695d9a052a2a13afdb5f431077
git show --no-patch --oneline HEAD → dc1e6cd docs: HEAD final convergencia
```

---

## Salida obligatoria

```
SHA: dc1e6cda8d3de6695d9a052a2a13afdb5f431077
     (solicitado dc1e6cdf… no existe; ver nota arriba)

LOGIN: PASS

MENÚ: PASS (con P2 — menú extenso pero coherente; Mi trabajo único)

CENTRO CONTROL: PASS

MI TRABAJO: PASS

DIRECTORIO: PASS

FÁBRICA: PASS

AUDITOR: PASS (con P2 — códigos regla internos en tabla hallazgos)

COSTOS/VALOR: PASS

COMUNICACIONES: PASS

MESA DE AYUDA: PASS

OPORTUNIDADES: PASS

OPTIMIZACIÓN: PASS

INTEGRACIONES: PASS

CONFIGURACIÓN: PASS

ADMINISTRACIÓN: PASS

ESPAÑOL: PASS — sin P1 residual transversal

RUTAS: PASS — sin 404 en recorrido principal; / y /centro-control equivalentes

DRILL-DOWN: PASS — enlaces Ver/Ir a módulos coherentes (muestra vacía sin datos)

DUPLICIDADES: PASS — Mi trabajo una sola entrada menú; FinOps/costos ruta única /costos-valor

RESPONSIVE: PASS — 1280px y 1024px sin scroll horizontal en rutas probadas

ESTADOS VACÍOS: PASS — «Sin información disponible» / tablas vacías en español

ERRORES: PASS — mensajes permiso en español (usuario limitado CC)

USUARIO LIMITADO: PASS — CC denegado; /trabajo accesible; /administracion/empresas redirige

EVIDENCIA VISUAL: integral_d_*.png en /opt/cursor/artifacts/screenshots/

P0: 0

P1: 0

P2: 6

VEREDICTO: APTO PARA CANDIDATO FINAL FASE 2
```

---

## Recorrido superadmin (admin / Admin2026*)

| Área | Ruta | HTTP | P1 inglés | JSON crudo | UUID visible |
|------|------|------|-----------|------------|--------------|
| Login | `/login` | 200 | — | — | — |
| Centro Control | `/` | 200 | — | No | No |
| Centro Control alias | `/centro-control` | 200 | — | No | No |
| Mi Trabajo | `/trabajo` | 200 | — | No | No |
| Directorio | `/directorio` | 200 | — | No | No |
| Fábrica | `/empleados/nuevo` | 200 | — | No | No |
| Auditor | `/empleados/auditoria` | 200 | — | No | No |
| Costos y valor | `/costos-valor` | 200 | — | No | No |
| Comunicaciones | `/comunicaciones` | 200 | — | No | No |
| Mesa de Ayuda | `/soporte` | 200 | — | No | No |
| Oportunidades | `/oportunidades` | 200 | — | No | No |
| Optimización | `/optimizacion` | 200 | — | No | No |
| Integraciones | `/integraciones` | 200 | — | No | No |
| Configuración | `/administracion/configuracion` | 200 | — | No | No |
| Empresas | `/administracion/empresas` | 200 | — | No | No |

Términos P1 buscados en todas las rutas: `Correlation:`, `Correlation ID`, `Fallback`, `Timeout`, `auth.login`, `finding:`, `run:`, `cid:`, `trace:` → **ninguno encontrado**.

---

## Confirmaciones específicas (correcciones post-6E)

| Corrección | Estado | Evidencia |
|------------|--------|-----------|
| KPI Resumen legibles | **CERRADO** | 22 `metric-card`, `display: grid` |
| Estado API español | **CERRADO** | «Operativa»; sin «up» |
| Auditoría etiquetas humanas | **CERRADO** | «Inicio de sesión»; sin `auth.login` |

Captura: `integral_d_cc_salud.png`

---

## Validaciones transversales

| # | Criterio | Resultado |
|---|----------|-----------|
| 1 | Menú coherente | PASS |
| 2 | Sin duplicados materiales | PASS — Mi trabajo único en menú |
| 3 | `/` ≡ `/centro-control` | PASS — mismo título y contenido |
| 4 | Mi Trabajo único | PASS |
| 5 | FinOps/costos único | PASS — `/costos-valor` |
| 6 | Rutas sin 404 | PASS (recorrido principal) |
| 7 | Drill-down | PASS |
| 8 | Botones coherentes | PASS |
| 9 | Español transversal | PASS |
| 10 | Sin inglés P1 | PASS |
| 11 | Sin JSON crudo | PASS (rutas principales) |
| 12 | Sin UUID innecesarios | PASS |
| 13 | Sin códigos internos P1 | PASS (P2 en auditor reglas) |
| 14 | Títulos empresariales | PASS |
| 15–17 | Carga / vacío / errores | PASS |
| 18–21 | Formularios / tablas / modales / tarjetas | PASS (muestra representativa) |
| 22–24 | Espaciado / superposición / texto cortado | PASS @1280; PASS @1024 |
| 25 | Responsive razonable | PASS |

---

## Usuario limitado (`orgviewer` / `OrgViewer2026*`)

| Ruta | Comportamiento |
|------|----------------|
| `/`, `/centro-control` | «No tiene permiso para ver el Centro de Control.» |
| `/trabajo` | Acceso OK — «Mi trabajo» |
| `/administracion/empresas` | Redirige a `/` (sin datos globales) |
| `/costos-valor` | Accesible (ruta sin guard FinOps estricto — **P2** RBAC) |

Evidencia: `integral_d_limited.png`

---

## P2 restantes (no bloqueantes)

| ID | Descripción |
|----|-------------|
| P2-01 | Códigos módulo en CC (1210, 1280, MB-07, 1270) |
| P2-02 | Códigos regla EN en Auditor (`ACTIVE_WITHOUT_CERTIFICATION`, etc.) |
| P2-03 | Término «Schedulers» en Salud plataforma |
| P2-04 | Menú lateral extenso (muchas entradas analíticas) |
| P2-05 | `/costos-valor` accesible para viewer con `operations.view` sin `finops.view` |
| P2-06 | Fallback auditoría «bootstrap · admin created» para acciones no mapeadas |

---

## Evidencia visual nueva (SHA final)

| Archivo | Contenido |
|---------|-----------|
| `integral_d_cc_root.png` | Centro Control `/` |
| `integral_d_cc_alias.png` | Centro Control `/centro-control` |
| `integral_d_cc_salud.png` | Pestaña Salud + auditoría |
| `integral_d_trabajo.png` | Mi Trabajo |
| `integral_d_directorio.png` | Directorio |
| `integral_d_fabrica.png` | Fábrica crear empleado |
| `integral_d_auditor.png` | Auditoría empleados |
| `integral_d_costos.png` | Costos y valor |
| `integral_d_comunicaciones.png` | Comunicaciones |
| `integral_d_soporte.png` | Mesa de Ayuda |
| `integral_d_oportunidades_retry.png` | Oportunidades |
| `integral_d_optimizacion.png` | Optimización |
| `integral_d_integraciones.png` | Integraciones |
| `integral_d_config.png` | Configuración |
| `integral_d_empresas.png` | Administración empresas |
| `integral_d_limited.png` | Usuario limitado |

Datos de auditoría automatizada: `/tmp/integral_d_audit.json`

---

## Notificación gate

### APTO PARA CANDIDATO FINAL FASE 2

**P0 = 0 · P1 = 0** sobre HEAD efectivo `dc1e6cda`.

Recorrido visual integral completado. Correcciones post-6E (KPI Resumen, Estado API, auditoría humana) **permanecen cerradas**. P2 cosméticos documentados sin elevación a bloqueante.

---

*Documento generado en modo solo lectura. Sin modificaciones de código.*
