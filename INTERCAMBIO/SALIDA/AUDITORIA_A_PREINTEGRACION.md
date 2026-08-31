# AUDITORÍA A — PRE-INTEGRACIÓN V1 + V2/FASE 2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** A  
**Modo:** Solo lectura — sin modificar código, sin merge, sin tocar ramas certificadas  
**Fecha:** 2026-08-31  
**Pregunta guía:** ¿Qué debemos vigilar para integrar V2 sin perder V1?

---

## Verificación SHA obligatoria

| Candidato | SHA completo | Mensaje commit | Verificación |
|-----------|--------------|----------------|--------------|
| **V1** | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` | `docs: HEAD final 25d73fc en informe candidata R2` | `git cat-file -t` → **commit** ✓ |
| **V2** | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` | `docs: HEAD final convergencia` (`cursor/convergencia-final-fase2-85e4`) | `git cat-file -t` → **commit** ✓ |

**Merge-base común:** `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` (ancestro antiguo; ramas hermanas divergentes).

**Magnitud del delta:** 376 archivos, +85 124 / −886 líneas (excl. `node_modules`).

**Worktrees de auditoría:** `/tmp/audit-v1-preint` @ e8cb853 · `/tmp/audit-v2-preint` @ dc1e6cd.

---

## Resumen ejecutivo

V2 es una **extensión aditiva** sobre el núcleo V1: conserva los 20 routers V1, añade 21 routers Fase 2, no elimina permisos V1 ni archivos de test V1, y la suite de certificación V1 **pasa íntegramente** sobre V2 (44 tests focalizados). El riesgo principal no es pérdida silenciosa de V1 en el código base de V2, sino **(a)** divergencia operativa post-V1 en la rama caliente `cursor/v1-hotfix-login-acceso-85e4` aún no portada, **(b)** cambio de contrato de autenticación (sesiones `sid`, MFA, SSO), **(c)** cambio de UX de entrada (`/` deja de ser `DashboardPage`), y **(d)** impracticabilidad de un merge masivo directo por volumen y genealogía.

**Veredicto al final del documento.**

---

## Salida obligatoria (clasificación)

```
SHA V1: e8cb853a2c447fd5e136a0907e44d68ce2c8cf81 ✓
SHA V2: dc1e6cda8d3de6695d9a052a2a13afdb5f431077 ✓

ARQUITECTURA: VIGILAR — V2 aditiva (+21 routers, +32 migraciones, +47 tests); merge-base 4c03cbe; merge masivo NO recomendado.
CENTRO CONTROL: VIGILAR — nuevo home V2 (CentroControlPage); V1 DashboardPage huérfano; API GET-only /api/centro-control/* preserva gobierno.
MI TRABAJO: VIGILAR — bandeja única nueva /api/trabajo/*; no existía en V1; CC consume vía adaptadores.
FINOPS: VIGILAR — endpoints V1 preservados; MB-07 planner añadido (/api/finops/planner/*); sin eliminación de rutas V1.
GOBIERNO: PRESERVADO EN V2 — Auditor→Humano→Fábrica; CC solo lectura; permisos V1 intactos (+107 nuevos).
G1-G4: PRESERVADO — test_gate_post6d_correcciones + convergencia_final_fase2: 21 passed en V2.
CAS: PRESERVADO — tests de concurrencia/idempotencia presentes en V2; sin debilitación detectada.
VALOR: PRESERVADO EN V2 — VERIFICADO/ESTIMADO/POTENCIAL; módulos 1210/1280 añadidos sin romper contrato V1.
SEMÁNTICA: PRESERVADO EN V2 — HECHO/INFERENCIA/RECOMENDACIÓN extendida a CC, trabajo, auditor, diagnóstico.
MULTIPROVEEDOR: MEJORA V2 — gateway openai/anthropic/azure/gemini/ollama; Ollama opcional (no obligatorio).
INTEGRACIONES: NUEVO V2 — bloque 1330 + rutas /integraciones; ausente en V1 (aditivo).
MAPA FINAL: COHERENTE EN V2 — App.tsx alineado con MAPA_FINAL_PLATAFORMA_FASE2.md; rutas V1 core conservadas.
SECRETOS: SIN REGRESIÓN DETECTADA — sin hardcodes productivos nuevos; contraseñas solo en fixtures de test.

P2 REEVALUADOS: 11 ítems — ninguno reclasificado P0/P1 (sección 15).

P0: 0
P1: 4
P2: 11

VEREDICTO: APTO PARA INICIAR CONVERGENCIA
```

