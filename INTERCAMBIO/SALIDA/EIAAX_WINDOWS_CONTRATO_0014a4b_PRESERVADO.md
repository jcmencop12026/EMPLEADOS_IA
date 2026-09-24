# EIAAX — Preservación contrato Windows certificado 0014a4b

**Fecha preservación:** 2026-09-03
**SHA certificado anterior:** `0014a4b` (recuperable vía `git show 0014a4b:scripts/windows/...`)

---

## Estado congelado (0014a4b)

### `eiaax_convergence_manifest.json`

```json
{
  "profile": "convergencia_comercial_v1",
  "branch": "cursor/convergencia-comercial-v1-85e4",
  "alembic_head": "1820a1b2c3d4e",
  "integration_sha": "482ff6f",
  "worktree_default": "D:\\EMPLEADOS_IA_CONVERGENCIA",
  "demo_db_name": "eiaax_integrado_demo.db",
  "runtime_marker": "eiaax-convergencia-v1-windows"
}
```

### `EiaaxDemo.Common.ps1` (extracto)

```
$script:ExpectedAlembicHead = "1820a1b2c3d4e"
$script:BackendPort = 8000
$script:FrontendPort = 5180
$script:DemoDbFileName = "eiaax_integrado_demo.db"
$script:ConvergenceWorktreeDefault = "D:\EMPLEADOS_IA_CONVERGENCIA"
```

### Comportamiento conocido

- Entrada única: `arrancar_convergencia_windows.ps1`
- Preparación: `preparar_demo_eiaax.ps1` → `seed_lote3_demo.py`
- Arranque: `iniciar_demo_eiaax.ps1`
- Credenciales: `org_a_admin` / `DemoA2026!`
- BD: `data/eiaax_integrado_demo.db`
- Alembic validado: `1820a1b2c3d4e`

### Recuperación

```bash
git checkout 0014a4b -- scripts/windows/
# o inspección sin checkout:
git show 0014a4b:scripts/windows/eiaax_convergence_manifest.json
git show 0014a4b:scripts/windows/EiaaxDemo.Common.ps1
```

**No se reescribió tag ni historia.** El commit `0014a4b` permanece en el grafo Git.

---

## Nueva versión autorizada (post-promoción)

Ver `INTERCAMBIO/SALIDA/EIAAX_WINDOWS_PROMOCION_CONTROLADA.md`.
