# Autoridad SHA — Candidato Windows convergencia

**Rama:** `cursor/convergencia-comercial-v1-85e4`  
**Worktree:** `D:\EMPLEADOS_IA_CONVERGENCIA`

---

## Regla única (sin ambigüedad)

Un solo SHA activo en todo momento:

```
git rev-parse --short HEAD
```

ejecutado en `D:\EMPLEADOS_IA_CONVERGENCIA` tras `git pull --ff-only origin cursor/convergencia-comercial-v1-85e4`.

Ese valor es simultáneamente:

- HEAD remoto final
- código funcional
- documentación incluida en el commit
- `Codigo activo SHA` mostrado por el arranque (post-sync)
- SHA de certificación (`EIAAX <sha> — WINDOWS REAL OPERATIVO`)

**No existen dos SHA activos.** Commits intermedios (`1417424`, `ac336b5`, etc.) son solo historia; la autoridad es siempre el HEAD actual de la rama.

---

## Relación histórica (referencia, no activa)

| SHA | Rol histórico |
|-----|----------------|
| `18b9be3` | Fix Python (`Resolve-EiaaxPython`, `PYTHON DISCOVERY`) |
| `f19c924` | Fix Git stderr → exit code como autoridad |
| `1417424` | Ruta autoritativa desde `$PSScriptRoot` |
| `ac336b5` | Alineación doc (absorbido en HEAD posterior) |
| HEAD actual | Todo lo anterior + bootstrap pre-Common |

---

## Bootstrap desde copia local anterior

`arrancar_convergencia_windows.ps1` ejecuta **antes** de cargar `EiaaxDemo.Common.ps1`:

1. `git fetch / checkout / pull --ff-only` con exit code como autoridad (stderr tolerado)
2. Si el SHA cambió, re-ejecuta el script ya actualizado (`EIAAX_BOOTSTRAP_REEXEC`)
3. Continúa con `Sync-EiaaxConvergenceRepository` (Common.ps1 corregido)

**Transición desde `18b9be3`:** requiere una vez obtener el script con bootstrap (el usuario ya demostró `git pull` manual). A partir de ahí, el arranque atómico se auto-actualiza sin wrapper exterior.

---

## Comando único Windows

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```
