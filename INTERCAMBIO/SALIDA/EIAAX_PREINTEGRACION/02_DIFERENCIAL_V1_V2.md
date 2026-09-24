# 02 — Diferencial V1 ↔ V2 (pre-inventario mínimo)

**V1 certificado:** `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81`
**V2 certificado:** `dc1e6cda8d3de6695d9a052a2a13afdb5f431077`
**Merge-base común:** `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4`
**Commits V1→V2:** 116
**Diff agregado:** 376 archivos, +85 124 / −886 líneas

---

## Resumen ejecutivo

V2 es un **superset funcional** de V1 con 32 migraciones Alembic adicionales, ~47 tests nuevos, y expansión masiva de backend (routers, modelos, servicios) y frontend (36 páginas nuevas). V1 certificado permanece operativo y acotado. Existe un **hotfix V1 login** (`1a85532`, 5 commits sobre `e8cb853`) **no presente** en V2 certificado.

---

## A. Componentes nuevos en V2 (no existen en V1)

### Backend — routers / dominios nuevos

| Módulo | Router / área |
|---|---|
| FinOps trazabilidad | `1110` |
| Señales reales | `senales` |
| Línea base / impacto | `linea_base` |
| Valoración económica / ROI | `valoracion` |
| Diagnóstico transversal | `diagnosticos` |
| Inteligencia externa | `inteligencia_externa` |
| Aprendizaje / repriorización | `aprendizaje` |
| Optimización | `optimizacion` |
| Modelo comercial | `comercial` |
| TCO / ecosistema | `tco` |
| Segmentación planes | `segmentacion` |
| Integraciones reales | `integraciones` |
| Implementación éxito cliente | `implementacion` |
| Seguridad avanzada / MFA | `security` |
| Identidad empresarial SSO | `identidad` |
| SCIM aprovisionamiento | `scim` |
| Gobernanza datos | `governance` |
| Continuidad / resiliencia | `continuidad` |
| Centro de Control | `control_center` |
| Mi Trabajo central | `trabajo` |
| Comunicaciones MB-11 | `comunicaciones` |
| Mesa ayuda MB-12 | `soporte` |
| Auditor empleados MVP | `empleados_auditor` |
| Planificador consumo MB-07 | (modelos + servicios) |
| Ciclo fábrica MB-06 | (migración `6b06`, eventos) |

### Frontend — páginas nuevas (muestra)

`CentroControlPage`, `ComercialPage`, `ComunicacionesPage`, `DiagnosticosPage`, `IntegracionesPage`, `InteligenciaExternaPage`, `OptimizacionPage`, `GobernanzaDatosPage`, `ContinuidadPage`, `EmployeeAuditorPage`, `ImplementacionPage`, y ~25 vistas detalle/wizard asociadas.

### Migraciones Alembic V2 exclusivas (32 revisiones nuevas)

Desde `1110a1b2c3d4e` hasta `1341a1b2c3d4e` (head V2), incluyendo merges de convergencia `1250*`, `1365*`, `14b0*`.

---

## B. Modificaciones sobre base V1 (archivos compartidos alterados)

| Área | Cambio relevante |
|---|---|
| `backend/app/main.py` | +20 imports modelos, +18 routers, schedulers/handlers adicionales |
| `backend/app/routers/auth.py` | V1: login simple. V2: MFA, recuperación, change password, sesiones |
| `frontend/src/App.tsx` / `AppShell.tsx` | Rutas y menú expandidos (~3x) |
| `frontend/src/api.ts` | V2: más endpoints; **bug orden `text`/`!res.ok` corregido solo en hotfix V1** |
| `frontend/src/auth/permissions.ts` | RBAC ampliado (74+ permisos en V2) |
| `backend/alembic/migration_ledger.json` | baseline_head `d1e2f3a4` → `1341a1b2c3d4e` |
| `docker-compose.yml` | Sin cambio estructural mayor entre SHAs (misma topología 3 servicios) |

---

## C. Conflictos potenciales (integración)

