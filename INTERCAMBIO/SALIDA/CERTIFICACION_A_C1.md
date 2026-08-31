# CERTIFICACIÓN A — C1 BASE SEGURA CONVERGENCIA V1+V2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** A  
**Modo:** Solo lectura — certificación ejecutada; sin modificar producto  
**Fecha:** 2026-08-31  
**Gate aplicado:** `INTERCAMBIO/SALIDA/GATE_A_INDEPENDIENTE_C1.md` (sin rediseño)  
**Autorización previa:** Auditoría pre-integración ACEPTADA (APTO PARA INICIAR CONVERGENCIA)

---

## Veredicto obligatorio

# C1 CERTIFICADO

---

## SHA realmente auditado

| Campo | Valor |
|-------|-------|
| **SHA solicitado por GENERAL** | `25ad1021ee6ea0322aceb0622252e7b748706d32` |
| **Verificación** | `git cat-file -t` → `commit` ✓ |
| **Mensaje** | `feat(c1): base segura convergencia V1+V2 con hotfix login selectivo` |
| **Worktree** | `/tmp/cert-c1-a` (detached HEAD, working tree clean) |

### Genealogía

| Comparación | Delta |
|-------------|-------|
| C1 vs **V2** (`dc1e6cd`) | 18 archivos, +1 323 / −19 líneas |
| C1 vs **V1** (`e8cb853`) | 391 archivos, +86 590 / −1 048 líneas |

C1 = base V2 + integración selectiva hotfix login y artefactos C1 (scripts admin, tests, ledger migraciones).

---

## Resumen ejecutivo

Se ejecutó el protocolo GATE A íntegro sobre `25ad102`. La **suite mínima M1–M8** completó con **111 passed, 2 skipped, 0 failed** en 46,96 s. Los **16 controles CTRL-00…CTRL-15** resultan **PASS**. No se detectaron hallazgos P0 ni P1. Se documentan **3 observaciones P2** (fragilidad de entorno de prueba y cobertura adicional no obligatoria).

---

## Resultados suite mínima M1–M8

**Comando ejecutado (literal del gate):**

```bash
cd /tmp/cert-c1-a
python -m pytest tests/test_p0_precertificacion_v1.py \
       tests/test_integration_v1_final.py \
       tests/test_gate_post6d_correcciones.py \
       tests/test_v1_hotfix_login.py \
       tests/test_docker_database_url.py \
       tests/test_knowledge_930.py \
       tests/test_bloque_1300_seguridad_avanzada.py \
       tests/test_convergencia_final_fase2.py \
       -q --tb=line
```

### Totales

| Métrica | Valor |
|---------|-------|
| **PASS** | **111** |
| **FAIL** | **0** |
| **SKIP** | 2 (M5 — casos documentados) |
| **ERROR** | 0 |
| **Duración** | 46,96 s |

### Desglose por módulo

| ID | Archivo | PASS | SKIP | FAIL |
|----|---------|------|------|------|
| **M1** | `test_p0_precertificacion_v1.py` | 14 | 0 | 0 |
| **M2** | `test_integration_v1_final.py` | 10 | 0 | 0 |
| **M3** | `test_gate_post6d_correcciones.py` | 16 | 0 | 0 |
| **M4** | `test_v1_hotfix_login.py` | 6 | 0 | 0 |
| **M5** | `test_docker_database_url.py` | 20 | 2 | 0 |
| **M6** | `test_knowledge_930.py` | 20 | 0 | 0 |
| **M7** | `test_bloque_1300_seguridad_avanzada.py` | 20 | 0 | 0 |
| **M8** | `test_convergencia_final_fase2.py` | 5 | 0 | 0 |

### Gates G1–G4 (dentro de M3)

| Gate | Test | Resultado |
|------|------|-----------|
| G1 | `test_g1_deviation_requires_explicit_authorization` | **PASS** |
| G2 | `test_g2_solicitar_aprobacion_transitions_trabajo` | **PASS** |
| G3 | `test_g3_dedup_oportunidad_vs_1290_humana` | **PASS** |
| G4 | `test_g4_automatica_no_autoaprueba_oportunidad` | **PASS** |

---

## Resultados controles CTRL-00…CTRL-15

