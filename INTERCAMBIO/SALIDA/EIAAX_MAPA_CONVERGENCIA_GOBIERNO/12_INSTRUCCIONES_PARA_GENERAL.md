# 12 — Instrucciones para GENERAL

**Misión Agente A:** análisis solo lectura — **completada**  
**Entrega:** `INTERCAMBIO/SALIDA/EIAAX_MAPA_CONVERGENCIA_GOBIERNO/` (12 documentos)  
**Referencia:** Seguridad/Gobierno `c433bac`  
**Rama documentación:** `cursor/mapa-convergencia-gobierno-3e3d`

---

## Objetivo GENERAL

Integrar ramas sin crear:
- dos sistemas de aprobaciones
- dos sistemas de visibilidad
- permisos contradictorios
- clasificación duplicada
- exposición economía privada
- bypass multiempresa
- proveedores IA duplicados
- trazabilidad fragmentada

---

## Fase 0 — Preparación

1. Fetch todas las ramas/SHAs listados en doc 01
2. Crear rama integración desde `c433bac` (gobierno+seguridad como base transversal)
3. **No** merge naive — resolver migraciones primero (doc 10)

---

## Fase 1 — Migraciones (P0)

1. Conservar `1410_gobierno_operacional` y `1420_empresa_seguridad` como primeros hijos de `1405`
2. Renumerar revision IDs conflictivos:

| Original | Rama | Acción |
|----------|------|--------|
| `1410_partners` | 2afd673 | Nuevo ID único, down=1410 gobierno o merge intermedio |
| `1410_resultados` | af0e8cd | Nuevo ID único |
| `1410_piiax` | ee57fab | Nuevo ID único |
| `1420_arquitecto` | 2afd673 | Nuevo ID, después partners |
| `1420_motor_eval` | ee57fab | Nuevo ID, después piiax 1410 |
| `1420_entregas` | f32c815 | Nuevo ID, después resultados |
| `1430_fabrica` | 2afd673 | Nuevo ID, después arquitecto |
| `1600/1700/1710` | fbfd6a2 | Después cadena 14xx estabilizada |

3. `alembic merge` si múltiples heads temporales
4. Validar `upgrade head` en PostgreSQL limpio

---

## Fase 2 — Autoridades canónicas (P0)

Implementar/adaptar según doc 01:

| Dominio | Acción |
|---------|--------|
| Aprobaciones | Extraer/usar motor único; CN adapter → gobierno |
| Visibilidad | Todos los dominios vía `set_visibilidad_nivel` |
| Clasificación | `asignar_clasificacion` en objetos nuevos |
| RBAC | Merge `permissions.py` superset |
| IA | Un catálogo LLM; PIIAX como adapter |
| Economía | DTOs internal/entity; strip PDF |
| Trazabilidad | Propagar `correlation_id` |

---

## Fase 3 — Merge por oleadas

### Oleada 1 — Base transversal (ya en c433bac)
- Gobierno operacional + empresa seguridad
- Tests: `test_gobierno_operacional`, `test_empresa_seguridad_gobierno_datos`

### Oleada 2 — Partners + Arquitecto + Fábrica (`2afd673`)
- Merge `partner_*`, `transformacion_*`, `factory_bridge_service`
- Resolver `permissions.py`, `main.py`
- Renumerar migraciones aplicadas en oleada 1
- Tests: `test_mb03_partners`, `test_fabrica_mb06_bridge`

### Oleada 3 — Resultados + Comunicaciones (`af0e8cd` + `f32c815`)
- Tablas resultados + entregas
- Gate comunicaciones → seguridad
- Tests MB-11 / resultados

### Oleada 4 — BP2 (`ee57fab`)
- Motor siguiente acción, PIIAX prep
- Vista entidad con filtros visibilidad
- Integración gobierno evaluación (`evaluacion_integracion_gobierno`)
- Tests BP2

### Oleada 5 — Centro Negocios (`fbfd6a2`)
- Motor 1600 + CN 1700/1710
- Reemplazar `LocalNegocioApprovalAdapter`
- Economía privada tests
- Tests CN

---

## Fase 4 — Adaptadores específicos

| Adaptador | Disposición |
|-----------|-------------|
| `LocalNegocioApprovalAdapter` | REEMPLAZAR por gobierno |
| `EmployeeFactoryApproval` | CONSERVAR |
| `ApprovalPort` | CONSERVAR contrato |
| `ProveedorExternoAdapter` | CONSERVAR |
| `evaluacion_service.set_visibilidad` | CONSERVAR dual-write |
| BP2 stubs PIIAX | CONSERVAR hasta PIIAX real |

---

## Fase 5 — Verificación

Ejecutar matriz doc 11:
- Migraciones single head
- Tests seguridad + gobierno + dominio
- Tests adversarial: tenant, partner, visibilidad, economía
- Frontend build
- Recorrido manual: expediente → aprobación → vista entidad → informe

---

## Archivos críticos merge manual

```
backend/app/main.py
backend/app/permissions.py
backend/app/services/evaluacion_service.py
backend/app/services/coordinator.py
backend/app/services/gobierno_operacional_service.py
backend/app/services/empresa_seguridad_service.py
frontend/src/App.tsx
frontend/src/api.ts
frontend/src/auth/permissions.ts
frontend/src/navigation/menu.ts
tests/conftest.py
```

---

## Qué NO hacer

- No crear tercer catálogo proveedores IA
- No dejar `NegocioApprovalRecord` como autoridad global
- No merge migraciones sin renumerar 1410/1420
- No exponer `private_economy` en APIs públicas
- No permitir partner access solo por asociación
- No implementar P1 BP2 (`catalogo_proveedores_ref`) en misma PR si retrasa P0

---

## Referencia rápida documentos

| # | Tema |
|---|------|
| 01 | Autoridades canónicas |
| 02 | Aprobaciones |
| 03 | Visibilidad y clasificación |
| 04 | RBAC, multiempresa, partners |
| 05 | Economía privada |
| 06 | IA y proveedores |
| 07 | Trazabilidad y evidencia |
| 08 | Empleados IA |
| 09 | Comunicaciones |
| 10 | Migraciones colisiones |
| 11 | Riesgos integración |
| 12 | Este documento |

---

## Contacto / handoff

- Agente A no implementa código ni migraciones
- Dudas de autoridad: priorizar capa `empresa_seguridad` + `gobierno_operacional` sobre dominio
- Colisiones no listadas: aplicar mismo patrón renumerar + adaptador

**Estado:** listo para convergencia GENERAL
