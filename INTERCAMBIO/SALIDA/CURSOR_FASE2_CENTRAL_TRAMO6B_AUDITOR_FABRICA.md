# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 6B (AUDITOR + FÁBRICA + CICLO DE MEJORA)

**Tipo:** Integración selectiva Auditor, Fábrica MB-06 y ciclo de mejora
**Fecha:** 2026-08-30
**Agente:** GENERAL
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central certificada (Tramo 6A)** | `ab8f790a7b061703d193a4ff19fc584c7b4f26ba` |
| **HEAD Tramo 6B** | `6604aac60896f7ae8ecb06e57e2969acee8408b3` |
| **Método** | Cherry-pick selectivo + merge manual de conflictos |
| **main / V1** | NO modificados |

### Commits integrados

| Orden | SHA central | Origen | Contenido |
|-------|-------------|--------|-----------|
| 1 | `a16f571` | `9fbe416` | Auditor MVP determinístico |
| 2 | `168c3f3` | `599d69b` | Auditor → Mi Trabajo (delta) |
| 3 | `53f4b12` | `6430da8` | Fábrica MB-06 ciclo de vida |
| 4 | `dba6296` | `dccc40f` | UI aprobaciones ficha empleado |
| 5 | `882eddf` | `8759bb9` | Certificación MB-06 e2e |
| 6 | `6604aac` | `817f501` + bridge | Ciclo mejora + trazabilidad |

**No portados:** Centro de Control ejecutivo, MB-07, MB-11, merge main, bandeja histórica `8aefc87`/`40e76bc`.

---

## 1. Alembic — cadena final

| Campo | Valor |
|-------|-------|
| **Head entrada** | `1391a1b2c3d4e` (Mesa de Ayuda) |
| **Head salida** | `14b1c2d3e4f5` |
| **Cabezas** | **1** |

### Cadena lineal certificada

```text
1391a1b2c3d4e  (Mesa de Ayuda — preservada)
    ├── 1400a1b2c3d4e  (Auditor MVP)
    └── 6b06a1b2c3d4e  (Fábrica MB-06)   [paralelo desde 1391]
            ↓
    14b0c1d2e3f4  (merge vacío)
            ↓
    14b1c2d3e4f5  (employee_improvement_traces)
```

| Migración | down_revision | Reparent |
|-----------|---------------|----------|
| `1400a1b2c3d4e` | `1391a1b2c3d4e` | SÍ (era `1330b`) |
| `6b06a1b2c3d4e` | `1391a1b2c3d4e` | SÍ (era `1330b`) |
| `14b0c1d2e3f4` | (`6b06`, `1400`) | merge |
| `14b1c2d3e4f5` | `14b0c1d2e3f4` | sin cambio |

### Roundtrip SQLite

| Paso | Resultado |
|------|-----------|
| upgrade head | PASS |
| downgrade -1 | PASS |
| re-upgrade | PASS |

**PostgreSQL:** PENDIENTE POR ENTORNO

---

## 2. Componentes integrados

### Auditor MVP

- Métricas, umbrales, salud, hallazgos, recomendaciones determinísticas
- RBAC: `auditor_empleados.view`, `.execute`, `.configure`
- Ruta: `/empleados/auditoria`
- **Regla:** Auditor RECOMIENDA, NO modifica empleado automáticamente
- Tests: `test_employee_auditor_mvp.py` — 12 PASS

### Auditor → Mi Trabajo

- Delta en `trabajo_service.py` (sin reemplazar bandeja)
- Tipos: `auditor_empleado_critico`, `auditor_empleado_intervencion`, `auditor_empleado_revision`
- Deduplicación 820 con `finding_id`, `correlation_id`, `notification_id`
- Filtro `employee_id` + preservación `case_id` soporte
- Tests: `test_auditor_integracion_mi_trabajo.py` — PASS

### Fábrica MB-06

- Ciclo de vida: inventario, salud, validación, versiones, pruebas, aprobación, rollback, capacitación, retiro, publicación con guardas
- `EmployeeDetailPage`: 12 pestañas incl. Aprobación
- Permisos: `employee.approve`, `.pause`, `.retire`, `.rollback`, `.train`
- Tests: `test_employee_lifecycle_factory_mb06.py`, `test_agent_factory_e2e.py` — PASS

