# EIAAX — Preparación prueba humana Windows (candidato 33d7cb21)

**Fecha:** 2026-09-03  
**Rama:** `cursor/experiencia-v1-convergencia-85e4`  
**PR:** #168  
**Ruta Windows autoritativa:** `D:\EMPLEADOS_IA_CONVERGENCIA`

---

## A. SHA exacto

```
526ec1987c2cb87f308266f87599d8b8d5e18200
```

(Base macrobloque: `33d7cb21`. Este commit añade Horizonte al seed certificado Windows.)

---

## B. Rama

`cursor/experiencia-v1-convergencia-85e4`

---

## C. Head Alembic

```
1831a1b2c3d4e
```

Cadena: `1820 → 1830 (inteligencia económica) → 1831 (Empleado IA 2.0)`

---

## D. BD Windows utilizada

```
D:\EMPLEADOS_IA_CONVERGENCIA\data\eiaax_integrado_demo.db
```

Equivalente Linux validado: `/workspace/data/eiaax_integrado_demo.db`

---

## E. Cómo se prepara Horizonte (sin pasos manuales del usuario)

El mecanismo certificado `scripts\windows\preparar_demo_eiaax.ps1` invoca automáticamente:

```
backend\scripts\seed_lote3_demo.py
```

**Adaptación producto (sin tocar `scripts/windows/**`):** `seed_lote3_demo.py` ahora llama a `demo_comercial_service.seed_demo_comercial()` para la organización A tras el seed Lote 3. Esto crea:

| Campo | Valor |
|---|---|
| Entidad | `[DEMO] Clínica Demo Horizonte` |
| Etiqueta | `DEMO — DATOS SIMULADOS` |
| Expediente demo | EVA-2026-0002 (junto con Lote 3 EVA-2026-0001) |
| Operaciones / indicadores / informe | Según `demo_comercial_service` |

- **Idempotente:** `seed_demo_comercial` reutiliza expediente existente (`reused=True`) sin duplicar.
- **Multiempresa:** Org B no recibe semilla Horizonte; solo Org A.
- **Sin reset manual:** El usuario no ejecuta `seed_demo_horizonte.py`, `DATABASE_URL`, `alembic` ni `npm` por separado.

`preparar_demo_eiaax.ps1` recrea únicamente la BD demo certificada (`eiaax_integrado_demo.db`), comportamiento Windows ya validado.

---

## F. Credenciales demo verificadas

| Uso | Usuario | Contraseña | Rol |
|---|---|---|---|
| Login Windows certificado | `org_a_admin` | `DemoA2026!` | admin |
| Solo lectura Org A | `org_a_viewer` | `DemoA2026!` | viewer |
| Org B | `org_b_admin` | `DemoB2026!` | admin |

**No usar** `admin` / `Admin2026!` — pertenecen a `seed_demo_horizonte.py` (BD separada `eiaax_horizonte_demo.db`), no al runtime Windows.

**Horizonte en Centro de Control:** Contexto → `[DEMO] Clínica Demo Horizonte — EVA-2026-0002`

---

## G. Evidencia startup equivalente Windows

Simulación Linux con BD `eiaax_integrado_demo.db` (mismo nombre y convención que Windows):

| Paso | Resultado |
|---|---|
| `seed_lote3_demo.py` (equivalente preparar) | PASS |
| Migraciones hasta `1831a1b2c3d4e` | PASS |
| `PRAGMA integrity_check` SQLite | `ok` |
| Backend `http://127.0.0.1:8000/health` | PASS (`demo_db_name: eiaax_integrado_demo.db`, `alembic_current: 1831`) |
| Frontend `http://127.0.0.1:5180` | PASS |
| Proxy `/health` vía 5180 | PASS |

---

## H. Evidencia login

| Prueba | Resultado |
|---|---|
| `POST /api/auth/login` vía proxy 5180 (`org_a_admin` / `DemoA2026!`) | PASS — token emitido |
| Redirección post-login (auditoría visual) | PASS |
| Centro de Control carga | PASS |
| Manifest demo `GET /api/demo-comercial/manifest` | PASS — `Clínica Demo Horizonte`, etiqueta `DEMO — DATOS SIMULADOS` |
| Auditoría visual 36 pantallas (`cert_visual_audit.mjs`) | **36/36 PASS** |

---

## I. Evidencia persistencia / reinicio

| Prueba | Resultado |
|---|---|
| Detener backend y reiniciar con misma BD | PASS |
| Expedientes tras reinicio | `[DEMO] Clínica Demo Horizonte`, `Unidad Operativa Demo A` presentes |
| Re-ejecución idempotente `seed_demo_comercial` | PASS — `reused=True`, 1 expediente Horizonte |

---

## J. `scripts/windows/**` = 0 diff

```
git diff 0014a4b -- scripts/windows/
```

**Resultado:** 0 líneas (verificado).

---

## K. Procedimiento Windows — BLOQUEO

**No se entrega comando operativo** hasta resolver el bloqueo siguiente.

### Causa exacta

El candidato `33d7cb21` introduce migraciones `1830` y `1831` (head `1831a1b2c3d4e`). Los scripts Windows congelados en `0014a4b` validan:

| Archivo | Valor congelado |
|---|---|
| `scripts/windows/EiaaxDemo.Common.ps1` | `$ExpectedAlembicHead = "1820a1b2c3d4e"` |
| `scripts/windows/eiaax_convergence_manifest.json` | `"alembic_head": "1820a1b2c3d4e"` |

`preparar_demo_eiaax.ps1` y `arrancar_convergencia_windows.ps1` llaman `Confirm-EiaaxAlembicState`, que **falla** si `alembic heads` ≠ `1820` (el código en `33d7cb21` reporta `1831`).

Además, `arrancar_convergencia_windows.ps1` sincroniza git a `cursor/convergencia-comercial-v1-85e4` (manifest), no a `cursor/experiencia-v1-convergencia-85e4` donde vive el candidato.

### Resolución requerida (GENERAL — autorizada, fuera de este agente)

1. Actualizar en `scripts/windows/**` (cambio congelado autorizado):
   - `ExpectedAlembicHead` → `1831a1b2c3d4e`
   - `eiaax_convergence_manifest.json` → `alembic_head: 1831a1b2c3d4e` y `branch: cursor/experiencia-v1-convergencia-85e4` (o merge PR #168 a convergencia-comercial)
2. Tras eso, el procedimiento único certificado será:

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

### Estado producto

La adaptación demo Horizonte en `seed_lote3_demo.py` está lista para el mecanismo Windows existente; **no requiere cambios en `scripts/windows/**`**.

---

## Notificación

**EIAAX — Preparación Windows candidato 33d7cb21:** producto adaptado (Horizonte en seed certificado, credenciales verificadas, 36/36 visual). **Bloqueo operativo:** scripts Windows congelados en Alembic `1820` y rama `convergencia-comercial` impiden `arrancar` con candidato `33d7cb21` hasta actualización autorizada de `scripts/windows/**`.