| Control | Descripción breve | Resultado | Evidencia |
|---------|-------------------|-----------|-----------|
| **CTRL-00** | SHA C1 válido y checkout limpio | **PASS** | `commit`; worktree clean |
| **CTRL-01** | Base V2 preservada | **PASS** | 22 routers V2 presentes; M3+M8 PASS |
| **CTRL-02** | Deltas críticos V1 reincorporados | **PASS** | Scripts admin; M4 PASS |
| **CTRL-03** | Hotfix login incorporado | **PASS** | M4 (6 tests); diff `api.ts`, `LoginPage.tsx` |
| **CTRL-04** | Bug `parseDetail(text)` antes de `text` | **PASS** | M4 `test_api_ts_reads_body_before_error_handling`; L79<L81 en `api.ts` |
| **CTRL-05** | Login 401 ≠ sesión vencida | **PASS** | `userMessage(..., path)` L44-47; M4 `test_api_ts_login_401_uses_path_aware_message` |
| **CTRL-06** | DATABASE_URL / Docker | **PASS** | M5 20 PASS; `docker-compose.yml` idéntico a V2 (0 líneas diff) |
| **CTRL-07** | Knowledge auth y descarga | **PASS** | M6 20 PASS incl. `test_download_without_token_rejected` |
| **CTRL-08** | RBAC / multiempresa V1 | **PASS** | 0 permisos V1 eliminados; M2 tenant tests PASS |
| **CTRL-09** | Routers V1 relevantes | **PASS** | 19 routers V1 verificados + `main.py` include_router |
| **CTRL-10** | Permisos V1 + extensión V2 | **PASS** | removed=∅; +107 vs V1; superset V2 |
| **CTRL-11** | Pruebas V1 conservadas | **PASS** | 0 archivos M1–M8 eliminados; sin skip/xfail añadido |
| **CTRL-12** | Un único head Alembic | **PASS** | `alembic heads` → `1341a1b2c3d4e` (1 head); M3 `test_validate_migrations_runs_without_pythonpath` PASS |
| **CTRL-13** | sid JWT sin regresión silenciosa | **PASS** | M7 `test_active_sessions_and_revoke`, `test_revoked_jwt_rejected` PASS |
| **CTRL-14** | MFA / sesiones V2 coherentes | **PASS** | M7 20/20 PASS incl. MFA, rate limit, recovery |
| **CTRL-15** | No debilitar tests | **PASS** | C1 añade tests (`test_v1_hotfix_login`, `test_convergencia_c1`); M1–M8 sin relajación |

---

## Hallazgos clasificados

### P0 — pérdida / corrupción / seguridad

**Ninguno.**

### P1 — regresión funcional material

**Ninguno** en ejecución del protocolo gate sobre SHA `25ad102`.

### P2 — mejora / no bloqueante

| ID | Hallazgo | Evidencia |
|----|----------|-----------|
| P2-01 | **Fragilidad entorno de prueba:** si `BOOTSTRAP_ADMIN_PASSWORD` o `DATABASE_URL` quedan contaminados en el shell padre, M7 puede fallar (tests usan `Admin2026*` hardcodeado vs password de `settings`). Con aislamiento conftest (ejecución gate estándar) **no reproduce**. | Reproducción incidental con `JWT_SECRET`/`DATABASE_URL` externos: 8 FAIL en M7; gate literal sin env extra: 0 FAIL |
| P2-02 | `test_convergencia_c1.py` añadido en C1 pero **fuera** de suite M1–M8 obligatoria | Archivo nuevo; cobertura ledger/routers C1 adicional |
| P2-03 | Funciones secundarias en `api.ts` (upload/OIDC) mantienen patrón `text` post-`!res.ok` en ramas auxiliares (~L1850+) | No cubiertas por M4; función principal `api()` corregida |

---

## Evidencia por objetivo de misión (1–15)

