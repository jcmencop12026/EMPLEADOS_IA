# 06 — Verificación del respaldo

## Checklist obligatorio

| Verificación | Resultado |
|--------------|-----------|
| `git bundle verify` | **PASS** |
| Restauración Git temporal | **PASS** |
| SHA restaurado = SHA respaldado (`d034566`) | **PASS** |
| Tag `eiaax-v1-preconvergencia-windows-operativo` → `d034566` | **PASS** |
| Checksums SHA256 artefactos Git | **PASS** (ver `SHA256SUMS.txt`) |
| BD demo copiada + checksum | **PENDIENTE** (requiere ejecución Windows de `COPIAR_BD_DEMO_DESDE_WINDOWS.ps1`) |
| Un solo Alembic head documentado (`1770a1b2c3d4e`) | **PASS** |
| Scripts Windows incluidos en árbol | **PASS** (13 scripts, parser OK en `d034566`) |
| Ausencia de secretos en manifiesto | **PASS** (solo `credentials.example`) |
| Respaldo Lote 3 anterior intacto | **PASS** (`EIAAX_LOTE_3` sin modificar) |
| A+B+C+D integrados | **NO** |

## Detalle verificación Git

```
Bundle: eiaax-v1-preconvergencia-windows-d034566-20260901T182500Z.bundle
Verify: is okay
Clone test: /tmp/eiaax-recovery-preconv
HEAD after checkout: d0345663f0fcc286d9b68146735a05208839bd7e
Tag^{commit}:       d0345663f0fcc286d9b68146735a05208839bd7e
Match: PASS
```

## Detalle verificación árbol

Recuperado desde bundle:

- `backend/alembic/versions/1770a1b2c3d4e_mesa_ayuda_soporte_evolucion_mb12.py` — presente
- `scripts/windows/iniciar_demo_eiaax.ps1` — presente
- `frontend/vite.config.ts` — `strictPort: true` en `d034566`

## Secretos revisados

| Elemento | Estado |
|----------|--------|
| Manifiestos `.md` | Sin contraseñas reales |
| `credentials.example` | Solo placeholders documentales |
| Bundle Git | Sin `.env` con secretos |
| Logs | No incluidos |

## Integridad global

| Componente | Estado |
|------------|--------|
| Código Git | **ÍNTEGRO Y RESTAURABLE** |
| BD demo Windows | **PENDIENTE COPIA LOCAL** (script listo) |
| Respaldo Lote 3 | **INTACTO** |

## Declaración final

**ESTE ES EL PUNTO OPERATIVO WINDOWS ANTERIOR A LA CONVERGENCIA COMERCIAL V1 A+B+C+D.**

SHA: `d034566`  
Tag: `eiaax-v1-preconvergencia-windows-operativo`  
A+B+C+D: **NO integrados**
