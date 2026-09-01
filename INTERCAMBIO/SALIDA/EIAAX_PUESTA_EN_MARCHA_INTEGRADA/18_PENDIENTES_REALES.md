# Pendientes reales

| ID | P | Descripción |
|----|---|-------------|
| PG-01 | P2 | Upgrade PostgreSQL aislado 1600→1770 (procedimiento en `02_POSTGRESQL.md`) |
| UI-01 | P2 | Estilos CSS tema oscuro (`data-theme="dark"`) |
| REC-A | P2 | Recorrido comercial UI completo hasta PDF/contrato/go-live (semilla parcial; API validada) |
| CAP-01 | P2 | Capturas tema oscuro y sidebar colapsado |

## Cerrado (P0/P1 = 0)

- Backend y frontend arrancan
- 178 tests PASS (170 regresión + 8 journeys)
- Multiempresa API PASS
- Gobierno Operacional efectivo en tests
- Economía privada protegida (viewer)
- EIAAX sin PIIAX
- Un solo Alembic head

## ¿Listo para prueba humana integrada?

**SÍ** — con semilla demo y guía `COMO_PROBAR_EIAAX_INTEGRADO.md`.  
PostgreSQL real y tema oscuro quedan como validación posterior (P2).
