# GATE A INDEPENDIENTE — CERTIFICACIÓN C1

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** A  
**Modo:** Solo lectura — preparación de gate; **no ejecutar hasta recibir SHA C1 de GENERAL**  
**Fecha preparación:** 2026-08-31  
**Auditoría base aceptada:** `INTERCAMBIO/SALIDA/AUDITORIA_A_PREINTEGRACION.md`  
**Veredicto pre-integración:** APTO PARA INICIAR CONVERGENCIA (P0=0, P1=4, P2=11)

---

## Referencias de línea base

| Rol | SHA / rama | Uso en este gate |
|-----|------------|------------------|
| **V1 certificada** | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` | Deltas críticos a reincorporar en C1 |
| **V2 certificada** | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` | Base funcional Fase 2 esperada en C1 |
| **Hotfix V1 login** | `origin/cursor/v1-hotfix-login-acceso-85e4` (HEAD `1a85532`) | Obligatorio en C1 según auditoría |
| **C1 candidato** | *Pendiente — GENERAL* | Objeto de certificación |

---

## Protocolo de ejecución (cuando GENERAL entregue SHA C1)

1. Verificar objeto Git: `git cat-file -t <SHA_C1>` → `commit`.
2. Checkout limpio del SHA en worktree dedicado (sin modificar ramas certificadas).
3. Registrar mensaje commit y diff estadístico vs V2 (`dc1e6cd`) y vs V1 (`e8cb853`).
4. Ejecutar **suite mínima obligatoria** (sección siguiente) + controles estáticos.
5. Ejecutar **controles adicionales recomendados** según tiempo disponible.
6. Completar matriz PASS/FAIL por control.
7. Emitir veredicto: `C1 CERTIFICADO` o `C1 RECHAZADO` con evidencia.
8. **No corregir** hallazgos durante certificación; solo documentar.

**Exclusión explícita:** no duplicar certificación PostgreSQL profunda del Agente B.

---

## Suite mínima obligatoria

| # | Archivo de prueba | Propósito |
|---|-------------------|-----------|
| M1 | `tests/test_p0_precertificacion_v1.py` | P0 V1: LLM determinístico, tenant inactivo, scheduler |
| M2 | `tests/test_integration_v1_final.py` | Integración V1: RBAC, multitenant, LLM, health |
| M3 | `tests/test_gate_post6d_correcciones.py` | G1–G4, CAS, concurrencia, migraciones |
| M4 | `tests/test_v1_hotfix_login.py` | Hotfix login: orden `api.ts`, 401, scripts admin |
| M5 | `tests/test_docker_database_url.py` | DATABASE_URL y contraseñas especiales |
| M6 | `tests/test_knowledge_930.py` | Auth y descarga protegida de conocimiento |
| M7 | `tests/test_bloque_1300_seguridad_avanzada.py` | MFA, sesiones, tokens, rate limit |
| M8 | `tests/test_convergencia_final_fase2.py` | Coherencia convergencia Fase 2 (CC, Mi Trabajo) |

### Comando sugerido

```bash
pytest tests/test_p0_precertificacion_v1.py \
       tests/test_integration_v1_final.py \
       tests/test_gate_post6d_correcciones.py \
       tests/test_v1_hotfix_login.py \
       tests/test_docker_database_url.py \
       tests/test_knowledge_930.py \
       tests/test_bloque_1300_seguridad_avanzada.py \
       tests/test_convergencia_final_fase2.py \
       -q --tb=short
```

**Condición PASS global suite:** 100 % passed (skipped solo si documentado y no debilita control).

### Pruebas adicionales recomendadas (no sustituyen mínimas)

| Archivo | Motivo |
|---------|--------|
| `tests/test_correccion_focal_post6e_p1.py` | Regresiones UI/CC post-6E |
| `tests/test_centro_control_cableado_ejecutivo_fase2.py` | Cableado ejecutivo CC |
| `tests/test_bandeja_trabajo_humano.py` | Mi Trabajo único |
| `tests/test_consumption_planner_mb07.py` | FinOps MB-07 |
| `tests/test_llm_gateway_v1.py` | Gateway multiproveedor V1 |
| `tests/test_bloque_1270_multiproveedor.py` | Routing LLM Fase 2 |

### Controles estáticos obligatorios (sin pytest)

