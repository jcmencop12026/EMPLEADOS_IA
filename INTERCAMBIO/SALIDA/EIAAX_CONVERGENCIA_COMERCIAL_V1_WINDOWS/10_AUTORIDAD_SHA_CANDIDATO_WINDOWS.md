# Autoridad SHA — Candidato Windows convergencia

**Rama:** `cursor/convergencia-comercial-v1-85e4`  
**Worktree:** `D:\EMPLEADOS_IA_CONVERGENCIA`

---

## Regla única (sin ambigüedad)

| **HEAD remoto final** | **`23aaafa`** |
| **Código funcional** | **`23aaafa`** |
| **Documentación** | **`23aaafa`** |
| **Codigo activo SHA** (consola) | **`23aaafa`** (post-sync) |
| **Runtime / certificación** | **`23aaafa`** |

No existen dos SHA activos. Los commits intermedios `1417424` y `ac336b5` fueron consolidados; solo importa el HEAD final de la rama.

---

## Historial consolidado (referencia)

| SHA | Contenido |
|-----|-----------|
| `18b9be3` | Fix Python (`Resolve-EiaaxPython`, `PYTHON DISCOVERY`) |
| `f19c924` | Fix Git stderr → exit code como autoridad |
| `1417424` | Ruta autoritativa desde `$PSScriptRoot` |
| `ac336b5` | Solo doc (alineación SHA) — absorbido en HEAD final |
| **HEAD final** | **`36b5e94`** — bootstrap pre-Common + política SHA única |

---

## Bootstrap desde copia local anterior

`arrancar_convergencia_windows.ps1` ejecuta **antes** de cargar `EiaaxDemo.Common.ps1`:

1. `git fetch / checkout / pull --ff-only` con exit code como autoridad (stderr tolerado)
2. Si el SHA cambió, re-ejecuta el script ya actualizado
3. Continúa con `Sync-EiaaxConvergenceRepository` (Common.ps1)

Esto evita que una copia local con `Common.ps1` antiguo impida auto-actualizarse.

**Nota transición desde `18b9be3`:** la primera vez requiere obtener el script con bootstrap (p. ej. `git pull` manual que el usuario ya demostró). A partir de ahí, el arranque atómico se auto-actualiza.

---

## Comando único Windows

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```
