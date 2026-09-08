# EIAAX — Corrección final causal PR #171

**Declaración:** NO MERGE — ESPERANDO REAUDITORÍA CHATGPT

## Identificación

| Campo | Valor |
|---|---|
| PR | #171 |
| Rama | `cursor/ajuste-transversal-1-85e4` |
| SHA inicial (auditado ChatGPT) | `20dcfd139d687123fc9f707e1bdc15081584ac44` |
| SHA final | `c8614a0254561876531d48cc7d79b65383f541de` |
| Artifact | `eiaax-visual-pr171-c8614a0254561876531d48cc7d79b65383f541de` |

## Causa exacta del ciclo 5×3

La clase modificadora `v1-cycle-stepper--wrap` aplicaba sobre `.v1-cycle-stepper__track`:

```css
display: grid;
grid-template-columns: repeat(5, minmax(0, 1fr));
```

Con 15 etapas y `flex-direction: column` en cada `.v1-cycle-step`, el resultado era **5 columnas × 3 filas de tarjetas grandes** (~medio viewport), exactamente lo rechazado en la auditoría.

## Corrección aplicada

1. **Eliminada** la clase `v1-cycle-stepper--wrap` del componente `CycleStepper.tsx`.
2. **Reemplazado** el grid 5×3 por un **stepper horizontal compacto**:
   - `display: flex; flex-wrap: nowrap` en el track
   - scroll horizontal interno controlado
   - chips en fila (número + nombre), altura ~36–48px
   - conectores visuales entre etapas (`::after`)
   - estados reales: `done`, `current`, `next`, `pending` (sin progreso inventado)
3. **Compactación CC empresa** (sin romper cabecera unificada, 4 tarjetas ejecutivas, selector, Presentar, Ver empresa):
   - hero `cc-empresa-hero` con banda meta horizontal
   - KPI en fila única (`repeat(6, 1fr)`)
   - padding vertical reducido en resumen y executive card
4. **Certificación** `cert_transversal_visual.mjs`:
   - viewport **1440×900** añadido
   - auditoría anti-5×3 (altura máx, filas máx 2, detección grid 5 cols)
   - 72/72 checks visuales

## Archivos cambiados

- `frontend/src/components/v1/CycleStepper.tsx`
- `frontend/src/styles/eiaax-experience-v1.css`
- `frontend/src/components/centroControl/CentroControlEmpresaPanel.tsx`
- `scripts/cert_transversal_visual.mjs`

## Evidencia visual (scrollY = 0)

| Captura | Estado |
|---|---|
| `1366x768_01-centro-de-control-global.png` | Stepper horizontal compacto, NO 5×3 |
| `1366x768_02-centro-de-control-empresa-seleccionada.png` | Mejoras preservadas + hero/KPI compactos |
| `1440x900_01-centro-de-control-global.png` | Stepper una fila |
| `1440x900_02-centro-de-control-empresa-seleccionada.png` | Empresa compacta |
| `1920x1080_01-centro-de-control-global.png` | 15 etapas en banda horizontal |

## Regresión local

| Suite | Resultado |
|---|---|
| `npm run build` | PASS |
| `cert_transversal_visual.mjs` | **72/72** visual + **18/18** tabs |
| `cert_vista_empresa_flow.mjs` | PASS |
| `test_macrointegral_v1_correcciones.py` | (CI) |

## CI

Run `34117716789` — **5/5 PASS** (último push `57b89c6`).

## Prueba humana Windows

Copia aislada: `D:\EIAAX_V1_PRUEBA`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\EIAAX_V1_PRUEBA\scripts\windows\actualizar_prueba_humana_v1.ps1"
```

SHA por defecto: `57b89c6a04bff6452bab06e1b4e4c73a5f2647a3`

**Nota:** los scripts `detener_demo_eiaax.ps1`, `preparar_demo_eiaax.ps1` e `iniciar_demo_eiaax.ps1` leen `$env:EIAAX_WORKTREE`; el actualizador la fija antes de invocarlos (no usar `-EIAAX_WORKTREE` como parámetro de script).
