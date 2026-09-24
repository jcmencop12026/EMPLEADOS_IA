# 03 — Riesgos de convergencia V1 + V2

**Fecha:** 2026-08-31
**Alcance:** Pre-integración (sin ejecución funcional)

---

## Matriz de riesgos

| ID | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R-01 | **Pérdida datos PostgreSQL** al aplicar 32 migraciones sin backup | Media | Crítico | pg_dump CERT antes; staging con restore; `migration_control` preflight |
| R-02 | **Login roto** post-despliegue (api.ts bug + MFA V2) | Alta | Alto | Cherry-pick hotfix V1 login; prueba PASO1 equivalente en staging |
| R-03 | **Merge masivo** pierde estabilidad V1 certificada | Alta | Crítico | Integración selectiva; prohibir merge `e8cb853`→`dc1e6cd` |
| R-04 | **RBAC/permisos** admin V1 insuficientes en V2 | Media | Alto | Verificar `superadmin` + 74 permisos; test `/api/auth/me` |
| R-05 | **Migraciones divergentes** (ledger vs BD real) | Media | Crítico | `alembic current` + ledger JSON; no `stamp` manual |
| R-06 | **Regresión UI** (menú, CC, español) | Media | Medio | Suite visual focal post-6E; walkthrough CC |
| R-07 | **Schedulers V2** efectos colaterales en BD V1 | Media | Medio | Desactivar schedulers en staging inicial; activar por bloque |
| R-08 | **CORS/puertos** frontend-backend | Baja | Medio | Mantener `.env` CERT; validar `CORS_ORIGINS` |
| R-09 | **Scripts Windows frágiles** reintroducidos | Media | Medio | Reutilizar patrón compose override; prohibir `python -c` |
| R-10 | **Pérdida hotfix V1** no cherry-picked | Alta | Alto | Bloque 0 explícito en plan integración |
| R-11 | **Conflictos auth** (recuperación email V1 vs MFA V2) | Media | Medio | Documentar flujo; no deshabilitar MFA sin decisión |
| R-12 | **Tiempo inactividad** frontend durante deploy | Baja | Bajo | Blue/green o compose `--no-deps` solo frontend |
| R-13 | **Tests insuficientes** para 116 commits | Media | Alto | Regresión completa V2 (1240+) tras cada bloque |
| R-14 | **Secretos en respaldos** | Baja | Crítico | Solo `git archive`; nunca `.env` productivo |
| R-15 | **Tag/certificado movido** accidentalmente | Baja | Crítico | Prohibido `git tag -f`; ramas de trabajo separadas |

---

## Riesgos por categoría

### Datos y migraciones (CRÍTICO)

- Salto `d1e2f3a4b5c6` → `1341a1b2c3d4e` irreversible sin restore.
- Merges Alembic (`1250f1`, `1365`, `14b0`) requieren orden correcto.
- Tablas nuevas: comercial, comunicaciones, SCIM, MFA, integraciones, etc.

### Autenticación y acceso (ALTO)

- V1: login simple, admin recuperado manualmente (CERRADO).
- V2: MFA, sesiones, change password — puede bloquear admin si mal configurado.
- Hotfix `api.ts` V1 **no está** en V2 certificado.

### Funcional / regresión (ALTO)

- 47 archivos de test nuevos en V2 no cubren entorno V1_CERT Docker.
- Mi Trabajo adapter en V2 usa usuario autenticado (fix post-6E) — distinto a V1.

### Operacional (MEDIO)

- `D:\EMPLEADOS_IA_CERT` debe permanecer en `e8cb853` hasta cutover formal.
- Worktree convergencia separado obligatorio.

### Visual / UX (MEDIO)

- Centro Control, integraciones panel, etiquetas ES — cambios extensos.
- Login V1 hotfix UX superior al V2 cert en manejo errores 401.

---

## Capacidades en riesgo de pérdida

| Capacidad | Si integración bruta |
|---|---|
| Estabilidad V1 certificada | **PERDIDA** |
| Procedimiento admin V1 CERRADO | Requiere re-validación |
| Simplicidad despliegue 3 contenedores | Mantenible si compose base igual |
| Documentación V1_CERT operativa | Desactualizada hasta adaptar |

---

## Controles obligatorios antes de GO

1. Respaldo PG lógico verificado (`pg_restore --list`).
2. Respaldo código V1/V2 SHA-256 verificado.
3. Entorno staging con dump V1 restaurado.
4. Rama `cursor/eiaax-convergencia-v1-v2` aislada.
5. Plan por bloques aprobado.
6. Rollback documentado (restore PG + checkout SHA).

---

## Recomendación GO / NO-GO

| Veredicto | Justificación |
|---|---|
| **GO condicionado** | Respaldos código OK; inventario y plan listos; PG pendiente en CERT |
| **NO-GO inmediato** si | Sin dump PG, merge masivo, o migración directa sobre CERT |

**Nivel de confianza pre-integración:** MEDIO-ALTO (código) / BAJO (datos, hasta pg_dump CERT).
