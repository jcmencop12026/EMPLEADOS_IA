# CURSOR — RECUPERACIÓN FORENSE CERTIFICACIÓN 1030

**Fecha:** 2026-08-27
**Proyecto:** EMPLEADOS_IA (`D:\EMPLEADOS_IA` / `/workspace`)
**Tipo:** recuperación y diagnóstico exclusivamente — **sin certificar, sin reconstruir, sin modificar código**
**Rama activa (sin cambios funcionales):** `cursor/preintegracion-1020-1030` @ `2e86ae3`
**PR #25:** https://github.com/jcmencop12026/EMPLEADOS_IA/pull/25 — continúa NO APTO (bloqueante: paquete externo)

---

## 1. Objetivo cumplido

Localizar el paquete externo original `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip` y sus componentes (`casos_oraculo.csv`, matriz R01–R12, protocolo reauditoría, casos OP/NS/PX, harness adversarial) mediante búsqueda exhaustiva en disco, Git, ramas, stashes, ZIPs y bundles.

**Resultado:** el paquete externo original **no está presente** en este entorno/repositorio.

---

## 2. Escenario forense declarado

### **D — NO EXISTE EVIDENCIA DE QUE EL PAQUETE ORIGINAL HAYA ESTADO EN ESTE EQUIPO/REPOSITORIO**

No aplica A (completo), B (componentes originales todos recuperados), ni C (recuperación parcial de componentes **originales**). Los artefactos internos encontrados son **derivados del desarrollo**, no recuperación del paquete adversarial externo.

---

## 3. Hallazgos por componente

| Componente | ¿Apareció? | Evidencia |
|------------|------------|-----------|
| `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip` | **NO** | 0 ZIP 1030 en disco; 0 en Git |
| `casos_oraculo.csv` | **NO** | Nunca versionado; solo citado en informes markdown (`4ac956f`) |
| `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv` | **NO** | Ausente disco y Git |
| `OPORTUNIDADES_1030_REAUDITORIA.md` | **NO** | Ausente disco y Git; pickaxe sin resultados |
| `PX_CONTROLES.json` | **NO** | Ausente disco y Git |
| Casos OP-A…OP-F (definición externa) | **NO** | Solo salidas JSON internas |
| Casos NS-1/NS-2 (definición externa) | **NO** | Solo salidas JSON internas |
| Casos PX-1…PX-4 (definición externa) | **NO** | Solo salidas JSON internas |
| Harness/script certificación **externo** | **NO** | Existe harness **interno** distinto |
| ZIP completo | **NO** | |

### Oráculo (`casos_oraculo.csv`)

- **No localizado** → **no leído**, **no copiado**, **no utilizado** en este pedido.
- Cumplida protección de certificación ciega para esta fase.

---

## 4. Búsquedas ejecutadas

### 4.1 Disco

- Recorrido completo `/workspace` con `find` + `rg`
- `INTERCAMBIO/ENTRADA`: solo `MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` (16 642 B)
- `INTERCAMBIO/HISTORICO`: vacío
- Sin carpetas `BACKUP*`, `RECUPER*`, `PARA_CHATGPT*` con contenido 1030
- **0** archivos `*.bundle`

Detalle: `RECUPERACION_CERTIFICACION_1030/01_BUSQUEDA_DISCO.md`

### 4.2 Git

- `git log --all`, `git branch -a`, `git tag`, `git stash list` (13), `git reflog`
- `git log --all -S` para cadenas del paquete 1030
- `git rev-list --all --objects`
- Ramas PR #24, PR #25, 1020, main: **sin archivos del paquete externo**
- Único ZIP histórico en ENTRADA: motor 1000 (`f0b9929`)

Detalle: `RECUPERACION_CERTIFICACION_1030/02_BUSQUEDA_GIT.md`

### 4.3 ZIPs

- Inspección `unzip -l` del ZIP 1000: sin contenido 1030
- ZIP 1030: **no existe**

Detalle: `RECUPERACION_CERTIFICACION_1030/03_ZIPS_Y_BUNDLES.md`

---

## 5. Artefactos internos (no equivalen al paquete externo)

