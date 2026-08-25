# CURSOR — SALUD-960 — DEMO FUNCIONAL Y CONTROL VISUAL

**Estado:** `SALUD-960 DEMO VALIDADA`  
**Rama:** `cursor/salud-ips-engine-960`  
**PR:** #14  
**NO MERGE · NO APTO PARA MERGE**

---

## 1. Recorrido realizado

| Paso | Acción | Resultado |
|------|--------|-----------|
| 1 | Login `admin` → `/salud/diagnostico` | OK |
| 2 | Clic **Ejecutar diagnóstico (datos demo)** | Análisis COMPLETADO en ~2s |
| 3 | Verificación barra KPI | Valores coinciden con backend |
| 4 | Pestañas: Resumen → Calidad → Indicadores → Hallazgos | OK |
| 5 | Selección hallazgo + panel trazabilidad | OK |
| 6 | Retroalimentación **Correcto** en hallazgo | Mensaje confirmación |
| 7 | Oportunidades: selección 2 propuestas + **Crear plan** | Plan con 2 tareas |
| 8 | Seguimiento: **Registrar seguimiento** | Confirmación visible |
| 9 | Especialistas: dominios + puntajes + factores | OK |
| 10 | Experiencia: pregunta natural | Respuesta con evidencia |
| 11 | **Demo datos incompletos** → Indicadores | "Información insuficiente" donde corresponde |

Flujo cubierto:

```
Datos IPS → procesamiento → calidad → indicadores → hallazgos →
causas/evidencia → oportunidades → propuestas → plan → seguimiento → experiencia
```

---

## 2. Resultados obtenidos (validados vs backend/tests)

| Métrica | Esperado | UI | Coincide |
|---------|----------|-----|----------|
| Facturación | $276.000.000 / 8 facturas | $276.000.000 / 8 facturas | ✅ |
| Sin radicar | 2 | 2 | ✅ |
| Glosas | $15.700.000 | $15.700.000 | ✅ |
| Cartera 91+ | $38.000.000 | $38.000.000 | ✅ |
| Hallazgos | ≥1 | 5 | ✅ |
| Especialistas | ≥1 | 6 asignaciones | ✅ |

**No hay hardcode en frontend** — todos los valores provienen de `/api/salud/analisis` y `/api/salud/diagnostico`.

---

## 3. Especialistas seleccionados

**Solicitud:** "Analiza la situación financiera y operativa de esta IPS."

**Dominios detectados:** Estratégico, Facturación, Radicación, Glosas, Cartera, Contratos (según datos demo).

**Ejemplo de asignación (no rígida por nombre):**

| Especialista | Dominio | Puntaje | Capacidades | Herramientas | Experiencia |
|--------------|---------|---------|-------------|--------------|-------------|
| Analista de Facturación IA | Facturación | 0.93 | 1.00 | 1.00 | 0.50 |
| Analista de Radicación IA | Radicación | 0.93 | 1.00 | 1.00 | 0.50 |
| … | … | … | … | … | … |

**Consolidador:** Analista Estratégico IPS IA.

La selección usa `score_employee_for_domain()` (capacidades 35%, herramientas 15%, especialidad, disponibilidad, experiencia).

---

## 4. Hallazgos principales (demo)

1. 2 facturas sin radicar — impacto $79.000.000
2. Demora promedio factura→radicación: 15,8 días
3. Alta concentración en un pagador: 75%
4. Porcentaje de glosa elevado: 5,69%
5. Cartera vencida 91+ días: $38.000.000

---

## 5. Propuestas generadas

- Control diario de facturas pendientes de radicación (Coordinador de radicación, 60 días)
- Gestión de cobro cartera 91+ (Analista de cartera, 60 días)
- Diversificación de pagadores (Analista de facturación, 60 días)
- Revisión causales de glosa (Analista de glosas, 60 días)

Todas con evidencia, causa probable, meta e indicador de seguimiento.

---

## 6. Preguntas ejecutivas respondidas

| Pregunta | ¿Responde la plataforma? |
|----------|--------------------------|
| ¿Qué problemas tiene esta IPS? | ✅ Resumen + hallazgos |
| ¿Cuánto representan? | ✅ Impacto acumulado $132.700.000 |
| ¿Dónde están? | ✅ Categoría + indicador por hallazgo |
| ¿Por qué probablemente ocurren? | ✅ Causa probable + evidencia |
| ¿Qué hacer primero? | ✅ Priorización + acciones prioritarias |
| ¿Qué impacto esperamos? | ✅ Impacto esperado en propuestas |
| ¿Cómo mediremos mejora? | ✅ Meta + indicador seguimiento + registro resultado |