---

## 1. Funcionalidad nueva en V2 (no presente en V1)

### 1.1 Routers backend nuevos (21)

| Router | Dominio |
|--------|---------|
| `control_center` | Centro de Control ejecutivo (1230) |
| `trabajo` | Bandeja humana unificada |
| `empleados_auditor` | Auditor de empleados (MB) |
| `comunicaciones` | MB-11 |
| `soporte` | MB-12 Mesa de ayuda |
| `optimizacion` | 1290 |
| `comercial` | 1280 |
| `diagnosticos` | 1220 |
| `senales` | 1120 |
| `valoracion` | 1210 |
| `linea_base` | 1200 |
| `aprendizaje` | 1260 |
| `integraciones` | 1330 |
| `inteligencia_externa` | 1240 |
| `continuidad` | 1360 |
| `governance` | 1350 |
| `security` | 1300 MFA/políticas |
| `identidad` | 1370 SSO |
| `scim` | 1380 aprovisionamiento |
| `segmentacion` | 1310 |
| `tco` | 1320 |
| `implementacion` | 1340 |

**Routers V1:** 20 en ambos candidatos; **ninguno eliminado**.

### 1.2 Migraciones Alembic

- **V1:** 21 archivos en `backend/alembic/versions/`
- **V2:** 53 archivos (+32, cadenas 1100–1507, merges 1250a/b/f, 1365, 14b0)
- **Head V2:** `1341a1b2c3d4e` (centro comunicaciones MB-11) + extensiones posteriores en la misma rama

**Vigilar:** aplicar cadena completa en entornos que parten de esquema V1; validar round-trip y backup previo.

### 1.3 Frontend — rutas nuevas (extracto)

Rutas V2 no en V1: `/centro-control`, `/trabajo`, `/empleados/auditoria`, `/lineas-base`, `/comercial/*`, `/tco`, `/implementacion/*`, `/senales/*`, `/diagnosticos/*`, `/inteligencia-externa/*`, `/continuidad`, `/soporte/*`, `/integraciones/*`, `/aprendizaje/*`, `/optimizacion/*`, `/gobernanza-datos`, `/comunicaciones`, `/mi-seguridad`, `/administracion/identidad`, `/administracion/usuarios/:userId`.

### 1.4 Tests

- **V1:** 42 archivos `test_*.py`
- **V2:** 89 archivos (+47)
- **Eliminados respecto a V1:** **0**
- Tests V1 de certificación presentes en V2: `test_p0_precertificacion_v1.py`, `test_integration_v1_final.py`, `test_docker_database_url.py`, etc.

---

## 2. Funcionalidad V1 modificada en V2

