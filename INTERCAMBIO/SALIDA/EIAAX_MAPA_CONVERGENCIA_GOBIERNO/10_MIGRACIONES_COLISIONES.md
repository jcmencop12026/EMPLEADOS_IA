# 10 — Migraciones: colisiones y dependencias

**Regla:** NO modificar Alembic en esta misión. GENERAL resuelve secuencia física.

**Ancestro común:** `7e9abba` → `1405a1b2c3d4e_expediente_evaluacion_1405`

---

## Colisión P0 — mismo revision ID, archivos distintos

### `1410a1b2c3d4e` — CINCO reclamantes

| Archivo | Rama / SHA | Contenido |
|---------|------------|-----------|
| `1410a1b2c3d4e_gobierno_operacional_eiaax.py` | Seguridad `c433bac` | Gobierno operacional |
| `1410a1b2c3d4e_evaluacion_piiax_prep_1410.py` | BP2 `ee57fab` | Prep PIIAX evaluación |
| `1410a1b2c3d4e_inteligencia_resultados_1410.py` | Resultados `af0e8cd`, Com `f32c815` | Tablas resultados |
| `1410a1b2c3d4e_partners_mb03.py` | Fábrica `2afd673`, Partners `fe646d4` | Partners MB-03 |

**down_revision:** todos → `1405a1b2c3d4e`

### `1420a1b2c3d4e` — CUATRO reclamantes

| Archivo | Rama / SHA | Contenido |
|---------|------------|-----------|
| `1420a1b2c3d4e_empresa_seguridad_gobierno_datos.py` | Seguridad `c433bac` | Clasificación, evidencia, visibilidad |
| `1420a1b2c3d4e_evaluacion_motor_siguiente_1420.py` | BP2 `ee57fab` | Motor siguiente acción |
| `1420a1b2c3d4e_arquitecto_transformacion.py` | Fábrica `2afd673` | Arquitecto transformación |
| `1420a1b2c3d4e_centro_informacion_entregas_1420.py` | Comunicaciones `f32c815` | Entregas informe |

**down_revision:** todos → `1410a1b2c3d4e` (pero cada rama tiene distinto 1410)

---

## Genealogía por rama (post-1405)

```
BASE 1405 (7e9abba)
│
├─ SEGURIDAD c433bac
│    └─ 1410 gobierno_operacional
│         └─ 1420 empresa_seguridad_gobierno_datos  ★ HEAD seguridad
│
├─ BP2 ee57fab
│    └─ 1410 evaluacion_piiax_prep
│         └─ 1420 evaluacion_motor_siguiente
│
├─ CENTRO NEGOCIOS fbfd6a2  (sin colisión 1410/1420)
│    └─ 1600 motor_economico
│         └─ 1700 centro_negocios
│              └─ 1710 centro_negocios_cierre
│
├─ FABRICA 2afd673
│    └─ 1410 partners_mb03
│         └─ 1420 arquitecto_transformacion
│              └─ 1430 fabrica_mb06_puente
│
├─ RESULTADOS af0e8cd
│    └─ 1410 inteligencia_resultados_1410
│
└─ COMUNICACIONES f32c815
     └─ 1410 inteligencia_resultados_1410  (mismo que resultados)
          └─ 1420 centro_informacion_entregas_1420
```

---

## Otras revisiones a considerar en merge

| Revision | Rama | Notas |
|----------|------|-------|
| `1430a1b2c3d4e` | Fábrica `2afd673` | Depende de 1420 arquitecto — renumerar tras resolver 1420 |
| `1600` / `1700` / `1710` | CN `fbfd6a2` | Cadena independiente desde 1405 — insertar después de resolver 1410-1430 |
| `1341` | base | centro_comunicaciones_mb11 — ya en ancestro |
| `14b0` / `14b1` | base | factory auditor merge — en todas las ramas |

---

## Estrategia recomendada GENERAL (secuencia lógica, no IDs finales)

Propuesta de **orden de aplicación** tras merge de código:

1. `1405` — ya común
2. **1410_gobierno_operacional** — primero (transversal seguridad/gobierno)
3. **1410_partners** — renumerar ID (ej. `1411...`)
4. **1410_inteligencia_resultados** — renumerar (ej. `1412...`)
5. **1410_evaluacion_piiax_prep** — renumerar (ej. `1413...`)
6. **1420_empresa_seguridad** — segundo pilar transversal
7. **1420_arquitecto** — renumerar
8. **1420_evaluacion_motor** — renumerar
9. **1420_entregas_informe** — renumerar
10. **1430_fabrica** — renumerar
11. **1600 → 1700 → 1710** motor/CN
12. Merge heads si quedan múltiples (alembic merge revision)

> Los IDs `1411`, `1412`, etc. son ilustrativos. GENERAL asigna revisiones únicas reales.

---

## Dependencias de código (no solo migración)

| Migración | Servicios que asumen tablas |
|-----------|----------------------------|
| 1410 gobierno | `gobierno_operacional_*`, routers gobierno |
| 1420 seguridad | `empresa_seguridad_*`, evaluacion dual-write |
| 1410 partners | `partner_*`, routers partners |
| 1420 arquitecto | `transformacion_*`, dossier |
| 1430 fábrica | bridge, requerimientos |
| 1410 resultados | `resultados_*` |
| 1420 entregas | comunicaciones entregas |
| 1600-1710 | motor económico, CN |

**Orden de merge código sugerido:**
1. Seguridad + Gobierno (`c433bac`)
2. Partners + Arquitecto + Fábrica (renumeradas)
3. Resultados + Comunicaciones
4. BP2
5. Centro Negocios (1600+)

---

## Hotspots merge código (archivos tocados en ≥2 ramas)

| Archivo | Ramas en conflicto |
|---------|-------------------|
| `backend/app/main.py` | Todas |
| `backend/app/permissions.py` | Seguridad, BP2, CN, Fábrica |
| `backend/app/services/evaluacion_service.py` | Seguridad, BP2 |
| `frontend/src/App.tsx` | Varias |
| `frontend/src/api.ts` | Varias |
| `frontend/src/auth/permissions.ts` | Varias |
| `frontend/src/navigation/menu.ts` | Varias |
| `tests/conftest.py` | Varias |

---

## Mapa colisión resumido

| ID | Conflictos | Severidad | Resolver por |
|----|------------|-----------|--------------|
| `1410a1b2c3d4e` | 5 archivos | **P0** | Renumerar 4; conservar 1 gobierno como primero |
| `1420a1b2c3d4e` | 4 archivos | **P0** | Renumerar 3; conservar empresa_seguridad tras gobierno |
| `1430` vs futuro | Cadena fábrica | P1 | Renumerar tras 1420 |
| Heads múltiples | Post-merge | P1 | `alembic merge` |

---

## Verificación post-secuencia

```bash
alembic history
alembic upgrade head   # en entorno limpio
pytest tests/test_empresa_seguridad_gobierno_datos.py
pytest tests/test_gobierno_operacional.py
# + tests rama integrada
```

No ejecutar en esta misión — instrucción para GENERAL.
