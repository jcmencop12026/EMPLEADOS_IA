# EIAAX — Espacio Externo Controlado V1

**Rama:** `cursor/espacio-externo-v1-3e3d`  
**Migración:** `1430a1b2c3d4e_espacio_externo_empresa.py`  
**Base:** Seguridad/Gobierno `c433bac` + mapa convergencia `1668dfd`

---

## Capacidades existentes reutilizadas

| Capacidad | Origen | Uso |
|-----------|--------|-----|
| `EvaluacionExpediente` + información adaptativa | BP1 `1405` | Mismo dossier; sin duplicar |
| `get_vista_entidad` | `evaluacion_service` | Vista filtrada backend |
| `set_visibilidad` + dual-write gobierno | Gobierno operacional | Hallazgos publicables |
| `write_audit` | Auditoría transversal | Acciones espacio externo |
| RBAC `permissions.py` + rol sistema | `840` | Permisos nuevos + `external_prospect` |
| `VistaEntidadPreview` | Patrón BP2 (portado) | UI legible interna y externa |
| `empresa_seguridad` visibilidad 4 niveles | `1420` | Autoridad futura (P1 cableado completo) |

---

## Brechas construidas (V1)

1. **EntidadEmpresa** — prospecto/cliente sobre mismo expediente; promoción sin nueva org
2. **EntidadEmpresaAcceso** — invitación/revocación usuarios externos
3. **EmpresaPublicacion** + historial — estados `PRIVADO` → `PREPARADO_PRESENTAR` → `PUBLICADO_EMPRESA` con versión
4. **EvaluacionEntregaExterna** — flujo solicitud/entrega/validación/suficiencia
5. **Columnas** en `evaluaciones_informacion`: fuente, validación, suficiencia
6. **API** `/api/espacio-externo/*` — gestión interna + portal `/mi-espacio`
7. **Frontend** — `EspacioExternoPortalPage`, admin en consola evaluación, `VistaEntidadPreview`

---

## Modelo de acceso efectivo

```
tenant (organization_id)
  + RBAC (espacio_externo.* / external_prospect)
  + EntidadEmpresaAcceso activo
  + EmpresaPublicacion.estado == PUBLICADO_EMPRESA (para resultados/propuesta)
  + contrato_ref (cliente contratado — secciones ampliadas)
```

---

## Tests

`tests/test_espacio_externo_v1.py` — **9/9 PASS**

- Aislamiento tenant
- Acceso prospecto portal
- Publicación bloquea vista sin publicar
- Vista entidad sin economía privada
- Entrega + validación + suficiencia mínima
- Promoción prospecto → cliente (misma entidad)
- Revocación acceso
- Externo sin FinOps

---

## Build

`npm run build` — PASS

---

## P0 / P1 / P2

| Prioridad | Item |
|-----------|------|
| **P0** | Publicación obligatoria para vista externa — implementado |
| **P0** | Backend impone visibilidad — implementado |
| **P0** | Sin economía privada en vista externa — implementado |
| **P1** | Cablear `set_visibilidad_nivel` 4 niveles en publicación |
| **P1** | Secciones cliente: implementación, empleados IA, informes, soporte (stubs UI) |
| **P1** | Adjuntos/archivos evidencia (ahora texto + evidencia_ref) |
| **P2** | Email invitación automática |
| **P2** | COMPARTIDO_ESPECIFICO por destinatario |

---

## Riesgos de integración (GENERAL)

- Migración `1430` colisiona con fábrica `1430` en rama `2afd673` — renumerar en merge
- Rol `external_prospect` debe sembrarse en todos los entornos (`bootstrap_permissions`)
- Menú "Mi empresa" visible solo con `espacio_externo.portal`
- No integrado con Partners MB-03 (grant adicional futuro)

---

## SHA

Ver `SHA.txt` en este directorio tras commit final.
