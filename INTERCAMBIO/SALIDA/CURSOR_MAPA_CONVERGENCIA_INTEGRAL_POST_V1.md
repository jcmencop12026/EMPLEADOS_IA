# EMPLEADOS IA — Mapa de convergencia integral POST-V1

**Tipo:** Solo análisis — convergencia NO ejecutada  
**Fecha análisis:** 2026-08-29  
**Base convergida oficial:** `cursor/1250-convergencia-final-post-v1` @ `eb229806136e29acddc0f592b5f017f5c3cb2958`  
**Comando remoto:** `git fetch origin --prune` ejecutado

---

## 1. Verificación remota de ramas

| Bloque | Rama remota | Existe | SHA completo verificado | Commits exclusivos vs base | Merge-base con base |
|--------|-------------|--------|-------------------------|----------------------------|---------------------|
| 1250 | `cursor/1250-convergencia-final-post-v1` | Sí | `eb229806136e29acddc0f592b5f017f5c3cb2958` | 0 | `eb22980` (idéntico) |
| 1260 | `cursor/1260-aprendizaje-repriorizacion` | Sí | `6a6cfbcfaf64fde501e0586700d8e6639498f644` | 1 | `062db083ab9439e74f766ea570cdfbddb1af49e1` (1250A) |
| 1270 | `cursor/1270-multiproveedor-observabilidad-9a85` | Sí | `f89639a7305f86dabe149337de3a89c189372a01` | 10 | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` (pre-1250) |
| 1280 | `cursor/1280-modelo-comercial-valor-85e4` | Sí | `9a616739c4ab1f0766cf7d46005baf2a4c3e4fec` | 15 | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` |
| 1290 | `cursor/1290-optimizacion-recomendaciones` | Sí | `7141b434772f1510a58f6f23db3e21bff871103b` | 3 | `062db08` (vía 1260 en árbol) |
| 1300 | `cursor/1300-seguridad-avanzada-mfa` | Sí | `09194d8f281a1506d694844dead43e5ee93849e6` | 1 | `6352836813da85e31514e19cef125bcff53b4191` (fix tests pre-1250) |
| 1310 | `cursor/1310-segmentacion-planes-verticales` | Sí | `379ffcf04cd0d56a3aeda0b307f718845d5c12d3` | 17 | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` |
| 1320 | `cursor/1320-tco-ecosistema-aliados` | Sí | `703bbf9dfe3075a3c8fa622c1cb9056995b23be4` | 18 | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` |
| 1330 | `cursor/1330-integraciones-reales-conectores` | Sí | `5271ae54f62113b231b20541700e102c6dca3320` | 3 | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` |
| 1340 | `cursor/1340-implementacion-exito-cliente` | Sí | `5670a5727943a50bb78e3d1d41af7ed745516059` | 20 | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` |
| 1360 | `cursor/1360-continuidad-resiliencia` | Sí | `3edc6370488edf3441268b40fde6954f93767ff9` | 1 | `eb22980` (base oficial) |
| 1350 | — | **No** | — | — | RESERVADO |
| 1370 | — | **No** | — | — | RESERVADO |

**Notas SHA:**
- `1340` HEAD corto `5670a57` → completo `5670a5727943a50bb78e3d1d41af7ed745516059` ✓
- `1320` HEAD reportado alternativo `703bbf9aec8e807e...` **no coincide** con remoto; válido: `703bbf9dfe3075a3c8fa622c1cb9056995b23be4`
- `1350` y `1370`: sin rama remota en `origin` al momento del análisis

---

## 2. Genealogía real

### 2.1 Árbol conceptual

```
                    [pre-V1 / 1110 / 1200 / 1210 / 1120]
                                    |
            +-----------------------+------------------------+
            |                       |                        |
      1270 (1210)              1280 (1200)              1330 (1120)
            |                       |                        |
            |                  1310 / 1320                   |
            |                       |                        |
            |                    1340 (1320)                   |
            |                                                |
      1250A (062db08) ---- 1260 ---- 1290                    |
            |                                                |
      1250 fix (6352836) -- 1300                             |
            |                                                |
      1250A + 1250B ---- 1250f (eb22980) ---- 1360           |
            (convergencia oficial)                           |
```

