# 03 — SHA Candidato C1-R1

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Rama:** `cursor/eiaax-convergencia-v1-v2`  
**Fecha UTC:** 2026-08-31

---

## SHA

| Referencia | SHA |
|---|---|
| **SHA inicial C1-R1** (C1 certificado pre-corrección UX) | `25ad1021ee6ea0322aceb0622252e7b748706d32` |
| **SHA candidato C1-R1** (único, post P1-D-UX-01) | `c3e5aa0f39eaf53fc6033cac08bcfe6b850d9f2e` |
| V1 certificado (intacto) | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| V2 certificado (intacto) | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| Tag Fase 2 (intacto) | `fase2-candidato-final-certificado` → `dc1e6cd` |

---

## Commits en el delta C1-R1

```
25ad1021 — feat(c1): base segura convergencia V1+V2 con hotfix login selectivo  [SHA inicial]
→ c3e5aa0f — fix(c1-r1): fallback determinístico ruta inicial / (P1-D-UX-01)   [SHA candidato]
```

---

## Verificación

```bash
git rev-parse 25ad1021ee6ea0322aceb0622252e7b748706d32   # inicial
git rev-parse HEAD                                        # candidato C1-R1
```

---

## Veredicto

**C1-R1 APTO PARA RECERTIFICACIÓN**
