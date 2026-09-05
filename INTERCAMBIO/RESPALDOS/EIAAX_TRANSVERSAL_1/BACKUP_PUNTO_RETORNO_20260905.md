# Punto de retorno — Macrobloque Transversal 1

**Fecha/hora:** 2026-09-05 (UTC)
**Ruta:** `/workspace` (`D:\EMPLEADOS_IA_CONVERGENCIA`)
**Rama origen:** `cursor/integracion-funcional-final-85e4`

## SHA protegido

`3e6d2c3d825983280e640f70849e76e78abcbb6b`

## Mecanismos de restauración

| Mecanismo | Referencia | Comando restauración |
|---|---|---|
| Tag anotado | `backup/eiaax-antes-ajuste-transversal-1-20260905` | `git checkout backup/eiaax-antes-ajuste-transversal-1-20260905` |
| Rama respaldo | `backup/eiaax-antes-ajuste-transversal-1-20260905` | `git checkout backup/eiaax-antes-ajuste-transversal-1-20260905` |
| SHA exacto | `3e6d2c3` | `git checkout 3e6d2c3d825983280e640f70849e76e78abcbb6b` |

## Estado Git al crear backup

- Working tree: limpio (sin modificados rastreados)
- Untracked: `.venv-eiaax-demo/`, `data/evidence/`, respaldos previos, logs locales
- HEAD local = HEAD remoto `origin/cursor/integracion-funcional-final-85e4`

## Archivos locales preservados

- BD demo: no presente en `backend/eiaax_integrado_demo.db` en este entorno
- Evidencia E2E previa: `data/evidence/` (no rastreada, intacta)

## Verificación

```bash
git show-ref --verify refs/tags/backup/eiaax-antes-ajuste-transversal-1-20260905
git show-ref --verify refs/heads/backup/eiaax-antes-ajuste-transversal-1-20260905
# Ambos apuntan a 3e6d2c3d825983280e640f70849e76e78abcbb6b
```
