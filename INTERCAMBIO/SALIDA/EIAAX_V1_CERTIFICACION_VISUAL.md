# EIAAX V1 — Certificación visual y funcional

**Fecha:** 2026-09-02  
**Rama autoritativa:** `cursor/convergencia-comercial-v1-85e4`

---

## A. SHA autoritativo exacto

```
git rev-parse origin/cursor/convergencia-comercial-v1-85e4
→ ac166dc (post-certificación visual; incluye b1b18b8 → 4909bff)
```

## B. Confirmación feature incluida

| Pregunta | Respuesta |
|----------|-----------|
| `4909bff` está contenido en `b1b18b8` | **SÍ** (`git merge-base --is-ancestor 4909bff b1b18b8`) |
| `b1b18b8` contiene TODO el candidato funcional V1 | **SÍ** (fast-forward desde maestro; solo añade doc SHA) |

## C. Rama autoritativa

`cursor/convergencia-comercial-v1-85e4`

## D. scripts/windows diff

```
git diff 0014a4b -- scripts/windows/
→ VACÍO (0 líneas)
```

## E. Pantallas inspeccionadas (36/35 requeridas + CC salud duplicado en flujo)

| # | Pantalla | Resultado | Notas |
|---|----------|-----------|-------|
| 1 | Login | PASS | Logo EIAAX, formulario único |
| 2 | CC — todas las empresas | PASS | Consola maestra visible |
| 3 | CC — empresa seleccionada | PASS | Selector contexto + panel empresa |
| 4 | CC — salud inline | PASS | Tab Salud sin enlaces primarios externos |
| 5 | Empresas | PASS | Cabina/Centro/Presentar |
| 6 | Mi trabajo | PASS | |
| 7 | Centro de Operaciones | PASS | Strip acceso rápido |
| 8 | Nueva solicitud | PASS | «¿Qué necesita hacer hoy?» principal |
| 9 | Ejecuciones | PASS | Estado vacío útil |
| 10 | Aprobaciones | PASS | |
| 11 | Automatizaciones | PASS | |
| 12 | Evaluaciones | PASS | |
| 13-22 | Cabina (10 tabs) | PASS | Empresa→Vista Empresa |
| 23 | Directorio | PASS | |
| 24 | Detalle empleado | PASS | Dossier + jerarquía acciones |
| 25 | Auditoría empleados | PASS | |
| 26 | Centro de confianza | PASS | |
| 27 | Config — General | PASS | Tabs compactos |
| 28 | Config — Identidad | PASS | Marca madre + upload logo |
| 29 | Config — Servicios | PASS | |
| 30 | Config — IA / Integraciones | PASS | |
| 31 | Guía rápida | PASS | 15 pasos con enlaces |
| 32 | Presentación | PASS | Sin datos privados detectados |
| 33 | Ver como empresa | PASS | |
| 34 | Navegación principal | PASS | Secciones Inicio/Trabajo/Empresas/… |
| 35 | Asistente EIAAX | PASS | Compacto cerrado, usable abierto |

**Herramienta:** `node scripts/cert_visual_audit.mjs` (Playwright headless, 1440×900)  
**Credenciales audit:** `org_a_admin` / `DemoA2026!`  
**Resultado:** 36 PASS · 0 FAIL · 0 SKIP

## F. Defectos encontrados

| ID | Pantalla | Hallazgo | Severidad |
|----|----------|----------|-----------|
| D1 | Cabina — Diagnóstico | `AccionesExternasPanel` usado sin import → ReferenceError al renderizar hallazgos | P0 |
| D2 | Auditoría previa (10 pantallas) | Cobertura insuficiente vs. 35 pantallas requeridas | Proceso |

## G. Correcciones realizadas

| ID | Corrección | Archivo |
|----|------------|---------|
| D1 | Añadido `import { AccionesExternasPanel } from "../components/evaluacion/AccionesExternasPanel"` | `EvaluacionConsolePage.tsx` |
| D2 | Script certificación 36 pantallas + test import | `scripts/cert_visual_audit.mjs`, `tests/test_convergencia_cierre_v1.py` |

## H. Segunda inspección

Re-ejecutado `cert_visual_audit.mjs` tras corrección D1:

```
Total: 36 | PASS: 36 | FAIL: 0 | SKIP: 0
```

Todas las tabs de cabina (incl. Diagnóstico) PASS sin ReferenceError.

## I. Pruebas después de correcciones

| Prueba | Resultado |
|--------|-----------|
| `npm run build` | PASS |
| `test_convergencia_maestro_v1.py` (6) | PASS |
| `test_convergencia_cierre_v1.py` (8) | PASS |
| Bundle core (`hotfix`, `puesta_en_marcha`, etc.) | 20 PASS, 8 skipped |

## J. E2E

Recorrido automatizado: login → CC global/empresa/salud → empresas → operaciones → nueva solicitud → cabina 10 tabs → presentación → vista empresa → config 4 tabs → empleado → menú → asistente.

## K. P0 / P1 / P2 finales

| Prioridad | Count |
|-----------|-------|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |

## L. Credenciales Windows demo

**Autoritativas:** `org_a_admin` / `DemoA2026!`  
Bootstrap fresco: `admin` / `Admin2026*`

## M. Comando único Windows

Bootstrap certificado sincroniza `origin/cursor/convergencia-comercial-v1-85e4` sin modificar `scripts/windows/**`.

---

## Trazabilidad pantalla → hallazgo → corrección → revalidación

```
Cabina/Diagnóstico → ReferenceError AccionesExternasPanel → import añadido → tab Diagnóstico PASS (audit #14)
Cobertura audit → solo 10 pantallas → script 36 pantallas → 36/36 PASS
```
