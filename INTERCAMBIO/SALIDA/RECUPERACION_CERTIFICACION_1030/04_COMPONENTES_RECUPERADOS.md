# 04 — Componentes recuperados (y no recuperados)

## A. Componentes del paquete externo original — NO RECUPERADOS

| Componente | Estado | Evidencia ausencia |
|------------|--------|-------------------|
| `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip` | **AUSENTE** | No en disco, Git, stashes, bundles |
| `casos_oraculo.csv` | **AUSENTE** | Nunca en Git; solo citado en informes |
| `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv` | **AUSENTE** | Nunca en Git ni disco |
| `OPORTUNIDADES_1030_REAUDITORIA.md` | **AUSENTE** | Nunca en Git ni disco |
| `PX_CONTROLES.json` | **AUSENTE** | Nunca en Git ni disco |
| Casos OP-A…OP-F (definición externa/oráculo) | **AUSENTE** | Sin carpeta `CASOS/OP-*` tipo paquete |
| Casos NS-1/NS-2 (definición externa) | **AUSENTE** | |
| Casos PX-1…PX-4 (definición externa) | **AUSENTE** | |
| Harness certificación adversarial externo | **AUSENTE** | |

### Controles bloqueantes R01–R12 (matriz externa)

La matriz `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv` con controles R01–R12 **no fue localizada**. No se puede verificar existencia de definiciones oficiales de:

R01 Proactividad real, R02 Señal≠oportunidad, R03 Priorización global, R04 Momento, R05 Datos insuficientes, R06 Contradicción, R07 Transversalidad, R08 Idempotencia, R09 Valor materializado, R10 Cross-tenant, R11 Siguiente mejor acción, R12 Trazabilidad.

*(Los controles fueron verificados internamente en PR25 vía tests, pero eso es independiente del paquete externo.)*

---

## B. Artefactos internos recuperados (NO son el paquete externo original)

### B.1 `oportunidades_1030_interno/` (14 archivos)

| Archivo | Tamaño aprox. | Origen | Versionado Git | Commit primer add |
|---------|---------------|--------|----------------|-------------------|
| `CASO_OP_A.json` … `CASO_OP_F.json` | ~1.2 KB c/u | Salida certificación desarrollo PR #24 | Sí | `922c8e1` / `90beef9` |
| `CASO_NS_1.json`, `CASO_NS_2.json` | ~1.2 KB | Idem | Sí | `922c8e1` |
| `E2E_REACTIVO.json`, `E2E_PROACTIVO.json` | 1.8–1.3 KB | Idem | Sí | `922c8e1` |
| `PRIORIZACION_GLOBAL.json` | 3.6 KB | Idem | Sí | `922c8e1` |
| `SEGUNDA_EJECUCION.json` | 1.4 KB | Idem | Sí | `922c8e1` |
| `TRAZABILIDAD.json` | 3.7 KB | Idem | Sí | `922c8e1` |

**Naturaleza:** resultados JSON generados al ejecutar el sistema durante desarrollo/certificación interna. Contienen IDs de ejecución reales de SQLite de test, no inputs estáticos del paquete adversarial.

**Diferencia vs paquete externo:** no incluyen `setup.json`, `solicitud.txt`, `resultado_esperado.json` por caso como en paquete 1010 embebido.

### B.2 `reauditoria_externa_1030_interno/` (14 archivos)

| Archivo | Origen | Commit |
|---------|--------|--------|
| `run_blind_certification.py` | Script **autorado internamente** en PR25 | `4ac956f` |
| `brutos/*_ANTES_ORACULO.json` (12) | Salida del script interno | `4ac956f` |
| `resumen_fase_ciega.json` | Metadatos fase ciega interna | `4ac956f` |

**Naturaleza:** certificación ciega **reconstruida** a partir de payloads embebidos en `tests/test_oportunidades_proactivas_1030.py`, no del paquete ZIP externo.

### B.3 `test_oportunidades_proactivas_1030.py`

| Campo | Valor |
|-------|-------|
| Ruta original | `tests/test_oportunidades_proactivas_1030.py` |
| Función | Harness pytest con payloads `_signal_payload("OP-A")` etc. |
| Commit | `922c8e1` / `90beef9` |
| Es paquete externo | **NO** — código de prueba del producto |

### B.4 Referencias comparativas (otros paquetes)

| Carpeta copiada | Propósito |
|-----------------|-----------|
| `referencia_1010_paquete_embedded/` | Muestra estructura adversarial 1010 cuando ZIP no estaba en ENTRADA |
| `referencia_1000_entrada/` | ZIP 1000 confirmado como paquete externo real versionado |

---

## C. Comparación de versiones

No se encontraron **múltiples versiones** de `casos_oraculo.csv`, matriz 1030, ni protocolo reauditoría. No aplica análisis de divergencia entre versiones originales.

Única variante de evidencia 1030: salidas JSON de distintas ejecuciones (IDs/timestamps diferentes) en `oportunidades_1030/` vs `reauditoria_externa_1030/brutos/`.

---

## D. Protección del oráculo

`casos_oraculo.csv` **no fue localizado**. Por tanto:

- **NO se leyó** su contenido
- **NO se copió** (no existe fuente)
- **NO se utilizó** para adaptar código ni resultados en este pedido