| Área | V1 (e8cb853) | V2 (dc1e6cd) | Impacto integración |
|------|--------------|--------------|---------------------|
| **Home UI** | `DashboardPage` en `/` | `CentroControlPage` en `/` y `/centro-control` | Cambio intencional Fase 2; bookmarks y formación de usuarios V1 |
| **auth.py** | Login simple → JWT | Login + MFA + recuperación + rate limit + sesiones `sid` | Clientes/scripts V1 que asumen JWT plano deben adaptarse |
| **deps.py** | `get_current_user` | + validación sesión `sid`, `get_mfa_pending_user` | Tokens V1 sin `sid` **rechazados** en V2 |
| **permissions.py** | ~496 líneas | ~913 líneas (+107 códigos) | Sin eliminaciones; roles V1 deben mapear permisos nuevos si se usan módulos Fase 2 |
| **gateway.py** | openai + ollama | + anthropic, azure-openai, gemini, routing service | Aditivo; proveedores V1 siguen válidos |
| **finops.py** | Endpoints V1 | + `/planner/*`, economics por oportunidad | Aditivo |
| **LoginPage.tsx** | Formulario básico | + MFA, SSO/OIDC, descubrimiento org | Sustituye flujo simple; ver hotfix V1 no portado |
| **App.tsx** | 20 rutas core | 50+ rutas con `RequirePermission` granular | Rutas V1 core preservadas salvo home |

---

## 3. Funcionalidad V1 potencialmente perdida

### 3.1 P1 — Rama caliente V1 no absorbida por V2

La rama `origin/cursor/v1-hotfix-login-acceso-85e4` contiene **5 commits posteriores a e8cb853** ausentes en dc1e6cd:

| Commit | Contenido | Estado en V2 |
|--------|-----------|--------------|
| `beb1760` | `api.ts` — `userMessage(status, detail, path)`; lectura de `text` antes de `!res.ok`; scripts admin | **NO portado** |
| `7d27cb7` | Informe recuperación acceso | Solo docs |
| `15aafe8` | Scripts Windows robustos | **NO en V2** |
| `a84b2c3` | Deploy frontend sin templates Docker frágiles | **NO en V2** |
| `1a85532` | PASO2 docker compose override | **NO en V2** |

**Evidencia `api.ts` (bug + mensaje login):**

En **ambos** SHA auditados, `frontend/src/api.ts` usa `parseDetail(text)` en la rama de error **antes** de `const text = await res.text()` — orden incorrecto que el hotfix corrige:

```72:95:frontend/src/api.ts
  if (!res.ok) {
    const detail = parseDetail(text);  // text aún no definido
    ...
  }
  ...
  const text = await res.text();
```

En el hotfix (`beb1760`), `userMessage` distingue 401 en login:

```typescript
if (path === "/api/auth/login") return detail || "Credenciales incorrectas";
```

En V2, `userMessage` sigue devolviendo siempre *"Su sesión ha vencido"* para cualquier 401.

**Clasificación:** P1 — regresión operativa vs línea caliente V1; no bloquea planificar convergencia, pero **debe portarse antes de certificar convergencia productiva**.

### 3.2 P2 — Otros ítems no portados

| Ítem | V1 / hotfix | V2 |
|------|-------------|-----|
| `DashboardPage` como home | Activo en `/` | Archivo existe; **sin ruta** (huérfano) |
| `test_v1_hotfix_login.py` | En hotfix | Ausente |
| `INTERCAMBIO/SALIDA/V1_CERT/*.ps1` | Scripts recuperación Windows | Ausente |
| `reset_admin_password.py`, `inspect_admin_user.py` | Hotfix | Ausente en V2 |
| Toggle visibilidad contraseña en login | Hotfix | Ausente (`type="password"` fijo) |

### 3.3 No perdido (verificado)

- Permisos V1: **0 eliminados** (diff automatizado de códigos)
- Routers V1: **0 eliminados**
- Tests V1: **0 archivos eliminados**
- `docker-compose.yml`: **sin diff** entre SHAs
- Suite focal V1 sobre V2: **44 passed, 2 skipped**

---

## 4. Duplicados y código obsoleto