### 2.2 Padre directo (first-parent) de cada tip

| Rama | Padre inmediato | Interpretación |
|------|-----------------|----------------|
| 1260 | `062db08` (1250A) | Deriva de convergencia parcial 1250A, **no** de 1250f |
| 1290 | `fa6db17` → cadena 1260 | Depende funcionalmente de 1260 |
| 1300 | `6352836` (fix tests) | Base pre-1250B limpia, **no** 1250f |
| 1270 | `cd13421` → cadena 1210/1110 | Deriva de valoración 1210 |
| 1280 | `f8f5e17` → cadena 1200/1210/1110 | Deriva de línea base 1200 + comercial |
| 1310 | `aa04780` → cadena 1280 | Extiende 1280 |
| 1320 | `8849a6a` → cadena 1280 | Extiende 1280 (paralelo a 1310) |
| 1340 | `14f05d4` → cadena 1320 | Extiende 1320 |
| 1330 | `5eaad7e` → `38f7b7d` (1120) | Deriva de señales 1120 |
| 1360 | `eb22980` (1250f) | **Única rama alineada con convergencia final** |

### 2.3 Contenido heredado que NO debe reaplicarse

Al integrar desde tips de rama completa vs `eb22980`, el diff muestra **miles de eliminaciones** (1220, 1240, Centro de Control, inteligencia externa, tests de convergencia 1250). Contenido ya presente en base y que **no** debe volver a integrarse:

| Bloque | Commits/historial heredado (omitir en convergencia) |
|--------|-----------------------------------------------------|
| 1270 | `bc7e53c` (1110), `8f8e57f` (1210), docs 1110/1210 |
| 1280 | `0278177` (1200), `8f8e57f` (1210), `0dd9cf7` merge 1200, 1110 docs |
| 1310/1320/1340 | Toda la cadena 1280 heredada + docs |
| 1330 | `38f7b7d` (1120), `5eaad7e` (docs 1120) — **1120 ya en 1250** |
| 1260/1290/1300 | Ausencia de routers 1240/control_center en tip (regresión si se mergea tip) |

**Conclusión genealógica:** La convergencia debe usar **commits funcionales netos** sobre `eb22980`, no merge de tips de rama.

---

## 3. Commits exclusivos propuestos para incorporación

| Bloque | Commits a incorporar | Tipo | Omitir |
|--------|---------------------|------|--------|
| **1360** | `3edc6370488edf3441268b40fde6954f93767ff9` | feat completo | — |
| **1300** | `09194d8f281a1506d694844dead43e5ee93849e6` | feat completo | — |
| **1260** | `6a6cfbcfaf64fde501e0586700d8e6639498f644` | feat completo | — |
| **1290** | `fa6db179f223fd2185e702e0cf748511cb68e2ac` | feat | `7141b43` (solo docs HEAD) |
| **1270** | `cd13421fb47b61c5c7836097fb2e499a7f619ce6` | feat | `f89639a` (docs), cadena 1110/1210 |
| **1280** | `e64676b`, `f8f5e17`, `64fb7d9` (test fix) | feat + test | docs `41b2926`, `9a61673` |
| **1310** | `aa04780535e5e458eb4a0b244c8def87b5cc947a` | feat | `379ffcf` (docs) |
| **1320** | `80cc277` (SHA completo en árbol: buscar en `703bbf9^`) | feat | docs `8849a6a`, `703bbf9` |
| **1330** | `5271ae54f62113b231b20541700e102c6dca3320` | feat | `38f7b7d`, `5eaad7e` |
| **1340** | `14f05d4099dd8cd25f587c628b3bb10f94cc6558` | feat | `5670a57` (docs), cadena 1280/1320 |

**Alternativa comercial:** Integrar tip `1340` funcionalmente equivale a 1280+1320+1340, pero **solo** si se extraen parches sin eliminar módulos 1250.

---

## 4. Dependencias funcionales

