# EMPLEADOS_IA — ANÁLISIS DEL PUENTE V1 FINAL → CONVERGENCIA POST-V1

**Tipo:** Solo lectura — crítico antes de converger  
**Fecha:** 2026-08-29  
**Verificado en:** `origin` (fetch explícito de ambos SHA)

---

## 1. Genealogía exacta

| Referencia | SHA completo |
|------------|--------------|
| **V1 candidata final** | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| **POST-V1 histórica** | `eb229806136e29acddc0f592b5f017f5c3cb2958` |
| **MERGE-BASE** | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` |

### Relación de ancestro

| Pregunta | Resultado |
|----------|-----------|
| ¿V1 contiene POST-V1? | **NO** |
| ¿POST-V1 contiene V1? | **NO** |
| ¿Merge-base es ancestro común? | **SÍ** (ancestro de ambos) |

Son **ramas hermanas** divergentes desde `4c03cbe` (post-certificación R2 / pre-bloques 1100).

### Commits exclusivos

| Lado | Cantidad | Commits funcionales relevantes |
|------|----------|-------------------------------|
| **V1** (4c03cbe..e8cb853) | **10** | `72e6b0e`, `460405f`, `36a7af6`, `eb7476d` (+ 6 docs) |
| **POST-V1** (4c03cbe..eb229806) | **17** | `a976a43`…`eb22980` (1100–1250, 1230, 1240, merges Alembic) |

---

## 2. Delta funcional V1 (presente en e8cb853, ausente en eb229806)

Análisis por **diff real** y commits funcionales (no solo mensajes).

### Seguridad — **P0**

| Cambio | Archivos | Descripción |
|--------|----------|-------------|
| Validación producción endurecida | `security_config.py`, `main.py` | JWT mín. 32 chars; `BOOTSTRAP_ADMIN_PASSWORD` obligatorio fuera de SQLite; CORS explícito en `prod` (sin `*`) |
| Bootstrap Docker | `docker-compose.yml`, `.env.example` | Contraseña bootstrap requerida en despliegue Docker |

### PostgreSQL / DATABASE_URL / Docker — **P0**

| Cambio | Archivos | Descripción |
|--------|----------|-------------|
| Módulo nuevo | `backend/app/db_url.py` | Construcción segura de URL con contraseñas especiales (`URL.create`) |
| Resolución env | `config.py` | Precedencia `DATABASE_URL` explícita sobre `POSTGRES_*` |
| Entrypoint | `docker_entrypoint.sh`, `alembic/env.py` | Integración construcción URL en arranque |
| Tests | `tests/test_docker_database_url.py` | Cobertura round-trip contraseñas especiales |

### Frontend / Knowledge — **P1**

| Cambio | Archivos | Descripción |
|--------|----------|-------------|
| Descarga autenticada | `KnowledgePage.tsx`, `api.ts` | Sustituye `window.open` sin token por `downloadKnowledgeDocument` autenticado |
| Español pre-release | ~15 páginas + `labels.ts` | Correcciones UI visibles |

### RBAC / tests — **P1**

| Cambio | Archivos | Descripción |
|--------|----------|-------------|
| Tests seguridad V1 | `tests/test_security_rbac_v1.py` | Validación RBAC pre-release |
| Knowledge tests | `tests/test_knowledge_930.py` | Ajustes descarga autenticada |

### Otros — **P2**

| Cambio | Nota |
|--------|------|
| `alembic/env.py` | Mejoras alineadas con DATABASE_URL |
| `conftest.py` en V1 | V1 **elimina** imports post-V1 y `bootstrap_permissions` — **no portar tal cual** al puente |

### Archivos nuevos solo en V1 (árbol completo)

- `backend/app/db_url.py`
- `tests/test_docker_database_url.py`

---

## 3. Riesgo de pérdida si convergimos desde eb229806 sin puente V1

| ID | Riesgo | Clasificación |
|----|--------|---------------|
| R1 | Sin `security_config` endurecido → despliegue prod con JWT corto / bootstrap por defecto / CORS `*` | **P0** |
| R2 | Sin `db_url.py` → fallos Docker/PostgreSQL con contraseñas especiales | **P0** |
| R3 | Sin precedencia `DATABASE_URL` en `config.py` | **P0** |
| R4 | Sin fixes `docker-compose` / entrypoint | **P0** |
| R5 | Descarga Knowledge sin autenticación | **P1** |
| R6 | Regresiones UI español pre-release | **P1** |
| R7 | Sin `test_docker_database_url` / `test_security_rbac_v1` | **P1** |
| R8 | Cherry-pick ingenuo de `conftest` V1 borraría setup post-V1 | **P2** (evitable en resolución) |

**Totales si usamos eb229806 directamente:** P0=**4**, P1=**3**, P2=**1**

### Áreas revisadas

| Área | eb229806 sin V1 |
|------|-----------------|
| `main.py` | Tiene routers 1100–1240/1230; **carece** validación `app_env`/`cors_origins` en lifespan |
| `database/config` | **Sin** `db_url.py`; config sin precedencia final V1 |
| `auth` | OK base; sin impacto crítico adicional |
| `permissions` | **Más completo** que V1 (incluye bloques post-V1) |
| `bootstrap` | **Más débil** en prod sin fixes V1 |
| `frontend` | **Sin** descarga Knowledge autenticada |
| `docker-compose` | Versión pre-fix V1 |
| `migraciones` | HEAD `1250f` — **correcto** para post-V1 |
| `tests/conftest` | **Mejor** que V1 (imports 1200–1240) |
| `scheduler` | Sin delta V1 relevante |
| `Knowledge` | **P1** descarga no autenticada |

---

## 4. Delta POST-V1 (presente en eb229806, ausente en e8cb853)

**65 archivos/rutas** solo en POST-V1. Funcionalidad crítica:

### Bloques 1100–1220 (convergencia 1250a)

- FinOps 1110, Señales 1120, Línea base 1200, Valoración 1210, Diagnóstico 1220
- Modelos, servicios, routers, permisos, tests, páginas frontend

### Bloques 1230 / 1240 / 1250b–f

- **1230** Centro de Control ejecutivo (`control_center.py`, `CentroControlPage.tsx`, tests 1230/1250c)
- **1240** Inteligencia externa (modelos, router, páginas, tests)
- Migraciones merge: `1250b1c2d3e4f`, `1250f1a2b3c4d`

### Infraestructura de permisos post-V1

- `LINEA_BASE_PERMISSIONS`, `VALORACION_PERMISSIONS`, `DIAGNOSTICOS_PERMISSIONS`, `INTELIGENCIA_EXTERNA_PERMISSIONS`
- `usePermissions.ts` (frontend)

### Otros

- `bootstrap_permissions` en `conftest.py` (tests post-V1)
- Modificaciones 1110/1120 FK (roundtrip SQLite)

**Pérdida si partimos solo de V1/main:** toda la convergencia post-V1 certificada — impacto **P0 masivo** (no viable).

---

## 5. Alembic

### Cabezas

| Ref | HEAD ledger | `schema_repair.HEAD_REVISION` |
|-----|-------------|-------------------------------|
| **V1** `e8cb853` | `d1e2f3a4b5c6` | `d1e2f3a4b5c6` |
| **POST-V1** `eb229806` | `1250f1a2b3c4d` | `1250f1a2b3c4d` |

### Conexión V1 → post-V1 — **DEMOSTRADA**

```
d1e2f3a4b5c6  (merge multitenant+LLM — presente en AMBOS)
      ↓
