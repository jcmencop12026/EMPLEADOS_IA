# Cierre pipeline Windows — PARSER VALIDATION FAIL

**Rama:** `cursor/convergencia-comercial-v1-85e4`
**Worktree:** `D:\EMPLEADOS_IA_CONVERGENCIA`

---

## 1. Causa exacta de `PARSER VALIDATION: FAIL`

**Archivo:** `scripts/windows/test_convergence_atomic.ps1`
**Línea:** 124
**Contenido:** cadena con em-dash Unicode (`EIAAX — WINDOWS NO CERTIFICADO`)
**Error en Windows PowerShell 5.1:** el archivo estaba en UTF-8 **sin BOM**. PS 5.1 interpreta archivos sin BOM con la codepage del sistema; los bytes UTF-8 del em-dash producen errores de parseo.

Los archivos visibles al final del scroll (`test_preparador_productivo.ps1`, `validar_arranque_windows.ps1`, etc.) mostraban PASS porque se listan alfabéticamente **después** del archivo fallido. El agregador terminaba en FAIL sin listar explícitamente cuál archivo había fallado.

## 2. Defecto del agregador (secundario)

| Problema | Efecto |
|----------|--------|
| Sin resumen `FAILED FILES:` | El usuario solo veía los últimos PASS |
| `Get-EiaaxCollectionCount` con `List[object]` bajo StrictMode | Podía lanzar excepción al finalizar la validación |
| `Invoke-EiaaxPowerShellFile` usaba `$LASTEXITCODE` | En PS 5.1 el exit code del hijo podía quedar stale |
| Suite remota usaba `pwsh` sin validar parser primero | PASS remoto no reproducía PS 5.1 Windows |

## 3. Correcciones aplicadas

- UTF-8 BOM en **todos** los `.ps1` de `scripts/windows/`
- `Ensure-EiaaxWindowsScriptsUtf8Bom` en arranque atómico (normaliza antes de validar)
- `validate_ps_parse.ps1`: resumen `FAILED FILES:`, parseo vía copia temporal si falta BOM
- `Invoke-EiaaxPowerShellFile`: `Start-Process -PassThru` con exit code explícito
- `Get-EiaaxCollectionCount`: soporta `ICollection` (listas genéricas)
- `ejecutar_tests_desarrollo_windows.ps1`: ejecuta parser **primero** con shell de producción
- `test_parser_aggregate.ps1`: regresión agregador + política BOM

## 4. Por qué GENERAL reportó suite PASS antes

La suite remota (Linux) ejecutaba tests individuales con **pwsh 7**, que tolera UTF-8 sin BOM. **No ejecutaba** `validate_ps_parse.ps1` como primer paso obligatorio con la misma semántica que Windows 5.1.

## 5. Conservado

Git stderr fix, bootstrap pre-Common, ruta autoritativa, Python discovery/resolution, Alembic, runtime identity, fail-closed.

## 6. Comando único

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

## 7. Limitación remota

El agente remoto valida con `pwsh` cuando `powershell.exe` 5.1 no está disponible. La política BOM y el agregador corrigen el caso Windows 5.1 documentado.