```
1250f (eb22980)
 ├── 1360 continuidad (directo)
 ├── 1300 seguridad (re-parent Alembic requerido)
 ├── 1260 aprendizaje
 │    └── 1290 optimización
 ├── 1270 multiproveedor IA (extiende llm_providers)
 ├── 1330 conectores (salud → 1360/1350 futuro)
 └── 1280 comercial
      ├── 1310 segmentación
      ├── 1320 TCO
      │    └── 1340 implementación / éxito cliente
      └── (1310 y 1320 son paralelos sobre 1280)

Futuro (NO integrar ahora):
  1350 → requiere 1270 + 1330
  1370 → requiere 1300
  1360 adapters → 1260 + 1270 + 1330 + Centro Control (post-convergencia)
```

---

## 5. Orden de integración recomendado

**No usar orden numérico estricto.** Orden técnico que minimiza duplicación, conflictos y regresiones:

| Paso | Bloque | Justificación |
|------|--------|---------------|
| 0 | Crear `cursor/convergencia-integral-post-v1` desde `eb22980` | Rama única de integración |
| 1 | **1360** | Ya alineado; aditivo; sin pérdida de 1250 |
| 2 | **1300** | Seguridad/MFA temprano; toca auth/sesiones |
| 3 | **1270** | Extiende LLM; antes de 1330/1350 futuro |
| 4 | **1330** | Conectores ortogonales; 1120 ya en base |
| 5 | **1280** | Base comercial (2 migraciones) |
| 6 | **1310** | Segmentación sobre comercial |
| 7 | **1320** | TCO sobre comercial (paralelo 1310 ya integrado) |
| 8 | **1340** | Implementación sobre TCO |
| 9 | **1260** | Aprendizaje |
| 10 | **1290** | Requiere 1260 |
| 11 | **Merge migration Alembic** | Una sola head final |
| 12 | **Centro Control** | Cablear adaptadores 1320/1360 + futuros |

**Rama comercial alternativa:** Si conflictos 1310↔1320 en `commercial_models.py`, integrar 1280 → 1320 → 1340 → 1310 (segmentación al final).

---

## 6. Alembic — DAG y estrategia de head única

### 6.1 Revisiones nuevas por bloque

| Revisión | down_revision actual | En rama | Notas |
|----------|---------------------|---------|-------|
| `1260a1b2c3d4e` | `1250a1b2c3d4e` | 1260, 1290 | Re-parent → head convergencia |
| `1290a1b2c3d4e` | `1260a1b2c3d4e` | 1290 | Lineal tras 1260 |
| `1270a1b2c3d4e` | `1210b2c3d4e5f` | 1270 | Re-parent; 1210 ya en 1250 |
| `1280a1b2c3d4e` | `1200b1c2d3e4f` | 1280–1340 | Re-parent; 1200 ya en 1250 |
| `1280b2c3d4e5f` | `1280a1b2c3d4e` | 1280–1340 | Lineal |
| `1310a1b2c3d4e` | `1280b2c3d4e5f` | 1310 | Tras comercial |
| `1320a1b2c3d4e` | `1280b2c3d4e5f` | 1320, 1340 | Paralelo a 1310 |
| `1340a1b2c3d4e` | `1320a1b2c3d4e` | 1340 | Tras TCO |
| `1330a1b2c3d4e` | `1120a1b2c3d4e` | 1330 | Re-parent; 1120 ya en 1250 |
| `1300a1b2c3d4e` | `1250a1b2c3d4e` | 1300 | Re-parent |
| `1360a1b2c3d4e` | `1250f1a2b3c4d` | 1360 | **Correcto** |

### 6.2 Heads si se integran tips sin re-parent

Se producirían **múltiples heads** (mínimo 6): `1360`, `1300`, `1270`, `1330`, `1340` (cadena), `1290`.

### 6.3 DAG objetivo (lineal sobre 1250f)

```
1250f1a2b3c4d
  → 1360a1b2c3d4e
  → 1300a1b2c3d4e'        (re-parent)
  → 1270a1b2c3d4e'        (re-parent)
  → 1330a1b2c3d4e'        (re-parent)
  → 1280a1b2c3d4e'
  → 1280b2c3d4e5f
  → 1310a1b2c3d4e
  → 1320a1b2c3d4e
  → 1340a1b2c3d4e
  → 1260a1b2c3d4e'
  → 1290a1b2c3d4e
  → [opcional: 1400merge convergencia integral]
```

