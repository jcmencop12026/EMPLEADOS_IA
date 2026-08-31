# Migraciones

## Revisión 1410a1b2c3d4e

**Archivo:** `backend/alembic/versions/1410a1b2c3d4e_partners_mb03.py`  
**Down revision:** `1405a1b2c3d4e` (BP1 evaluación EIAAX)

### Tablas creadas

1. `partners`
2. `partner_organization_grants`
3. `partner_user_memberships`
4. `partner_audit_events`

### Ledger

`backend/alembic/migration_ledger.json` actualizado:

- `baseline_head`: `1410a1b2c3d4e`
- `protected_revisions` incluye `1410a1b2c3d4e`

### Aplicar

```bash
cd backend && alembic upgrade head
```

En tests SQLite: `Base.metadata.create_all` + bootstrap automático.
