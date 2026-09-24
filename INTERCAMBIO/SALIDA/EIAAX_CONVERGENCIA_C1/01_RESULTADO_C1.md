# 01 — Resultado Bloque C1

**Proyecto:** EIAAX / EMPLEADOS_IA
**Rama:** `cursor/eiaax-convergencia-v1-v2`
**Fecha UTC:** 2026-08-31
**Tipo:** Integración controlada — Base segura convergencia

---

## SHA

| Referencia | SHA |
|---|---|
| SHA inicial C1 | `1dcc6569b9cc8511d07aa6dd9fb770b3b875e2ce` |
| SHA candidato C1 | `d3e4e158d98321a1aad1706d68f98714881d7395` |
| V1 certificado (intacto) | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| V2 certificado (intacto) | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| Tag Fase 2 (intacto) | `fase2-candidato-final-certificado` → `dc1e6cd` |

---

## Hotfix de acceso — integración SELECTIVA

**Referencia hotfix:** `1a855325d67921b5d53c015605741d94a3eab32b`
**Método:** integración manual selectiva (NO cherry-pick completo del commit)

| Componente | Acción | Motivo |
|---|---|---|
| `frontend/src/api.ts` | **Integrado** | Fix P0: leer `text` antes de `!res.ok`; 401 login con `path` |
| `frontend/src/pages/LoginPage.tsx` | **Integrado selectivo** | Ojo contraseña + panel olvidó; **conserva MFA y SSO V2** |
| `frontend/src/styles.css` | **Integrado** | Estilos password-field, login-forgot |
| `backend/scripts/inspect_admin_user.py` | **Añadido** | Recuperación acceso sin exponer hash |
| `backend/scripts/reset_admin_password.py` | **Añadido** | Reset seguro con getpass |
| Scripts INTERCAMBIO V1_CERT | **NO incluidos** | Operacionales CERT; fuera alcance C1 |
| Reversión tests V2 del hotfix branch | **Evitado** | Hotfix branch basado en V1; no se tocó suite V2 |

### Comportamiento login C1

- Error 401 en login: mensaje correcto en español (no `ReferenceError`)
- Mostrar/ocultar contraseña con `aria-label` en español
- "¿Olvidó su contraseña?": panel informativo (sin recuperación falsa por correo)
- MFA V2: conservado (`verifyMfaLogin`, pantalla MFA)
- SSO V2: conservado (`discoverLogin`, OIDC)

---

## Archivos modificados

```
frontend/src/api.ts
frontend/src/pages/LoginPage.tsx
frontend/src/styles.css
backend/scripts/inspect_admin_user.py          (nuevo)
backend/scripts/reset_admin_password.py        (nuevo)
tests/test_v1_hotfix_login.py                  (nuevo)
tests/test_convergencia_c1.py                  (nuevo)
INTERCAMBIO/SALIDA/EIAAX_CONVERGENCIA_C1/*     (entregables)
```

---

## Alembic

| Campo | Valor |
|---|---|
| Head único | `1341a1b2c3d4e` |
| Head V1 histórico en ledger | `d1e2f3a4b5c6` (protegido) |
| Migraciones modificadas | **NINGUNA** |
| Migraciones ejecutadas contra CERT PG | **NINGUNA** |

---

## Validación

| Prueba | Resultado |
|---|---|
| `npm run build` frontend | **PASS** |
| Suite C1 focal (72 tests) | **PASS** (2 skipped) |
| Regresión completa `tests/` | **1251 passed**, 4 skipped, **0 failed** |
| Backend inicia (TestClient) | **PASS** (implícito en suite) |
| V2 routers preservados | **PASS** (`test_convergencia_c1`) |

---

## P0 / P1 / P2 abiertos

| ID | Severidad | Estado | Descripción |
|---|---|---|---|
| — | — | — | Sin P0/P1 abiertos en C1 |
| PG-CERT | P1 | **PENDIENTE Agente B** | pg_dump CERT antes de migrar BD real |
| C2-MIGRATE | P2 | Pendiente | Aplicar 32 migraciones en staging |

---

## Confirmaciones obligatorias

| Restricción | Cumplida |
|---|---|
| V1 `e8cb853` no modificado | **SÍ** |
| V2 `dc1e6cd` no modificado | **SÍ** |
| Tag certificado no movido | **SÍ** |
| `D:\EMPLEADOS_IA_CERT` no modificado | **SÍ** |
| PostgreSQL CERT no migrado | **SÍ** |
| C2 no iniciado | **SÍ** |

---

## VEREDICTO

# C1 APTO PARA CERTIFICACIÓN

Condición: certificación PostgreSQL real pendiente de Agente B (fuera alcance cloud C1).