**Acciones posteriores (no ejecutar ahora):**
- Editar `down_revision` de migraciones re-parentadas O crear migraciones merge vacías
- Actualizar `migration_ledger.json` y `schema_repair.HEAD_REVISION`
- `assert_single_head()` debe devolver una sola revisión

---

## 7. Modelos — inventario y conflictos

| Bloque | Archivos modelo | Tablas nuevas principales | Riesgo |
|--------|-----------------|---------------------------|--------|
| 1260 | `learning_models.py` | `ciclos_aprendizaje`, `retroalimentaciones`, `recalibraciones`, `patrones_aprendizaje`, `aprendizaje_auditoria` | Bajo |
| 1270 | (extiende `llm_models`) | tablas LLM routing/observabilidad en migración 1270 | Medio — solapamiento gateway V1 |
| 1280–1340 | `commercial_models.py` | `commercial_*` (planes, propuestas, escenarios…) | **Alto** — archivo compartido 1280/1310/1320/1340 |
| 1310 | `segmentation_models.py` | `commercial_sectors`, `commercial_segments`, `commercial_packages`, … | Medio — FK a comercial |
| 1290 | `optimization_models.py` | `optimizacion_*` | Bajo |
| 1300 | `security_models.py` | `organization_security_policies`, `user_mfa_*`, `user_sessions`, `security_events`, … | Medio — FK users/orgs |
| 1320 | `tco_models.py` | `tco_*` (14+ tablas) | Medio |
| 1340 | `implementacion_models.py` | `impl_*`, `exito_*` | Medio |
| 1330 | `integration_models.py` | `integration_connectors`, `integration_executions`, `integration_webhook_events` | Bajo |
| 1360 | `continuidad_models.py` | `cont_*` (20 tablas) | Bajo — prefijo aislado |

**Duplicados / colisiones previsibles:**
- `commercial_models.py`: crecimiento incremental 1280→1310; integrar fuera de orden rompe FK
- Enums: `commercial_*`, `seguridad.*`, `integraciones.*` — revisar nombres en `permissions.py`
- 1270 vs `llm_models` existente en 1250: posible duplicación de políticas de proveedor

---

## 8. Routers

| Bloque | Router nuevo | Prefijo API | Registro main.py | Colisión |
|--------|--------------|-------------|------------------|----------|
| 1260 | `aprendizaje.py` | `/api/aprendizaje` | Sustituye CC/1240 si merge tip | **Alta** |
| 1290 | `optimizacion.py` | `/api/optimizacion` | Junto aprendizaje | Media |
| 1270 | (extiende `llm_providers`) | `/api/llm/*` | Elimina senales/CC en tip | **Alta** |
| 1280 | `comercial.py` | `/api/comercial` | Elimina diagnosticos/CC | **Alta** |
| 1310 | `segmentacion.py` | `/api/segmentacion` | — | Media |
| 1320 | `tco.py` | `/api/tco` | — | Media |
| 1340 | `implementacion.py` | `/api/implementacion` | — | Media |
| 1330 | `integraciones.py` | `/api/integraciones` | Elimina valoracion/linea_base | **Alta** |
| 1300 | `security.py` | `/api/security` | Aditivo parcial | Media |
| 1360 | `continuidad.py` | `/api/continuidad` | **Aditivo correcto** | Baja |

**main.py en base 1250 conserva:** auth, organization, platform, admin, audit, assistant, agent_factory, capabilities, tools, knowledge, test_lab, operations, automations, notifications, finops, salud, experience, oportunidades, **senales**, **linea_base**, valoracion, **diagnosticos**, **inteligencia_externa**, **control_center**, llm_providers.

**Regla convergencia:** Acumular routers nuevos sin eliminar los de 1250.

---

## 9. RBAC — permisos nuevos 1260–1360

