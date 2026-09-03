# Causa raíz — incidente #2 hash herramienta no coincide

## Incidente Windows real

Tras corregir el incidente #1 (script inexistente), el bootstrap materializó herramientas pero abortó en:

`Backup-SqliteConsistente-104f785.py`

| Campo | Valor |
|-------|-------|
| SHA-256 esperado | `80ea222948a823b583a8f86687fa33d1a8b22a9aeeaccc69a4303c4e0a2c4b9f` |
| SHA-256 obtenido | `2af4a2c30610ea8bfb53224b174b2c20130a1be2ecfb8dfaec6df0e9594489d9` |

El aborto fail-closed fue **correcto**.

## A. SHA-256 del blob Git exacto

```
git rev-parse eiaax-tools-respaldo-104f785:INTERCAMBIO/SALIDA/.../Backup-SqliteConsistente-104f785.py
→ blob 66e12ead386815beb6ed9b9e47084aa70c74f924

git cat-file blob 66e12ead... | sha256
→ 80ea222948a823b583a8f86687fa33d1a8b22a9aeeaccc69a4303c4e0a2c4b9f
```

## B. Mismo archivo en be13183 / tag / rama

El blob **no cambió** entre `6dc90fc` y `be13183` para el helper Python (`66e12ead...`).

El hash esperado `80ea2229...` es el SHA-256 **correcto** del contenido Git.

## C. Origen del hash esperado anterior

Calculado desde el blob Git en entorno Linux (autoridad correcta).

## D. Origen del hash obtenido `2af4a2c3...`

Producido por **materialización textual corrupta** en bootstrap v1:

```
git show ref:path
  → array de strings PowerShell
  → -join "`n"
  → [IO.File]::WriteAllText (UTF-8 con/sin BOM, newline extra en .py)
```

En Windows/Git for Windows esto puede alterar bytes por:

- conversión CRLF/LF en salida textual de `git show`;
- rejoin con `\n` distinto al blob;
- append de `\n` adicional en archivos `.py`;
- encoding BOM en `.ps1` aplicado también por analogía en pipeline.

**No es un cambio del archivo en Git.** Es **corrupción en tránsito**.

## E. Transformación confirmada

| Mecanismo | ¿Preserva blob? |
|-----------|-----------------|
| `git show` → texto → `WriteAllText` | **NO** |
| `git archive` → zip → `Expand-Archive` | **SÍ** |
| `git cat-file blob` → bytes → `WriteAllBytes` | **SÍ** |
| `git hash-object` sobre archivo materializado | verificación binaria |

Prueba controlada: tras `git archive`, `git hash-object` == blob id para las 3 herramientas.

## F. Cambios entre commits

El helper Python **no fue modificado** entre `6dc90fc` y `be13183`. El fallo no fue drift de contenido sino **método de extracción**.

## Corrección definitiva

1. **Eliminar** pipeline `git show` → texto para herramientas.
2. **Launcher mínimo** usa solo `git archive` + `Expand-Archive`.
3. Bootstrap recibe `-ToolsDirectory` ya extraído byte-safe.
4. Verificación doble por herramienta:
   - `git rev-parse ref:path` == blob catalogado
   - `git hash-object archivo` == blob catalogado
   - SHA-256 contenido == catalogado
5. Bootstrap inicial ya **no** se carga con `iex (git show ...)`.

## Hashes definitivos (catálogo de confianza)

| Herramienta | Blob Git | SHA-256 contenido |
|-------------|----------|-------------------|
| `Cerrar-Respaldo-Integral-104f785.ps1` | `8665a7097f7747392265a1e43a601d04e591d94d` | `77fdbc52a42454b1f8cf43e48ae0ef407f0b78525e98bf2d4550f35c7e3b4fe1` |
| `Backup-SqliteConsistente-104f785.py` | `66e12ead386815beb6ed9b9e47084aa70c74f924` | `80ea222948a823b583a8f86687fa33d1a8b22a9aeeaccc69a4303c4e0a2c4b9f` |
| `Bootstrap-Ejecutar-Respaldo-104f785.ps1` | `fbbc248d960f1a8998fbbd6009b77a056b9fba08` | `7c7b62aa2ad2e3f2a4e937d5d892dfb6e9336c95ef4e793bbef9fee935ed5078` |
| `Launch-Respaldo-Integral-104f785.ps1` | `fc1b2ce11a94c3d2b49d5c452952e5efd2420ad4` | `5cef81447a90f0ba364ac4066c047a9aaa721dd79f9e36c23eac1fdec2147b6f` |

Tag herramientas: `eiaax-tools-respaldo-104f785` → commit `aa85bb8519bace15bf6d284dc2eea6b02384ebbf`

## Comando único Windows (byte-safe, sin archivos locales previos)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $ErrorActionPreference='Stop'; Set-Location 'D:\EMPLEADOS_IA_CONVERGENCIA'; $p='104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a'; if((git rev-parse HEAD).Trim() -ne $p){ throw 'HEAD protegido requerido' }; git fetch origin tag eiaax-tools-respaldo-104f785 2>&1 | Out-Null; $z=Join-Path $env:TEMP ('eiaax_'+[guid]::NewGuid().ToString()+'.zip'); $e=Join-Path $env:TEMP ('eiaax_'+[guid]::NewGuid().ToString()); git archive --format=zip -o $z eiaax-tools-respaldo-104f785 INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785; if($LASTEXITCODE -ne 0){ throw 'git archive fallo' }; Expand-Archive -LiteralPath $z -DestinationPath $e -Force; $t=Join-Path $e 'INTERCAMBIO\SALIDA\EIAAX_RESPALDO_ESTABLE_104f785'; & (Join-Path $t 'Bootstrap-Ejecutar-Respaldo-104f785.ps1') -ToolsDirectory $t; $c=$LASTEXITCODE; Remove-Item $z -Force -EA SilentlyContinue; Remove-Item $e -Recurse -Force -EA SilentlyContinue; if((git rev-parse HEAD).Trim() -ne $p){ throw 'HEAD cambio' }; exit $c }"
```
