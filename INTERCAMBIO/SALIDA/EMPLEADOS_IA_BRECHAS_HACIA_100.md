# EMPLEADOS IA — BRECHAS HACIA 100 %

**Agente:** C (análisis / inventario funcional)  
**Fecha:** 2026-08-29  
**Rama analizada:** `cursor/1250-convergencia-final-post-v1` @ `eb229806`  
**Base de matriz:** `INTERCAMBIO/SALIDA/EMPLEADOS_IA_MATRIZ_MAESTRA_MACROBLOQUES.md`  
**Producto actual:** ~69.8 % núcleo | Integración BE↔FE ~54 %

---

## 1. Resumen de brechas por prioridad

| Prioridad | Cantidad | Descripción |
|-----------|----------|-------------|
| **P0** | 4 | Bloquean operación segura, convergencia o cierre comercial del producto |
| **P1** | 12 | Capacidades núcleo incompletas con alto impacto en valor percibido |
| **P2** | 14 | Integración visual, extensión CC, producto hijo, calidad operativa |
| **P3** | 11 | Mejoras, deuda técnica, nice-to-have post-100 % |

**Total brechas registradas:** 41

---

## 2. TOP 10 BRECHAS (impacto sistémico)

| # | Brecha | Tipo | P | Estado actual | Acción requerida |
|---|--------|------|---|---------------|------------------|
| 1 | Convergencia ramas certificadas 1260–1360 no integradas en núcleo único | BRECHA DE PRODUCTO | P0 | PREPARADO en ramas | Ejecutar plan convergencia post-1250 sin tocar Fase2 central |
| 2 | Centro de Negocios (1280–1340) ausente en producto convergido | BRECHA COMERCIAL | P0 | PREPARADO rama comercial | Portar cadena 1280→1320→1340→1310 sobre base 1250f |
| 3 | Identidad avanzada MFA/SSO/SCIM (1300) no en núcleo | BRECHA OPERATIVA | P0 | PREPARADO rama comercial | Converger security/identidad/scim tras comercial |
| 4 | Integraciones reales 1330 (PH-02) sin router en central | BRECHA DE INTEGRACIÓN | P0 | PREPARADO rama 1330 | Convergencia conectores + gobierno trazas |
| 5 | Arquitecto transformación sin capa unificada ni repriorización 1260 | BRECHA FUNCIONAL | P1 | PARCIAL distribuido | Integrar aprendizaje 1260 + UI |
| 6 | Centro de Control sin adaptadores 1240/1260/comercial | BRECHA DE INTEGRACIÓN | P1 | PARCIAL | Extender `control_center_adapters` |
| 7 | Fábrica empleados: capacitación y auditoría continua ausentes | BRECHA FUNCIONAL | P1 | NO IMPLEMENTADO | Diseñar ciclo auditoría empleado (sin desarrollar ahora) |
| 8 | Mesa de ayuda / soporte (MB-12) inexistente | BRECHA FUNCIONAL | P1 | NO IMPLEMENTADO | Definir PH o módulo núcleo mínimo |
| 9 | Semántica HECHO/INFERENCIA/RECOMENDACIÓN sin contrato global | BRECHA DE PRODUCTO | P1 | PARCIAL | Unificar enums/schemas transversales |
| 10 | Frontend ~59 % — vistas comerciales/aprendizaje fuera de build central | BRECHA VISUAL | P1 | PARCIAL | Converger PRs vistas + routers |

---

## 3. Brechas P0 — críticas

| ID | Brecha | Tipo | Capacidades | Evidencia | Pendiente exacto |
|----|--------|------|-------------|-----------|------------------|
| B-P0-01 | Núcleo divergente: central 1250 vs ramas 1260–1360 | PRODUCTO | CT-10, CT-11, CT-12, CT-21, CT-22, MB-09 | `main.py` sin routers comercial/aprendizaje/integraciones | Plan convergencia GENERAL post-1250 |
| B-P0-02 | Modelo comercial no desplegable desde central | COMERCIAL | MB09-01..10, CT-21 | Routers ausentes; rama `comercial-valor-cierre-final-pre-fase2-dec7` | Merge cadena comercial HEAD `1340b1c2d3e4f` |
| B-P0-03 | MFA/SSO/SCIM enterprise | OPERATIVA | CT-05, CT-06 | Solo JWT + `AdminSecurityPage` básica | Portar bloque 1300 |
| B-P0-04 | Conectores integraciones 1330 | INTEGRACIÓN | CT-10, PH-02 | Sin `integraciones` router | Convergencia rama 1330 |

