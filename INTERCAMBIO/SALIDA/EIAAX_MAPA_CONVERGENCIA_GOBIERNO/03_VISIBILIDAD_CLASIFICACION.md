# 03 — Visibilidad y clasificación

**Autoridad visibilidad:** `empresa_seguridad_service.set_visibilidad_nivel`  
**Autoridad clasificación:** `empresa_seguridad_service.asignar_clasificacion`

---

## Niveles canónicos

| Código | Uso |
|--------|-----|
| `INTERNO_EIAAX` | Operación, costos, notas analista, borradores |
| `VISIBLE_ENTIDAD` | Vista entidad, informes aprobados para cliente |
| `COMPARTIDO_ESPECIFICO` | Destinatario explícito (partner, área, email) |
| `RESTRINGIDO` | Mínimo privilegio; requiere RBAC + clasificación |

Registro: `gobierno_visibilidad_log` (migración `1420` en rama Seguridad).

---

## Comparativa por rama

| Fuente | SHA | Mecanismo | Alineación |
|--------|-----|-----------|------------|
| BP1 `visible_entidad` | `7e9abba`+ | Flag booleano + `EvaluacionVisibilidadLog` | Dual-write a gobierno en `c433bac` ✓ |
| Gobierno Operacional | `c433bac` | `set_visibilidad_general` → log | Canónico intermedio |
| Gobierno de Datos | `c433bac` | `set_visibilidad_nivel` 4 niveles | **Canónico final** |
| Gobierno 1350 | base | `GovClassificationLevel`, retención | Catálogo clasificación |
| Inteligencia Resultados | `af0e8cd` | Campos visibilidad en informes/indicadores | Revisar — posible flag local |
| Comunicaciones | `f32c815` | Entregas informe, canales, adjuntos | Debe consultar gobierno antes de envío |
| Vista Entidad | `ee57fab` | `VistaEntidadView.tsx` filtra por `visible_entidad` | Adaptar a 4 niveles |
| Centro Negocios | `fbfd6a2` | PDF propuesta, economía privada | Strip según nivel + permiso |

---

## Conflictos

### V-01 — Boolean vs 4 niveles

| Campo | Valor |
|-------|-------|
| **ORIGEN** | BP1 histórico `visible_entidad: bool` |
| **COMPONENTES** | `evaluacion_service.set_visibilidad`, `evaluacion_models`, frontend evaluación |
| **AUTORIDAD** | 4 niveles en `gobierno_visibilidad_log` |
| **CONSERVAR** | Flag BP1 como derivado: `visible_entidad = nivel in (VISIBLE_ENTIDAD, COMPARTIDO_ESPECIFICO)` |
| **ADAPTAR** | `set_visibilidad` ya dual-write en `c433bac` — extender a todos los dominios |
| **RETIRAR** | APIs que expongan hallazgo solo por flag sin consultar log |
| **RIESGO** | Filtrado frontend insuficiente; fuga RESTRINGIDO |

### V-02 — Resultados sin gobierno

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `af0e8cd` / `f32c815` |
| **COMPONENTES** | `resultados_*` services, entregas informe |
| **AUTORIDAD** | `set_visibilidad_nivel` antes de publicar informe |
| **CONSERVAR** | Modelos resultados |
| **ADAPTAR** | Pipeline publicación llama seguridad |
| **RETIRAR** | `publicado=true` sin nivel |
| **RIESGO** | Informe impacto con datos internos |

### V-03 — Comunicaciones bypass

| Campo | Valor |
|-------|-------|
| **ORIGEN** | MB-11 entregas y notificaciones |
| **COMPONENTES** | Routers comunicaciones, plantillas, adjuntos |
| **AUTORIDAD** | Gobierno datos — validar clasificación+visibilidad pre-envío |
| **CONSERVAR** | Canal, plantilla, preferencias |
| **ADAPTAR** | Gate único: `empresa_seguridad_service` valida objeto |
| **RETIRAR** | Validación duplicada inconsistente en cada canal |
| **RIESGO** | Email externo con adjunto RESTRINGIDO |

### V-04 — Clasificación sin objeto transversal

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Dominios con campo texto `clasificacion` |
| **COMPONENTES** | `GovCatalogEntry`, `empresa_objeto_clasificacion` |
| **AUTORIDAD** | `asignar_clasificacion` |
| **CONSERVAR** | Catálogo 1350 |
| **ADAPTAR** | Todo objeto clasificable usa `TIPOS_OBJETO_CLASIFICABLE` |
| **RETIRAR** | Clasificación huérfana |
| **RIESGO** | Política retención no aplicada |

---

## Rutas/API con riesgo de bypass

| Ruta / patrón | Rama | Riesgo | Mitigación |
|---------------|------|--------|------------|
| `GET /api/evaluaciones/*/hallazgos` sin filtro nivel | BP1/BP2 | Medio | Filtrar por visibilidad+log |
| `GET /api/evaluaciones/vista-entidad/*` | BP2 | Alto | Solo `VISIBLE_ENTIDAD`+; nunca INTERNO |
| `GET /api/negocio/propuestas/*/pdf` | CN | Alto | Strip economía + respetar clasificación |
| `POST /api/comunicaciones/enviar` | MB-11 | Alto | Pre-check gobierno |
| `GET /api/resultados/informes/*` | Resultados | Medio | RBAC + visibilidad |
| `GET /api/gobierno-operacional/visibilidad` | Gobierno | Bajo | Legacy enriquecido; preferir empresa-seguridad |
| Queries sin `organization_id` | Varias | Crítico | DENY — multitenant |

---

## Clasificación — alias y compatibilidad

- `PUBLICA` → `PUBLICO` (alias en `CLASIFICACION_ALIASES`)
- Objetos mínimos: expediente, hallazgo, informe, propuesta, empleado_ia, evidencia
- Partners: grant **no** sustituye clasificación; objeto RESTRINGIDO sigue bloqueado aunque haya grant

---

## Diagrama de flujo deseado

```
Dominio quiere publicar/compartir
        │
        ▼
asignar_clasificacion (si nuevo o cambio)
        │
        ▼
set_visibilidad_nivel (4 niveles + motivo + correlation_id)
        │
        ▼
gobierno_visibilidad_log + write_audit
        │
        ▼
Consumidor (vista entidad, CN PDF, comunicación) lee nivel + RBAC
```
