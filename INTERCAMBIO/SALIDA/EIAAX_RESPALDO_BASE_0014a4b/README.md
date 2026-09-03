# EIAAX — Respaldo local base 0014a4b (cierre seguro)

**Estado:** PREPARADO, AUDITADO Y LISTO PARA EJECUCIÓN SEGURA EN WINDOWS  
**No declara respaldo físico local completo** hasta ejecutar el script en Windows real.

## Archivos

| Archivo | Rol |
|---------|-----|
| `Cerrar-Respaldo-Local-0014a4b.ps1` | **Script único** de ejecución (entry point) |
| `Backup-SqliteConsistente-0014a4b.py` | Helper invocado por el PS1 (backup API SQLite) |
| `auditar_respaldo_0014a4b.py` | Auditoría remota/CI (no ejecutar en Windows operativo) |

## Comando único para Windows

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
Set-ExecutionPolicy -Scope Process Bypass
.\INTERCAMBIO\SALIDA\EIAAX_RESPALDO_BASE_0014a4b\Cerrar-Respaldo-Local-0014a4b.ps1
```

> Si `INTERCAMBIO` no está en el checkout de convergencia, usar ruta absoluta al script versionado en el repositorio que contenga estos archivos.

## Qué hace el script (fail-closed)

1. Cambia internamente a `D:\EMPLEADOS_IA_CONVERGENCIA`
2. Verifica tag `eiaax-v1-windows-real-operativo-0014a4b` → SHA `0014a4b01a3ccf3e849a6609c8c784873f20f497`
3. Crea bundle **local** en `D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_WINDOWS_REAL_OPERATIVO_0014a4b\`
4. `git bundle verify` + restauración temporal
5. Backup SQLite con `sqlite3.Connection.backup()` (sin `Copy-Item` sobre BD activa)
6. `PRAGMA integrity_check = ok` sobre la copia
7. Genera `MANIFIESTO_RESPALDO_LOCAL.md`
8. Imprime **PASS/FAIL** único

## Base protegida

| Campo | Valor |
|-------|-------|
| SHA | `0014a4b01a3ccf3e849a6609c8c784873f20f497` |
| Tag | `eiaax-v1-windows-real-operativo-0014a4b` |
| Rama | `cursor/convergencia-comercial-v1-85e4` |
| Alembic | `1820a1b2c3d4e` |

## Auditoría remota ejecutada

```
PASS: Archivos de entrega presentes
PASS: Auditoría estática PS1
PASS: Lógica SQLite backup + integrity_check
PASS: Lógica bundle verify + restore temporal
```

SHA-256 scripts (pre-commit):

- `Cerrar-Respaldo-Local-0014a4b.ps1`: `2b8b8030b00598153e7eff218f5ed3fbb0b01d392a44c994fcd4e10a7029539e`
- `Backup-SqliteConsistente-0014a4b.py`: `530ed017f827b4f7444eac4a90f5ccea64d88a0774fe04ef3d3c7652b7257359`

## Lo que NO hace

- No modifica backend/frontend/producto
- No mueve ni recrea el tag existente
- No modifica la BD activa (solo lectura vía backup API)
- No detiene EIAAX automáticamente
- No usa `Copy-Item` sobre `eiaax_integrado_demo.db`

## Criterio de cierre en Windows

Declarar **EIAAX — BASE 0014a4b RESPALDADA Y RECUPERABILIDAD VERIFICADA** solo cuando el script imprima:

```
RESULTADO FINAL: PASS
BUNDLE VERIFY = PASS
SQLITE INTEGRITY_CHECK = ok
```