| Bloque | Permisos nuevos |
|--------|-----------------|
| 1260 | `aprendizaje.view`, `.evaluate`, `.recalibrate`, `.approve` |
| 1290 | `optimizacion.view`, `.simulate`, `.create`, `.approve`, `.configure` |
| 1280 | `comercial.view`, `.simulate`, `.create`, `.approve`, `.manage_plans` |
| 1310 | `segmentacion.view`, `.manage`, `.recommend`, `.approve_discount`, `planes.*` |
| 1320 | `tco.view`, `.manage`, `.simulate`, `proveedores.*`, `alianzas.*` |
| 1340 | `implementacion.*`, `exito_cliente.*` |
| 1330 | `integraciones.view`, `.create`, `.configure`, `.test`, `.execute`, `.manage_secrets` |
| 1300 | `seguridad.view`, `.manage_policy`, `.revoke_sessions`, `.audit` |
| 1360 | `continuidad.*`, `incidentes.*`, `backups.*` |

**Conflictos:**
- `admin.security.view` (existente) vs `seguridad.*` (1300) — clarificar namespaces
- `proveedores.*` (1320) vs `llm.*` (1270) — convergencia futura 1270/1320
- `seed_permissions` / `ROLE_PERMISSIONS_FALLBACK` — actualizar admin, operator, viewer en un solo commit final

---

## 10. Frontend

| Bloque | Rutas nuevas | Menú | Páginas | Conflictos |
|--------|--------------|------|---------|------------|
| 1260 | `/aprendizaje` | Análisis | `AprendizajePage`, `AprendizajeDetailPage` | Elimina InteligenciaExterna en tip |
| 1290 | `/optimizacion` | Análisis | `OptimizacionPage`, `OptimizacionDetailPage` | — |
| 1280 | `/comercial` | Comercial | `ComercialPage`, `ComercialPropuestaDetailPage` | Modifica CentroControlPage |
| 1310 | `/segmentacion` | Comercial | `SegmentacionPage` | — |
| 1320 | `/tco` | Comercial | `TcoPage` | — |
| 1340 | `/implementacion` | Operaciones/CS | `ImplementacionPage`, `ImplementacionDetailPage` | — |
| 1330 | `/integraciones` | Operaciones | `IntegracionesPage`, wizard, detail | Elimina rutas diagnóstico |
| 1300 | `/mi-seguridad` | Usuario | `MiSeguridadPage`; extiende `LoginPage`, `AdminSecurityPage` | **Alta** — login/MFA |
| 1360 | `/continuidad` | Análisis | `ContinuidadPage` | **Aditivo** |

**Archivos de alto conflicto:** `App.tsx`, `AppShell.tsx`, `api.ts`, `auth/permissions.ts`, `CentroControlPage.tsx`, `AdminSecurityPage.tsx`, `LoginPage.tsx`.

---

## 11. Centro de Control — adaptadores

| Bloque | Adaptador existente | Acción posterior |
|--------|--------------------|------------------|
| 1250 | `control_center.router` + `CentroControlPage` | Mantener como hub |
| 1320/1340 | `tco_service.centro_control_resumen()` + endpoint en `tco.py` | Integrar en CC tras convergencia |
| 1360 | `continuidad_service.centro_control_resumen()` + `centro_control_adapter` | Integrar en CC |
| 1260 | No implementado | Consumir aprendizaje/patrones |
| 1270 | No implementado | Métricas multiproveedor |
| 1280/1310 | No implementado | Resumen comercial |
| 1290 | No implementado | Recomendaciones activas |
| 1300 | No implementado | Postura seguridad/MFA |
| 1330 | Prep en 1360 (`integracion_1330_prep`) | Salud conectores |

**NO modificar 1230/1250C ahora** — cableado en fase post-convergencia.

---

## 12. Pruebas — inventario y matriz

### 12.1 Suites focales por bloque

| Bloque | Archivo test principal |
|--------|------------------------|
| 1260 | `tests/test_aprendizaje_1260.py` |
| 1270 | `tests/test_bloque_1270_multiproveedor.py` |
| 1280 | `tests/test_modelo_comercial_1280.py` |
| 1290 | `tests/test_optimizacion_1290.py` |
| 1300 | `tests/test_bloque_1300_seguridad_avanzada.py` |
| 1310 | `tests/test_segmentacion_1310.py` |
| 1320 | `tests/test_tco_1320.py` |
| 1330 | `tests/test_integraciones_1330.py` |
| 1340 | `tests/test_implementacion_1340.py` |
| 1360 | `tests/test_continuidad_1360.py` |