| Hallazgo | Ubicación | Clasificación |
|----------|-----------|---------------|
| Bloque `if (res.status === 204)` duplicado | `frontend/src/api.ts` L89-94 | P2 — código muerto/bug menor |
| `DashboardPage.tsx` huérfano | `frontend/src/pages/` | P2 — obsoleto post-1230; `fetchDashboardSummary()` aún en `api.ts` |
| Documentación convergencia múltiple en `INTERCAMBIO/SALIDA/` | ~146 archivos .md | P2 — no bloqueante; riesgo de referenciar SHA obsoletos |
| Adaptadores gateway | V2 mantiene Ollama + cloud | P2 — Ollama opcional; no duplicación de dominio FinOps/CC |

---

## 5. Rutas incompatibles

| Ruta / contrato | V1 | V2 | Riesgo |
|-----------------|----|----|--------|
| `/` | Dashboard | Centro Control | P1 UX — usuarios V1 esperan panel antiguo |
| `/panel` | No existía | Redirect → `/` | P2 — alias nuevo |
| `/api/auth/login` | `TokenResponse` | `TokenResponse \| MfaChallengeResponse` | P1 — clientes deben manejar MFA |
| `/api/auth/me` | JWT user | Requiere sesión `sid` válida | P1 — tokens V1 legacy inválidos |
| Rutas admin seguridad | `admin.security.view` | `admin.security.view` **o** `seguridad.view` | P2 — ampliación compatible |
| FinOps V1 | `/api/finops/*` core | Preservado + `/planner/*` | Compatible hacia atrás |

---

## 6. Contratos modificados

### 6.1 Autenticación y sesión (P1)

V2 introduce:

- Payload JWT con `sid` (session id) obligatorio en `deps.py`
- Flujo MFA (`mfa_pending` token type)
- SSO/OIDC público (`discoverLogin`, `beginPublicOidc`)
- Políticas de sesión por organización (`session_duration_minutes`)
- Rate limiting en login/recuperación

**Vigilar:** scripts de integración, Postman collections y automatizaciones que usen solo `username/password → token` de V1.

### 6.2 FinOps (aditivo)

Nuevos endpoints planner MB-07 (todos GET/PATCH/POST bajo `/api/finops/planner/`). Contratos V1 de costos, logs y oportunidades **sin eliminación**.

### 6.3 Centro de Control (nuevo)

- `GET /api/centro-control/resumen-ejecutivo` — solo lectura, permiso `control_center.view`
- `GET /api/centro-control/indicadores-config`
- Sin endpoints mutantes — gobierno preservado

### 6.4 Mi Trabajo (nuevo)

- `GET /api/trabajo/items` — agregación `collect_items()` desde múltiples fuentes
- No existía en V1; no rompe contrato previo

---

## 7. Tests eliminados o debilitados

| Verificación | Resultado |
|--------------|-----------|
| Archivos test V1 ausentes en V2 | **Ninguno** |
| `test_integration_v1_final.py` | V2 añade `test_i`, `test_j` (más cobertura) |
| Suite focal V1 en V2 | **44 passed** (`test_p0_precertificacion_v1`, `test_integration_v1_final`, `test_docker_database_url`) |
| Gate G1-G4 en V2 | **21 passed** (`test_gate_post6d_correcciones`, `test_convergencia_final_fase2`) |
| `test_v1_hotfix_login.py` | Solo en rama hotfix; **no en V2** — P2 (cobertura operativa Windows/login) |

**Conclusión:** no hay debilitación de la certificación V1 en el árbol V2; falta cobertura del hotfix post-V1.

---

## 8. Decisiones contradictorias

| Tema | Decisión A | Decisión B | Resolución recomendada |
|------|------------|------------|------------------------|
| Pantalla de inicio | V1: Dashboard operativo | Fase 2: Centro Control ejecutivo | Intencional — documentar en release notes; no reactivar Dashboard sin decisión de producto |
| Mensaje error login | Hotfix V1: credenciales vs sesión | V2 api.ts: siempre "sesión vencida" en 401 | Portar hotfix antes de producción |
| Orden parseo `api.ts` | Hotfix: `text` antes de error | V1 SHA y V2: orden invertido | Portar hotfix (afecta todos los errores HTTP) |
| Certificación previa | CERTIFICACION_INTEGRAL: APTO Fase 2 | Esta auditoría: vigilancia V1 | Compatible — certificación asume V2 como producto; pre-integración exige checklist V1 |

