# 09 — Criterios de convergencia para GENERAL

Documento de handoff. **No integrar desde este agente.**

---

## Alcance del lote único A+B+C+D

Integrar en **un solo lote controlado** sobre base `75fc689`:

| Candidato | SHA | Rol en convergencia |
|-----------|-----|---------------------|
| A | `f0d02bc` | Espacio externo, evidencias, **publicación canónica** |
| B | `2bb3caa` | Flujo comercial prospecto→cliente |
| C | `25c79d5` | Centro Estratégico, gobierno, evaluación |
| D | `40b7c9b` | Demo, presentación (adapter publicación) |

**Excluido:** Windows, PIIAX, ramas históricas 23/25 PR.

---

## Decisiones obligatorias antes de codificar

1. **Publicación:** sobrevive `EmpresaPublicacion` (A); D y C son consumidores/adapters.
2. **Economía:** sobrevive `motor_economico` (central); B/C solo CONECTAR.
3. **Informes:** sobrevive MB-11; sin scheduler paralelo.
4. **Control center:** una autoridad (fusión B∩C — ver `05_CONFLICTOS.md`).
5. **Migraciones:** no portar revision ids `1410`/`1420`/`1430` literales de A/C/D; GENERAL renumerará (**14** objetos — ver `06`).

---

## Métricas del informe (conteos)

| Métrica | Cantidad |
|---------|----------|
| **Duplicidades críticas de autoridad** | **7** |
| **Conflictos de archivos ALTO** | **6** |
| **Migraciones a reconstruir / renumerar** | **14** |
| **Autoridades a unificar** | **9** |
| **Huecos funcionales V1 reales** | **12** (3 P0, 5 P1, 4 P2) |

### Duplicidades críticas (7)

1. Publicación (A / D / C UI)
2. Economía (B pricing vs central motor)
3. Control center service (B vs C)
4. Evaluación visibility (A 1430 vs C strategic)
5. Oportunidades (B flujo vs C strategic)
6. Presentación ejecutiva vs publicación empresa
7. Gobierno aprobaciones (central vs C extensión — fusionar, no duplicar)

### Conflictos ALTO (6)

Ver `05_CONFLICTOS.md`: `main.py`, `permissions.py`, `control_center_service.py`, `control_center.py`, migración `1410`, `App.tsx` / menú.

---

## Orden recomendado de integración

**C → B → D → A**

Detalle y pruebas acumulativas: `07_ORDEN_PORTADO.md`.

---

## P0 encontrados

| ID | Descripción |
|----|-------------|
| P0-1 | Triple autoridad publicación |
| P0-2 | Colisión cadena Alembic |
| P0-3 | Dual `control_center_service` |

---

## P1 encontrados

| ID | Descripción |
|----|-------------|
| P1-1 | Suficiencia evidencias pre-evaluación |
| P1-2 | Economía POTENCIAL/REAL filtración prospecto |
| P1-3 | Prospecto→cliente dossier único |
| P1-4 | Cuatro audiencias una fuente |
| P1-5 | Contrato→implementación→Empleados IA |

---

## P2 encontrados

| ID | Descripción |
|----|-------------|
| P2-1 | Expansión/renovación |
| P2-2 | Soporte MB-12 portal externo |
| P2-3 | Correlation_id uniforme |
| P2-4 | Evitar scheduler informes paralelo |

---

## Checklist de aceptación post-convergencia

- [ ] Un solo `alembic head`
- [ ] Un router y servicio `control_center` activo
- [ ] `EmpresaPublicacion` única autoridad de publicación
- [ ] `motor_economico` única autoridad económica; sin leak a prospecto
- [ ] MB-11 única autoridad informes
- [ ] Flujo `04_FLUJO_COMERCIAL_UNIFICADO.md` demostrable en staging
- [ ] Tests acumulados verdes (A+B+C+D suites)
- [ ] `permissions.py` sin duplicados contradictorios
- [ ] Documentación INTERCAMBIO archivada con PR de convergencia

---

## Restricciones recordatorio

- NO merge desde este análisis
- NO cherry-pick
- NO modificar ramas candidatas
- NO tocar Windows / GENERAL exclusivo
- Tip documental posterior ≠ autoridad funcional central

---

## Entregables en esta carpeta

| Archivo | Contenido |
|---------|-----------|
| `01_RESUMEN.md` | Inventario y resumen ejecutivo |
| `02_MATRIZ_CAPACIDADES.md` | REUTILIZAR / PORTAR / CONECTAR / DESCARTAR / DECISIÓN |
| `03_AUTORIDADES_CANONICAS.md` | 9 autoridades unificadas |
| `04_FLUJO_COMERCIAL_UNIFICADO.md` | Recorrido DEMO→expansión |
| `05_CONFLICTOS.md` | BAJO / MEDIO / ALTO |
| `06_MIGRACIONES.md` | 14 migraciones — acción convergencia |
| `07_ORDEN_PORTADO.md` | C→B→D→A |
| `08_HUECOS_REALES_V1.md` | 12 huecos P0/P1/P2 |
| `09_CRITERIOS_CONVERGENCIA_GENERAL.md` | Este documento |

---

**Estado:** PRECONVERGENCIA COMPLETA — listo para GENERAL.
