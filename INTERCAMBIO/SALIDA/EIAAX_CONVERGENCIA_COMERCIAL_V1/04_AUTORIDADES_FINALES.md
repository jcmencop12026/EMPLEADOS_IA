# Autoridades finales (una por dominio)

| Dominio | Autoridad canónica | Consumidores / adapters |
|---------|-------------------|-------------------------|
| **Dossier** | `transformacion_service` / `DossierEmpresarial` | Centro Estratégico (lectura `create=False`), flujo comercial, evaluación |
| **Publicación** | `EmpresaPublicacion` (A) | `presentacion_publicacion_adapter` (D), Vista Entidad |
| **Economía** | `motor_economico` | Centro Estratégico economía privada (solo lectura), flujo comercial propuesta |
| **Oportunidades** | `opportunity_models` / servicio oportunidades | Flujo comercial, Centro Estratégico |
| **Resultados** | MB-12 / `resultados` | Demo, presentación, espacio externo adapters |
| **Informes** | MB-11 / `comunicaciones` | `informes_comerciales_adapter` (D) — sin scheduler paralelo |
| **Gobierno/aprobaciones** | `gobierno_operacional` | Sin duplicar en bloques portados |
| **Implementación** | `implementacion` | `espacio_externo_adapters` |
| **Auditoría/trazabilidad** | `audit` central | Todos los servicios portados usan `write_audit` |

## Centros de control

- **MB-08 Operacional:** `control_center` — intacto
- **Centro Estratégico:** `strategic_control` — complementario, no sustituto

## Privacidad

- Vista Entidad y portal externo respetan publicación backend
- Economía privada solo con `strategic_control.economia_privada`
- Sin exposición externa de costos, margen, prompts, notas internas
