# EMPLEADOS_IA — PLAN ÚNICO DE CONVERGENCIA FINAL POST-V1

**Tipo:** Diseño / procedimiento — **NO EJECUTAR**  
**Fecha:** 2026-08-29 (actualizado — base puente fijada)  
**Base de integración:** `f2f1c0e832d17255c0d4a42a0c6ac06b4814d002` (`cursor/base-puente-v1-post-v1`)  
**HEAD funcional puente:** `d57b831e41b8e017da612c3c442f9f29c981f674`  
**Referencia histórica (ya no es base directa):** `eb229806136e29acddc0f592b5f017f5c3cb2958`  
**Agente:** Cursor (plan de convergencia)

---

## 0. Regla de arranque (obligatoria)

La **convergencia real NO debe comenzar** hasta:

1. Recibir la **cadena limpia de identidad** de **A** (`1300→1370→1380` sobre base puente).
2. Recibir el **1330 limpio de B** (rama y SHA certificados).
3. Recibir de **C** el **mapa quirúrgico** de `1260` / `1270` / `1290`.
4. Cerrar en sesión de reconciliación un **orden definitivo** que sustituya las secciones marcadas como no definitivas.

**Insumos ya completados (no bloquean arranque por sí solos):**

- Mapa integral A
- Preparación release V1 (C)
- Análisis puente V1/post-V1
- Base puente V1/post-V1 (`cursor/base-puente-v1-post-v1`)
- Mapa cadena comercial: `1280→1310`, `1280→1320→1340`

Este plan es el **procedimiento único**; los insumos pendientes de A/B/C siguen siendo **bloqueantes** para la ejecución.

---

## 0.1. Flujo conceptual de convergencia

```
BASE PUENTE REAL (9ce1bd7 — funcional d57b831)
    ↓
piezas limpias 1260–1380
    ↓
convergencia controlada
    ↓
Alembic única cabeza
    ↓
pruebas acumulativas
    ↓
PostgreSQL (gate obligatorio)
    ↓
frontend
    ↓
matriz maestra 94 capacidades
    ↓
certificación post-V1
```

**NO ejecutar aún esta convergencia.**

---

## 1. Rama de convergencia final

| Campo | Valor propuesto |
|-------|-----------------|
| **Nombre** | `cursor/convergencia-final-post-v1-integracion` |
| **Creación** | Solo tras gate §0 |
| **Origen** | `9ce1bd7b1ab545563f1b6aefb193d2ad401e9805` |
| **Destino futuro** | Rama de integración certificada; **NO merge a `main`** en esta fase |
| **Convención** | Un commit de merge/replay por **grupo funcional** certificado; tags anotados opcionales `conv-grupo-N` |

**NO crear esta rama hasta completar gate §0.**

---

## 2. Base correcta

| Elemento | SHA / HEAD | Contenido ya integrado |
|----------|------------|------------------------|
| **Base única (puente)** | `f2f1c0e832d17255c0d4a42a0c6ac06b4814d002` | POST-V1 1100–1250 + delta funcional V1 (4 cherry-picks) + docs |
| **HEAD funcional** | `d57b831e41b8e017da612c3c442f9f29c981f674` | Último commit de código antes del documental |
| **Ancestro POST-V1** | `eb229806136e29acddc0f592b5f017f5c3cb2958` | Contenido 1100–1220, 1230, 1240, merge `1250f` |
| **Alembic HEAD base** | `1250f1a2b3c4d` | Cadena hasta convergencia final post-V1 |
| **Prohibido como base** | HEAD `1380`, `1370`, `1300` aislados | Eliminan artefactos de 1250 (1240, 1230, migraciones 1250b/f) |
| **Prohibido como base** | `6352836` (pre-1250) | Origen de ramas divergentes (identidad, 1350) |
| **Ya no usar como base directa** | `eb229806` solo | Sustituido por base puente certificada |

### Contenido verificado en base puente

| Componente | Estado |
|------------|--------|
| 1100–1220 (FinOps, Señales, Línea base, Valoración, Diagnóstico) | Preservado |
| 1230 Centro de Control | Preservado |
| 1240 Inteligencia Externa | Preservado |
| Delta V1 (DATABASE_URL, security prod, Knowledge auth, español) | Integrado |
| Certificación SQLite | 774 passed, 4 skipped |
| Certificación frontend | PASS |
| PostgreSQL | **PENDIENTE** |

