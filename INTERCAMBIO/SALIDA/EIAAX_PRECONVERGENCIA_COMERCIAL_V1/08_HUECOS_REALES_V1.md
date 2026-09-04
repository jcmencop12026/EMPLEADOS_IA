# 08 — Huecos funcionales V1 reales

Comparación: capacidades del flujo objetivo vs lo que aportan A+B+C+D sobre central `75fc689`.

**Total huecos reales identificados: 12** (3 P0, 5 P1, 4 P2)

---

## P0 — Bloquean convergencia comercial V1

| # | Hueco | Estado en candidatos | Acción GENERAL |
|---|-------|----------------------|----------------|
| **P0-1** | **Unificación publicación** — tres implementaciones (A `EmpresaPublicacion`, D `PresentacionPublicacion`, C selección cockpit) sin contrato único | Parcial en cada rama | Implementar adapter D→A; C solo UI; deprecar tabla D a medio plazo |
| **P0-2** | **Colisión migraciones 1410/1420/1430** — imposible `alembic upgrade` lineal con portado literal | A, C, D | Reconstruir cadena (`06_MIGRACIONES.md`); **14 revisiones** |
| **P0-3** | **`control_center_service` dual** (B extiende comercial; C extiende estratégico/gobierno) | B ∩ C | Una implementación; B consume APIs C o módulo fusionado |

---

## P1 — Degradan flujo o riesgo compliance

| # | Hueco | Rama | Notas |
|---|-------|------|-------|
| **P1-1** | **Suficiencia evidencias → evaluación** — reglas explícitas “suficiente/no suficiente” antes de evaluar | A parcial (validación manual); C evalúa | Regla de negocio única en servicio evaluación |
| **P1-2** | **Economía POTENCIAL vs REAL** en UI prospecto | B/C referencian motor; filtración no probada E2E | Tests de no-filtración + permisos |
| **P1-3** | **Prospecto → cliente** transición con dossier único | B modela; A portal no amarra automático | Evento único post-contrato |
| **P1-4** | **Cuatro audiencias** mismo dossier en presentación | D UI; A audiencias publicación; sin prueba unificada | Una fuente lectura por audiencia |
| **P1-5** | **Implementación post-venta → Empleados IA** | Central tiene EIA; candidatos no enlazan contrato→implementación | Conectar B implementación flag con central |

---

## P2 — V1 aceptable con deuda documentada

| # | Hueco | Notas |
|---|-------|-------|
| **P2-1** | Expansión/renovación comercial automática | Ningún candidato cierra ciclo |
| **P2-2** | Soporte MB-12 desde portal externo | A no expone ticket; central MB-12 separado |
| **P2-3** | Correlation_id end-to-end en todos los routers | Parcial en B/C; no uniforme en A/D |
| **P2-4** | Scheduler informes comerciales | D podría duplicar; debe usar solo MB-11 |

---

## Huecos que NO son reales (ya cubiertos)

| Capacidad | Autoridad |
|-----------|-----------|
| Motor económico base | Central `motor_economico` |
| Informes operativos | MB-11 `communications_service` |
| Resultados / KPIs | Central `resultados` |
| Partners | Central `partners` |
| Gobierno base | Central + extensión C |
| Upload evidencias seguro | A `evidencia_entrega_service` + `knowledge_storage` |

---

## Lista compacta para informe final

**Huecos funcionales V1 reales (12):**

1. P0-1 Publicación triple
2. P0-2 Migraciones colisionantes
3. P0-3 Control center dual
4. P1-1 Suficiencia evidencias
5. P1-2 Economía filtración prospecto
6. P1-3 Prospecto→cliente dossier
7. P1-4 Cuatro audiencias unificadas
8. P1-5 Contrato→implementación→EIA
9. P2-1 Expansión/renovación
10. P2-2 Soporte portal externo
11. P2-3 Correlation_id uniforme
12. P2-4 Scheduler informes paralelo

---

## P0 / P1 / P2 resumen ejecutivo

| Prioridad | Cantidad | IDs |
|-----------|----------|-----|
| **P0** | 3 | P0-1, P0-2, P0-3 |
| **P1** | 5 | P1-1 … P1-5 |
| **P2** | 4 | P2-1 … P2-4 |
