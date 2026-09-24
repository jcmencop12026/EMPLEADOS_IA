# Evidencia Macrobloque Integral V1 — PR #171

## Índice local (agente)

| Suite | Reporte | Capturas |
|-------|---------|----------|
| Visual transversal (44 checks) | `transversal-visual/report.json` | `transversal-visual/*.png` |
| Flujo Vista Empresa E2E | `vista-empresa-flow/report.json` | `vista-empresa-flow/*.png` |

## CI GitHub Actions

En cada PR, el job **Certificación visual PR171** sube el artefacto:

`eiaax-visual-pr171-<SHA>`

Contiene `data/evidence/` completo (capturas + reportes JSON).

## Reproducir localmente

```bash
# Backend + frontend en 127.0.0.1:8000 / 5180
EIAAX_BASE=http://127.0.0.1:5180 node scripts/cert_transversal_visual.mjs
EIAAX_BASE=http://127.0.0.1:5180 node scripts/cert_vista_empresa_flow.mjs
node scripts/cert_macrointegral_v1.mjs
```