```bash
# Un único head Alembic
cd backend && alembic heads | wc -l   # debe ser 1

# Permisos V1 no eliminados (script comparación vs e8cb853)
python3 -c "
import re
def perms(p): return set(re.findall(r'\"([a-z][a-z0-9_.]+)\"', open(p).read()))
v1=perms('backend/app/permissions.py')  # desde checkout e8cb853
c1=perms('backend/app/permissions.py')  # desde checkout C1
assert not (v1-c1), f'Permisos V1 eliminados: {v1-c1}'
"

# Routers V1 presentes
for r in admin agent_factory assistant audit auth automations capabilities \
         experience finops knowledge llm_providers notifications operations \
         oportunidades organization platform salud test_lab tools; do
  test -f backend/app/routers/${r}.py || echo "FALTA router V1: $r"
done
```

---

## Controles de certificación

### CTRL-00 — Verificación SHA C1

| Campo | Valor |
|-------|-------|
| **CONTROL** | El SHA C1 existe, es alcanzable y se audita en checkout limpio. |
| **RIESGO PROTEGIDO** | Certificación sobre commit incorrecto o inexistente. |
| **EVIDENCIA/PRUEBA** | `git cat-file -t <SHA_C1>`; `git show --no-patch --oneline <SHA_C1>`; `git status` limpio. |
| **CONDICIÓN PASS** | Objeto tipo `commit`; working tree clean; SHA coincide con el entregado por GENERAL. |
| **SEVERIDAD SI FALLA** | **P0** — gate inválido; detener. |

---

### CTRL-01 — Preservar V2 certificado como base funcional

| Campo | Valor |
|-------|-------|
| **CONTROL** | C1 mantiene la base Fase 2 certificada en `dc1e6cd`: routers V2, migraciones, CC, Mi Trabajo, FinOps planner, MFA/SSO. |
| **RIESGO PROTEGIDO** | Regresión masiva Fase 2 al integrar deltas V1. |
| **EVIDENCIA/PRUEBA** | Diff C1 vs `dc1e6cd`: no eliminación de routers V2 (`control_center`, `trabajo`, `comunicaciones`, `soporte`, `integraciones`, `security`, `identidad`, `scim`, etc.). M8 PASS. Tests G1–G4 en M3 PASS. |
| **CONDICIÓN PASS** | Todos los routers V2 de la auditoría pre-integración presentes; M3 y M8 sin fallos; sin eliminación de `test_convergencia_final_fase2.py` ni debilitación de sus aserciones. |
| **SEVERIDAD SI FALLA** | **P0** si se pierde módulo Fase 2 entero; **P1** si falla M8 o G1–G4. |

---

### CTRL-02 — Reincorporar deltas críticos V1

| Campo | Valor |
|-------|-------|
| **CONTROL** | C1 incorpora lo que V2 no tenía respecto a V1 operativo post-certificación (hotfix y operativa). |
| **RIESGO PROTEGIDO** | Pérdida de correcciones V1 posteriores a `e8cb853` no absorbidas en `dc1e6cd`. |
| **EVIDENCIA/PRUEBA** | Presencia de `backend/scripts/reset_admin_password.py`, `inspect_admin_user.py`; M4 PASS; diff vs `e8cb853` en áreas críticas documentadas en auditoría (login, api.ts, scripts). |
| **CONDICIÓN PASS** | Scripts admin recovery presentes; M4 PASS íntegro (4 tests); no regresión de M1/M2 respecto a baseline V2. |
| **SEVERIDAD SI FALLA** | **P1** — operación/recuperación V1 comprometida. |

---

### CTRL-03 — Hotfix de login incorporado

| Campo | Valor |
|-------|-------|
| **CONTROL** | Port completo del hotfix `cursor/v1-hotfix-login-acceso-85e4` en login/recuperación. |
| **RIESGO PROTEGIDO** | Regresión UX y operativa login documentada como P1-01 en auditoría. |
| **EVIDENCIA/PRUEBA** | M4: `test_api_ts_reads_body_before_error_handling`, `test_login_page_password_toggle`, `test_login_wrong_password_returns_401`, `test_reset_admin_script_exists`. Inspección `LoginPage.tsx`: toggle contraseña, enlace recuperación. |
| **CONDICIÓN PASS** | Los 4 tests M4 PASS; `showPassword` y `¿Olvidó su contraseña?` en LoginPage. |
| **SEVERIDAD SI FALLA** | **P1** |

