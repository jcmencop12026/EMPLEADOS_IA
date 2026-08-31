# EIAAX — Gobierno Operacional

**Agente:** A  
**Tipo:** DESARROLLO  
**SHA inicial (BP1):** `7e9abba11f4c4f216142c6c70d662229ffc585bb`  
**SHA final:** _(ver commit de esta rama)_  
**Rama:** `cursor/gobierno-operacional-eiaax-3e3d`  
**Migración:** `1410a1b2c3d4e`

---

## Veredicto

**EIAAX — GOBIERNO OPERACIONAL FINALIZADO**

Gobierno operacional coherente implementado reutilizando RBAC, auditoría (`write_audit`), aprobaciones (`ApprovalRequest` / `coordinator.decide_approval`) y patrón de visibilidad BP1 (`EvaluacionVisibilidadLog`), sin reconstruir gateway IA ni tocar rama central.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    API /api/gobierno-operacional            │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Acciones     │ Aprobaciones │ Visibilidad  │ Gobierno IA    │
│ LECTURA      │ SOLICITADA   │ dominio gen. │ políticas/org  │
│ ANÁLISIS     │ → PENDIENTE  │ log unificado│ verificación   │
│ PROPUESTA    │ → APROBADA   │              │                │
│ EJECUCIÓN    │ → EJECUTADA  │              │                │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬───────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
 gobierno_accion_*  ApprovalRequest  gobierno_vis_*  gobierno_ia_*
 gobierno_eventos   (operaciones)    + BP1 log       policies
       │              │              │                │
       └──────────────┴──────────────┴────────────────┘
                          │
                    write_audit / AuditLog
                          │
                   Centro de Confianza (solo evidencia real)
```

### Componentes nuevos

| Archivo | Rol |
|---------|-----|
| `gobierno_operacional_models.py` | 5 tablas: políticas, solicitudes, visibilidad, IA, eventos |
| `services/gobierno_operacional_service.py` | Lógica de negocio y Centro de Confianza |
| `routers/gobierno_operacional.py` | API REST con RBAC backend (no frontend como autoridad) |
| `schemas_gobierno_operacional.py` | Contratos Pydantic |
| `1410a1b2c3d4e_gobierno_operacional_eiaax.py` | Migración Alembic |
| `CentroConfianzaPage.tsx` | Vista compacta frontend |

### Reutilización obligatoria

- **RBAC:** `permissions.py` + `check_permission` — permisos `gobierno.*`
- **Auditoría:** `write_audit()` en cada evento de gobierno
- **Aprobaciones legacy:** `ApprovalRequest` referenciado en Centro de Confianza
- **Visibilidad BP1:** `evaluacion_service.set_visibilidad` hace dual-write a `gobierno_visibilidad_log`
- **IA:** políticas por org sin tocar `llm_routing_service` / gateway

---

## Modelo de acción

| Tipo | Aprobación humana (default) | Auto-ejecutar |
|------|----------------------------|---------------|
| LECTURA | No | Sí |
| ANÁLISIS | No | Sí |
| PROPUESTA | Sí | No |
| EJECUCIÓN | Sí | No |

Políticas configurables por organización, rol, recurso, criticidad, empleado IA y capacidad externa.

---

## Flujo de aprobaciones

```
SOLICITADA → PENDIENTE → APROBADA/RECHAZADA → EJECUTADA/FALLIDA/CANCELADA
```

Registro: solicitante, aprobador/rechazador, payload autorizado, timestamps, motivo, `correlation_id`, resultado.

---

## Permisos nuevos

| Código | Descripción |
|--------|-------------|
| `gobierno.view` | Consultar políticas y solicitudes |
| `gobierno.manage` | Gestionar políticas de acción |
| `gobierno.execute` | Solicitar acciones |
| `gobierno.approve` | Aprobar/rechazar solicitudes |
| `gobierno.visibility` | Cambiar visibilidad generalizada |
| `gobierno.ia_policy` | Gestionar políticas IA |
| `gobierno.audit` | Ver eventos de trazabilidad |
| `gobierno.confianza.view` | Centro de Confianza |

---

## API principal

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/api/gobierno-operacional/confianza` | `gobierno.confianza.view` |
| POST | `/api/gobierno-operacional/acciones/evaluar` | `gobierno.view` |
| GET/POST | `/api/gobierno-operacional/politicas` | view/manage |
| GET/POST | `/api/gobierno-operacional/solicitudes` | view/execute |
| POST | `/api/gobierno-operacional/solicitudes/{id}/decidir` | `gobierno.approve` |
| GET/POST | `/api/gobierno-operacional/visibilidad` | view/visibility |
| GET/POST | `/api/gobierno-operacional/ia/politicas` | `gobierno.ia_policy` |
| POST | `/api/gobierno-operacional/ia/verificar` | `gobierno.view` |
| GET | `/api/gobierno-operacional/eventos` | `gobierno.audit` |

