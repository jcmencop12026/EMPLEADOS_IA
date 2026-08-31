# 09 — Comunicaciones (MB-11)

**Rama:** `f32c815` (Centro Información/Comunicaciones + entregas informe)  
**Base común:** `1341` centro_comunicaciones_mb11

---

## Alcance gobernado por Seguridad de Datos

| Actividad | Debe gobernar | Autoridad |
|-----------|---------------|-----------|
| Entrega de informes | Clasificación + visibilidad pre-envío | `empresa_seguridad_service` |
| Mensajes externos | Destinatario + nivel mínimo | `set_visibilidad_nivel` + RBAC |
| Adjuntos | Mismo objeto que mensaje | Evidencia vínculo |
| Versiones compartidas | Historial visibilidad | `gobierno_visibilidad_log` |
| Destinatarios | COMPARTIDO_ESPECIFICO | Log con motivo y versión |

---

## Principio: validación única, no duplicada

```
                    ┌─────────────────────────────┐
                    │ empresa_seguridad_service    │
                    │  - puede_compartir(objeto)   │
                    │  - filtrar_campos(dto)       │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
      Comunicaciones          Vista entidad         Partners
      (envío informe)         (render)              (scope limitado)
```

Los canales (email, in-app, webhook) **no reimplementan** reglas de privacidad: llaman gate transversal.

---

## Integración con Resultados (`af0e8cd` / `f32c815`)

Migración `1420_centro_informacion_entregas_1420` en rama comunicaciones — **colisiona** con `1420_empresa_seguridad` (ver doc 10).

Flujo deseado:
1. Informe resultados pasa a estado "listo para entrega"
2. Clasificación y visibilidad asignadas (mínimo `VISIBLE_ENTIDAD` para externo)
3. Aprobación humana si contiene datos sensibles (gobierno)
4. Comunicaciones crea entrega con `correlation_id` del informe
5. Adjuntos referencian evidencia, no copian sin vínculo

---

## Conflictos

### C-01 — Validación privacidad en cada canal

| Campo | Valor |
|-------|-------|
| **ORIGEN** | MB-11 implementación por canal |
| **COMPONENTES** | Routers comunicaciones, plantillas, notificaciones 820 |
| **AUTORIDAD** | Gate único seguridad |
| **CONSERVAR** | Preferencias, plantillas, idempotencia 820 |
| **ADAPTAR** | Pre-hook `puede_compartir` antes de `publish` |
| **RETIRAR** | Filtros ad-hoc por tipo mensaje |
| **RIESGO** | Email bypass más permisivo que in-app |

### C-02 — Informe sin aprobación

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Entregas automáticas al generar informe |
| **COMPONENTES** | Resultados + comunicaciones |
| **AUTORIDAD** | Gobierno PROPUESTA/EJECUCIÓN según política |
| **CONSERVAR** | Borrador interno automático |
| **ADAPTAR** | Envío externo requiere aprobación |
| **RETIRAR** | `enviar_al_publicar=true` por defecto |
| **RIESGO** | Informe con INTERNO_EIAAX al cliente |

### C-03 — Adjuntos sin clasificación

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Archivos subidos a comunicación |
| **COMPONENTES** | Storage, adjuntos |
| **AUTORIDAD** | `asignar_clasificacion` al subir |
| **CONSERVAR** | Storage |
| **ADAPTAR** | Objeto clasificable tipo ADJUNTO/COMUNICACION |
| **RETIRAR** | Adjunto sin registro transversal |
| **RIESGO** | PDF económico adjunto sin strip |

### C-04 — Notificaciones 820 vs gobierno

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Sistema alertas legacy |
| **COMPONENTES** | notifications 820, comunicaciones |
| **AUTORIDAD** | Notificación respeta visibilidad del recurso referenciado |
| **CONSERVAR** | Bus eventos |
| **ADAPTAR** | Payload notification sin campos private |
| **RETIRAR** | Detalle completo en push externo |
| **RIESGO** | Push móvil con dato RESTRINGIDO |

---

## Destinatarios y COMPARTIDO_ESPECIFICO

Registrar en `gobierno_visibilidad_log`:
- `nivel_visibilidad = COMPARTIDO_ESPECIFICO`
- `motivo` = destinatario(s)
- `version` = versión informe/mensaje
- `correlation_id` = hilo expediente

Revocación: nuevo log con nivel más restrictivo; comunicaciones no reenvía versiones antiguas.

---

## RBAC comunicaciones

Permisos esperados (verificar en merge `permissions.py`):
- Lectura centro comunicaciones
- Envío externo (rol elevado)
- Administración plantillas

Partners: **sin** permiso envío externo salvo grant explícito futuro y nunca INTERNO.

---

## GENERAL — orden integración

1. Resolver migración 1420 entregas (renumerar)
2. Implementar gate `puede_compartir` en servicio comunicaciones
3. Cablear entregas informe → resultados con correlation_id
4. Tests: informe RESTRINGIDO → envío bloqueado
5. Tests: informe VISIBLE_ENTIDAD → envío OK sin campos economía
