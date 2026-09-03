# 03 — Capacidades existentes (Grupo A)

**Grupo A — YA EXISTE:** preservar y reutilizar.  
**Criterio:** estado VERDE, AMARILLO funcional, o MORADO (operativo con deuda UX no bloqueante).  
**Base:** SHA `b19b04dd438f5b13b422e9a760f54fa074fb52ed`  
**Filas Grupo A:** **109 / 136** (80,1%)

---

## Resumen por macrobloque

| MB | Nombre | Filas A | Dominio |
|---|---|---:|---|
| MB-01 | Control Plataforma | 14/14 | 100% operativo |
| MB-02 | Empresas/Organizaciones | 5/5 | 100% — C2 certificado |
| MB-03 | Partners | 1/4 | Solo TCO aliados (parcial) |
| MB-04 | Arquitecto Transformación | 5/6 | Motor completo; sin UI marca |
| MB-05 | Estudio/Diagnóstico | 8/10 | Motor certificado Fase 2 |
| MB-06 | Fábrica Empleados IA | 7/7 | Certificado + auditor integrado |
| MB-07 | Recursos/Capacidad/Costos | 5/5 | FinOps único + MB-07 |
| MB-08 | Centro Control BI | 6/8 | Certificado C1-R1/C2 |
| MB-09 | Centro Negocios | 6/7 | Tramo 4 certificado |
| MB-10 | Centro Oportunidades | 6/6 | 100% |
| MB-11 | Comunicaciones | 4/4 | Tramo 6D certificado |
| MB-12 | Mesa Ayuda | 4/4 | Tramo 6A certificado |
| TX | Transversal plataforma | 11/16 | RBAC, MT, CC, trabajo |
| ID | Identidad básica | 1/12 | Shell responsive |

---

## Núcleo preservar sin reconstruir

### Plataforma y seguridad
- Auth login hotfix + MFA + SSO + SCIM (parcial)
- RBAC 74+ permisos, deny-by-default
- Multiempresa con aislamiento tenant + SUPERADMIN cross-org (C2)
- Audit log, migration control fail-closed
- Health endpoints

### Operación central certificada
- **Centro de Control** — 6 pestañas, adapters MB-07/11/12, home C1-R1
- **Mi Trabajo** — bandeja única, dedup G2/G3, contexto org C2
- **Fábrica MB-06** — ciclo vida completo, aprobación humana
- **Auditor empleados** — MVP determinístico, integración fábrica/trabajo

### Motores analíticos y de valor (Fase 2)
- Diagnósticos 1220, señales 1120, líneas base 1200
- Valoración 1210, inteligencia externa 1240
- Oportunidades 1100, optimización 1290, aprendizaje 1260
- Comercial 1280, segmentación 1310, TCO 1320, implementación 1340
- FinOps 1110 + planificador MB-07 + multiproveedor 1270

### Integraciones operativas
- Comunicaciones MB-11 (CC + trabajo)
- Mesa ayuda MB-12 (CC + trabajo + SLA)
- Automatizaciones, notificaciones, integraciones conectores
- Gobernanza datos, continuidad, knowledge

---

## Activos técnicos reutilizables

| Activo | Ubicación | Reutilizar para |
|---|---|---|
| `resolve_organization_id` | `control_center_service.py` | Cualquier módulo cross-org futuro |
| `collect_items` + dedup | `trabajo_service.py` | Nuevas fuentes bandeja |
| `control_center_adapters.py` | adapters por módulo | Nuevos KPIs CC sin duplicar |
| `permissions.py` + `ROUTE_PERMISSIONS` | backend + frontend | Nuevas rutas sin matriz divergente |
| `navigation/menu.ts` + `homeRoute.ts` | frontend | Sidebar + home unificados |
| `OrganizationProvider` | C2 | Extender contexto tenant UI |
| 53 migraciones Alembic | `alembic/versions/` | Evolución schema incremental |
| 1280 tests PASS | `tests/` | Regresión continua |

---

## Deuda conocida dentro de Grupo A (no reconstruir)

| Ítem | Estado | Acción |
|---|---|---|
| KPI integraciones CC | AMARILLO P2 | Completar adapter, no rehacer CC |
| SCIM rate limit in-memory | AMARILLO P2 | Endurecer en prod |
| Residual inglés tablas | AMARILLO P2 | Pasada i18n focal |
| Wizard fábrica densidad botones | MORADO P2 | Ajuste UX, no nuevo motor |
| Sidebar largo | MORADO P2 | Norma Visual futura |
| DashboardPage huérfano | NEGRO | Eliminar archivo, no nueva página |

---

## Conclusión Grupo A

El producto integrado **no debe reconstruirse desde cero**. La base Fase 2 + convergencia C1/C2 es sólida, certificada y extensible. Las mejoras pendientes son **incrementales** sobre estos activos.