---

## 3. Orden de incorporación por grupos funcionales

### Orden reconciliado (mapa integral A — referencia principal)

```
G6  1360 (continuidad)
  → G5  1350 (gobierno datos)
  →     merge Alembic (1350 ∥ 1360)
  → G3  identidad 1300→1370→1380   [NO DEFINITIVO — pendiente A]
  → G2  1270 (observabilidad)     [NO DEFINITIVO — pendiente C]
  → G4  1330 limpio (B)           [NO DEFINITIVO — pendiente B]
  → G1  cadena comercial (1280→1310 / 1280→1320→1340)
  → G2  1260                        [NO DEFINITIVO — pendiente C]
  → G2  1290                        [NO DEFINITIVO — pendiente C]
  → G9  merge final Alembic + pruebas
  →     integración Centro de Control
```

**No dar por definitivo** el orden relativo de `1260` / `1270` / `1290` hasta el mapa quirúrgico de **C**.  
**No dar por definitiva** la identidad hasta la cadena limpia de **A**.  
**No dar por definitivo** `1330` hasta la versión limpia de **B**.

### Tabla de grupos

| Fase | Grupo | Bloques / ramas | Método preferido | Notas |
|------|-------|-----------------|------------------|-------|
| **G0** | *(ya en base puente)* | 1100–1250 + V1 | — | `7cf3906` certificada (SQLite APTA; PG PENDIENTE) |
| **G6** | Continuidad / resiliencia | `1360` | Merge controlado o cherry-pick | Extiende desde base puente |
| **G5** | Gobierno de datos | `1350` limpio | Cherry-pick funcional | Convergencia Alembic con 1360 |
| **G3** | Identidad empresarial | `1300` → `1370` → `1380` | **Cherry-pick secuencial** | **[PENDIENTE A]** cadena limpia |
| **G2** | Observabilidad | `1270`, `1290`, `1260` | Cherry-pick o merge controlado | **[PENDIENTE C]** mapa quirúrgico |
| **G4** | Conectores | `1330` limpio (**B**) | Cherry-pick / replay | **[PENDIENTE B]** |
| **G1** | Valor / ROI / comercial | `1280`, `1310`, `1320`, `1340` | Cherry-pick funcional | Mapa comercial completado; orden vs G2 sujeto a C |
| **G9** | Consolidación final | Todos los grupos | Merge revision Alembic única + pruebas acumulativas | Tras G1–G8 |

**Principio:** incorporar sobre **base puente** (`7cf3906`), no sobre `eb229806` ni HEADs divergentes sin limpieza.

---

## 4. Cuándo usar cherry-pick funcional

Usar **cherry-pick** (o replay manual equivalente) cuando:

| Condición | Ejemplo en este proyecto |
|-----------|--------------------------|
| La rama diverge de la base puente | `1300`, `1370`, `1380`, `1330` actual, `1350`, `1310`, `1280` |
| Un merge directo **eliminaría** archivos de la base | HEAD `1380` vs base puente (omisiones confirmadas) |
| El commit funcional es **único y acotado** | Commits de cadena identidad limpia (A) |
| Se necesita preservar historial limpio de convergencia | Un commit por grupo certificado en rama final |

**Procedimiento cherry-pick:**

1. `git cherry-pick -n <SHA>` (sin commit automático) o aplicar parche.
2. Resolver conflictos en archivos de integración (ver §9).
3. Verificar que **no se borran** routers/modelos de grupos ya integrados.
4. Ejecutar pruebas del grupo (§10).
5. Commit único: `conv(grupo-N): <descripción>`.

---

## 5. Cuándo usar merge controlado

Usar **merge controlado** (`git merge --no-ff`) cuando:

| Condición | Ejemplo |
|-----------|---------|
| La rama **tiene la base puente como ancestro directo** | `1360-continuidad-resiliencia` (verificar tras rebase sobre puente) |
| No hay eliminación masiva de artefactos de base | Verificar con `git diff --name-status base..rama` |
| El bloque es **autocontenido** con pocos archivos puente | Tras revisión del mapa A |
| Se acepta historial de la rama fuente | Solo si B/C certifican rama limpia |

