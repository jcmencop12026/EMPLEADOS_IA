# 01 — Cierre de convergencia técnica V1 + V2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Fecha UTC:** 2026-08-31  
**Rama convergencia:** `cursor/eiaax-convergencia-v1-v2`

---

## Declaración

# CONVERGENCIA TÉCNICA V1 + V2 COMPLETA

No queda delta material de capacidades V1 o V2 certificadas pendiente de incorporar en el producto convergido.

**NO se inicia C3/C4.** No existe brecha de convergencia que justifique un bloque adicional de integración código.

---

## SHA y referencias certificadas

| Referencia | SHA | Estado |
|---|---|---|
| **Candidato convergido C2** | `b19b04dd438f5b13b422e9a760f54fa074fb52ed` | Base certificada actual |
| C1-R1 | `3226ba5ee9b998547c7026c98b69972dfacd2d3d` | CERTIFICADO (A/B/C/D) |
| C2 | `b19b04dd438f5b13b422e9a760f54fa074fb52ed` | CERTIFICADO (A/B/C/D) |
| V1 certificado | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` | **INTACTO** |
| V2 / Fase 2 certificado | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` | **INTACTO** |
| Tag Fase 2 | `fase2-candidato-final-certificado` → `dc1e6cd` | **INTACTO** |

**HEAD rama (docs post-C2):** `5d035d724af50ad3d5e83311de0399cb9c76d3e6` — solo alineación SHA en entregables; código producto = `b19b04d`.

---

## Evidencia de completitud

### Relación git

| Comparación | Resultado |
|---|---|
| Merge-base V2 ↔ candidato | `dc1e6cd` (= V2 íntegro como ancestro directo) |
| Archivos V2 ausentes en candidato | **0** |
| Archivos código V1 no presentes en candidato (excl. `.md`) | **0** |
| Rutas API compartidas V1 perdidas | **0** |

### Commits de convergencia (sobre V2)

```
dc1e6cd  V2 certificado
1dcc656  respaldo y preintegración V1+V2
25ad102  C1 — hotfix login selectivo
3226ba5  C1-R1 — fallback home /
b19b04d  C2 — multiempresa + CC + Mi Trabajo
```

### Deltas V1 reintegrados o preservados

| Capacidad V1 crítica | Estado en `b19b04d` |
|---|---|
| DATABASE_URL / precedencia env | Preservado |
| Knowledge auth | Preservado |
| Multiempresa / tenant_scope | Preservado + reforzado C2 |
| RBAC deny-by-default | Preservado |
| Hotfix login (api.ts, LoginPage) | Integrado selectivo C1 |
| MFA / SSO V2 | Conservado (no regresión a login V1 simple) |

### Excluido intencionalmente (no es brecha de convergencia)

| Ítem | Motivo |
|---|---|
| Scripts `V1_CERT/*.ps1` Windows | Operacionales CERT; fuera alcance convergencia código |
| `docker-compose.frontend-hotfix.yml` V1 | Deploy V1 puntual; no aplica producto convergido |
| Reversión tests V2 del branch hotfix V1 | Evitado — hotfix basado en árbol V1 |

### Nota de diseño documentada (no bloqueante)

Endpoints fuera de CC/trabajo/auditor/finops no exponen `organization_id` override para SUPERADMIN — decisión V1.1; cubierto en inventario como evolución POST-V1, no como brecha de convergencia.

---

## Infraestructura y pruebas

| Verificación | Resultado |
|---|---|
| Alembic head único | `1341a1b2c3d4e` — sin migraciones nuevas en C1/C1-R1/C2 |
| `pytest tests/` en `b19b04d` | **1280 passed**, 4 skipped, 0 failed |
| `npm run build` | **PASS** |
| Certificaciones C1-R1 | A/B/C/D APTO — P0/P1 = 0 |
| Certificaciones C2 | A/B/C/D APTO — P0/P1 = 0 |

---

## Respaldo candidato convergido

| Artefacto | Valor |
|---|---|
| Archivo | `INTERCAMBIO/RESPALDOS/EIAAX_CONVERGENCIA/EIAAX_C2_b19b04d_20260831T202948Z.tar.gz` |
| SHA-256 | `17330d8084a5c9ef2e30cf3b6cdf4c389e05f269babb8103f3aaf02c92d0527f` |
| Manifiesto | `*.tar.gz.sha256` |

Respaldos V1/V2 previos permanecen intactos en `INTERCAMBIO/RESPALDOS/EIAAX_PREINTEGRACION/`.

**Tag de release final V1:** NO creado (según instrucción).

---

## Prerrequisitos operativos (no código)

| Ítem | Estado | Nota |
|---|---|---|
| `pg_dump` CERT PostgreSQL | Pendiente Agente B | No bloquea cierre convergencia código |
| `alembic upgrade head` en BD V1 real | Pendiente staging | Plan documentado preintegración |
| Walkthrough visual CERT | Pendiente Agente B | Operacional |

---

## Veredicto final

| Pregunta | Respuesta |
|---|---|
| ¿Convergencia V1+V2 completa? | **SÍ** |
| ¿Crear C3 por brecha V1/V2? | **NO** |
| ¿Siguiente fase? | **Inventario Maestro** sobre producto integrado `b19b04d` |
