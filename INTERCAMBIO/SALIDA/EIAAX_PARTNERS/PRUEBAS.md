# Pruebas — MB-03 Partners

## Comando

```bash
python3 -m pytest tests/test_mb03_partners.py -q
python3 -m pytest tests/test_bloque_producto_1_evaluacion.py -q  # regresión BP1
cd frontend && npm run build
```

## Casos MB-03 (9)

| Test | Verifica |
|------|----------|
| test_mb03_crear_y_activar_partner | CRUD básico |
| test_mb03_asociar_organizacion_y_auditar | Grant + auditoría |
| test_mb03_aislamiento_partner_a_no_accede_org_de_partner_b | Aislamiento A/B |
| test_mb03_sin_grant_no_accede | Deny sin grant |
| test_mb03_revocacion_efectiva | Revocación |
| test_mb03_manipulacion_api_partner_id_incorrecto | Anti-tampering |
| test_mb03_rbac_sin_permiso_manage | RBAC plataforma |
| test_mb03_asignar_usuario_y_listar | Membresías |
| test_mb03_recorrido_e2e_operativo | Flujo completo |

## Datos de prueba

- Mínimo 2 partners (Alpha/Beta, A/B aislamiento, E2E)
- Varias organizaciones por escenario
- Usuarios con `role=viewer` (sin permisos plataforma partners)

## Resultado esperado

17 tests passed (9 MB-03 + 8 BP1 evaluación) en ejecución de regresión conjunta.
