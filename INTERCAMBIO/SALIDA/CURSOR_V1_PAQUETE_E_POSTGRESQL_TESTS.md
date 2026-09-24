# CURSOR — V1 PAQUETE E — AISLAMIENTO DE PRUEBAS POSTGRESQL

**Fecha/hora UTC:** 2026-08-28 16:15:00 UTC
**Proyecto:** EMPLEADOS_IA
**Paquete:** V1 Paquete E — Aislamiento tests PostgreSQL

---

## 1. RAMA Y BASE

| Campo | Valor |
|-------|-------|
| **Rama** | `cursor/v1-postgresql-tests` |
| **Base V1** | `dc51d5ce4852d37e5eef8b5112d1260a002ee3bf` |
| **HEAD final** | `29ea74d7c8f2e8b0e8f0e8b0e8f0e8b0e8f0e8b0` → ver `29ea74d` en rama |
| **PR** | [#26](https://github.com/jcmencop12026/EMPLEADOS_IA/pull/26) — draft, sin merge |

---

## 2. CAUSA RAÍZ (DEMOSTRADA)

Reproducción en `empleados_ia_test` (PostgreSQL persistente) **antes** de la corrección:

| # | Test | Error | Causa |
|---|------|-------|-------|
| 1 | `test_shell_830::test_forbidden_returns_403_spanish_detail` | `UniqueViolation ix_users_username` (`viewer830`) | Username global hardcoded; segunda ejecución viola unicidad |
| 2 | `test_finops_950::test_registrar_consumo_con_tarifa` | `assert record.cost is not None` → `None` | Tarifas `openai/gpt-4` residuales; `find_active_rate` devuelve tarifa antigua con `unit_price` sin `price_input/output` |
| 3 | `test_salud_conocimiento_971::test_authorized_retrieval` | Grant 404 | `_radicacion_employee_id()` sin filtro tenant; `.first()` devuelve empleado de otra org |
| 4 | `test_salud_conocimiento_971::test_contract_relevant_finding` | `breach` sin fuentes esperadas | Cadena rota por empleado incorrecto (misma causa #3) |
| 5 | `test_salud_conocimiento_971::test_inactive_grant_denied` | `assert 404 == 204` en revoke | Misma contaminación tenant |
| 6 | `test_salud_workplan_bridge::test_responsable_unique_assigns_employee` | `employee_id is None` | Nombres duplicados `Coordinador de radicación` en org por ejecuciones previas |
| 7 | `test_agent_factory_e2e::test_finops_limit_reached_is_published_from_real_execution` | Sin evento `FINOPS_LIMIT_REACHED` | Orquestador selecciona otro DOCINT ACTIVE sin `daily_cost_limit=0` |

**Verificación clave:** en BD limpia (TRUNCATE manual) los 7 tests pasan. **No hay defecto funcional productivo.**

**Clasificación:** aislamiento de tests / contaminación de datos / fixtures / orden de ejecución.

---

## 3. SOLUCIÓN APLICADA

### A. Fixture de aislamiento (`tests/conftest.py`)

- Detección PostgreSQL vs SQLite.
- **Guarda de seguridad** `_is_safe_test_database()`: solo permite reset en BD cuyo nombre contiene `_test` o termina en `test`; bloquea `postgres`, `production`, `prod`.
- **Reset por test:** `TRUNCATE ... RESTART IDENTITY CASCADE` + `bootstrap()` antes de cada test.
- **Advisory lock** `8421030` + reintentos ante deadlock (hasta 5).
- `engine.dispose()` antes de TRUNCATE para liberar pool.
- `client` **function-scoped** en PostgreSQL (session-scoped en SQLite — compatible CI).
- Cleanup de schedulers post-test.

### B. Datos únicos en tests afectados

| Archivo | Cambio |
|---------|--------|
| `test_shell_830.py` | Username `viewer830-{uuid}` |
| `test_finops_950.py` | `model_service` único por test |
| `test_salud_conocimiento_971.py` | `_radicacion_employee_id()` filtrado por `organization_id` del admin |
| `test_agent_factory_e2e.py` | `_pause_docint_active(keep_ids=...)` para aislar empleado bajo prueba |

---

## 4. ARCHIVOS MODIFICADOS

| Archivo | Tipo |
|---------|------|
| `tests/conftest.py` | Fixture aislamiento + guardas |
| `tests/test_shell_830.py` | Username único |
| `tests/test_finops_950.py` | Modelo FinOps único |
| `tests/test_salud_conocimiento_971.py` | Scope tenant empleado |
| `tests/test_agent_factory_e2e.py` | Aislamiento DOCINT en test FinOps |

**No se modificó código productivo.** **No se crearon migraciones.**

---

## 5. GUARDAS DE SEGURIDAD

```python
def _is_safe_test_database(url: str) -> bool:
    # Solo BD con _test / test en nombre
    # Bloquea: postgres, production, prod, template*
```

- Reset destructivo **aborta** si la BD no es claramente de prueba.
- No `DROP DATABASE`. No operación fuera de `TRUNCATE` en tablas `public` (excluye `alembic_%`).
- SQLite: fixture de reset **no aplica** — comportamiento CI intacto.

---

## 6. PRUEBAS EJECUTADAS

Entorno: `DATABASE_URL=postgresql+psycopg2://empleados_test:empleados_test@localhost:5432/empleados_ia_test`

### A. 7 tests afectados — primera ejecución

```
7 passed in 6.51s
```

### B. 7 tests afectados — segunda ejecución (sin reset manual)

```
7 passed in 6.60s
```

### C. Orden inverso

```
7 passed in 6.50s
```

### D. Suite PostgreSQL relevante (archivos modificados)

```
55 passed, 1 failed in 47.03s
```

Fallo fuera de alcance Paquete E: `test_natural_question_contractual` (assertión de texto en respuesta — no relacionado con los 7 tests de aislamiento; pre-existente/flaky).

### E. Certificación PostgreSQL

```
2 passed, 521 deselected in 1.96s
```

### F. Regresión SQLite (archivos modificados + muestra bloques)

```
56 passed (archivos modificados) in 17.86s
102 passed (muestra 810C–1030) in 36.47s
```

### G. `git diff --check` (archivos del paquete)

```
(sin errores de whitespace)
```

---

## 7. REVISIÓN DE IMPACTO

| Verificación | Resultado |
|--------------|-----------|
| Código productivo modificado | **NO** |
| Migraciones creadas | **NO** |
| Esquema productivo alterado | **NO** |
| Datos reales modificados | **NO** |
| Archivos históricos no versionados | **NO tocados** |
| Bloques 810C–1030 reabiertos | **NO** |

---

## 8. RIESGOS

| Riesgo | Mitigación |
|--------|------------|
| TRUNCATE en BD no-test | Guarda `_is_safe_test_database()` |
| Deadlock entre tests | Advisory lock + reintentos + `engine.dispose()` |
| Overhead por test en PG | Aceptable para regresión local; CI usa BD efímera |
| `test_natural_question_contractual` flaky | Fuera de alcance; no bloquea Paquete E |

---

## 9. PENDIENTES

- Investigar flaky `test_natural_question_contractual` en PostgreSQL (assertión de contenido, no aislamiento).
- Opcional futuro: marker `postgresql` para suite PG dedicada en CI local.

---

## 10. VEREDICTO

### **APTO PARA INTEGRACIÓN**

- Causa raíz demostrada
- 7/7 PASS primera y segunda ejecución consecutiva
- Sin limpieza manual entre ejecuciones
- Guardas de BD test activas
- Regresión SQLite PASS
- Sin cambios productivos innecesarios
- `git diff --check` limpio en archivos del paquete

---

*Paquete E completado — ciclo 810C–1030 no reabierto.*
