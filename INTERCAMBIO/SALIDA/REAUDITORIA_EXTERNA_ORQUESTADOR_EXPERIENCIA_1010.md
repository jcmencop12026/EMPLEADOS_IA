# REAUDITORÍA EXTERNA ADVERSARIAL — ORQUESTADOR-EXPERIENCIA-1010

**Fecha:** 2026-08-27 11:01 UTC
**Rama:** `cursor/orquestador-experiencia-1010-12b6` @ `897cf2c57239c5e2bea2a85a4804dc808902ab50`
**PR:** #22 — NO MERGE
**Paquete:** paquete_embedded_especificacion — /workspace/INTERCAMBIO/SALIDA/reauditoria_orquestador_1010/paquete_embedded

## Veredicto final

**ORQUESTADOR-EXPERIENCIA-1010 — APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN**

## Matriz de evaluación

| CASO | PROBLEMA | LÍDER | COMPLEMENTARIOS | VALIDADOR | DISIDENTE | EXPERIENCIA | PESO | COSTO | RIESGO | RAZÓN (extracto) | RESULTADO | VEREDICTO |
|------|----------|-------|-----------------|-----------|-----------|-------------|------|-------|--------|------------------|-----------|-----------|
| OX-A | radicacion_tardia | Analista de Radicación IA | Analista de Cartera IA, Analista de Facturación IA | Analista de Cartera IA | Analista de Glosas IA | 4 refs | 0.8 | 0.18 | 0.7 | Seleccionado Analista de Radicación IA como líder porque capacidades alineadas c… | congelado | PASS |
| OX-B | glosas_devoluciones | Analista de Glosas IA | Analista de Cartera IA, Analista de Facturación IA | Analista de Cartera IA | Analista de Radicación IA | 5 refs | 0.785 | None | 0.7 | Seleccionado Analista de Glosas IA como líder porque capacidades alineadas con g… | congelado | PASS |
| OX-C | comportamiento_pagador | Analista de Cartera IA | Analista Contractual IA | Analista Contractual IA | Analista de Facturación IA | 5 refs | 0.613 | 0.01 | 0.7 | Seleccionado Analista de Cartera IA como líder porque capacidades alineadas con … | congelado | PASS |

> **OX-C observación:** Contractual alcanza experiencia=0.80 vs Cartera 0.613 (calidad > volumen). Cartera lidera por afinidad de capacidad/especialidad en dominio `cartera` (score 0.847 vs 0.786). Competencia real demostrada.
| OX-D | diagnostico_integral | Analista Estratégico IPS IA | Analista de Cartera IA, Analista Contractual IA, Analista de Facturación IA | Analista de Facturación IA | Analista de Radicación IA | 5 refs | 0.785 | None | 0.7 | Seleccionado Analista Estratégico IPS IA como líder porque capacidades alineadas… | congelado | PASS |
| OX-E | datos_insuficientes | Analista Estratégico IPS IA |  | Analista de Facturación IA |  | 0 refs | 0.35 | None | 0.7 | Seleccionado Analista Estratégico IPS IA como líder porque capacidades alineadas… | congelado | PASS |
| OX-F | radicacion_tardia | Analista de Radicación IA | Analista de Cartera IA, Analista de Facturación IA | Analista de Cartera IA | Analista de Glosas IA | 1 refs | 0.785 | None | 0.7 | Seleccionado Analista de Radicación IA como líder porque capacidades alineadas c… | congelado | PASS |
| OX-G | comportamiento_pagador | Analista de Cartera IA | Analista de Facturación IA | Analista de Facturación IA | Analista Contractual IA | 0 refs | 0.35 | None | 0.7 | Seleccionado Analista de Cartera IA como líder porque capacidades alineadas con … | congelado | PASS |
| OX-H | radicacion_tardia | Analista de Radicación IA | Analista de Facturación IA |  | Analista de Cartera IA | 0 refs | 0.35 | None | 0.7 | Seleccionado Analista de Radicación IA como líder porque capacidades alineadas c… | congelado | PASS |

## Controles adversariales

- **OX-A…E dinámico:** PASS
- **Anti-líder prefabricado:** PASS
- **OX-F aprendizaje:** PASS
- **OX-G feedback vs real:** PASS
- **OX-H tenant:** PASS
- **Costo FINOPS:** PASS
- **Diversidad/validador:** PASS
- **Metamórfico:** PASS
- **Trazabilidad:** PASS

