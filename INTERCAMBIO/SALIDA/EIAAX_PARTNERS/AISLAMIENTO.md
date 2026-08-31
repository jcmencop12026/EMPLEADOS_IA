# Aislamiento multi-partner

## Garantías implementadas

1. **Partner A ≠ Partner B** — concesiones atadas a `partner_id`; grant de B no visible desde contexto de A
2. **Sin grant → 403** — `assert_org_grant` exige grant ACTIVO y scope en `alcance_json`
3. **Revocación efectiva** — estado REVOCADO invalida acceso inmediatamente
4. **Membresía obligatoria** — usuarios partner (sin `partners.manage`) deben ser miembros activos del partner consultado
5. **Manipulación API** — revocar grant con `partner_id` incorrecto → 404

## Separación del aislamiento multitenant certificado

- Las organizaciones siguen aisladas por `organization_id` en el modelo tenant
- Partners **no** obtienen acceso transversal: solo organizaciones en `partner_organization_grants`
- El contexto partner (`get_org_context_for_partner`) no expone datos de otras orgs
- BP1 evaluación y multitenant existente no modificados

## Pruebas de aislamiento

Ver `tests/test_mb03_partners.py`:

- `test_mb03_aislamiento_partner_a_no_accede_org_de_partner_b`
- `test_mb03_sin_grant_no_accede`
- `test_mb03_revocacion_efectiva`
- `test_mb03_manipulacion_api_partner_id_incorrecto`
