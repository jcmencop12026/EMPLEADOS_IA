# CURSOR — Fix heredado migraciones 1110/1120 post-V1 (rama aislada)

## Identificación

| Campo | Valor |
|-------|-------|
| Rama | `cursor/post-v1-fix-migraciones-heredadas-1110-1120` |
| Base oficial | `cursor/1250-convergencia-final-post-v1` @ `eb229806136e29acddc0f592b5f017f5c3cb2958` |
| HEAD rama | `0ec856f70f38761705f141f9054c2e480b2f7e76` |
| Alembic head | `1250f1a2b3c4d` (único) |

## Hallazgo principal

**Los fixes de roundtrip SQLite para 1110 y 1120 ya están absorbidos en la base oficial post-V1 `eb229806`.**

No se requieren modificaciones adicionales a archivos de migración en esta rama. El objetivo de aislar el fix heredado independiente de 1350 se cumple documentando que la convergencia final post-V1 ya lo incorporó (vía línea 1250B / merge `1250f1a2b3c4d`).

## Auditoría previa (FASE 2)

### Comparación 1120

| Referencia | Estado |
|------------|--------|
| `eb229806` (base oficial) | FK nombrada `fk_proactive_signals_source_id` en `batch_alter_table` ✓ |
| `cursor/1250b-fix-migration-roundtrip-85e4` @ `32304e6` | Idéntico patrón (`ef1717b`) ✓ |
| `cursor/1350a-recert-migrations` @ `ceedde5` | Sin diferencias con `eb229806` en 1120 ✓ |
| `cursor/1250a-fix-aislamiento-tests` @ `6352836` | **SIN fix** — roundtrip FAIL |

**1120 ya corregido en base oficial:** **SÍ** (completo)

### Comparación 1110

| Referencia | Estado |
|------------|--------|
| `eb229806` | `batch_alter_table` + `create_foreign_key("fk_finops_records_opportunity_id")` ✓ |
| `ceedde5` | Igual funcionalmente; usa constante `FK_FINOPS_RECORDS_OPPORTUNITY` (cosmético) |
| `6352836` (1250a) | `op.create_foreign_key` sin batch → FAIL en SQLite |

**1110 ya corregido en base oficial:** **SÍ** (completo; diferencia cosmética de constante vs literal)

### Duplicación / cambios necesarios

- **No duplicar** commits de `ceedde5` ni `1250b`: ya presentes en `eb229806`.
- **No crear** migración nueva.
- **Diff de migraciones en esta rama:** 0 archivos modificados.

## Reproducción sobre base oficial

| Test | Motor | Resultado |
|------|-------|-----------|
| `test_migration_roundtrip_upgrade_downgrade_upgrade` | SQLite | **PASS** |
| Roundtrip manual upgrade → downgrade a840 → upgrade | PostgreSQL 16 | **PASS** → `1250f1a2b3c4d` |
| `pytest tests/` | SQLite | **746 passed, 0 failed, 2 skipped** |
| `npm run build` | — | **PASS** |
| `npm audit --audit-level=high` | — | 0 vulnerabilidades |

### Contraste con 1250a (sin convergencia final)

Base `6352836` reproduce el fallo heredado (`Constraint must have a name` en 1120) documentado en 1350A. La convergencia final `eb229806` lo resolvió antes de esta rama aislada.

## Alembic

```
HEADS: 1
HEAD: 1250f1a2b3c4d
Genealogía: 1250A + 1250B → 1250f1a2b3c4d
```

Sin migración 1350. Sin nueva revisión.

## Diff de esta rama

| Métrica | Valor |
|---------|-------|
| ARCHIVOS MODIFICADOS (migraciones) | 0 |
| ARCHIVOS MODIFICADOS (total) | 1 (este informe) |
| LÍNEAS +/− (migraciones) | 0 |
| MIGRACIONES TOCADAS | ninguna (ya en base) |
| FUNCIONALIDAD NUEVA | NO |
| MODELOS MODIFICADOS | NO |
| FRONTEND MODIFICADO | NO |
| FUNCIONALIDAD 1350 INCLUIDA | NO |

## Riesgos

| Riesgo | Nivel | Nota |
|--------|-------|------|
| Ramas derivadas de `1250a` @ `6352836` sin merge final | Medio | Siguen con migraciones rotas en SQLite limpio |
| Dependencia de PR #52 para migraciones | **Eliminado** | Fix ya en `eb229806` |
| Re-aplicar fix en ramas 1350 | Bajo | Redundante si convergen desde `1250-convergencia-final-post-v1` |

## Recomendación de integración futura

1. Usar `cursor/1250-convergencia-final-post-v1` @ `eb229806` como ancla post-V1 para convergencias posteriores (1260–1370, 1350, etc.).
2. **No** depender de PR #51/#52 para corregir 1110/1120.
3. Ramas basadas solo en `1250a-fix-aislamiento-tests` deben rebase/merge contra convergencia final antes de certificar migraciones.
4. Esta rama `cursor/post-v1-fix-migraciones-heredadas-1110-1120` sirve como **punto de certificación documentado** sin diff funcional adicional.

## Veredicto

**APTO PARA INCORPORAR EN CONVERGENCIA**

Fix heredado ya presente en base oficial; roundtrip y regresión verificados. Rama neutra sin código 1350 ni funcionalidad nueva.

**NO MERGE** (integración explícita humana cuando corresponda).