---

### CTRL-04 — Eliminar bug `parseDetail(text)` antes de `await res.text()`

| Campo | Valor |
|-------|-------|
| **CONTROL** | En `frontend/src/api.ts`, el cuerpo HTTP se lee **antes** de evaluar `!res.ok`. |
| **RIESGO PROTEGIDO** | ReferenceError o mensajes de error incorrectos en toda la API frontend (P1-03 auditoría). |
| **EVIDENCIA/PRUEBA** | M4 `test_api_ts_reads_body_before_error_handling`: índice de `const text = await res.text()` **menor** que índice de `if (!res.ok)`. Revisión manual de función `api()`. |
| **CONDICIÓN PASS** | Orden correcto en `api()` principal; sin uso de `text` no definido en rama de error. |
| **SEVERIDAD SI FALLA** | **P1** (fallo runtime en errores HTTP); escala **P0** si afecta flujos de autenticación sin mensaje visible. |

---

### CTRL-05 — Distinguir login 401 de sesión vencida

| Campo | Valor |
|-------|-------|
| **CONTROL** | `userMessage` distingue 401 en `/api/auth/login` vs 401 en rutas autenticadas. |
| **RIESGO PROTEGIDO** | Usuario con credenciales incorrectas ve "sesión vencida" (P1-02 auditoría). |
| **EVIDENCIA/PRUEBA** | Inspección `frontend/src/api.ts`: `userMessage(status, detail, path?)` con rama `path === "/api/auth/login"` → `detail || "Credenciales incorrectas"`. M4 backend 401 en login incorrecto. Prueba manual opcional: POST login malo no redirige con `expired=1`. |
| **CONDICIÓN PASS** | Firma `userMessage` acepta `path`; mensaje login ≠ mensaje sesión; en 401 no-login se mantiene limpieza de token y redirect `/login?expired=1` solo fuera de login. |
| **SEVERIDAD SI FALLA** | **P1** |

---

### CTRL-06 — DATABASE_URL y contratos Docker

| Campo | Valor |
|-------|-------|
| **CONTROL** | Resolución segura de `DATABASE_URL`; `docker-compose.yml` compatible con despliegue V1/V2. |
| **RIESGO PROTEGIDO** | Fallo de arranque con contraseñas especiales; regresión despliegue Docker. |
| **EVIDENCIA/PRUEBA** | M5 PASS completo. Diff `docker-compose.yml` C1 vs `e8cb853` y vs `dc1e6cd` sin regresiones no documentadas. Presencia `app/db_url.py`, `app/config.py` con precedencia documentada. |
| **CONDICIÓN PASS** | M5 100 % PASS; compose válido; sin eliminación de variables críticas (`POSTGRES_*`, `DATABASE_URL`). |
| **SEVERIDAD SI FALLA** | **P0** si impide arranque/BD; **P1** si rompe despliegue estándar. |

---

### CTRL-07 — Knowledge auth y descarga protegida

| Campo | Valor |
|-------|-------|
| **CONTROL** | Conocimiento exige autenticación y RBAC; descarga sin token rechazada; aislamiento multitenant en download. |
| **RIESGO PROTEGIDO** | Exfiltración de documentos; bypass RBAC en `/api/knowledge/*/download`. |
| **EVIDENCIA/PRUEBA** | M6: `test_download_without_token_rejected` (401), `test_download_cross_tenant_denied`, `test_download_without_knowledge_view_permission_denied`, `test_download_with_invalid_token_rejected`. |
| **CONDICIÓN PASS** | M6 PASS; ningún endpoint download público sin auth. |
| **SEVERIDAD SI FALLA** | **P0** |

---

### CTRL-08 — RBAC y multiempresa V1

| Campo | Valor |
|-------|-------|
| **CONTROL** | Permisos V1 preservados; aislamiento tenant en APIs sensibles V1. |
| **RIESGO PROTEGIDO** | Escalada privilegios; fuga cross-tenant. |
| **EVIDENCIA/PRUEBA** | Script permisos (0 eliminados vs `e8cb853`). M2: `test_b_*`, `test_d_*`, `test_e_*`, `test_g_*`. M3: `test_concurrency_unauthorized_user_denied`. M7: `test_multitenant_session_isolation`, `test_security_policy_rbac`. |
| **CONDICIÓN PASS** | 0 permisos V1 eliminados; M2 y M7 sin fallos en casos tenant/RBAC. |
| **SEVERIDAD SI FALLA** | **P0** |