| ID | Conflicto | Severidad |
|---|---|---|
| C-01 | **32 migraciones** V2 sobre misma BD V1 sin staging | CRÍTICA |
| C-02 | `auth.py` reescrito en V2 vs login V1 simple | ALTA |
| C-03 | Hotfix `api.ts`/`LoginPage.tsx` en V1 no mergeado a V2 | ALTA |
| C-04 | RBAC/permisos: V2 asume roles/permisos nuevos | ALTA |
| C-05 | `frontend/src/api.ts` duplicados Mi Trabajo (ya corregido en V2 tramo 6D) | MEDIA |
| C-06 | Menú/navegación: V2 unifica CC; V1 menú reducido | MEDIA |
| C-07 | Scripts Windows V1_CERT solo en rama hotfix | BAJA (operacional) |

---

## D. Reemplazos (V2 sustituye comportamiento V1)

| V1 | V2 |
|---|---|
| Login/auth mínimo | Auth + MFA + recuperación + sesiones |
| Navegación reducida | Shell unificado + Centro Control |
| Sin Mi Trabajo central | `trabajo.router` + bandejas integradas |
| Sin módulos comerciales/FinOps | Módulos completos 1110–1340 |

---

## E. Duplicados / solapamientos

- Capabilities/tools/knowledge: extendidos, no duplicados limpios
- Notificaciones (`820a*`): base común, V2 añade comunicaciones MB-11 encima
- Orchestration/work plans: base V1, V2 añade optimización/aprendizaje

---

## F. Migraciones incompatibles / salto

| Punto | Detalle |
|---|---|
| Head V1 | `d1e2f3a4b5c6` |
| Head V2 | `1341a1b2c3d4e` |
| Salto | 32 revisiones lineales + merges |
| Riesgo | `alembic upgrade head` sobre BD V1 productiva **sin backup** = NO-GO |
| Mecanismo | `migration_ledger.json` + `migration_control.py` (fail-closed) |

---

## G. Riesgos de regresión (preview)

- Login UI/UX V1 hotfix perdido si se despliega V2 sin cherry-pick
- Permisos: usuario `superadmin` V1 puede no mapear nuevos permisos V2
- CORS/puertos: si cambia `FRONTEND_PORT` entre entornos
- Schedulers V2 (automation, proactive, communications) activos al arrancar

---

## H. Capacidades V1 que podrían perderse si integración es bruta

| Capacidad V1 | Riesgo |
|---|---|
| Simplicidad auth (sin MFA obligatorio) | MFA V2 puede bloquear login |
| Menú reducido / curva aprendizaje baja | Sobrecarga UI |
| Scripts PASO1/PASO2 V1_CERT | No aplican a V2 sin adaptación |
| Estabilidad certificada `e8cb853` | Regresión si merge masivo |

---

## I. Cambios visuales

| Elemento | V1 | V2 |
|---|---|---|
| Login | Básico (hotfix: ojo contraseña, olvidó) | Sin hotfix; shell expandido post-login |
| Centro Control | No | Sí (`CentroControlPage`, alias `/centro-control`) |
| Etiquetas ES | Parcial | Normalización focal post-6E |
| KPI cards CSS | Hotfix focal | Corregido en `dc1e6cd` |

---

## J. Decisiones que requieren integración selectiva

1. **Cherry-pick hotfix login V1** (`beb1760`..`1a85532`) sobre rama convergencia — solo `api.ts`, `LoginPage.tsx`, `styles.css` (+ tests).
2. **Auth backend:** mantener MFA V2 pero validar login bootstrap admin V1.
3. **Migraciones:** aplicar en entorno staging con dump V1 restaurado, no en CERT directo.
4. **Scripts Windows:** mantener separados V1_CERT vs convergencia hasta estabilizar compose.
5. **No merge `e8cb853` → `dc1e6cd`:** usar V2 como base + parches selectivos V1.

---

## Hotfix V1 pendiente de integrar (referencia)

| SHA | Descripción |
|---|---|
| `beb1760` | fix api.ts, LoginPage, scripts admin |
| `1a85532` | PASO2 compose definitivo |

Diff V2 vs hotfix en `frontend/src/api.ts`: V2 **no** tiene fix orden `text` antes de `!res.ok`.

---

## Matriz rápida por capa

| Capa | V1 | V2 | Delta |
|---|---|---|---|
| Migraciones | 21 | 53 | +32 |
| Tests | 52 archivos | 99 archivos | +47 |
| Páginas FE | 33 | 69 | +36 |
| Routers BE | ~15 | ~35 | +20 |
| Permisos | base | 74+ documentados | ampliado |