1110a1b2c3d4e  down_revision = d1e2f3a4b5c6  (solo en POST-V1)
      ↓
1120a1b2c3d4e
      ↓
1200 / 1210 / 1220  (paralelos)
      ↓
1250a1b2c3d4e  (merge triple)
      ↓
1250b1c2d3e4f  (1240 + diagnóstico)
      ↓
1250f1a2b3c4d  (merge final post-V1)
```

- El archivo `d1e2f3a4b5c6_merge_multitenant_llm_v1.py` **existe en ambos** refs.
- La cadena 1100–1250 **extiende** desde `d1e2f3a4b5c6`; no la reemplaza.
- V1 **no contiene** migraciones 1110–1250f (HEAD se queda en `d1e2f3`).
- POST-V1 **sí incluye** `d1e2f3` como ancestro efectivo del grafo.

**Conclusión Alembic:** no hay discontinuidad entre V1 y post-V1; hay **extensión lineal/merge** desde el mismo punto `d1e2f3`. El puente de código no requiere reescribir migraciones V1; solo preservar HEAD `1250f` y no regresar a `d1e2f3` como cabeza.

---

## 6. Evaluación de estrategias

| Estrategia | Descripción | Riesgo pérdida | Conflictos | Alembic | Pruebas | Veredicto |
|------------|-------------|----------------|------------|---------|---------|-----------|
| **A** | Partir de main/V1 final y reaplicar 1100–1380 | **Alto** (replay 17+ commits, 65 archivos) | Muy alto | Replay completo desde `d1e2f3` | Difícil | **Descartada** |
| **B** | Partir de `eb229806` + delta V1 (4 commits) | **Bajo** | Bajo–medio (~10 archivos) | HEAD `1250f` intacto | Focal docker/security + regresión 1250 | **Viable** |
| **C** | Base puente certificada = B + acta de certificación | **Mínimo** | Controlado una vez | `1250f` + sin cambio migraciones | Batería puente explícita | **Recomendada** |
| **D** | Usar solo main post-merge V1 sin POST-V1 | **P0 masivo** | — | Rompe cadena | — | **Descartada** |

### Estrategia recomendada: **C** (implementación = **B** con certificación)

**Procedimiento para obtener BASE DEFINITIVA** (no ejecutar ahora):

1. Crear rama puente desde `eb229806136e29acddc0f592b5f017f5c3cb2958`
2. Cherry-pick **en orden** los commits funcionales V1:
   - `36a7af6` — Docker DATABASE_URL seguro
   - `eb7476d` — Precedencia DATABASE_URL
   - `72e6b0e` — Seguridad producción / bootstrap Docker
   - `460405f` — Knowledge autenticado + español UI
3. Resolver conflictos preservando **siempre** routers/modelos/permisos post-V1 de `eb229806`
4. En `conftest.py`: mantener imports 1200–1240 y `bootstrap_permissions` de POST; no aplicar eliminaciones V1
5. Ejecutar: `test_docker_database_url`, `test_security_rbac_v1`, `test_knowledge_930`, `test_migration_control`, tests 1230/1240/1250
6. `npm run build`
7. Certificar SHA resultante como **BASE PUENTE** para convergencia 1260–1380

**No usar** `eb229806` ni `e8cb853` directamente como base final.

**Tras release V1 en main:** el merge de V1 a `main` no sustituye este puente; `main` quedará en el lado V1 sin POST-V1. La convergencia definitiva debe anclarse al **SHA puente certificado**, no al `main` post-merge aislado.

---

## 7. Respuesta a las opciones A/B/C/D del objetivo

| Opción | ¿Usar como base convergencia? |
|--------|-------------------------------|
| **A. eb229806 directo** | **NO** — pierde fixes P0 V1 |
| **B. main final post-merge V1** | **NO** — pierde 65 artefactos post-V1 |
| **C. Rama puente V1+POST-V1** | **SÍ** — única que preserva ambos |
| **D. Otra demostrada** | Equivalente a C vía cherry-pick B |

---

## 8. Impacto en plan único anterior

**Archivo:** `CURSOR_PLAN_UNICO_CONVERGENCIA_FINAL_POST_V1.md`  
**¿Requiere actualización?** **SÍ**

### Correcciones necesarias (cuando se actualice, no ahora)

| Sección | Cambio |
|---------|--------|
| §2 Base correcta | Sustituir `eb229806` por **SHA puente certificado** (procedimiento §6) |
| §0 Gate | Añadir gate **Puente V1/POST-V1 certificado** antes de convergencia |
| Insumos pendientes | **Mapa integral A** → **COMPLETADO** |
| Insumos pendientes | **Preparación release C** → **COMPLETADO** |
| G0 baseline | Incluir verificación fixes V1 (docker, security, Knowledge) |
| Pruebas G0 | Añadir `test_docker_database_url`, `test_security_rbac_v1` |

### Tareas activas (no duplicar)

- **A:** limpieza 1300→1370→1380 — fuera de alcance
- **B:** limpieza 1330 — fuera de alcance
- **C:** mapeo 1280→1310/1320→1340 — fuera de alcance
- **D:** herramientas V1/Docker — fuera de alcance

Este análisis se limita al **puente de bases**.

### Nota 1350

Rama `cursor/1350-gobierno-datos-privacidad` puede tener commits documentales posteriores al funcional limpio. En convergencia, usar **SHA funcional certificado** por B/A, no HEAD documental automático.

---

## 9. SHA verificados en origin

| Ref | SHA | Estado fetch |
|-----|-----|--------------|
| V1 | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` | OK |
| POST-V1 | `eb229806136e29acddc0f592b5f017f5c3cb2958` | OK |

---

## Veredicto

**APTO PARA DEFINIR BASE FINAL** — mediante estrategia C (puente certificado), no mediante `eb229806` ni V1 aislados.

---

## Restricciones respetadas

- Sin modificación de código, ramas, merge, rebase, migraciones, main, PR #32
- Sin `git add`
