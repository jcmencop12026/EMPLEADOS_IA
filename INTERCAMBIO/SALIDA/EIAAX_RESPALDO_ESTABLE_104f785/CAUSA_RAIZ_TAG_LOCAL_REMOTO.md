# Causa raíz — conflicto tag local/remoto `eiaax-tools-respaldo-104f785`

## Incidente Windows

```
! [rejected] eiaax-tools-respaldo-104f785 -> eiaax-tools-respaldo-104f785
  (would clobber existing tag)
```

El bootstrap anterior ejecutaba:

```bat
git fetch origin tag eiaax-tools-respaldo-104f785
```

Si el repositorio Windows ya tenía un tag local con el **mismo nombre** pero apuntando a un **commit distinto** del remoto, Git rechaza la operación para no sobrescribir el tag local.

## A. Causa exacta

| Elemento | Descripción |
|---|---|
| Tag local | `eiaax-tools-respaldo-104f785` → commit **distinto** (creado en sesión previa o fetch parcial) |
| Tag remoto | `refs/tags/eiaax-tools-respaldo-104f785` en `origin` → commit autoritativo de herramientas |
| Fallo | `git fetch origin tag NAME` intenta actualizar el tag local → **rechazado** |

El producto `104f785` **no estaba dañado**. El bloqueo ocurrió **antes** de `[1/5]` porque la preparación no pudo obtener la referencia remota vía tag.

## B. Referencias (autoridad remota tras corrección)

| Ref | Commit esperado |
|---|---|
| `origin` tag `eiaax-tools-respaldo-104f785` | commit del paquete de herramientas (post-fix) |
| `refs/eiaax/bootstrap-tools-104f785` | **misma** referencia remota, ref dedicada bootstrap |
| Producto protegido `104f785` | `104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a` (sin cambios) |

## C. Corrección mínima

1. **No** tocar ni borrar el tag local `eiaax-tools-respaldo-104f785`.
2. Fetch explícito a ref dedicada:

   ```
   git fetch origin +refs/tags/eiaax-tools-respaldo-104f785:refs/eiaax/bootstrap-tools-104f785
   ```

3. Materializar con `git archive` usando **`refs/eiaax/bootstrap-tools-104f785`** (no el nombre del tag local).
4. Ejecutar `Entrada-Respaldo-Integral-104f785.cmd` materializado.

Archivos modificados (solo paquete herramientas, no producto):

- `Entrada-Respaldo-Integral-104f785.cmd`
- `Launch-Respaldo-Integral-104f785.ps1`
- `Bootstrap-Ejecutar-Respaldo-104f785.ps1`
- `COMANDO_WINDOWS_UNA_LINEA.txt`

## D. Garantías

- Tag local **no** se elimina ni reescribe.
- HEAD producto `104f785` **no** se modifica.
- `scripts/windows/**` **no** se toca.
- BD original **no** se toca (respaldo usa copia consistente).