| Ubicación original | Naturaleza | Copia en recuperación |
|--------------------|------------|----------------------|
| `INTERCAMBIO/SALIDA/oportunidades_1030/` | Salidas JSON desarrollo PR #24 | `RECUPERADOS/oportunidades_1030_interno/` |
| `INTERCAMBIO/SALIDA/reauditoria_externa_1030/` | Certificación ciega interna PR25 | `RECUPERADOS/reauditoria_externa_1030_interno/` |
| `tests/test_oportunidades_proactivas_1030.py` | Payloads embebidos en pytest | `RECUPERADOS/test_oportunidades_proactivas_1030.py` |
| `reauditoria_orquestador_1010/paquete_embedded/` | Referencia estructural 1010 | `RECUPERADOS/referencia_1010_paquete_embedded/` |
| `INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000...zip` | Referencia paquete real 1000 | `RECUPERADOS/referencia_1000_entrada/` |

Detalle y diferencias: `RECUPERACION_CERTIFICACION_1030/04_COMPONENTES_RECUPERADOS.md`

---

## 6. Patrón histórico comparativo

| Entrega | ZIP ENTRADA | En Git | Sustituto SALIDA |
|---------|-------------|--------|------------------|
| Motor 1000 | ✅ | ✅ | `reauditoria_externa_motor_1000/` |
| Orquestador 1010 | ❌ | ❌ | `paquete_embedded/` |
| **Oportunidades 1030** | **❌** | **❌** | **❌ (sin embebido)** |

El 1030 es el único paquete adversarial referenciado en informes que **nunca ingresó** al repositorio ni obtuvo sustituto embebido documentado.

---

## 7. Carpeta de recuperación creada

```
INTERCAMBIO/SALIDA/RECUPERACION_CERTIFICACION_1030/
  00_INVENTARIO.md
  01_BUSQUEDA_DISCO.md
  02_BUSQUEDA_GIT.md
  03_ZIPS_Y_BUNDLES.md
  04_COMPONENTES_RECUPERADOS.md
  05_HASHES_SHA256.csv          (56 archivos hasheados)
  06_CONCLUSION.md
  RECUPERADOS/
    oportunidades_1030_interno/
    reauditoria_externa_1030_interno/
    referencia_1010_paquete_embedded/
    referencia_1000_entrada/
    test_oportunidades_proactivas_1030.py
```

**Originales no movidos.** Solo copias en `RECUPERADOS/`.

Hash ZIP 1000 referencia: `d77d28c61de7c55864a586bddb3089415ee6202895008c136981c9c060cb0ecd`

---

## 8. Documentos externos citados por el usuario

`OPORTUNIDADES_1030_REAUDITORIA.md` y `OPORTUNIDADES_1030_MATRIZ_EVALUACION.csv` fueron mencionados como nueva evidencia, pero **no están en el filesystem de este entorno Cloud Agent**. Podrían existir únicamente en el equipo físico `D:\EMPLEADOS_IA` del usuario sin haberse sincronizado al remoto.

---

## 9. Siguiente paso seguro (NO ejecutado)

1. Buscar en el equipo físico Windows fuera del clon Git (Downloads, USB, correo, carpetas PARA_CHATGPT).
2. Si se localiza el ZIP original: copiar intacto a `INTERCAMBIO/ENTRADA/`, registrar SHA-256, **no abrir oráculo** hasta congelar brutos.
3. Si no se localiza: solicitar reenvío al proveedor de certificación — **no reconstruir oráculo** desde resultados internos.
4. Tras disponer del paquete: certificación ciega → comparación oráculo → actualizar veredicto PR #25.

---

## 10. Prohibiciones respetadas

- Sin modificar código 1020/1030, migraciones, BD, PR #25
- Sin certificar, PASS, APTO, merge, cierre PR #24
- Sin reconstruir paquete ni oráculo
- Sin alterar resultados anteriores de certificación
- Sin leer `casos_oraculo.csv` (no existente)

---

## 11. Referencias cruzadas

- Informe reauditoría PR25: `CURSOR_REAUDITORIA_FINAL_PR25_1020_1030.md`
- Evidencia interna previa: `reauditoria_externa_1030/brutos/`
- Patrón 1010 sin ZIP: `REAUDITORIA_EXTERNA_ORQUESTADOR_EXPERIENCIA_1010.md`

---

*Recuperación forense completada — escenario D*