| # | Objetivo | Estado C1 |
|---|----------|-----------|
| 1 | Preservar V2 certificado | ✓ Routers V2 intactos; M8 PASS |
| 2 | Reincorporar deltas críticos V1 | ✓ Scripts admin + hotfix |
| 3 | Hotfix login | ✓ M4 6/6 PASS |
| 4 | Eliminar bug `parseDetail` antes de `text` | ✓ Orden corregido en `api()` |
| 5 | Distinguir login 401 vs sesión | ✓ `userMessage` con `path` |
| 6 | DATABASE_URL / Docker | ✓ M5 PASS; compose sin regresión |
| 7 | Knowledge auth / descarga | ✓ M6 PASS |
| 8 | RBAC / multiempresa V1 | ✓ M2 + permisos |
| 9 | Routers V1 | ✓ 19/19 |
| 10 | Permisos V1 + V2 | ✓ 0 eliminados |
| 11 | Pruebas V1 | ✓ Conservadas |
| 12 | Un head Alembic | ✓ `1341a1b2c3d4e` |
| 13 | sid sin regresión | ✓ M7 sesiones |
| 14 | MFA/sesiones V2 | ✓ M7 completo |
| 15 | No debilitar tests | ✓ Sin debilitación |

---

## SID / tokens legacy — comportamiento certificado

### Emisión (tokens nuevos C1)

- Login exitoso crea sesión BD y JWT con `sid` (`auth.py` → `_issue_session_token`).
- Verificado por M7: `test_active_sessions_and_revoke`, `test_max_sessions_policy`.

### Validación (`deps.py`)

| Condición | Comportamiento observado | Resultado certificación |
|-----------|--------------------------|-------------------------|
| JWT con `sid` válido | Acceso normal; `touch_session` | **PASS** (M2, M7) |
| JWT con `sid` revocado | **401** `"Sesión inválida o revocada"` | **PASS** (`test_revoked_jwt_rejected`) |
| JWT sin claim `sid` | Usuario resuelto **sin** validación de sesión en BD (heredado) | **Documentado** — no es FAIL de C1 |
| Token `mfa_pending` en API protegida | **401** MFA pendiente | **PASS** (`test_mfa_pending_token_not_usable_as_access`) |

### Política operativa convergencia (sin compatibilidad artificial)

1. **Tokens nuevos post-C1:** siempre con `sid`; revocación efectiva.
2. **Tokens legacy sin `sid`:** pueden funcionar hasta expiración JWT; **no** participan de revocación por sesión — planificar re-login en ventana de despliegue.
3. **No se implementó** shim de compatibilidad en esta certificación (conforme gate).

---

## Evidencia hotfix integrado (C1 vs V2)

Archivos modificados respecto a `dc1e6cd`:

| Archivo | Cambio |
|---------|--------|
| `frontend/src/api.ts` | Orden `text`/`!res.ok`; `userMessage(..., path)` |
| `frontend/src/pages/LoginPage.tsx` | Toggle contraseña, panel recuperación, MFA/SSO conservados |
| `backend/scripts/reset_admin_password.py` | **Nuevo** |
| `backend/scripts/inspect_admin_user.py` | **Nuevo** |
| `tests/test_v1_hotfix_login.py` | **Nuevo** (6 tests) |
| `tests/test_convergencia_c1.py` | **Nuevo** (cobertura C1 adicional) |

M4 verifica explícitamente conservación MFA/SSO V2:

```python
assert "verifyMfaLogin" in src, "MFA V2 debe conservarse en login"
assert "discoverLogin" in src, "SSO V2 debe conservarse en login"
```

---

## Salida obligatoria

```
SHA: 25ad1021ee6ea0322aceb0622252e7b748706d32 ✓
VEREDICTO: C1 CERTIFICADO

CTRL-00..15: 16/16 PASS
M1–M8: 111 PASS / 0 FAIL / 2 SKIP

P0: 0
P1: 0
P2: 3

G1-G4: PASS (4/4)
Alembic head: 1341a1b2c3d4e (único)
Permisos V1 eliminados: 0
Routers V1: 19/19
Routers V2: 22/22
```

---

## Restricciones respetadas

- ✓ No modificar producto  
- ✓ No corregir hallazgos durante auditoría  
- ✓ No merge  
- ✓ No tocar SHAs V1/V2 certificados  
- ✓ No iniciar C2  
- ✓ No rediseñar gate  
- ✓ No duplicar certificación PostgreSQL Agente B  

---

## Próximo paso

C1 queda **certificado** como base segura de convergencia. GENERAL puede proceder a fases posteriores (C2 u operativa) según plan maestro. Agente A no inicia C2.

---

*Certificación A — Agente A — 2026-08-31 — gate `GATE_A_INDEPENDIENTE_C1.md`*