**Merge controlado requiere:** revisión previa de diff, resolución explícita en los 7 archivos puente habituales (`main.py`, `permissions.py`, `App.tsx`, `AppShell.tsx`, `api.ts`, `auth/permissions.ts`, `migration_ledger.json`).

---

## 6. Cuándo NO usar merge directo

| Caso | Motivo | Acción |
|------|--------|--------|
| **HEAD `1380`** sobre base puente | Pierde 1240, 1230, `1250b`, `1250f` | Cherry-pick cadena limpia A |
| **HEAD `1300` o `1370`** sobre base | Divergencia en raíz (`6352836`) | Igual que arriba (subconjunto) |
| **`1330` actual** (`5271ae5`) | Diverge en `4c03cbe`; requiere limpieza | Esperar **1330 limpio de B** |
| Cualquier rama sin certificación “limpio preparado” | Riesgo de regresión | Bloquear hasta entrega A/B/C |
| Merge a **`main`** | Fuera de alcance; V1 y PR #32 intocables | Prohibido en esta convergencia |
| Merge de **múltiples grupos** en un solo paso | Imposibilita rollback granular | Un grupo por iteración |

---

## 7. Tratamiento de migraciones Alembic

### Estado en base puente

```
Base puente 7cf3906:
  … → 1250a → 1250b → 1250f  (HEAD: 1250f1a2b3c4d)
  + delta V1 (sin migraciones nuevas)
```

### Anclas y convergencias pendientes

| Paralelo | Requiere |
|----------|----------|
| `1350` ∥ `1360` | Convergencia de ramas Alembic antes de G9 |
| `1310` ∥ `1320` | Convergencia de ramas Alembic |
| Identidad | `1300 → 1370 → 1380`; re-anclar `1300a` a `1250f` |
| Observabilidad | `1260 → 1290` (orden sujeto a C) |
| `1330` | Debe provenir de versión limpia (**B**) |

### Estrategia (diseño)

| Paso | Acción |
|------|--------|
| 1 | Mantener `1250f1a2b3c4d` como ancla hasta primer grupo que aporte migración |
| 2 | Por cada grupo con migración nueva: `down_revision` → **HEAD vigente** de rama convergencia |
| 3 | Identidad: al portar `1300a`, `down_revision` de `1250a` → **`1250f1a2b3c4d`** |
| 4 | Encadenar `1370a` → `1300a'`, `1380a` → `1370a'` |
| 5 | Grupos paralelos: no integrar hasta mapa de heads |
| 6 | Actualizar `migration_ledger.json` y `schema_repair.HEAD_REVISION` por grupo |
| 7 | Ejecutar `assert_single_head` tras cada grupo |

**NO crear merge revision hasta inventario completo de heads.**

---

## 8. Creación de merge revision única (si aplica)

| Momento | Tipo | Descripción |
|---------|------|-------------|
| **Tras G1–G8** | Merge revision **única final** | Unifica todos los heads residuales |
| **1350 ∥ 1360** | Merge intermedio posible | Solo tras certificación de ambos grupos |
| **Identificador propuesto** | `1390a1b2c3d4` o convención acordada | **[PENDIENTE A]** numeración oficial |
| **Contenido** | `upgrade()` / `downgrade()` vacíos si solo unifica heads | Patrón `1250a`, `1250f` |

**Regla:** una sola cabeza Alembic al cierre. No crear merge revision en esta fase de diseño.

---

## 9. Resolución de conflictos por archivo

### Archivos puente (alta frecuencia)

| Archivo | Regla de resolución |
|---------|---------------------|
| `backend/app/main.py` | **Unión** de imports y routers; nunca eliminar `inteligencia_externa`, `control_center` |
| `backend/app/permissions.py` | **Unión** de permisos; preservar identidad, conectores, gobierno, continuidad |
| `backend/app/routers/auth.py` | Priorizar MFA 1300 + SSO 1370; no romper login local |
| `backend/app/deps.py` | Mantener `get_current_user` + contexto seguridad 1300 |
| `backend/alembic/migration_ledger.json` | HEAD = revisión vigente |
| `backend/scripts/schema_repair.py` | `HEAD_REVISION` = cabeza única post-grupo |
| `frontend/src/App.tsx` | **Unión** de rutas |
| `frontend/src/AppShell.tsx` | **Unión** sidebar; español |
| `frontend/src/api.ts` | **Unión** funciones API |
| `frontend/src/auth/permissions.ts` | Espejo frontend de permisos backend |
| `tests/conftest.py` | **Unión** imports de modelos |

