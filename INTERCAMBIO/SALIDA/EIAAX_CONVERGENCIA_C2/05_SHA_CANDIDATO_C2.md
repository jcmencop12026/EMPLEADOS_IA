# 05 — SHA Candidato C2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Rama:** `cursor/eiaax-convergencia-v1-v2`  
**Fecha UTC:** 2026-08-31

---

## SHA

| Referencia | SHA |
|---|---|
| **SHA inicial C2** (C1-R1 certificado) | `3226ba5ee9b998547c7026c98b69972dfacd2d3d` |
| **SHA candidato C2** (único) | `afce8c34229addb2fdd0fce5b8c99b800e4f29d7` |
| V1 certificado (intacto) | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| V2 certificado (intacto) | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| Tag Fase 2 (intacto) | `fase2-candidato-final-certificado` → `dc1e6cd` |

---

## Delta C2

```
3226ba5e — fix(c1-r1): fallback determinístico ruta inicial /     [base certificada]
→ afce8c34 — feat(c2): gobierno multiempresa CC + Mi Trabajo       [candidato]
```

---

## Regresión completa

```
pytest tests/  →  1280 passed, 4 skipped, 0 failed
npm run build  →  PASS
alembic heads  →  1341a1b2c3d4e (head único)
```

---

## Referencias certificadas intactas

- V1 `e8cb853` — sin modificación
- V2 `dc1e6cd` — sin modificación
- Tag `fase2-candidato-final-certificado` — sin modificación
- Migraciones — sin cambios
- Permisos RBAC — sin cambios de catálogo

---

## Veredicto

**C2 APTO PARA CERTIFICACIÓN**
