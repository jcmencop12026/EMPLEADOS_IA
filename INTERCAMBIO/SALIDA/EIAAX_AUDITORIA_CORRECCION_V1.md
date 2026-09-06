# EIAAX — Corrección única auditoría independiente (PR #171)

**Estado:** Pendiente certificación CI sobre SHA final (no declarar APTO).

## Resumen de bloqueadores resueltos

### 1. Coherencia SHA evidencia visual

- Nuevo módulo `scripts/lib/cert_sha.mjs`: `resolveCertSha()` exige `git HEAD` = `EIAAX_SHA` = `GITHUB_SHA`.
- Certificaciones escriben `sha` en `report.json` y `sha-manifest.json`; `assertReportSha()` antes de salir.
- `scripts/verify_cert_sha_coherence.mjs` valida ambos reportes + nombre de artefacto CI.
- CI usa `github.event.pull_request.head.sha` (no merge `github.sha` ni `GITHUB_SHA` del runner).
- Eliminados `report.json` versionados (causa del mismatch `e242eb5` vs `36d1739`).

### 2. Backend Publicable cliente (fail-closed)

- `backend/app/services/publicable_cliente_service.py`: whitelist de campos, validación negativa, endpoint dedicado.
- `GET /api/evaluaciones/{id}/informe-publicable-cliente` (permiso `evaluacion.vista_entidad`).
- `GET /api/evaluaciones/{id}/impacto?vista_entidad=true` con enforcement de permiso (fix: `user_permissions(user, db)`).
- Frontend Cabina Informes — pestaña «Publicable cliente» consume API filtrada.
- `tests/test_publicable_cliente_v1.py`: aislamiento A/B, informes INTERNO excluidos, permisos, no publicado, campos prohibidos.

### 3. Fix auxiliar demo

- `DEMO_NECESIDAD_RESUMEN` en `demo_comercial_constants.py` (evita 500 en vista entidad demo).

## Archivos modificados

- `.github/workflows/qa.yml`
- `.gitignore`
- `backend/app/demo_comercial_constants.py`
- `backend/app/routers/evaluaciones.py`
- `backend/app/services/publicable_cliente_service.py` (nuevo)
- `frontend/src/api.ts`
- `frontend/src/components/evaluacion/CabinaInformesPanel.tsx`
- `scripts/lib/cert_sha.mjs` (nuevo)
- `scripts/verify_cert_sha_coherence.mjs` (nuevo)
- `scripts/cert_transversal_visual.mjs`
- `scripts/cert_vista_empresa_flow.mjs`
- `tests/test_publicable_cliente_v1.py` (nuevo)
- Eliminados del índice: `data/evidence/*/report.json`

## SHA

| Campo | Valor |
|-------|-------|
| SHA inicial (auditoría) | `36d173957b6a876e106d18a33898af5281ebc8b8` |
| SHA final | `88b90c3cae0e300048d437c2fa761d1bbbd6c915` |

## Certificación CI (SHA final `88b90c3`)

| Prueba | Resultado |
|--------|-----------|
| Run ID | `33977698792` |
| Jobs | 5/5 PASS |
| Visual 44/44 + tabs 18/18 | PASS (job Certificación visual PR171) |
| Vista Empresa E2E | PASS |
| Coherencia SHA | HEAD = artefacto = report.json = `88b90c3cae0e300048d437c2fa761d1bbbd6c915` |

## Artefacto CI

Nombre exacto: `eiaax-visual-pr171-88b90c3cae0e300048d437c2fa761d1bbbd6c915`

`report.json` → `"sha": "88b90c3cae0e300048d437c2fa761d1bbbd6c915"`

## Pendientes reales

- Auditoría independiente ChatGPT (no declarar APTO desde este agente).