---

### CTRL-09 — Routers V1 relevantes

| Campo | Valor |
|-------|-------|
| **CONTROL** | Los 20 routers núcleo V1 permanecen registrados en `main.py`. |
| **RIESGO PROTEGIDO** | Pérdida silenciosa de dominio V1 (auth, finops, knowledge, operations, etc.). |
| **EVIDENCIA/PRUEBA** | Checklist archivos `backend/app/routers/{admin,agent_factory,assistant,audit,auth,automations,capabilities,experience,finops,knowledge,llm_providers,notifications,operations,oportunidades,organization,platform,salud,test_lab,tools}.py`. Inspección `main.py` include_router para cada uno. M2 health y endpoints representativos PASS. |
| **CONDICIÓN PASS** | 19 routers V1 listados presentes + `__init__.py`; todos incluidos en app. |
| **SEVERIDAD SI FALLA** | **P1** por router operativo ausente; **P0** si afecta auth/tenant/finops/knowledge. |

---

### CTRL-10 — Permisos V1 + extensión V2

| Campo | Valor |
|-------|-------|
| **CONTROL** | Matriz RBAC: superset V1; permisos Fase 2 añadidos sin sustituir códigos V1. |
| **RIESGO PROTEGIDO** | Roles V1 pierden acceso; colisión o renombre de permisos. |
| **EVIDENCIA/PRUEBA** | Diff automatizado `permissions.py` C1 vs `e8cb853`: `removed == ∅`. Conteo permisos C1 ≥ V2 (`dc1e6cd`). M2 RBAC PASS. |
| **CONDICIÓN PASS** | Ningún código permiso V1 eliminado; permisos V2 (`control_center.view`, `trabajo.view`, etc.) presentes. |
| **SEVERIDAD SI FALLA** | **P1**; **P0** si afecta `admin.*`, `llm.*`, `audit.view`, `knowledge.*`. |

---

### CTRL-11 — Pruebas V1 relevantes conservadas

| Campo | Valor |
|-------|-------|
| **CONTROL** | Archivos de test V1 no eliminados ni vaciados para forzar PASS. |
| **RIESGO PROTEGIDO** | Debilitación de certificación (objetivo 15). |
| **EVIDENCIA/PRUEBA** | Diff tests/ C1 vs `dc1e6cd`: sin eliminación de `test_p0_precertificacion_v1.py`, `test_integration_v1_final.py`, `test_docker_database_url.py`, `test_knowledge_930.py`, `test_llm_gateway_v1.py`. M1–M2 PASS. Revisión que ningún test V1 tenga `pytest.skip` nuevo ni aserciones relajadas vs V2. |
| **CONDICIÓN PASS** | 0 archivos test V1 eliminados; M1+M2 PASS; sin `@pytest.mark.skip` añadido en tests obligatorios. |
| **SEVERIDAD SI FALLA** | **P1**; **P0** si se omite M1 o M6. |

---

### CTRL-12 — Un único head Alembic

| Campo | Valor |
|-------|-------|
| **CONTROL** | Cadena de migraciones lineal; un solo head. |
| **RIESGO PROTEGIDO** | Esquema BD indeterminado en despliegue convergido. |
| **EVIDENCIA/PRUEBA** | `alembic heads` → exactamente 1 revisión. M3 `test_validate_migrations_runs_without_pythonpath` PASS. |
| **CONDICIÓN PASS** | 1 head; test migraciones PASS; sin archivos merge huérfanos. |
| **SEVERIDAD SI FALLA** | **P0** |

---

### CTRL-13 — Requisito `sid` en JWT sin regresión silenciosa

