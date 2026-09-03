# EIAAX — Promoción controlada candidato Windows

**Fecha:** 2026-09-03
**Candidato promovido:** `e7808efcad2d61d9d671079ac33a02ac1f8f6455`
**PR:** #168 → integrado en rama autoritativa
**Contrato anterior preservado:** `0014a4b` (ver `EIAAX_WINDOWS_CONTRATO_0014a4b_PRESERVADO.md`)

---

## A. Estado final PR #168

| Campo | Valor |
|---|---|
| Base | `cursor/convergencia-comercial-v1-85e4` |
| Head candidato | `e7808ef` (6 commits, fast-forward limpio) |
| Conflictos | Ninguno |
| `scripts/windows/**` en PR producto | 0 cambios |
| Migraciones | Lineales `1820 → 1830 → 1831` |
| Integración | Fast-forward merge local → push rama autoritativa |

---

## B. Rama autoritativa final

```
cursor/convergencia-comercial-v1-85e4
```

La rama temporal `cursor/experiencia-v1-convergencia-85e4` cumplió su función de integración; el runtime productivo apunta a convergencia-comercial.

---

## C. SHA autoritativo final

Tras actualización del contrato Windows (ver commit de promoción):

```
git rev-parse HEAD
```

Producto congelado: `e7808ef` + commit contrato Windows (metadatos únicamente).

---

## D. Alembic head / current

| Campo | Valor |
|---|---|
| heads | `1831a1b2c3d4e` (único head) |
| current (BD demo) | `1831a1b2c3d4e` |
| Cadena | `1820 → 1830 → 1831` |

---

## E. Diff `scripts/windows/**` vs `0014a4b`

```
diff --git a/scripts/windows/EiaaxDemo.Common.ps1
-$script:ExpectedAlembicHead = "1820a1b2c3d4e"
+$script:ExpectedAlembicHead = "1831a1b2c3d4e"

diff --git a/scripts/windows/arrancar_convergencia_windows.ps1
-    - seed + Alembic 1820
+    - seed + Alembic 1831

diff --git a/scripts/windows/eiaax_convergence_manifest.json
-  "alembic_head": "1820a1b2c3d4e",
-  "integration_sha": "482ff6f",
+  "alembic_head": "1831a1b2c3d4e",
+  "integration_sha": "e7808ef",
```

---

## F. Clasificación diff (METADATO vs LÓGICA)

| Archivo | Línea | Cambio | Clase |
|---|---|---|---|
| `EiaaxDemo.Common.ps1` | 17 | `ExpectedAlembicHead` 1820→1831 | **A — METADATO** |
| `eiaax_convergence_manifest.json` | alembic_head | 1820→1831 | **A — METADATO** |
| `eiaax_convergence_manifest.json` | integration_sha | 482ff6f→e7808ef | **A — METADATO** |
| `arrancar_convergencia_windows.ps1` | comentario .DESCRIPTION | Alembic 1820→1831 | **A — METADATO** |

---

## G. Confirmación LÓGICA = 0

**B (lógica de startup) = 0 cambios.**

Sin alteración de: ownership, puertos, backend, frontend, npm, proxy, health, procesos, logs, preparación, seguridad, abortos, seed.

---

## H. Pruebas nuevo contrato Windows (equivalente GENERAL)

| Paso | Resultado |
|---|---|
| Fast-forward merge PR #168 | PASS |
| `alembic heads` (único) | PASS — `1831` |
| Upgrade 1820→1831 (BD preservada) | PASS — orgs conservadas |
| `seed_lote3_demo.py` | PASS |
| `PRAGMA integrity_check` | `ok` |
| Backend health | PASS (`demo_db_name: eiaax_integrado_demo.db`, `alembic_current: 1831`) |
| Frontend HTTP | PASS |
| Proxy `/health` vía 5180 | PASS |
| Tests IE/IA2.0/import (23) | PASS |

---

## I. Login

| Prueba | Resultado |
|---|---|
| `org_a_admin` / `DemoA2026!` vía proxy 5180 | PASS |
| Auditoría visual 36 pantallas | **36/36 PASS** |

---

## J. Persistencia / reinicio

| Prueba | Resultado |
|---|---|
| Detener backend → reiniciar misma BD | PASS |
| Horizonte `EVA-2026-0002` presente | PASS |
| `seed_demo_comercial` idempotente | PASS (sin duplicados) |

---

## K. Demo Horizonte

| Campo | Valor |
|---|---|
| Entidad CC | `[DEMO] Clínica Demo Horizonte` |
| Código | `EVA-2026-0002` |
| Etiqueta | `DEMO — DATOS SIMULADOS` |
| Preparación | Automática vía `preparar_demo_eiaax.ps1` → `seed_lote3_demo.py` |

---

## L. Riesgos

| Riesgo | Mitigación |
|---|---|
| BD demo existente en 1820 en Windows real | `alembic upgrade head` en preparar/seed migra a 1831; probado sin pérdida de orgs |
| `preparar` recrea BD demo | Comportamiento certificado previo; no afecta BD fuera de `eiaax_integrado_demo.db` |
| CI PR #168 fallido pre-merge | Validación local GENERAL PASS; revisar CI post-push |
| Recuperar contrato 1820 | `git checkout 0014a4b -- scripts/windows/` |

---

## M. Comando único para el usuario

Desde `D:\EMPLEADOS_IA_CONVERGENCIA`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

**Credenciales:** `org_a_admin` / `DemoA2026!`
**Horizonte:** Centro de Control → Contexto → `[DEMO] Clínica Demo Horizonte — EVA-2026-0002`
**Detener:** `scripts\windows\detener_demo_eiaax.ps1`

---

## Regresión startup vs 0014a4b

| Aspecto | Conservado |
|---|---|
| Entrada única `arrancar_convergencia_windows.ps1` | Sí |
| Puertos 8000/5180 | Sí |
| Preparar → iniciar → detener | Sí |
| Ownership PID/worktree | Sí |
| Health/proxy checks | Sí |
| Seed `seed_lote3_demo.py` | Sí (+ Horizonte integrado en producto) |
| Única evolución | Alembic 1831 + manifest SHA + demo Horizonte |
