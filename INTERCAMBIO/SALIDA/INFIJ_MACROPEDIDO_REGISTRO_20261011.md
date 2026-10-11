# INFIJ / FÁBRICA-J — Registro consolidado de ejecución (macropedido)

**Fecha UTC:** 2026-10-11  
**Entorno agente:** `/workspace` (repositorio **EMPLEADOS_IA** / Enterprise AI OS — equivalente documentado a `D:\EMPLEADOS_IA`; no montado `E:\FABRICA_J\CENTRO_CONTROL` en esta VM).

---

## Fase 0 — Preservación y versión activa

| Campo | Valor |
|---|---|
| **Estado** | PARCIAL |
| **Versión activa** | Git `main` @ `dc51d5c` (rama de trabajo `cursor/infiJ-p0-seguridad-baseline-94a6`) |
| **Rutas Windows solicitadas** | `E:\FABRICA_J\CENTRO_CONTROL`, respaldos `BASELINE_INFIJ_*` y `PRE_SEGURIDAD_*` — **no presentes en entorno cloud**; no verificables ni modificables desde aquí |
| **Línea base nueva** | `/workspace/data/BASELINES/BASELINE_20261011_163227/` (`MANIFEST.json` + `snapshot_*.tar.gz`) |
| **Rollback** | Extraer tarball sobre raíz del proyecto comparando SHA-256 del manifiesto |
| **Skills / AGENTS.md** | No existe `AGENTS.md` en repo; reglas aplicables: macropedido + `DOCS/` + `INTERCAMBIO/SALIDA/CURSOR_GAP_ANALYSIS_V1_Y_PARALELIZACION.md` |

---

## Fase 1 — P0-A Seguridad, login, usuarios y permisos

| Campo | Valor |
|---|---|
| **Estado** | PARCIAL (núcleo implementado; usuarios JC/TESTER-J vía variables de entorno, no credenciales en informe) |
| **Archivos modificados** | Ver commit en rama `cursor/infiJ-p0-seguridad-baseline-94a6` |
| **Componentes reutilizados** | RBAC existente (`permissions.py`, admin 840), `audit.py`, bootstrap `seed.py` |
| **Pruebas** | `PYTHONPATH=backend python3 -m pytest tests/test_auth_security_p0.py -q` → **7 passed** |
| **Evidencias** | Registro intentos `auth_login_attempts`; auditoría `auth.login.failed`, `auth.logout`; revocación JWT `tv` + `token_version` |
| **Regresiones** | Ninguna detectada en suite P0 auth |
| **Pendientes P0-A** | MFA; rate-limit por IP; política de expiración JWT configurable por rol; flujo documentado recuperación propietario en Windows local |
| **Gastos externos** | $0 |

### Comportamiento añadido (resumen)

- Bloqueo temporal tras intentos fallidos (`LOGIN_MAX_FAILED_ATTEMPTS`, `LOGIN_LOCKOUT_MINUTES`).
- Revocación real de sesión: `POST /api/auth/logout`, invalidación en reset de contraseña / cambio de rol / desactivación.
- Rol de sistema **`auditor`** (certificación/revisión sin permisos admin críticos).
- Bootstrap opcional propietario y auditor: `BOOTSTRAP_OWNER_*`, `BOOTSTRAP_AUDITOR_*`.
- Arranque bloqueado en `APP_ENV` no desarrollo si secretos/bootstrap inseguros (`validate_security_settings`).

---

## Fases 2–7 (macropedido)

| Fase | Estado | Notas |
|---|---|---|
| **P0-B CORE-CONFIG-J** | BLOQUEADO en cloud | Config org parcial en `admin_service.get_org_config`; falta módulo multi-aplicación completo |
| **P0-C CORE-SKILLS-J** | BLOQUEADO | Sin catálogo skills en repo; requiere ubicación INFIJ/Centro Control o anexos |
| **P0-D Certificación componentes** | PENDIENTE | Matriz/inventario 1217 activos no presente en este repositorio |
| **P1 Cabina / ELIA / conectividad** | BLOQUEADO | UI Cabina Gerente y doc conectividad `.docx` no localizados en `/workspace` |
| **P1-D Arranque / P1-E Despacho** | PARCIAL | Scripts `ARRANCAR.bat`, tests arranque DB existentes; no ejecutado arranque Windows |

---

## Instrucción explícita

**Remisiones:** no iniciadas (conforme macropedido §16).