| Campo | Valor |
|-------|-------|
| **CONTROL** | Tokens emitidos por login incluyen `sid`; validación de sesión coherente; comportamiento legacy documentado. |
| **RIESGO PROTEGIDO** | Sesiones zombi; bypass de revocación; fallos silenciosos en convergencia. |
| **EVIDENCIA/PRUEBA** | M7: `test_active_sessions_and_revoke`, `test_revoked_jwt_rejected`, `test_max_sessions_policy`. Inspección `auth.py` `_issue_session_token` → payload con `sid`. Inspección `deps.py` `_resolve_user_from_payload`. Ver sección **SID / tokens legacy** abajo. |
| **CONDICIÓN PASS** | Login nuevo devuelve JWT con `sid` válido en BD; revocación invalida acceso; M7 tests sesión PASS; comportamiento legacy documentado y acorde a implementación (sin compatibilidad artificial añadida en certificación). |
| **SEVERIDAD SI FALLA** | **P1**; **P0** si revocación no funciona o bypass multitenant. |

---

### CTRL-14 — Coherencia MFA / sesiones V2

| Campo | Valor |
|-------|-------|
| **CONTROL** | MFA, sesiones múltiples, recuperación contraseña y rate limiting V2 intactos tras merge C1. |
| **RIESGO PROTEGIDO** | Debilitación seguridad Fase 2 al portar hotfix V1. |
| **EVIDENCIA/PRUEBA** | M7 PASS íntegro (20 tests): `test_login_with_mfa_challenge`, `test_mfa_mandatory_policy_blocks_without_enrollment`, `test_mfa_pending_token_not_usable_as_access`, `test_rate_limit_login`, `test_forgot_password_no_enumeration`. |
| **CONDICIÓN PASS** | M7 100 % PASS; `mfa_pending` no usable como access token; políticas MFA no relajadas. |
| **SEVERIDAD SI FALLA** | **P0** |

---

### CTRL-15 — No debilitar tests para producir PASS

| Campo | Valor |
|-------|-------|
| **CONTROL** | C1 no introduce skips, mocks excesivos ni aserciones debilitadas en suite obligatoria. |
| **RIESGO PROTEGIDO** | PASS falso en certificación. |
| **EVIDENCIA/PRUEBA** | Diff tests/ C1 vs `dc1e6cd`: buscar `pytest.skip`, `xfail`, aserciones `>=` sustituyendo `==`, eliminación de `assert`. Diff M3 tests G1–G4 vs versión en `dc1e6cd`. |
| **CONDICIÓN PASS** | Sin debilitación detectada en archivos M1–M8; conteo tests ≥ V2 para archivos obligatorios. |
| **SEVERIDAD SI FALLA** | **P0** — rechazo automático de C1. |

---

## Gates G1–G4 (dentro de M3)

| Gate | Test | Condición PASS |
|------|------|----------------|
| **G1** | `test_g1_deviation_requires_explicit_authorization` | Desviación auditor→fábrica exige autorización explícita |
| **G2** | `test_g2_solicitar_aprobacion_transitions_trabajo` | Hallazgo auditor no duplica obligación con aprobación pendiente |
| **G3** | `test_g3_dedup_oportunidad_vs_1290_humana` | Oportunidad 1290 humana no duplica `oportunidad_aprobacion` |
| **G4** | `test_g4_automatica_no_autoaprueba_oportunidad` | AUTOMÁTICA no sustituye aprobación humana |

**Severidad si falla cualquier G1–G4:** **P1** (escala **P0** si G4 permite auto-aprobación en producción).

---

## SID / tokens legacy — impacto y comportamiento esperado

### Diseño V2 (referencia `dc1e6cd` / C1 esperado)

1. **Login exitoso** (`auth.py` → `_issue_session_token`): crea fila en tabla de sesiones y emite JWT con claims `sub`, `role`, `org`, **`sid`**.
2. **Validación** (`deps.py` → `_resolve_user_from_payload`):
   - Si `type == mfa_pending` → **401** (no es access token).
   - Si claim **`sid` presente** → debe existir sesión válida, no revocada, del mismo `user_id`; si no → **401** `"Sesión inválida o revocada"`.
   - Si claim **`sid` ausente** → usuario resuelto **sin** validación de sesión en BD (comportamiento heredado para tokens pre-sesión).
3. **MFA**: login puede devolver `mfa_token` / `mfa_required` en lugar de access token final; verificación en `/api/auth/mfa/verify`.
4. **Revocación**: `test_revoked_jwt_rejected` y políticas `max_active_sessions` deben seguir operativos.

### Comportamiento esperado durante convergencia (sin compatibilidad artificial)

