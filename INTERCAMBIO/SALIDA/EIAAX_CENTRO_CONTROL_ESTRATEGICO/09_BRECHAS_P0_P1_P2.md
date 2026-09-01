# 09 — Brechas P0 / P1 / P2 y riesgos de integración

## P0 (antes de integrar a rama central)

| ID | Brecha | Notas |
|----|--------|-------|
| P0-1 | Commit dossier en flujos escritura | Cockpit usa `create=False`; Arquitecto debe persistir dossier |
| P0-2 | Economía privada completa | Falta margen, precio sugerido, desglose integraciones en adapter |
| P0-3 | Reconciliación migraciones 1410/1420 | Heredado de base MB-08 |

## P1

| ID | Brecha |
|----|--------|
| P1-1 | Exportación gráficos (CSV/PNG) |
| P1-2 | Drill-down periodo y agrupación |
| P1-3 | Lectura Sistemas — gobernanza con KPI reales |
| P1-4 | Modo comité — vista side-by-side en UI |
| P1-5 | Selector organización SuperAdmin en UI |

## P2

| ID | Brecha |
|----|--------|
| P2-1 | Voz accesibilidad (speechSynthesis) opcional |
| P2-2 | Notificación in-app al publicar dossier |
| P2-3 | Persistencia lectura activa por usuario |

## Riesgos de integración (rama independiente)

| Riesgo | Mitigación |
|--------|------------|
| Confusión MB-08 vs estratégico | Rutas y menú separados; docs frontera |
| Permisos no sembrados en tenants existentes | Seed `STRATEGIC_CONTROL_PERMISSIONS` en admin |
| `get_dossier_completo(create=False)` vs escritura | Parámetro opcional no rompe callers existentes |
| Adapter Continuidad | Fix `len(degradados)` — compatible MB-08 |

## Cerrado V1

- Cockpit 5 lecturas mismo dossier
- API + UI + RBAC + tenant + privacidad economía
- Semántica ANTES/PROYECTADO/REAL
- Separación MB-08 verificada
- Tests + build