### Identidad — conflictos conocidos

Al portar G3 sobre base puente, restaurar explícitamente:

- `external_models`, `inteligencia_externa`, `control_center`
- Migraciones `1240c3d4e5f6a`, `1250b1c2d3e4f`, `1250f1a2b3c4d`
- Tests 1230, 1240, 1250c, convergencia 1250
- Delta V1 (`db_url.py`, `security_config.py`, Knowledge auth)

---

## 10. Pruebas después de cada grupo

| Grupo | Pruebas mínimas obligatorias |
|-------|------------------------------|
| **G0** (base puente) | Suite SQLite 774+; frontend PASS; tests 1230/1240/1250/V1 |
| **G6** Continuidad | Tests 1360 + regresión G0 |
| **G5** Gobierno datos | Tests 1350 + regresión |
| **G3** Identidad | `test_bloque_1300_*`, `test_identidad_1370.py`, `test_scim_1380.py` |
| **G2** Observabilidad | Tests 1270/1290/1260 + regresión |
| **G4** Conectores | Tests 1330 (rama limpia B) |
| **G1** Comercial | Tests 1280/1310/1320/1340 |
| **Cada grupo** | `assert_single_head`; `npm run build` |

**Criterio de paso:** 0 fallos en pruebas del grupo + 0 regresiones en grupos anteriores.

---

## 11. Pruebas acumulativas finales

Ejecutar **una sola batería** tras merge revision final (G9):

```
pytest tests/test_migration_control.py
pytest tests/test_bloque_1230_centro_control.py
pytest tests/test_inteligencia_externa_1240.py
pytest tests/test_convergencia_final_1250.py
pytest tests/test_docker_database_url.py
pytest tests/test_security_rbac_v1.py
pytest tests/test_bloque_1300_seguridad_avanzada.py
pytest tests/test_identidad_1370.py
pytest tests/test_scim_1380.py
# + tests de cada grupo G1–G8 incorporado

cd frontend && npm run build

# PostgreSQL (gate obligatorio — ver §12)
DATABASE_URL=postgresql://... pytest <batería completa>

# SQLite
pytest <batería completa>
```

---

## 12. PostgreSQL

| Aspecto | Procedimiento |
|---------|---------------|
| **Gate base puente** | Antes de certificar convergencia integral: base puente + convergencia debe pasar PG real |
| Cuándo | Tras cada grupo G3+ y en batería final G9 |
| Setup | BD `*_test` dedicada; `alembic upgrade head` |
| Verificación | `alembic_version` = HEAD único; `test_migration_control.py` |
| Estado actual base puente | **PENDIENTE** — no declarar certificado |
| Riesgo | Merge revisions con múltiples parents — validar roundtrip en PG |

> No repetir PostgreSQL en Cloud sin entorno PG/Docker disponible.

---

## 13. SQLite

| Aspecto | Procedimiento |
|---------|---------------|
| Base puente | **774 passed, 4 skipped** (certificado) |
| Cuándo | Cada grupo (desarrollo) + CI |
| Riesgo conocido | Batch FK en migraciones (lección 1250/1110) |

---

## 14. Frontend

| Paso | Acción |
|------|--------|
| Base puente | `npm run build` — **PASS** |
| Tras cada grupo | `npm run build` obligatorio |
| Centro de Control | Preservar `CentroControlPage` de G0 |
| Idioma | Todo visible en español |

---

## 15. RBAC

| Paso | Acción |
|------|--------|
| Por grupo | Añadir permisos sin eliminar existentes |
| Identidad | `security.*`, `identidad.*` (1300/1370/1380) |
| Verificación | Tests `require_permission` por router nuevo |

---

## 16. Multiempresa

