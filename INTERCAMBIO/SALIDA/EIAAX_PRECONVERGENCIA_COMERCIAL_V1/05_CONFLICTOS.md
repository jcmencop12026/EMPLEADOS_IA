# 05 — Conflictos de archivos anticipados

Clasificación: **BAJO** (merge trivial) · **MEDIO** (merge manual cuidadoso) · **ALTO** (decisión arquitectónica previa)

---

## Resumen

| Nivel | Cantidad |
|-------|----------|
| ALTO | 6 |
| MEDIO | 11 |
| BAJO | 8 |

---

## ALTO

| Archivo / área | Ramas | Naturaleza | Mitigación |
|----------------|-------|------------|------------|
| `backend/app/main.py` | A,B,C,D | Registro routers superpuesto | Integrar en un solo bloque por dominio; orden dependencias |
| `backend/app/permissions.py` | A,B,C,D | Sets de permisos disjuntos pero mismo archivo | Merge por secciones; bootstrap único |
| `backend/app/services/control_center_service.py` | B,C | **Implementaciones paralelas** cockpit | Elegir C estratégico + B adapters comerciales; no dos servicios |
| `backend/app/services/control_center_adapters.py` | B,C | Adapters divergentes | Unificar adapters; B aporta negocio, C estratégico |
| `backend/alembic/versions/1410*` | A,C,D | **Misma revisión, distinto contenido** | Renumerar en convergencia; no port literal |
| Publicación (3 modelos) | A,D,C | Autoridades paralelas | Decisión 03 antes de portar D o A |

---

## MEDIO

| Archivo | Ramas | Notas |
|---------|-------|-------|
| `evaluacion_service.py` | A,B,D | Lógica vista entidad, suficiencia, demo — merge 3 vías |
| `evaluacion_models.py` | A,B | Campos validación externa vs comercial |
| `frontend/src/api.ts` | A,B,C,D | ~4000+ líneas; conflictos por sección API |
| `frontend/src/App.tsx` | A,B,C,D | Rutas nuevas cada rama |
| `frontend/src/navigation/menu.ts` | A,B,C,D | Ítems menú |
| `EvaluacionConsolePage.tsx` | A,B,D | Tabs admin + espacio externo |
| `VistaEntidadPreview.tsx` | A,D | Componente compartido con divergencia |
| `migration_ledger.json` | B,C,D | Ledger divergente |
| `economic_motor_models.py` | B vs central | B NEW file; central importa — verificar si stub |
| `gobierno_operacional_service.py` | A vs central | Central tiene router sin servicio completo |
| `communications_service.py` | D | Extensión MB-11 — verificar compatibilidad central |

---

## BAJO

| Archivo | Ramas | Notas |
|---------|-------|-------|
| `evaluacionLabels.ts` | A,D | Labels UI |
| `styles.css` | C,D | Estilos |
| `conftest.py` | A,B,C,D | Imports modelos — acumular todos |
| `audit.py` router | A | Extensión menor |
| `knowledge_storage.py` | A | EVIDENCE_ROOT namespace |
| `employee_lifecycle_service.py` | A,B,C,D | Touch menor en todas |
| `external_intelligence_service.py` | A,B,C,D | Touch menor |
| `tests/*` | cada rama | Aditivos — no conflicto si se portan todos |

---

## Servicios con implementación paralela (riesgo funcional)

| Capacidad | Implementación 1 | Implementación 2 | Veredicto |
|-----------|----------------|------------------|-----------|
| Centro control | B `control_center_*` comercial | C estratégico + MB-08 | **CONECTAR** en un servicio |
| Presentación | B `ComercialPresentacionEjecutiva` | D `presentacion_service` | **CONECTAR** |
| Publicación externa | A `EmpresaPublicacion` | D `PresentacionPublicacion` | **UNIFICAR** → A |
| Informes comerciales | D `InformeComercialConfig` | MB-11 scheduler | **K** D→MB-11 |
| Economía cockpit | B motor 1600 | C strategic_economy | **K** C lee B |

---

## Routers superpuestos (sin duplicar path)

| Router | Rama | Path prefix | Conflicto path |
|--------|------|-------------|----------------|
| `espacio_externo` | A | `/api/espacio-externo` | Ninguno |
| `flujo_comercial` | B | `/api/flujo-comercial` | Ninguno |
| `strategic_control` | C | `/api/strategic-control` | Ninguno |
| `presentacion` | D | `/api/presentacion` | Ninguno |
| `demo_comercial` | D | `/api/demo-comercial` | Ninguno |

**Riesgo bajo en paths** — conflicto es en **servicios compartidos**, no en rutas HTTP.

---

## Permisos duplicados / solapados

| Permiso | Ramas | Acción |
|---------|-------|--------|
| `evaluacion.visibility` | central, D adapter | R |
| `negocio.economy.private` / `strategic_control.economia_privada` | B, C | Unificar naming |
| `resultados.*` | D | R si central no tiene — verificar |
| `espacio_externo.*` | A | P exclusivo A |
