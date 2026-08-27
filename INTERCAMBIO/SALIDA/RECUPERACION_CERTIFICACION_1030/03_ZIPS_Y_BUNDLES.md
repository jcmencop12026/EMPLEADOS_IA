# 03 — ZIPs y bundles

## Inventario de archivos comprimidos

| Archivo | Tamaño | SHA-256 | Relación 1030 |
|---------|--------|---------|---------------|
| `INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` | 16 642 B | `d77d28c61de7c55864a586bddb3089415ee6202895008c136981c9c060cb0ecd` | Ninguna |

> Hash exacto en `05_HASHES_SHA256.csv` → `RECUPERADOS/referencia_1000_entrada/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip`

## ZIP buscado y ausente

| Archivo esperado | Estado |
|------------------|--------|
| `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip` | **NO EXISTE** en disco ni en Git |

## Inspección interna ZIP 1000 (listado, sin extraer sobre original)

```
MOTOR_ANALITICO_1000_DATASET_CERTIFICACION/
  MANIFIESTO.json
  MATRIZ_EVALUACION.csv
  ANTI_RESPUESTA_PREFABRICADA.json
  README_MAESTRO.md
  PEDIDO_CURSOR_CERTIFICACION_MOTOR_1000.md
  CASOS/CASO_A … CASO_E/
```

**Sin coincidencias** para: `casos_oraculo`, `OP-A`, `NS-1`, `PX-1`, `1030`, `OPORTUNIDADES`.

## Bundles Git (`*.bundle`)

| Resultado |
|-----------|
| **0 archivos** `*.bundle` en `/workspace` |

No aplicable `git bundle verify` ni `list-heads`.

## Estructura esperada del ZIP 1030 (inferida, NO recuperada)

Basada en documentación de informes PR25 y protocolo citado por el usuario (sin leer oráculo):

```
OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION/
  MANIFIESTO.json                    (presunto)
  casos_oraculo.csv                  (oráculo — NO LEÍDO, NO PRESENTE)
  OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv
  OPORTUNIDADES_1030_REAUDITORIA.md
  PX_CONTROLES.json
  CASOS/OP-A … OP-F, NS-1, NS-2, PX-1 … PX-4/  (presunto)
```

**Esta estructura es inferencia documental.** No se encontró ZIP ni carpeta descomprimida que la confirme.

## Acción tomada

- ZIP 1000 copiado a `RECUPERADOS/referencia_1000_entrada/` como referencia comparativa.
- **NO** se creó ZIP nuevo 1030.
- **NO** se extrajo ningún ZIP sobre ubicaciones originales.