| Verificación | Cuándo |
|--------------|--------|
| `organization_id` en queries nuevas | Tras G3, G4, G5 |
| Aislamiento SCIM cross-tenant | `test_scim_1380.py` |
| Aislamiento conectores | Tests 1330 (B) |

---

## 17. SUPERADMIN

| Verificación estática | Estado conocido (cadena identidad) |
|-----------------------|-------------------------------------|
| `PROTECTED_ASSIGNMENT_ROLE_CODES` | OK |
| `FORBIDDEN_AUTO_ROLES` (SSO) | OK |
| `PROTECTED_SCIM_ROLES` | OK |
| Break-glass solo superadmin | OK |

Tras G3: ejecutar tests de protección SUPERADMIN.

---

## 18. Conectores

| Estado | Acción |
|--------|--------|
| `1330` actual | **NO integrar** — diverge (`merge-base = 4c03cbe`) |
| **1330 limpio (B)** | Integrar en G4 tras SHA certificado |
| **[EN CURSO B]** | Rama limpia pendiente |

---

## 19. Gobierno de datos

| Estado | Acción |
|--------|--------|
| `1350` limpio preparado | G5 — cherry-pick sobre base puente |
| Convergencia Alembic | Con `1360` antes de G9 |
| Divergencia histórica | `merge-base = 6352836` |

---

## 20. Continuidad

| Estado | Acción |
|--------|--------|
| `1360` preparado | G6 — primer grupo en orden reconciliado |
| Candidato | Merge controlado si ancestro = base puente |

---

## 21. Identidad empresarial

| Bloque | SHA referencia (rama actual) | Método |
|--------|------------------------------|--------|
| 1300 | `09194d8f281a1506d694844dead43e5ee93849e6` | Cherry-pick #1 |
| 1370 | `3c545f64fe06569ecadbfa8523d65af798d472e3` | Cherry-pick #2 |
| 1380 | `a1c3319e87a4bd17279ab3b4756cca006208e932` | Cherry-pick #3 |

**Secuencia obligatoria:** 1300 → 1370 → 1380.  
**Alembic:** re-anclar `1300a` a `1250f`.  
**NO** merge directo de ningún HEAD de esta cadena.  
**[EN CURSO A]** — usar SHAs de cadena limpia cuando A entregue.

---

## 22. SCIM

| Aspecto | Procedimiento |
|---------|---------------|
| Integración | Parte de G3 |
| P2 conocido | Rate limit en memoria — no corregir en convergencia |
| Pruebas | `test_scim_1380.py` (22 tests) |

---

## 23. Valor / ROI / comercial

| Bloque | Rama | Estado |
|--------|------|--------|
| 1210 | En base vía 1250a | Integrado |
| 1280 | `cursor/1280-modelo-comercial-valor-85e4` | G1 — mapa completado |
| 1310 | `cursor/1310-segmentacion-planes-verticales` | G1 — mapa completado |
| 1320 | `cursor/1320-...` | G1 — mapa `1280→1320→1340` completado |
| 1340 | — | G1 — mapa completado |

---

## 24. Centro de Control

| Estado | Procedimiento |
|--------|---------------|
| **En base puente** | `control_center.py`, `CentroControlPage`, tests 1230/1250c |
| **Regla crítica** | Ningún cherry-pick puede eliminar estos artefactos |
| Post-convergencia | Integración final con observabilidad 1270 y matriz capacidades |

---

## 25. Observabilidad

| Bloque | Rama | Grupo |
|--------|------|-------|
| 1270 | `cursor/1270-multiproveedor-observabilidad-9a85` | G2 |
| 1260 | — | G2 — **[EN CURSO C]** |
| 1290 | — | G2 — **[EN CURSO C]** |
| Métricas SCIM | En G3 | G3 |

---

## 26. Actualización matriz maestra de 94 capacidades

| Estado | Responsable | Acción |
|--------|-------------|--------|
| Inventario por bloque | **A** | **COMPLETADO** (mapa integral) |
| Núcleo de valor | **C** | **COMPLETADO** (preparación release V1) |
| Tras convergencia G9 | Equipo convergencia | Marcar capacidades: `INTEGRADO` / `PARCIAL` / `P2` / `FUTURO` |
| Entregable | `INTERCAMBIO/SALIDA/` | Documento matriz — **no crear hasta cierre G9** |

---

