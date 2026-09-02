# MANIFIESTO — EIAAX V1 Windows Real Estable 104f785 (Git remoto verificado)

| Campo | Valor |
|-------|-------|
| **PROYECTO** | EIAAX |
| **TIPO** | RESPALDO INTEGRAL — COMPONENTE GIT (agente remoto) |
| **SHA corto** | `104f785` |
| **SHA completo** | `104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a` |
| **Tag** | `eiaax-v1-windows-real-estable-104f785` |
| **Tag object** | `63963a041f83c630dd16081c3e9b65c4ebb7f951` |
| **Rama** | `cursor/convergencia-comercial-v1-85e4` |
| **Base arranque protegida** | `0014a4b01a3ccf3e849a6609c8c784873f20f497` |
| **Alembic head** | `1820a1b2c3d4e` |
| **Fecha UTC** | `2026-09-02T21:43:00Z` |

## Estado Windows real (declarado)

- backend / frontend / ownership / Alembic / runtime identity: PASS
- login `org_a_admin` funcional
- aplicación: http://127.0.0.1:5180

## Bundle Git (remoto)

| Campo | Valor |
|-------|-------|
| Archivo | `INTERCAMBIO/RESPALDOS/EIAAX_V1_WINDOWS_ESTABLE_104f785/eiaax-v1-windows-real-estable-104f785.bundle` |
| Objetivo Windows | `D:\RESPALDOS_EIAAX\EIAAX_V1_WINDOWS_ESTABLE_104f785\eiaax-v1-windows-real-estable-104f785.bundle` |
| Tamaño | 7 434 752 bytes (aprox.) |
| SHA-256 | `9aca00b22e51a5f34091b611fba15e63a349bba1147925a53e92955e40d60988` |
| `git bundle verify` | PASS |
| Restauración temporal | PASS → `104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a` |

## scripts/windows

`git diff 0014a4b..104f785 -- scripts/windows/` → **sin cambios** (intactos).

## SQLite / carpeta física Windows

**Pendiente de materialización local** mediante script único:

`INTERCAMBIO\SALIDA\EIAAX_RESPALDO_ESTABLE_104f785\Cerrar-Respaldo-Integral-104f785.ps1`

El agente remoto no tiene acceso a `D:\EMPLEADOS_IA_CONVERGENCIA\data\eiaax_integrado_demo.db`.

## Comando Windows (respald integral PASS)

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
Set-ExecutionPolicy -Scope Process Bypass
.\INTERCAMBIO\SALIDA\EIAAX_RESPALDO_ESTABLE_104f785\Cerrar-Respaldo-Integral-104f785.ps1
```

## Recuperación código (offline)

```powershell
git clone D:\RESPALDOS_EIAAX\EIAAX_V1_WINDOWS_ESTABLE_104f785\eiaax-v1-windows-real-estable-104f785.bundle EIAAX_RESTORE_104f785
cd EIAAX_RESTORE_104f785
git checkout eiaax-v1-windows-real-estable-104f785
```

---

**Git remoto:** VERIFICADO Y RECUPERABLE  
**Integral (código + BD en D:\):** ejecutar script Windows para PASS final
