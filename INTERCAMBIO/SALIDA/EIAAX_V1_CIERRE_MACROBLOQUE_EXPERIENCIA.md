# EIAAX V1 — Cierre macrobloque experiencia (continuación c0f28b1)

**SHA candidato:** ver `git rev-parse HEAD` en rama `cursor/experiencia-v1-convergencia-85e4`
**Base:** `cursor/convergencia-comercial-v1-85e4`
**PR:** #168

---

## Preservado de c0f28b1

Logos, documentos cabina, Clínica Demo Horizonte, CC compacto, menú primary/advanced, Columnas, instructivo 10 partes, IE PR #166.

---

## Integración selectiva B — PR #162 Inteligencia económica

| Decisión | Detalle |
|---|---|
| **INTEGRADO** | Módulo `inteligencia_economica_*`, API `/api/inteligencia-economica`, tab Costos/Valor |
| **Migración** | `1830a1b2c3d4e` (reconciliada post-1820, sin colisión 1740 fábrica) |
| **NO duplica** | FinOps 1110, motor 1600, valoración 1210 — orquesta sobre existentes |
| **Protección cliente** | `inteligencia_economica.private` separado; pricing interno no expuesto en UI empresa |

---

## Integración selectiva D — PR #163 Empleado IA 2.0

| Decisión | Detalle |
|---|---|
| **INTEGRADO** | Ficha laboral, supervisión, evaluación, tab Ficha 2.0, hook autonomía en coordinator |
| **Migración** | `1831a1b2c3d4e` (5 tablas, parent 1830) |
| **POST-V1** | CC adapter señales (`employee_20_cc_adapter` sin cableado UI), bridge aprendizaje 1260 |
| **Adaptación** | `AUTONOMY_LEVEL` añadido sin eliminar `MATURITY` existente |

---

## P0 cerrado — Hallazgos 1220 → expediente

- `POST /api/flujo-comercial/expedientes/{id}/importar-diagnostico`
- Deduplicación por `diagnostic_finding_id`
- Vincula `expediente.diagnostic_id`
- Tests: `tests/test_importar_diagnostico_expediente.py` (2/2 PASS)

---

## P1 cerrado — Cadena analítica visible

- `CadenaAnaliticaPanel.tsx` — flujo EVIDENCIA→ACCIÓN compacto
- Integrado en cabina Diagnóstico y `CentroControlEmpresaPanel`
- API: `GET /api/inteligencia-empresarial/expedientes/{id}/cadena-analitica`

---

## Centro de Operaciones — seed demo

- `demo_comercial_service._seed_demo_operaciones`: planes RUNNING, WAITING_APPROVAL, COMPLETED, FAILED + aprobación pendiente
- Import diagnóstico en semilla cuando hay señales

---

## Presentar / Publicar / Ver como empresa

- Banner en `PresentacionRealPage`: reunión vs consulta posterior + enlaces Vista Empresa
- Enlaces existentes en CC y cabina preservados

---

## Migraciones finales

```
1820 → 1830 (economic_scenario_runs) → 1831 (employee_ia_20)
```

`migration_ledger.json` baseline_head: `1831a1b2c3d4e`

---

## Pruebas

| Suite | Resultado |
|---|---|
| `test_importar_diagnostico_expediente.py` | 2/2 PASS |
| `test_demo_comercial_ficticia.py` | 7/7 PASS |
| `test_inteligencia_economica_1740.py` | PASS |
| `test_employee_ia_20_evolution.py` | PASS |
| `test_inteligencia_empresarial_evolution.py` | 9/9 PASS |
| `test_convergencia_maestro_v1.py` + cierre | PASS |
| `npm run build` | PASS |
| `cert_visual_audit.mjs` (admin/Horizonte) | **36/36 PASS** |
| `git diff 0014a4b -- scripts/windows/` | **0 líneas** |

---

## Demo Clínica Demo Horizonte

```bash
python backend/scripts/seed_demo_horizonte.py
# admin / Admin2026!
# DATABASE_URL=sqlite:////workspace/data/eiaax_horizonte_demo.db
```

---

## P0/P1/P2 restantes REALES

| ID | Estado |
|---|---|
| P1 CC adapter empleado → CC | POST-V1 (código presente, sin UI) |
| P1 Bridge aprendizaje 1260 | POST-V1 |
| P2 Publicación espacio externo — flujo guiado paso a paso | Mejora UX |
| P2 Inventario menú completo clasificado | Parcial (audit visual 36 rutas PASS) |

---

## Procedimiento prueba humana

1. `python backend/scripts/seed_demo_horizonte.py`
2. Arrancar backend con `DATABASE_URL=.../eiaax_horizonte_demo.db` y frontend `:5180`
3. Login `admin` / `Admin2026!`
4. Centro de Control → seleccionar Clínica Demo Horizonte
5. Recorrer: cabina Diagnóstico (cadena + documentos) → oportunidades → presentación → Vista Empresa → Operaciones (datos demo) → Costos/Valor tab Inteligencia económica
6. Configuración → Identidad → logo >180 KB
7. Guía rápida e instructivo (10 partes)
