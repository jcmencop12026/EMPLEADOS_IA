# EIAAX — Convergencia Comercial V1 (candidato integrado)

**Agente:** GENERAL  
**Rama:** `cursor/convergencia-comercial-v1-85e4`  
**Fecha:** 2026-09-01  
**Estado:** Candidato integrado — **NO declarar V1 terminada**

---

## Base operativa

| Elemento | Valor |
|----------|-------|
| Punto seguro Windows | tag `eiaax-v1-preconvergencia-windows-operativo` |
| SHA base | `d034566` |
| Respaldo verificado | `INTERCAMBIO/RESPALDOS/EIAAX_V1_PRECONVERGENCIA_WINDOWS/` |
| Mapa de convergencia | `INTERCAMBIO/SALIDA/EIAAX_PRECONVERGENCIA_COMERCIAL_V1/` |

---

## SHAs fuente portados selectivamente

| Bloque | Descripción | SHA | Rama origen |
|--------|-------------|-----|-------------|
| **C** | Centro Estratégico | `25c79d5` | `cursor/centro-control-estrategico-v1-dec7` |
| **B** | Flujo Comercial V1 | `2bb3caa` | `cursor/flujo-comercial-v1-3581` |
| **D** | Demo + Presentación | `40b7c9b` | `cursor/demo-comercial-ficticia-9a85` |
| **A** | Espacio Externo + Evidencias | `f0d02bc` | `cursor/espacio-externo-v1-3e3d` |

**Orden aplicado:** C → B → D → A (según mapa `07_ORDEN_PORTADO.md`; validado por dependencias reales).

---

## Head Alembic final

```
1820a1b2c3d4e (único head)
```

Cadena post-base `1770a1b2c3d4e`:

| Rev | Contenido |
|-----|-----------|
| `1780a1b2c3d4e` | Flujo comercial V1 (sector expediente, presentaciones ejecutivas, instrumentos, garantías) |
| `1790a1b2c3d4e` | Presentación ejecutiva real + config informes comerciales |
| `1800a1b2c3d4e` | Espacio externo empresa (entidades, publicaciones, entregas) |
| `1810a1b2c3d4e` | Espacio externo cliente v1b (proyecto_id, audiencia) |
| `1820a1b2c3d4e` | Evidencias externas versionadas (adjuntos) |

`migration_ledger.json` → `baseline_head: 1820a1b2c3d4e`

---

## Criterio de cierre alcanzado (candidato)

- Base operativa Windows `d034566` preservada (scripts `npm.cmd`, idempotencia arranque)
- A + B + C + D portados selectivamente sin merge mecánico
- Una autoridad por dominio (sin adapters competidores nuevos)
- Dos centros de control complementarios (MB-08 operacional + Centro Estratégico)
- Un solo head Alembic, upgrade limpio
- Enlaces reales flujo comercial (API + routers + permisos + frontend rutas)
- 67 tests acumulativos A+B+C+D PASS
- Frontend build PASS
- **Windows real:** PENDIENTE — no declarar PASS

---

## Próximos pasos (fuera de este bloque)

1. Arrancar candidato con scripts Windows verificados
2. Recorrido visual humano
3. Cruzar backlog histórico + hallazgos humanos
4. Bloque final experiencia/orquestación V1