### Ciclo de mejora

- `auditor_factory_bridge.py` — navegación, iniciar mejora, ejecutar con RBAC, reauditoría
- `employee_improvement_traces` (migración 14b1)
- Acción `revisar_fabrica` en Mi Trabajo → `/empleados/{id}?tab=...&finding_id=...`
- `auto_execution_blocked: true` en contrato `/api/empleados-auditor/contrato-fabrica`
- Tests: `test_auditor_factory_cycle.py` — 9 PASS

---

## 3. Preservación central (Tramos 1–6A)

| Componente | Estado |
|------------|--------|
| Mesa de Ayuda MB-12 | PRESERVADA |
| Soporte → Mi Trabajo | PRESERVADO |
| 1290 PENDIENTE_EJECUCION_HUMANA | PRESERVADO |
| Deduplicación 820 soporte | PRESERVADA |
| Mi Trabajo única bandeja | SÍ |
| Centro de Control existente | NO modificado (sin cableado ejecutivo nuevo) |
| Comercial/TCO/ROI/FinOps/etc. | PRESERVADOS |

---

## 4. Seguridad

| Control | Resultado |
|---------|-----------|
| Multiempresa | PASS |
| RBAC (ver ≠ ejecutar fábrica) | PASS |
| SUPERADMIN patrón central | PASS |
| Secretos no expuestos | PASS |
| Autoejecución bloqueada | PASS (`auto_execution_blocked: true`) |
| Idempotencia ciclo mejora | PASS |

---

## 5. Pruebas

| Métrica | Antes (6A) | Después (6B) |
|---------|------------|--------------|
| Passed | 1102 | **1149** |
| Skipped | 4 | 4 |
| Failed | 0 | **0** |
| Nuevos tests | — | +47 |
| Fallos nuevos | — | **0** |

Focal certificado: 111 tests (Auditor + Fábrica + ciclo + preservación 6A)

---

## 6. Frontend

| Verificación | Resultado |
|--------------|-----------|
| `npm run build` | **PASS** |
| `/trabajo` | OK |
| `/empleados/auditoria` | OK |
| `/empleados/{id}` ficha fábrica | OK (12 pestañas) |
| Textos en español | OK |

---

## 7. Recorrido visual preparado

1. Login → Mi Trabajo → filtrar Auditor → abrir hallazgo → "Revisar en Fábrica"
2. Ficha empleado con banner contexto Auditor → iniciar mejora → acción autorizada (capacitar/probar)
3. Reauditoría opcional → clasificación resultado
4. Mesa de Ayuda y 1290 siguen visibles en bandeja

---

## 8. P0/P1/P2

**0 / 0 / 0**

---

## SALIDA FINAL

```
EMPLEADOS IA — FASE 2 CENTRAL TRAMO 6B TERMINADO

BASE:
ab8f790a7b061703d193a4ff19fc584c7b4f26ba

HEAD:
6604aac60896f7ae8ecb06e57e2969acee8408b3

AUDITOR:
PASS

AUDITOR → MI TRABAJO:
PASS

FÁBRICA:
PASS

CICLO DE MEJORA:
PASS

DECISIÓN HUMANA:
PASS

AUTOEJECUCIÓN BLOQUEADA:
PASS

TRAZABILIDAD:
PASS

IDEMPOTENCIA:
PASS

MESA DE AYUDA PRESERVADA:
PASS

SOPORTE → MI TRABAJO:
PASS

1290 PRESERVADO:
PASS

820:
PASS

MI TRABAJO ÚNICO:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

SECRETOS:
PASS

ALEMBIC HEADS:
1

ALEMBIC HEAD:
14b1c2d3e4f5

UPGRADE:
PASS

DOWNGRADE:
PASS

RE-UPGRADE:
PASS

REGRESIÓN ANTES:
1102

REGRESIÓN DESPUÉS:
1149

FALLOS NUEVOS:
0

ERRORES NUEVOS:
0

FRONTEND:
PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

PLATAFORMA EJECUTABLE:
SI

RECORRIDO VISUAL:
PREPARADO

P0/P1/P2:
0/0/0

MAIN:
NO

V1:
NO

MERGE MAIN:
NO

VEREDICTO:
TRAMO 6B APTO
```