### 12.2 Matriz post-convergencia

| Capa | Comando / alcance |
|------|-------------------|
| Focal por bloque | Cada `test_*_{bloque}.py` anterior |
| Migraciones | `tests/test_migration_control.py` + `alembic heads` única |
| Regresión 1250 | `test_convergencia_final_1250.py`, `test_inteligencia_externa_1240.py`, `test_diagnostico_transversal_1220.py`, `test_bloque_1250c_centro_control_integrado.py` |
| Multiempresa | Casos en cada suite focal |
| RBAC | Viewer denegado + admin permitido por bloque |
| Auditoría | Por bloque donde aplique |
| Frontend | `npm run build` |
| Integración | Smoke API por prefijo `/api/{modulo}` |

---

## 13. Riesgos de convergencia

### ALTO
1. **Merge de tips de rama** elimina módulos 1220/1240/Centro de Control
2. **Alembic multi-head** si no se re-parentan 1260/1300/1270/1280/1330
3. **main.py / App.tsx** — resolución manual acumulativa
4. **commercial_models.py** — cadena 1280→1310/1320→1340
5. **1300 MFA** — impacto en `auth`, `LoginPage`, sesiones activas

### MEDIO
6. **1270 vs llm_providers V1** — políticas y routing duplicados
7. **1330 vs señales 1120** — re-aplicar 1120 duplicaría ingesta
8. **permissions.py** — ~40 permisos nuevos + roles
9. **conftest.py** — imports de modelos acumulados
10. **schema_repair / migration_ledger** — HEAD único

### BAJO
11. **1360 `cont_*`** — prefijo aislado, ya en base correcta
12. **Tests docs-only commits** — omitibles

---

## 14. Procedimiento de convergencia (para ejecución futura)

1. `git fetch origin --prune`
2. Crear rama `cursor/convergencia-integral-post-v1` desde `eb229806136e29acddc0f592b5f017f5c3cb2958`
3. Por cada bloque en orden §5: aplicar commit(s) funcionales §3 (cherry-pick o replay manual)
4. Resolver conflictos preservando **todos** los routers de 1250
5. Re-parentar migraciones Alembic según DAG §6.3
6. Unificar `permissions.py`, `main.py`, `conftest.py`, `migration_ledger.json`, `schema_repair.py`
7. Ejecutar matriz de pruebas §12.2
8. `npm run build`
9. Crear migración merge final si quedan heads paralelas (1310∥1320)
10. Actualizar Centro de Control con adaptadores
11. Entregable convergencia + PR — **sin merge a main**

**Prohibido:** merge directo de tips, `git add .`, tocar V1/e8cb853, PR #32, ramas 1350/1370.

---

## 15. Posición futura reservada

| Bloque | Estado | Dependencias futuras |
|--------|--------|---------------------|
| **1350** | RESERVADO — sin rama remota | 1270 + 1330 |
| **1370** | RESERVADO — sin rama remota | 1300 |

---

## 16. Veredicto

| Criterio | Resultado |
|----------|-----------|
| RAMAS VERIFICADAS | **10** de 10 terminadas (+ 2 reservadas ausentes) |
| GENEALOGÍA | **PASS** |
| COMMITS EXCLUSIVOS | **PASS** |
| DEPENDENCIAS | **PASS** |
| ALEMBIC DAG | **PASS** (con re-parent obligatorio) |
| MODELOS | **PASS** (riesgo comercial ALTO) |
| ROUTERS | **PASS** (riesgo main.py ALTO) |
| RBAC | **PASS** |
| FRONTEND | **PASS** |
| PRUEBAS | **PASS** |
| RIESGOS | **PASS** (documentados) |
| 1350 | **RESERVADO/PENDIENTE** |
| 1370 | **RESERVADO/PENDIENTE** |
| CÓDIGO MODIFICADO | **NO** |
| CONVERGENCIA EJECUTADA | **NO** |

### VEREDICTO: **LISTO PARA CONVERGER**

Condición: ejecutar convergencia por **commits funcionales sobre eb22980**, no por merge de tips de rama.
