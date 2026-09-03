# Causa raíz — incidente script respaldo 104f785 no encontrado

## Incidente

El usuario ejecutó desde `D:\EMPLEADOS_IA_CONVERGENCIA`:

```powershell
.\INTERCAMBIO\SALIDA\EIAAX_RESPALDO_ESTABLE_104f785\Cerrar-Respaldo-Integral-104f785.ps1
```

Windows respondió `CommandNotFoundException` porque **el archivo no existe en el working tree del candidato protegido**.

## A. Dónde existen los artefactos

| Artefacto | Rama | Commit |
|-----------|------|--------|
| `Cerrar-Respaldo-Integral-104f785.ps1` | `cursor/espacio-externo-v1-3e3d` | `6dc90fc76203180338b4c3fd2ccdce6c1f7aeaf0` (y commits posteriores con bootstrap) |
| `Backup-SqliteConsistente-104f785.py` | idem | idem |
| `Bootstrap-Ejecutar-Respaldo-104f785.ps1` | idem | commit con tag `eiaax-tools-respaldo-104f785` → `1a627c83e3f6e8d9ea46c689504ca1e4220cba51` |

**Tag de herramientas (recuperación sin checkout):** `eiaax-tools-respaldo-104f785`

## B. Por qué NO están en Windows convergencia

El entorno Windows real está deliberadamente en:

| Campo | Valor |
|-------|-------|
| Rama | `cursor/convergencia-comercial-v1-85e4` |
| SHA | `104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a` |

En ese commit **no existe** el directorio:

`INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/`

Verificación:

```bash
git ls-tree 104f785 INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/
# (vacío — árbol inexistente)
```

## C. Commit 6dc90fc publicado en origin

Sí. Publicado en:

`origin/cursor/espacio-externo-v1-3e3d` → `6dc90fc76203180338b4c3fd2ccdce6c1f7aeaf0`

Recuperable con `git fetch` + `git show` **sin checkout**.

## D. Error del procedimiento anterior

Se asumió incorrectamente que los scripts estaban **materializados localmente** en el candidato `104f785`.

Los scripts solo existían en otra rama/commit documental (`espacio-externo-v1-3e3d`), no en el árbol operativo que se protegía.

**Causa raíz:** desalineación entre **commit protegido (producto)** y **commit que contenía herramientas de respaldo (documentación)**.

## Corrección

Bootstrap que:

1. Verifica `HEAD == 104f785` (antes y después)
2. `git fetch origin tag eiaax-tools-respaldo-104f785`
3. Materializa herramientas con `git show` en `D:\RESPALDOS_EIAAX\_bootstrap_tools_104f785\`
4. Verifica SHA-256 de cada archivo
5. Ejecuta respaldo integral (bundle + SQLite + manifiesto)
6. Elimina herramientas temporales
7. **No hace checkout / merge / cherry-pick / reset**

## Comando único Windows (no requiere archivo local previo)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Location 'D:\EMPLEADOS_IA_CONVERGENCIA'; git fetch origin tag eiaax-tools-respaldo-104f785 2>&1 | Out-Null; iex ((git show eiaax-tools-respaldo-104f785:INTERCAMBIO/SALIDA/EIAAX_RESPALDO_ESTABLE_104f785/Bootstrap-Ejecutar-Respaldo-104f785.ps1) -join [char]10)"
```

## Salida esperada

```
RESULTADO FINAL: PASS — RESPALDO 104f785 VERIFICADO Y RECUPERABLE
```