---

## 9. Funcionalidades parcialmente implementadas

| Componente | Estado | Evidencia |
|------------|--------|-----------|
| `DashboardPage` | Parcial — código sin ruta | Existe en V2, no importado en `App.tsx` |
| OIDC en `LoginPage` | Parcial — callback simulado `completeOidcCallback(begin.state, "good-code")` | Flujo UI presente; integración real depende de IdP |
| `fetchDashboardSummary()` en api.ts | Parcial — API client sin consumidor UI principal | P2 |
| Scripts recuperación V1 Windows | Parcial — solo en rama hotfix | P2 operativo |

---

## 10. Riesgo de integración por merge masivo

| Factor | Valor | Riesgo |
|--------|-------|--------|
| Archivos divergentes | 376 | **ALTO** |
| Líneas añadidas | +85 124 | **ALTO** |
| Merge-base antiguo | 4c03cbe | **ALTO** — conflictos semánticos en `main.py`, `permissions.py`, `api.ts`, `App.tsx` |
| Migraciones | +32 encadenadas | **ALTO** — requiere estrategia Alembic, no merge de archivos a ciegas |
| Ramas hermanas V1↔POST-V1 | Documentado en `CURSOR_ANALISIS_PUENTE_V1_FINAL_POST_V1.md` | **ALTO** |

**Recomendación:** convergencia por **integración selectiva** (véase §12), no `git merge` masivo V1→V2 o viceversa sin plan de migración y QA.

---

## 11. Componentes para integración selectiva

| Prioridad | Componente | Acción |
|-----------|------------|--------|
| **P0/P1** | Hotfix `cursor/v1-hotfix-login-acceso-85e4` | Cherry-pick o port manual a rama convergencia **antes** release |
| **P1** | `frontend/src/api.ts` | Corregir orden `text`/`!res.ok`; `userMessage(..., path)` |
| **P1** | Contrato auth/sesiones | Documentar breaking change; migración de sesiones activas |
| **P1** | Home `/` | Comunicar cambio Dashboard → Centro Control |
| **P2** | Scripts `V1_CERT` y admin recovery | Portar si se mantiene soporte Windows V1 |
| **P2** | Eliminar o cablear `DashboardPage` | Decisión producto: borrar o redirect legacy |
| **P2** | `test_v1_hotfix_login.py` | Añadir a suite convergencia post-port |
| Aditivo | 21 routers Fase 2 | Ya en V2 — no reintegrar desde V1 |
| Aditivo | 32 migraciones | Aplicar en orden; validar en staging con dump V1 |
| Aditivo | Permisos nuevos | Asignar a roles según matriz Fase 2 |

---

## 12. Dimensiones de vigilancia (detalle)

### ARQUITECTURA

V2 extiende monolito modular FastAPI + React sin microservicios nuevos. `main.py` importa modelos y routers adicionales; event handlers para auditor y comunicaciones. **Vigilar:** tiempo de arranque, orden de imports, y que ningún router V1 quede desregistrado en merges.

### CENTRO CONTROL

- Única página activa: `CentroControlPage` (`/` y `/centro-control`)
- API: solo `GET` en `/api/centro-control/*`
- **Vigilar:** que KPIs sigan viniendo de adaptadores reales (`control_center_adapters`), no de `DashboardPage` legacy

### MI TRABAJO

- Nuevo en V2: `/trabajo`, `/api/trabajo/items`
- CC integra resumen con usuario autenticado
- **Vigilar:** no duplicar bandejas en aprobaciones/notificaciones legacy

### FINOPS

