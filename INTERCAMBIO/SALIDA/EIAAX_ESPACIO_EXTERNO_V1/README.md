# EIAAX — Espacio Externo Controlado V1 (continuación cliente contratado)

**Rama:** `cursor/espacio-externo-v1-3e3d`  
**SHA base:** `27270f6`  
**Migraciones:** `1430a1b2c3d4e` + `1431a1b2c3d4e`  
**Base:** Seguridad/Gobierno `c433bac` + mapa convergencia `1668dfd`

---

## Qué se reutilizó (sin módulos paralelos)

| Dominio | Servicio/Router existente | Adaptador |
|---------|---------------------------|-----------|
| Vista entidad / resultados | `evaluacion_service.get_vista_entidad` | `adaptar_resultados_externo` |
| Implementación | `implementacion_service.tablero_proyecto` + `detalle_proyecto` | `adaptar_implementacion_externa` |
| Empleados IA | `agent_factory.list_employees` + `get_employee_detail` | `adaptar_empleados_ia_externo` |
| Informes (MB-11) | `communications_service` (`CommMessage`) | `adaptar_informes_externo` |
| Soporte (MB-12) | `support_service.list_cases` / `create_case_manual` / `get_case_detail` | `adaptar_soporte_*` |
| Publicación | `EmpresaPublicacion` estados existentes | Sin segunda autoridad |
| Gobierno visibilidad 4 niveles | `empresa_seguridad` / `gobierno_operacional` | **Dependencia** — no duplicada |

---

## Qué se completó (V1b — cliente contratado)

1. **Migración 1431** — `proyecto_id`, `capacidades_contrato_json`, `audiencia` en publicación
2. **`espacio_externo_adapters.py`** — sanitización backend (economía, secretos, notas internas)
3. **Portal cliente** — `/mi-espacio/implementacion`, `/empleados-ia`, `/informes`, `/soporte`
4. **Gestión interna** — `link-proyecto`, `configure-contrato`, `audiencia` en publicación
5. **Promoción** — capacidades por defecto sin duplicar org/usuario/dossier
6. **Frontend** — pestañas cliente en `EspacioExternoPortalPage`
7. **Tests** — matriz de seguridad ampliada (18/18 PASS)

---

## Visibilidad 4 niveles vs audiencias (aclaración técnica)

| Concepto | Autoridad | Significado |
|----------|-----------|-------------|
| **Gobierno 4 niveles** | `INTERNO_EIAAX` → `VISIBLE_ENTIDAD` → `COMPARTIDO_ESPECIFICO` → `RESTRINGIDO` | Control de datos en Centro de Control / gobierno operacional. **No duplicado** en espacio externo. |
| **Audiencias publicación** | `GERENCIA`, `OPERACION`, `SISTEMAS`, `FINANCIERO` | Alcance sobre **la misma publicación/version** (`EmpresaPublicacion.audiencia`). No crea copias de datos. |

---

## Modelo de acceso efectivo

```
tenant (organization_id)
  + RBAC (espacio_externo.* / external_prospect)
  + EntidadEmpresaAcceso activo
  + EmpresaPublicacion.estado == PUBLICADO_EMPRESA
  + capacidades_contrato_json (IMPLEMENTACION, EMPLEADOS_IA, …)
  + contrato_ref (cliente contratado)
```

---

## Matriz PASS/FAIL

| Criterio | Resultado |
|----------|-----------|
| Prospecto | **PASS** |
| Promoción prospecto→cliente | **PASS** |
| Cliente / Implementación | **PASS** (adaptador `implementacion_service`) |
| Cliente / Empleados IA | **PASS** (adaptador `agent_factory`) |
| Cliente / Resultados | **PASS** |
| Cliente / Informes | **PASS** (adaptador `communications_service`) |
| Cliente / Soporte | **PASS** (adaptador `support_service`) |
| Publicación/versionado | **PASS** |
| Aislamiento tenant | **PASS** |
| Economía privada | **PASS** |
| Revocación | **PASS** |
| Tests | **18 / PASS** |
| Frontend build | **PASS** |

---

## P0 / P1 / P2 reales

| Prioridad | Item | Estado |
|-----------|------|--------|
| **P0** | Publicación obligatoria vista externa | PASS |
| **P0** | Backend impone visibilidad | PASS |
| **P0** | Sin economía privada externa | PASS |
| **P0** | Cliente contratado secciones vía adaptadores | PASS |
| **P1** | Cablear `set_visibilidad_nivel` gobierno en flujo publicación | Dependencia Centro Control |
| **P1** | Adjuntos evidencia (texto + evidencia_ref) | Pendiente |
| **P2** | Email invitación automática | Pendiente |
| **P2** | COMPARTIDO_ESPECIFICO por destinatario granular | Pendiente |

---

## Migración — colisión 1430

**REQUIERE RENUMERACIÓN EN CONVERGENCIA POR GENERAL**

- `1430` colisiona con fábrica MB-06 en otra rama
- `1431` depende de `1430` local — renumerar ambas en merge
- No rebasear ni integrar central desde esta rama

---

## SHA

Ver `SHA.txt` en este directorio.
