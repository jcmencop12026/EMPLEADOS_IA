# 06 — Migraciones: inventario y acción en convergencia

**Regla:** la cadena central conserva **una sola cabeza**. Revisiones `1410`/`1420`/`1430` de A/C/D **NO se portan literalmente**.

Base central `75fc689`: última migración conocida en cadena `d1e2f3a4b5c6` (merge multitenant).

---

## Tabla consolidada

| Rama | Rev histórica | Archivo | Objeto creado/modificado | Depende de | Acción convergencia | Nueva rev |
|------|---------------|---------|--------------------------|------------|---------------------|-----------|
| **A** | `1410a1b2c3d4e` | `gobierno_operacional_eiaax.py` | Tablas gobierno operacional, políticas acción | post-1405 evaluación | **RENUMERAR** → `15xx` | **SÍ** |
| **A** | `1420a1b2c3d4e` | `empresa_seguridad_gobierno_datos.py` | Clasificación, evidencia vínculo, visibilidad | A 1410 o central gobierno | **RENUMERAR** → `15xx` | **SÍ** |
| **A** | `1430a1b2c3d4e` | `espacio_externo_empresa.py` | `entidades_empresa`, publicaciones, entregas | 1420 A | **RENUMERAR** → `15xx` | **SÍ** |
| **A** | `1431a1b2c3d4e` | `espacio_externo_cliente_v1b.py` | contrato, proyecto_id, audiencia | A 1430 | **RENUMERAR** → `15xx` | **SÍ** |
| **A** | `1432a1b2c3d4e` | `espacio_externo_evidencias_v1c.py` | `evaluacion_entrega_adjuntos` | A 1431 | **RENUMERAR** → `15xx` | **SÍ** |
| **B** | `1600a1b2c3d4e` | `motor_economico_eiaax.py` | **MOD** economic tables | central 1600? | **MERGE** contenido B en rev existente o nueva `16xx` | **SÍ** |
| **B** | `1700a1b2c3d4e` | `centro_negocios_eiaax.py` | **MOD** negocio | central | **MERGE** | **SÍ** |
| **B** | `1710a1b2c3d4e` | `centro_negocios_cierre.py` | **MOD** | 1700 | **MERGE** | **SÍ** |
| **B** | `1720a1b2c3d4e` | `continuidad_comercial_operacional.py` | **MOD** | 1710 | **MERGE** | **SÍ** |
| **B** | `1730a1b2c3d4e` | `flujo_comercial_v1.py` | `comercial_presentaciones`, instrumentos, garantías | 1720 | **RENUMERAR** → `17xx` tras merge | **SÍ** |
| **C** | `1410a1b2c3d4e` | `partners_mb03.py` | partners MB-03 | central | **RENUMERAR** → `15xx` **COLISIÓN A** | **SÍ** |
| **C** | `1420a1b2c3d4e` | `arquitecto_transformacion.py` | dossier transformación | C 1410 | **RENUMERAR** **COLISIÓN A** | **SÍ** |
| **C** | `1430a1b2c3d4e` | `fabrica_mb06_puente.py` | bridge empleados IA | C 1420 | **RENUMERAR** **COLISIÓN A** | **SÍ** |
| **D** | `1410a1b2c3d4e` | `inteligencia_resultados_1410.py` | resultados extensión | central | **RENUMERAR** **COLISIÓN A,C** | **SÍ** |
| **D** | `1420a1b2c3d4e` | `centro_informacion_entregas_1420.py` | MB-11 entregas ext. | D 1410 | **RENUMERAR** **COLISIÓN A** | **SÍ** |
| **D** | `1430a1b2c3d4e` | `presentacion_ejecutiva_v1.py` | `presentacion_publicacion` | D 1420 | **RENUMERAR** **COLISIÓN A,C** | **SÍ** |

**Total migraciones a reconstruir/renumerar: 14**

---

## Colisiones de revisión (mismo ID, distinto archivo)

| Rev | A | C | D |
|-----|---|---|---|
| `1410` | gobierno operacional | partners MB-03 | inteligencia resultados |
| `1420` | empresa seguridad | arquitecto transformación | MB-11 entregas |
| `1430` | espacio externo | fábrica MB-06 | presentación ejecutiva |

**Acción GENERAL:** asignar rango `1500-1599` gobierno+seguridad+partners+resultados; `1600-1699` motor/negocio; `1700-1799` flujo comercial; `1800+` espacio externo+presentación — o secuencia lineal única post-merge.

---

## Cadena de dependencias recomendada (nueva numeración)

```
central_head
  → gobierno_operacional (ex-A-1410)
  → empresa_seguridad (ex-A-1420)
  → partners_mb03 (ex-C-1410)
  → arquitecto_transformacion (ex-C-1420)
  → inteligencia_resultados (ex-D-1410)
  → mb11_entregas (ex-D-1420)
  → fabrica_mb06_bridge (ex-C-1430)
  → motor_economico_merge (ex-B-1600 MOD)
  → centro_negocios_merge (ex-B-1700-1710 MOD)
  → continuidad_merge (ex-B-1720 MOD)
  → flujo_comercial (ex-B-1730)
  → espacio_externo (ex-A-1430-1432)
  → presentacion_ejecutiva (ex-D-1430) — o adapter-only sin tabla
```

---

## No portar

- Archivos de migración con revision ID duplicado sin renumerar.
- `migration_ledger.json` de ramas — regenerar desde cadena unificada.

---

## Verificación post-portado

1. `alembic heads` = 1 cabeza.
2. `alembic upgrade head` en BD limpia.
3. Tests acumulativos por lote (ver 07).