- Canónico: `/costos-valor` + `/api/finops/*`
- MB-07 planner añadido sin quitar endpoints V1
- **Vigilar:** atribución `DIRECTO/TRANSVERSAL_ATRIBUIBLE/PLATAFORMA` en migraciones de datos V1

### GOBIERNO

- Auditor detecta → humano decide → fábrica ejecuta
- CC observa/navega sin mutar
- **Vigilar:** permisos `auditor_empleados.*`, `employee.*` en flujos MB-06

### G1-G4

- Tests gate post-6D presentes y **PASS** en V2
- **Vigilar:** re-ejecutar tras port del hotfix login

### CAS

- Tests concurrencia presentes
- **Vigilar:** sesiones múltiples V2 con `sid` bajo carga

### VALOR

- Separación VERIFICADO/ESTIMADO/POTENCIAL en módulos 1210/1280
- **Vigilar:** que ROI comercial no incluya POTENCIAL en realizados

### SEMÁNTICA

- HECHO/INFERENCIA/RECOMENDACIÓN en CC, trabajo, auditor
- **Vigilar:** consistencia al agregar fuentes V1 (oportunidades, operaciones) al CC

### MULTIPROVEEDOR

- Gateway: openai, anthropic, azure-openai, gemini, ollama
- **Vigilar:** configuración V1 de proveedores sigue funcionando; routing nuevo es opt-in

### INTEGRACIONES

- Bloque 1330 completo en V2
- **Vigilar:** secretos de conectores en gobernanza 1350

### MAPA FINAL

- `MAPA_FINAL_PLATAFORMA_FASE2.md` coherente con `App.tsx` y permisos
- **Vigilar:** actualizar mapa tras port hotfix y decisión Dashboard

### SECRETOS

- Sin hardcodes productivos nuevos detectados en diff
- Contraseñas en tests son fixtures (`*Test1`)
- **Vigilar:** variables MFA/OIDC/SCIM en despliegue convergido

---

## 13. Hallazgos P0 / P1 / P2

### P0 — pérdida / corrupción / seguridad

**Ninguno detectado** en el delta e8cb853→dc1e6cd que impida iniciar planificación de convergencia. No hay eliminación de permisos RBAC V1, ni endpoints de aislamiento multitenant, ni tests P0 V1 ausentes en V2.

### P1 — regresión funcional material

| ID | Hallazgo | Evidencia |
|----|----------|-----------|
| P1-01 | Hotfix login/recuperación V1 (`v1-hotfix-login-acceso-85e4`) no absorbido en V2 | 5 commits post-e8cb853 ausentes en dc1e6cd |
| P1-02 | `api.ts` — mensaje 401 en login incorrecto ("sesión vencida" vs credenciales) | `userMessage` sin parámetro `path` en V2; hotfix sí lo tiene |
| P1-03 | `api.ts` — posible fallo en rama de error (`text` antes de definir) | L73 vs L95 en ambos SHA; hotfix corrige orden |
| P1-04 | Contrato auth: JWT V1 sin `sid` incompatible con `deps.py` V2 | `session_id = payload.get("sid")` obligatorio |

### P2 — mejora / no bloqueante

| ID | Hallazgo |
|----|----------|
| P2-01 | `DashboardPage` huérfano |
| P2-02 | Bloque 204 duplicado en `api.ts` |
| P2-03 | Scripts Windows V1_CERT y admin recovery ausentes |
| P2-04 | `test_v1_hotfix_login.py` ausente |
| P2-05 | Toggle visibilidad contraseña login ausente |
| P2-06 | `fetchDashboardSummary()` sin consumidor principal |
| P2-07 | OIDC UI con callback simulado en desarrollo |
| P2-08 | Volumen documental INTERCAMBIO (riesgo SHA obsoletos) |
| P2-09 | 107 permisos nuevos sin asignación automática a roles V1 |
| P2-10 | Merge-base antiguo aumenta costo de conflictos git |
| P2-11 | `test_integration_v1_final` ampliado en V2 (test_i/j) — vigilar CI time |