---

## 4. Brechas P1 — alto impacto

| ID | Brecha | Tipo | Capacidades | Pendiente exacto |
|----|--------|------|-------------|------------------|
| B-P1-01 | Aprendizaje 1260 no convergido | FUNCIONAL | MB04-11, CT-16 | Router `aprendizaje` + UI `AprendizajePage` |
| B-P1-02 | Optimización/recomendación 1290 | FUNCIONAL | MB04-12, auditor rediseño | Router `optimizacion` + P1-ID-04 |
| B-P1-03 | Observabilidad/routing LLM 1270 | FUNCIONAL | CT-14 | Servicios `llm_routing_service` en central |
| B-P1-04 | CC sin inteligencia externa | INTEGRACIÓN | MB08-06, CT-20 | `InteligenciaExternaAdapter` |
| B-P1-05 | CC sin comercial/implementación | INTEGRACIÓN | MB08-08, MB-09 | Adaptadores post-convergencia comercial |
| B-P1-06 | Oportunidades externas pipeline incompleto | FUNCIONAL | MB10-02 | Enlace automático 1240→1030 |
| B-P1-07 | Automatizaciones no propuestas desde diagnóstico | FUNCIONAL | MB04-09 | Regla orquestador diagnóstico→automation |
| B-P1-08 | Versionado empleado sin UI rollback | FUNCIONAL | MB06-13, MB06-18 | Pantalla historial versiones |
| B-P1-09 | Capacitación empleados IA | FUNCIONAL | MB06-17, auditor capacitación | Módulo training |
| B-P1-10 | Partners/aliados operativos | FUNCIONAL | MB-03 | TCO 1320 o deprecar legacy |
| B-P1-11 | Gobierno datos 1350 | OPERATIVA | CT-11 | Router `governance` |
| B-P1-12 | Continuidad 1360 | OPERATIVA | CT-12 | Router `continuidad` |

---

## 5. Brechas P2 — integración y experiencia

| ID | Brecha | Tipo | Capacidades | Pendiente exacto |
|----|--------|------|-------------|------------------|
| B-P2-01 | Acciones ejecutivas write desde CC | VISUAL | MB08-05 | Botones aprobar/actuar in-place |
| B-P2-02 | DashboardPage huérfana | VISUAL | — | Eliminar o fusionar con CC |
| B-P2-03 | Hub comunicaciones unificado | VISUAL | MB11-04 | Vista única notif+audit+alertas |
| B-P2-04 | UI reglas alerta limitada | VISUAL | MB11-02 | CRUD visual alert-rules |
| B-P2-05 | Límites/costos empleado en wizard | VISUAL | MB06-10, MB06-11 | Panel FinOps en ficha empleado |
| B-P2-06 | Monitoreo empleado dedicado | VISUAL | MB06-16 | Dashboard por empleado |
| B-P2-07 | Superadmin consola global | VISUAL | CT-03, MB01-04 | Vista cross-tenant |
| B-P2-08 | ROI comercial vs operativo mezclado | COMERCIAL | MB09-05 | Separar dominios valoración |
| B-P2-09 | Sobreconsumo por plan cliente | COMERCIAL | MB09-12 | Políticas empaquetadas |
| B-P2-10 | PH-02 PIIP solo manifiesto | INTEGRACIÓN | PH-02 | Conectores reales post-1330 |
| B-P2-11 | Configurabilidad vertical | FUNCIONAL | CT-24 | Segmentación 1310 |
| B-P2-12 | Bloques 1370/1380 sin especificación código | PRODUCTO | — | Definir o archivar |
| B-P2-13 | Normatividad workflow | FUNCIONAL | auditor normativo | 1240 → acciones |
| B-P2-14 | Enlace automatizaciones en fábrica | INTEGRACIÓN | MB06-09 | Tab automatizaciones en wizard |

---

## 6. Brechas P3 — mejora y deuda