**Brecha menor:** comparación histórica visible solo tras segundo análisis de la misma IPS (funciona en backend, poco visible en UI).

---

## 7. Ciclo experiencia demostrado

```
Hallazgo → Retroalimentación "Correcto" → Propuesta seleccionada →
Plan de acción (2 tareas) → Seguimiento registrado → Caso en experiencia
```

**Operación manual restante:** vincular plan IPS con WorkPlan del orquestador (pendiente arquitectónico, no bloquea demo).

---

## 8. Caso datos incompletos

Botón **Demo datos incompletos** (solo facturación):

- Facturación: datos completos
- Radicación, Glosas, Cartera: **Información insuficiente**
- Sin números inventados

Captura: `11_datos_incompletos.png`

---

## 9. Acciones probadas

| Acción | Estado |
|--------|--------|
| Pestañas de navegación (9 secciones) | ✅ Funciona |
| Ejecutar demo completo | ✅ |
| Ejecutar demo parcial | ✅ |
| Seleccionar hallazgo → detalle trazabilidad | ✅ |
| Retroalimentación Correcto/Parcial/Incorrecto | ✅ |
| Checkbox propuestas | ✅ |
| Crear plan de acción | ✅ |
| Registrar seguimiento | ✅ |
| Pregunta natural | ✅ |
| Filtros avanzados | ⚠️ No implementados (no bloquean demo) |
| Regreso navegación browser | ✅ |

---

## 10. Problemas funcionales encontrados

| # | Problema | Severidad | Estado |
|---|----------|-----------|--------|
| 1 | Acciones prioritarias en resumen pueden repetir texto truncado | Baja | Documentado |
| 2 | Comparación histórica poco visible en UI | Baja | Pendiente |
| 3 | Plan IPS no enlaza automáticamente a WorkPlan | Media | Pendiente (fuera de alcance) |

**Sin bloqueos funcionales para la demo.**

---

## 11. Problemas visuales encontrados y correcciones

| Problema | Corrección aplicada |
|----------|---------------------|
| Indicadores mostraban JSON crudo | Tarjetas KPI legibles en español |
| Sin navegación por pestañas | 9 pestañas compactas |
| Sin detalle de hallazgo | Panel trazabilidad lateral |
| Sin acciones de feedback/plan | Botones Correcto, checkboxes, crear plan |
| Etiquetas técnicas en inglés (`facturacion`) | Mapeo a español (Facturación, etc.) |
| Sin barra KPI resumen | Barra superior con 4 métricas clave |
| Texto desbordado en tablas | `cell-truncate`, grid responsivo |

**No se realizó rediseño general** — solo correcciones puntuales en `DiagnosticoIpsPage.tsx` y `styles.css`.

---

## 12. Español

Revisión completa de la vista Diagnóstico IPS:

- ✅ Sin texto visible en inglés (Insights, Confidence, Status, etc.)
- ✅ Pestañas, botones, mensajes y estados en español
- ✅ "Información insuficiente" (no "Insufficient data")

---

## 13. Capturas generadas

Directorio: `INTERCAMBIO/SALIDA/SALUD_960_DEMO/`

| # | Archivo |
|---|---------|
| 1 | `01_diagnostico_completo.png` |
| 2 | `02_resumen_ejecutivo.png` |
| 3 | `03_calidad_datos.png` |
| 4 | `04_indicadores.png` |
| 5 | `05_hallazgos.png` |
| 6 | `06_hallazgo_detalle.png` |
| 7 | `07_oportunidades.png` |
| 8 | `08_plan_accion.png` |
| 9 | `09_seguimiento.png` |
| 10 | `10_experiencia.png` |
| 11 | `11_datos_incompletos.png` |
| 12 | `12_especialistas.png` |

---

## 14. Regresión

| Comando | Resultado |
|---------|-----------|
| `pytest` | **71 passed** |
| `npm run build` | **PASS** |
| `npm audit` | **0 vulnerabilities** |
| `git diff --check` | **PASS** |

---

## 15. Git

- **Rama:** `cursor/salud-ips-engine-960`
- **HEAD:** (actualizar tras commit demo)
- **PR:** #14 (draft, NO MERGE)

---

## 16. Pendientes (sin implementar en este turno)

- Embeddings para casos similares
- Integración CONOCIMIENTO-930
- Integración definitiva WorkPlan
- Nuevos agentes / gráficas decorativas
- Filtros avanzados en tabla de hallazgos

---

## Conclusión

**SALUD-960 DEMO VALIDADA**

El recorrido completo funciona desde la interfaz con datos demo ficticios. Los valores de UI coinciden con backend y tests. Trazabilidad, retroalimentación, plan de acción y caso incompleto demostrados con capturas.

**NO APTO PARA MERGE · NO MERGE**
