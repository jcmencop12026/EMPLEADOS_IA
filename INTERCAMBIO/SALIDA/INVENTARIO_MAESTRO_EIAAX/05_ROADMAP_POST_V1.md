# 05 — Roadmap post-V1 (Grupo C)

**Grupo C — PRODUCTO MAESTRO POST-V1:** conservar en roadmap; no olvidar.  
**Filas Grupo C:** **27 / 136** (19,9%)

---

## Principio

Estos ítems están en el diseño acumulado EIAAX pero **no bloquean** el cierre de convergencia V1+V2 ni la operación del producto integrado `b19b04d`. Deben permanecer trazados para evolución posterior.

---

## Identidad y experiencia avanzada

| ID | Capacidad | Estado | Origen diseño | Notas |
|---|---|---|---|---|
| ID-01 | Norma Visual EIAAX transversal | ROJO | Plan maestro | Tablas, tipografía, espaciado, componentes |
| ID-02 | Tema claro/oscuro | ROJO | Plan maestro | No iniciar en convergencia |
| ID-04–07 | Familias HERO/CORPORATIVO/EX/NODO/ÓRBITA/X | ROJO | Identidad EIAAX | Productos visuales futuros |
| ID-06 | Personalidad verbal | ROJO | Brand guidelines | Copy system |
| ID-07 | Config central identidad | ROJO | Arquitectura identidad | Single config service |
| ID-10 | PIIAX producto hijo | ROJO | Portfolio EIAAX | Integrable, independiente |
| ID-11 | Citas/Agendamiento hijo | ROJO | Portfolio EIAAX | Opcional |

---

## Capacidades técnicas avanzadas

| ID | Capacidad | Estado | Origen | Notas |
|---|---|---|---|---|
| TX-14 | Shadow Mode comparativo | ROJO | 803/805 docs | POST-V1 explícito |
| TX-09 | Tablas EIAAX (paginación/col. redim.) | MORADO | P2 histórico | Mejora transversal |
| TX-10 | Ayuda contextual avanzada | AMARILLO | Plan UX | Tooltips + guías |
| MB08-08 | Gráficos dinámicos BI | AMARILLO | CC evolución | Charts ejecutivos |
| MB04-05 | Módulo UI Arquitecto marca | AZUL | MB-04 diseño | Motor existe |
| MB05-08 | Wizard Estudio procesos marca | AZUL | MB-05 diseño | Motor 1220 existe |

---

## Infraestructura y despliegue

| ID | Capacidad | Estado | Notas |
|---|---|---|---|
| TX-16 | Docker/prod compose V1 evolucionado | X | EVOLUCIÓN POST-F2 en MATRIZ |
| — | SUPERADMIN org override en todos los routers | AMARILLO | Solo CC/trabajo/auditor/finops hoy |
| — | CAS/concurrencia C3 | ROJO | Auditor C3 futuro |
| — | Fábrica MB-06 profunda | AMARILLO | Ciclo actual certificado; evolución C3 |
| — | Inventario automático propuestas | ROJO | Demo comercial futura |

---

## Legacy / limpieza

| ID | Ítem | Estado | Acción futura |
|---|---|---|---|
| MB08-07 | `DashboardPage.tsx` huérfano | NEGRO | Eliminar archivo |
| MB03-03 | Tabla `partners` legacy SQLite | NARANJA | Migrar o deprecar al construir MB-03 |
| — | Menú ítems `future: true` | X | Mantener hasta wiring real |

---

## Secuencia sugerida post-V1 (sin fechas)

### Fase comercial inmediata (Grupo B)
Ver `04_BRECHAS_V1_COMERCIAL.md`

### Fase experiencia (Grupo C — prioridad media)
1. Norma Visual EIAAX (componentes base)
2. Gráficos dinámicos CC
3. Tablas EIAAX transversales
4. Ayuda contextual

### Fase portfolio (Grupo C — prioridad baja)
1. PIIAX integrable
2. Citas/Agendamiento
3. Shadow Mode
4. Familias visuales EX/ÓRBITA

---

## Qué NO olvidar del diseño histórico

Documentos de referencia preservados en `INTERCAMBIO/SALIDA/`:

- `CURSOR_PLAN_UNICO_CONVERGENCIA_FINAL_POST_V1.md` — plan maestro
- `MAPA_FINAL_PLATAFORMA_FASE2.md` — mapa rutas Fase 2
- `CURSOR_FASE2_CENTRAL_TRAMO*.md` — tramos 1–6
- Bloques 1100–1380 individuales
- `EMPLEADOS_IA_FABRICA_CICLO_VIDA.md`, MB-07, MB-11, MB-12
- Convergencia C1/C1-R1/C2 entregables

**Regla:** decisión más reciente prevalece; requisitos compatibles anteriores se conservan en matriz.

---

## Conclusión Grupo C

El 19,9% de filas en ROJO/NEGRO/X corresponde mayoritariamente a **evolución de producto maestro**, no a deuda de convergencia. Deben planificarse sin bloquear operación del candidato certificado.