### OX-F — Aprendizaje posterior (antes/después)

- ranking_antes (top): [{'employee_code': 'ips-radicacion-analyst', 'employee_name': 'Analista de Radicación IA', 'score': 0.867, 'factores': {'capacidad': 1.05, 'experiencia': 0.785, 'desempeno': 0.785, 'costo': 0.6, 'disponibilidad': 1.0, 'riesgo': 0.7, 'diversidad': 1.0}}, {'employee_code': 'ips-cartera-analyst', 'employee_name': 'Analista de Cartera IA', 'score': 0.715, 'factores': {'capacidad': 1.05, 'experiencia': 0.35, 'desempeno': 0.35, 'costo': 0.6, 'disponibilidad': 1.0, 'riesgo': 0.7, 'diversidad': 1.0}}]
- ranking_despues (top): [{'employee_code': 'ips-radicacion-analyst', 'employee_name': 'Analista de Radicación IA', 'score': 0.731, 'factores': {'capacidad': 1.05, 'experiencia': 0.396, 'desempeno': 0.396, 'costo': 0.6, 'disponibilidad': 1.0, 'riesgo': 0.7, 'diversidad': 1.0}}, {'employee_code': 'ips-cartera-analyst', 'employee_name': 'Analista de Cartera IA', 'score': 0.715, 'factores': {'capacidad': 1.05, 'experiencia': 0.35, 'desempeno': 0.35, 'costo': 0.6, 'disponibilidad': 1.0, 'riesgo': 0.7, 'diversidad': 1.0}}]
- peso_antes: 0.785 → peso_despues: 0.396
- score radicación: 0.867 → 0.731
- explicacion_antes: Seleccionado Analista de Radicación IA como líder porque capacidades alineadas con radicacion; 1 experiencias exitosas en radicacion; especialidad Radicación IPS relevante en dominio principal 'radicacion' (tipo: radicacion_tardia)
- explicacion_despues: Seleccionado Analista de Radicación IA como líder porque capacidades alineadas con radicacion; 1 fracasos previos en radicacion; especialidad Radicación IPS relevante en dominio principal 'radicacion' (tipo: radicacion_tardia)

### OX-G — Feedback engañoso vs resultado real

- estado: FRACASO (feedback: CORRECTO)
- peso_calidad: 0.63 — resultado real prevalece: True

### OX-H — Aislamiento tenant

- TENANT_A: `ce6bf9db-7e60-4ec6-987a-2d1166c39c8f`
- TENANT_B: `193d864b-d2a3-4335-8e42-2f88b157aa45`
- Experiencia B no consultada: True
- Prueba negativa: {'experiencias_utilizadas': [], 'exp_factor_radicacion': 0.35}

### Anti-líder prefabricado — por qué cambia cada selección

- **OX_A** dominio=`radicacion` → líder **Analista de Radicación IA**
- **OX_B** dominio=`glosas` → líder **Analista de Glosas IA**
- **OX_C** dominio=`cartera` → líder **Analista de Cartera IA**
- **OX_D** dominio=`estrategico` → líder **Analista Estratégico IPS IA**
- **OX_E** dominio=`estrategico` → líder **Analista Estratégico IPS IA**

## Regresión (Fase 11)

| Prueba | Resultado |
|--------|-----------|
| `pytest tests/test_orquestador_experiencia_1010.py` | 26 passed |
| `pytest tests/` | 465 passed, 2 skipped |
| `npm run build` | OK |
| `npm audit --audit-level=high` | 0 vulnerabilities |
| `git diff --check` | OK |
| `alembic heads` | 1010a1b2c3d4e (head único) |

## Artefactos

- Brutos: `INTERCAMBIO/SALIDA/reauditoria_orquestador_1010/brutos/OX_*_ANTES_ORACULO.json`
- Resumen ciego: `INTERCAMBIO/SALIDA/reauditoria_orquestador_1010/resumen_fase_ciega.json`
- Resumen post-oráculo: `INTERCAMBIO/SALIDA/reauditoria_orquestador_1010/resumen_post_oraculo.json`

## Nota sobre paquete externo

El ZIP `ORQUESTADOR_EXPERIENCIA_1010_CERTIFICACION_V1.zip` no estaba en `INTERCAMBIO/ENTRADA/`. Se utilizó `paquete_embedded/` derivado de la especificación adversarial (casos OX-A…OX-H). El algoritmo del producto no fue modificado para casos OX.
