# 10 — Pruebas y runtime

## Comandos

```bash
python3 -m pytest tests/test_arquitecto_transformacion.py -q
python3 -m pytest tests/test_bloque_producto_1_evaluacion.py -q  # regresión BP1
python3 -m pytest tests/test_mb03_partners.py -q                 # regresión partners
cd frontend && npm run build
```

## Casos (8)

| Test | Verifica |
|------|----------|
| registrar_necesidad_y_dossier | NECESIDAD → expediente + dossier |
| suficiencia_con_informacion_incompleta | No bloqueo, confianza |
| diagnostico_completo | Causas, alternativas, escenarios |
| causas_sintoma_vs_probable | Taxonomía causal |
| dossier_no_repregunta | Reutilización conocimiento |
| multitenant_aislamiento | Org A ≠ Org B |
| rbac_sin_permiso | 403 viewer |
| recorrido_e2e | Flujo representativo completo |

## Runtime navegador

Ruta: `/arquitecto-transformacion`

Recorrido: Inicio → Necesidad → Información → Diagnóstico → Transformación → Acción

Enlace cruzado a `/evaluaciones/{id}` para completar información.

## Resultado

25+ tests passed en suite focal (8 transformación + 8 BP1 + 9 partners).