| ID | Brecha | Tipo | Pendiente exacto |
|----|--------|------|------------------|
| B-P3-01 | Multiidioma / multirregión | FUNCIONAL | i18n framework |
| B-P3-02 | PH-01 Citas/agendamiento | PRODUCTO | Mantener fuera núcleo; API puente si cliente |
| B-P3-03 | Partners legacy table | DEUDA TÉCNICA | Deprecar `partners` preservado |
| B-P3-04 | Test 1220 flaky pre-existente | DEUDA TÉCNICA | `test_08_opportunity_and_deduplication` en base puente comercial |
| B-P3-05 | Documentación API deshabilitable prod | OPERATIVA | Ya existe; documentar runbook |
| B-P3-06 | Branding org avanzado | VISUAL | Campos UI org |
| B-P3-07 | Schedulers visibles en UI ops | VISUAL | Panel health schedulers |
| B-P3-08 | Matriz histórica 94 | PRODUCTO | Recuperar de fuente externa o declarar obsoleta |
| B-P3-09 | Bloques demo integral Fase2 | OPERATIVA | Rama `demo-integral-fase2` separada de central |
| B-P3-10 | Duplicidad experience vs aprendizaje | DEUDA TÉCNICA | Refactor post-1260 |
| B-P3-11 | Certificación adversarial ampliada 1260+ | OPERATIVA | Tests post-convergencia |

---

## 7. Brechas por tipo (transversal)

| Tipo | P0 | P1 | P2 | P3 | Total |
|------|----|----|----|----|-------|
| BRECHA FUNCIONAL | 0 | 6 | 4 | 2 | 12 |
| BRECHA DE INTEGRACIÓN | 1 | 3 | 3 | 0 | 7 |
| BRECHA VISUAL | 0 | 0 | 6 | 2 | 8 |
| BRECHA OPERATIVA | 2 | 2 | 0 | 2 | 6 |
| BRECHA COMERCIAL | 1 | 0 | 2 | 0 | 3 |
| BRECHA DE PRODUCTO | 1 | 1 | 1 | 2 | 5 |
| DEUDA TÉCNICA | 0 | 0 | 0 | 3 | 3 |

---

## 8. Ruta hacia 100 % (secuencia recomendada para GENERAL)

> Sin ejecutar convergencia en este análisis. Orden lógico por dependencias detectadas en código.

```
FASE A — Núcleo ya convergido (HECHO ~70%)
  1250: 810C→1250 + CC + 1240

FASE B — Aprendizaje y optimización
  1260 → 1270 → 1290 (+ P1-ID-04)
  Impacto: Arquitecto, CT-14/16, Auditor rediseño

FASE C — Cadena comercial
  1280 → 1320 → 1340 → 1310 (merge 1340b)
  Impacto: MB-09, CT-21/22, CC comercial

FASE D — Integración y gobierno
  1330 → 1350 → 1360 → 1300 (identidad)
  Impacto: CT-05/06/10/11/12, PH-02

FASE E — Cierre producto
  MB-12 mesa ayuda (o PH)
  MB-06 capacitación + auditoría continua empleados
  CC acciones write + adaptadores completos
  Semántica CT-19 unificada
  i18n CT-25
```

**Ganancia estimada por fase (núcleo 87 caps, misma fórmula):**

| Fase | Caps que pasan a IMPLEMENTADO (aprox.) | Producto total estimado |
|------|----------------------------------------|-------------------------|
| Actual | — | 69.8 % |
| B | +8 | ~78 % |
| C | +10 | ~88 % |
| D | +6 | ~94 % |
| E | +5 | ~100 % |

*Estimación basada en reclasificación PREPARADO→IMPLEMENTADO y PARCIAL→IMPLEMENTADO; no sustituye medición post-convergencia.*

---

## 9. Criterios de cierre al 100 %

Una capacidad solo cuenta como cerrada cuando:

1. **Backend** ejecutable en rama producto única (no solo rama certificada)
2. **Frontend** conectado si la capacidad es operativa para usuario final
3. **Tests** focales PASS en CI de la rama convergida
4. **RBAC + multiempresa** validados para la capacidad
5. **Centro de Control** la consume si es ejecutiva/estratégica
6. **Trazabilidad/auditoría** donde aplique CT-04
7. **Sin duplicar** capacidades de productos hijo en núcleo

---

## 10. Nota sobre matriz 94

La matriz histórica de 94 capacidades **no fue localizada**. Las 41 brechas anteriores derivan del inventario de **89 capacidades reales** documentadas en la matriz maestra. Si GENERAL recupera la matriz 94 de fuente externa, mapear cada ítem al ID CAP/MB/CT de esta matriz antes de recalcular porcentajes.

---

**Documento generado por Agente C — solo análisis, sin modificaciones de backend/frontend/migraciones.**
