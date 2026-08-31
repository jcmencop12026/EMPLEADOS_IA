# EIAAX — MB-03 Partners / Aliados

**Estado:** FINALIZADO  
**Rama:** `cursor/mb03-partners-aliados-dec7`  
**Base BP1:** `7e9abba11f4c4f216142c6c70d662229ffc585bb`  
**SHA final:** ver `SHA.txt` tras commit  
**Migración Alembic:** `1410a1b2c3d4e` (down: `1405a1b2c3d4e`)

## Notificación

**EIAAX — PARTNERS FINALIZADO**

## Contenido

| Documento | Descripción |
|-----------|-------------|
| [ARQUITECTURA.md](./ARQUITECTURA.md) | Capas, componentes y flujos |
| [MODELO.md](./MODELO.md) | Entidades y relaciones |
| [RBAC.md](./RBAC.md) | Permisos y roles partner |
| [AISLAMIENTO.md](./AISLAMIENTO.md) | Multi-partner y multiempresa |
| [RECORRIDO.md](./RECORRIDO.md) | Operaciones de negocio |
| [PRUEBAS.md](./PRUEBAS.md) | Cobertura y comandos |
| [MIGRACIONES.md](./MIGRACIONES.md) | Alembic 1410 |
| [P0_P1_P2.md](./P0_P1_P2.md) | Priorización entregable |

## Alcance entregado

- Entidad Partner con identificación, estado, contacto, relación comercial, vigencia y trazabilidad
- Concesiones explícitas Partner ↔ Organización (revocables)
- Usuarios partner con roles ADMIN / OPERADOR / LECTOR
- API REST `/api/partners/*`
- UI español: listado + detalle con pestañas
- Pruebas unitarias/integración (9 casos MB-03 + regresión BP1)
- Sin marketplace, comisiones, white-label ni PIIAX