| Escenario | Comportamiento esperado | ¿FAIL en certificación? |
|-----------|-------------------------|-------------------------|
| **Token nuevo post-login C1** | JWT con `sid`; sesión en BD; M7 PASS | **SÍ** si falla |
| **Sesión revocada / logout** | Token con `sid` revocado → 401 explícito | **SÍ** si falla |
| **Token V1 legacy sin `sid`** (emitido antes de convergencia, aún no expirado) | Puede autenticar hasta expiración JWT **sin** atarse a revocación por sesión | **NO** es FAIL de C1 si está documentado; vigilar en operaciones |
| **Token con `sid` inválido/fabricado** | 401 `"Sesión inválida o revocada"` | **SÍ** si acepta |
| **Token `mfa_pending` en API protegida** | 401 MFA pendiente | **SÍ** si permite acceso |
| **Fin de ventana convergencia** | Operaciones debe planificar re-login masivo o expiración JWT | Fuera de scope certificación; documentar en runbook |

### Comprobaciones explícitas en certificación C1

```bash
# Token nuevo tiene sid (inspección JWT payload tras login test)
pytest tests/test_bloque_1300_seguridad_avanzada.py::test_active_sessions_and_revoke -q
pytest tests/test_bloque_1300_seguridad_avanzada.py::test_revoked_jwt_rejected -q
pytest tests/test_bloque_1300_seguridad_avanzada.py::test_mfa_pending_token_not_usable_as_access -q
```

**Documentar en informe final C1:** política operativa para tokens legacy sin `sid` (aceptados hasta TTL vs invalidación forzada en despliegue).

**Prohibido en certificación:** implementar shim de compatibilidad artificial; solo observar y documentar comportamiento real.

---

## Matriz resumen de severidades

| ID | Tema | Severidad si FAIL |
|----|------|-------------------|
| CTRL-00 | SHA válido | P0 |
| CTRL-01 | Base V2 preservada | P0/P1 |
| CTRL-02 | Deltas V1 críticos | P1 |
| CTRL-03 | Hotfix login | P1 |
| CTRL-04 | Orden `api.ts` text/error | P1 (P0 en auth) |
| CTRL-05 | Mensaje 401 login vs sesión | P1 |
| CTRL-06 | DATABASE_URL / Docker | P0/P1 |
| CTRL-07 | Knowledge download | P0 |
| CTRL-08 | RBAC / multitenant | P0 |
| CTRL-09 | Routers V1 | P1/P0 |
| CTRL-10 | Permisos V1+V2 | P1/P0 |
| CTRL-11 | Tests V1 conservados | P1/P0 |
| CTRL-12 | Alembic 1 head | P0 |
| CTRL-13 | sid / sesiones | P1/P0 |
| CTRL-14 | MFA / sesiones V2 | P0 |
| CTRL-15 | No debilitar tests | P0 |
| G1–G4 | Gobierno post-6D | P1/P0 |

### Criterio de veredicto (cuando se ejecute)

| Resultado | Condición |
|-----------|-----------|
| **C1 CERTIFICADO** | 0 FAIL en P0; 0 FAIL en P1; suite mínima 100 % PASS |
| **C1 CERTIFICADO CON OBSERVACIONES** | Solo P2 abiertos; documentados; no debilitan controles |
| **C1 RECHAZADO** | Cualquier FAIL P0 o P1; o debilitación de tests (CTRL-15) |

---

## Registro de ejecución (completar al recibir SHA C1)

| Campo | Valor |
|-------|-------|
| SHA C1 | *pendiente* |
| Fecha ejecución | *pendiente* |
| Ejecutor | Agente A |
| M1–M8 resultado | *pendiente* |
| Controles PASS/FAIL | *pendiente* |
| Veredicto final | *pendiente* |

---

## Estado del gate

```
╔══════════════════════════════════════════════════════════════╗
║  EN RESERVA — ESPERANDO SHA C1 DE GENERAL                    ║
╚══════════════════════════════════════════════════════════════╝
```

Este documento define el gate independiente. **No se ha ejecutado certificación sobre C1** porque el candidato aún no ha sido entregado. Al recibir el SHA, Agente A ejecutará este protocolo sin modificar código.

---

*Gate A — Agente A — preparado 2026-08-31 — solo lectura*