## Insumos disponibles (confirmados)

| Insumo | SHA / referencia | Estado |
|--------|------------------|--------|
| **Base puente** | `f2f1c0e832d17255c0d4a42a0c6ac06b4814d002` | **COMPLETADO** |
| HEAD funcional puente | `d57b831e41b8e017da612c3c442f9f29c981f674` | **COMPLETADO** |
| Ancestro POST-V1 | `eb229806136e29acddc0f592b5f017f5c3cb2958` | Referencia histórica |
| Alembic HEAD base | `1250f1a2b3c4d` | Verificado |
| Mapa integral A | — | **COMPLETADO** |
| Análisis puente V1/post-V1 | `CURSOR_ANALISIS_PUENTE_V1_FINAL_POST_V1.md` | **COMPLETADO** |
| Certificación base puente | `CURSOR_BASE_PUENTE_V1_POST_V1_CERTIFICADA.md` | **COMPLETADO** |
| Mapa cadena comercial | `1280→1310`, `1280→1320→1340` | **COMPLETADO** |
| Preparación release V1 (C) | — | **COMPLETADO** |
| 1300 MFA/seguridad | `09194d8f281a1506d694844dead43e5ee93849e6` | Referencia (pendiente limpieza A) |
| 1370 SSO/identidad | `3c545f64fe06569ecadbfa8523d65af798d472e3` | Referencia (pendiente limpieza A) |
| 1380 SCIM | `a1c3319e87a4bd17279ab3b4756cca006208e932` | Referencia (pendiente limpieza A) |
| 1350 gobierno datos | `3216b7d826e4de7626a0cd59b9401b5722e11fee` | Preparado |
| 1360 continuidad | `4e3e8b2978d4c290fb4c28fcac218104e438a9e5` | Preparado |

---

## Insumos pendientes (en curso)

| Insumo | Responsable | Bloquea |
|--------|-------------|---------|
| **Cadena limpia identidad** `1300→1370→1380` | **A** | Orden definitivo G3 |
| **1330 limpio** (rama + SHA + tests) | **B** | Grupo G4 |
| **Mapa quirúrgico** `1260` / `1270` / `1290` | **C** | Orden definitivo G2 |
| Numeración merge revision final | **A** | §8 |
| Matriz 94 capacidades actualizada post-G9 | Equipo convergencia | §26 cierre |

---

## Checklist de ejecución (cuando se autorice)

- [ ] Gate §0 cerrado (A cadena limpia + B 1330 + C mapa 1260/1270/1290)
- [ ] Crear rama `cursor/convergencia-final-post-v1-integracion` desde `f2f1c0e`
- [ ] G6 → G5 → merge Alembic 1350∥1360 → G3 → G2 → G4 → G1 → G9 (orden sujeto a reconciliación final)
- [ ] Merge revision Alembic única (G9)
- [ ] Batería acumulativa §11 (SQLite + **PostgreSQL obligatorio** + frontend)
- [ ] Verificación SUPERADMIN §17
- [ ] Actualización matriz 94 capacidades §26
- [ ] Informe de cierre en `INTERCAMBIO/SALIDA/`
- [ ] **NO merge a main** sin acta de certificación explícita

---

## Restricciones respetadas en este documento

- NO se creó rama de convergencia
- NO se modificó código de aplicación
- NO merge / rebase / cherry-pick de 1260–1380 ejecutado
- NO se tocó `main`, V1, PR #32
- NO migraciones nuevas / merge revision creada
- P2 rate limit SCIM: registrado, no corregido
- PostgreSQL base puente: **PENDIENTE**, no certificado

---

## Veredicto del plan

**PLAN ACTUALIZADO** — base puente `f2f1c0e` (funcional `d57b831`) fijada como raíz de integración 1260–1380.

La convergencia es viable sobre la **base puente certificada** (funcional APTA; PostgreSQL PENDIENTE) mediante cherry-pick secuencial de grupos divergentes, merge controlado selectivo (1360) y merge revision Alembic final. El riesgo principal confirmado sigue siendo la **pérdida de 1250/1240/1230/V1** si se usa merge directo de HEAD identidad; mitigado por estrategia C y base puente ya construida.

**Convergencia 1260–1380 ejecutada:** **NO**