---

## 14. P2 reevaluados (auditorías previas)

Ítems de CERTIFICACION_INTEGRAL_FINAL_A y auditorías tramo 6 reexaminados en clave **pérdida V1**:

| Ítem previo P2 | ¿Pérdida V1 al integrar V2? | Reclasificación |
|----------------|----------------------------|-----------------|
| CC sin segundo dashboard | No — es reemplazo intencional | Permanece P2 |
| Ollama opcional | No — V1 ya lo tenía opcional | Permanece P2 |
| OIDC simulado en tests UI | No afecta V1 | Permanece P2 |
| KPIs "Sin información disponible" | No — mejora honestidad | Permanece P2 |
| CSS focal post-6E | No en V1 | Permanece P2 |
| Documentación SHA divergente en docs | No funcional | Permanece P2 |
| Mi Trabajo agregación parcial fuentes | Nuevo V2 | Permanece P2 |
| Integraciones 1330 mock en staging | Nuevo V2 | Permanece P2 |
| Segmentación 1310 sin datos reales | Nuevo V2 | Permanece P2 |
| SCIM 1380 requiere IdP externo | Nuevo V2 | Permanece P2 |
| Mesa ayuda MB-12 wiring | Nuevo V2 | Permanece P2 |

**Ningún P2 previo eleva a P0/P1 por pérdida V1.**

---

## 15. Evidencia de pruebas ejecutadas (solo lectura)

```bash
# V2 @ dc1e6cd — suite certificación V1
pytest tests/test_p0_precertificacion_v1.py \
       tests/test_integration_v1_final.py \
       tests/test_docker_database_url.py -q
# → 44 passed, 2 skipped

# V2 @ dc1e6cd — gate convergencia
pytest tests/test_gate_post6d_correcciones.py \
       tests/test_convergencia_final_fase2.py -q
# → 21 passed
```

---

## 16. Veredicto

### APTO PARA INICIAR CONVERGENCIA

**Con condiciones explícitas:**

1. **No ejecutar merge masivo** sin plan de migración DB y checklist §11.
2. **Portar obligatoriamente** el hotfix `cursor/v1-hotfix-login-acceso-85e4` (mínimo `api.ts` + tests) antes de certificar convergencia productiva.
3. **Comunicar breaking change** de autenticación (sesiones `sid`, MFA) a operaciones e integradores.
4. **Validar en staging** con dump de BD V1 + cadena Alembic completa V2.
5. **Re-ejecutar** suites `test_p0_precertificacion_v1`, `test_integration_v1_final`, `test_gate_post6d_correcciones` tras integración.

**Por qué no "NO APTO":** V2 preserva el núcleo certificable V1 (routers, permisos, tests), las suites focalizadas pasan, no hay P0 de seguridad o pérdida silenciosa de RBAC/multitenant, y los P1 identificados son **acotados y portables** desde una rama ya existente. El riesgo es de **proceso de integración**, no de invalidez del candidato V2.

**Por qué vigilancia es obligatoria:** divergencia genealógica masiva (376 archivos), rama hotfix V1 paralela, cambio de contrato auth, y sustitución de home UI hacen que una integración ingenua **sí** pueda producir regresiones V1 en producción.

---

## 17. Referencias cruzadas

- `INTERCAMBIO/SALIDA/CURSOR_ANALISIS_PUENTE_V1_FINAL_POST_V1.md` — genealogía V1 ↔ POST-V1
- `INTERCAMBIO/SALIDA/CERTIFICACION_INTEGRAL_FINAL_A.md` — certificación Fase 2 sobre dc1e6cd
- Rama hotfix V1: `origin/cursor/v1-hotfix-login-acceso-85e4`
- Rama convergencia V2: `origin/cursor/convergencia-final-fase2-85e4`

---

*Auditoría A — pre-integración — solo lectura — 2026-08-31*