---

## Centro de Confianza

Muestra **solo** controles con evidencia real:

- Aislamiento multitenant (organización activa)
- RBAC (roles con permisos)
- Auditoría (eventos `audit_logs`)
- Políticas de acción
- Aprobaciones (gobierno + operaciones)
- Gobierno IA
- Proveedores/modelos (si configurados)
- Visibilidad (si hay cambios registrados)

**No** muestra certificaciones ficticias ni controles sin evidencia.

Ruta UI: `/centro-confianza`

---

## Recorrido runtime representativo

1. Login admin → `POST /api/gobierno-operacional/acciones/evaluar` tipo `EJECUCION` → requiere aprobación
2. `POST /api/gobierno-operacional/solicitudes` → estado `PENDIENTE`
3. `POST .../decidir` approve → estado `EJECUTADA` + evento trazabilidad
4. `GET /api/gobierno-operacional/confianza` → controles con evidencia
5. Evaluación BP1: `PATCH visibilidad` → dual-write BP1 + gobierno
6. Cross-tenant: org B no puede decidir solicitud de org A → 404

---

## Pruebas

Archivo: `tests/test_gobierno_operacional.py`

| Test | Cobertura |
|------|-----------|
| `test_evaluar_accion_tipos` | Clasificación LECTURA/PROPUESTA/EJECUCIÓN |
| `test_flujo_aprobacion_completo` | PENDIENTE → EJECUTADA |
| `test_lectura_auto_ejecuta_sin_aprobacion` | Auto-aprobación LECTURA |
| `test_visibilidad_generalizada` | Dominio hallazgo |
| `test_ia_policy_verificar` | Política IA base |
| `test_centro_confianza_solo_evidencia_real` | Sin controles ficticios |
| `test_cross_tenant_solicitud_denied` | Aislamiento 2 orgs |
| `test_permiso_insuficiente_denegado` | Viewer sin execute → 403 |
| `test_eventos_trazabilidad` | actor/acción/correlation_id |
| `test_tipo_accion_invalido_rechazado` | Validación 422 |

Regresión BP1: `tests/test_bloque_producto_1_evaluacion.py` — **PASS**

Ejecutar:
```bash
pytest tests/test_gobierno_operacional.py tests/test_bloque_producto_1_evaluacion.py -q
```

---

## P0 / P1 / P2

| ID | Severidad | Descripción | Estado |
|----|-----------|-------------|--------|
| — | — | Sin hallazgos P0 | — |
| P1-01 | P1 | Integración profunda con `coordinator.decide_approval` para solicitudes gobierno vía `approval_request_id` | Pendiente GENERAL |
| P1-02 | P1 | Políticas IA con lista cerrada de proveedores desde `llm_models` | Mejora incremental |
| P2-01 | P2 | Extender visibilidad a indicadores/informes/planes sin dominio evaluación | Diseñado, API lista |
| P2-02 | P2 | Notificación voz Centro de Confianza | No bloqueante |

---

## Restricciones respetadas

- NO PIIAX, Partners, FinOps nuevo, rediseño visual global
- NO duplicar BP2 de GENERAL
- NO merge rama central
- NO reconstruir gateway IA

---

## Integración posterior (GENERAL)

1. Merge `cursor/gobierno-operacional-eiaax-3e3d` → rama de integración
2. Ejecutar `alembic upgrade head` en entornos destino
3. Verificar permisos bootstrap en orgs existentes (`bootstrap_permissions`)
4. Opcional: enlazar solicitudes gobierno con bandeja `/aprobaciones` unificada
