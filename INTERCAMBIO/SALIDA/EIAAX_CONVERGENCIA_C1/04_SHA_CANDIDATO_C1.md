# 04 — SHA candidato Bloque C1

**Rama:** `cursor/eiaax-convergencia-v1-v2`
**Fecha UTC:** 2026-08-31

---

## SHA

| Referencia | SHA |
|---|---|
| **SHA inicial C1** | `1dcc6569b9cc8511d07aa6dd9fb770b3b875e2ce` |
| **SHA candidato C1** | `d3e4e158d98321a1aad1706d68f98714881d7395` |

> Nota: reemplazar línea anterior con `git rev-parse HEAD` tras pull.

---

## Referencias certificadas (INTACTAS)

| Referencia | SHA | Modificado |
|---|---|---|
| V1 certificado | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` | **NO** |
| V2 certificado | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` | **NO** |
| Tag `fase2-candidato-final-certificado` | `dc1e6cd` | **NO** |

---

## Hotfix integrado

| Referencia | Método |
|---|---|
| `1a855325d67921b5d53c015605741d94a3eab32b` | Integración **selectiva** (no cherry-pick completo) |

---

## Alembic

| Campo | Valor |
|---|---|
| Head único esperado | `1341a1b2c3d4e` |
| Migraciones alteradas en C1 | 0 |

---

## Verificación rápida

```bash
git fetch origin cursor/eiaax-convergencia-v1-v2
git rev-parse origin/cursor/eiaax-convergencia-v1-v2
git rev-parse e8cb853a2c447fd5e136a0907e44d68ce2c8cf81
git rev-parse dc1e6cda8d3de6695d9a052a2a13afdb5f431077
python3 -m pytest tests/test_v1_hotfix_login.py tests/test_convergencia_c1.py -q
```

---

## VEREDICTO C1

**C1 APTO PARA CERTIFICACIÓN** (pendiente validación PostgreSQL real — Agente B)
