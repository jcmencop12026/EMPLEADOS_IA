# 01 — Respaldo pre-integración EIAAX

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Fecha UTC:** 2026-08-31  
**Agente:** General  
**Estado:** RESPALDO COMPLETADO — integración funcional **NO iniciada**

---

## 1. Verificación previa (sin modificar estado)

| Verificación | Resultado | Evidencia |
|---|---|---|
| SHA V1 existe | **PASS** | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` (`git cat-file -t commit`) |
| SHA V2 existe | **PASS** | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| Tag `fase2-candidato-final-certificado` | **PASS** | Apunta a `dc1e6cd` |
| Remote `origin` | **PASS** | `github.com/jcmencop12026/EMPLEADOS_IA` |
| SHAs recuperables vía fetch | **PASS** | `git fetch origin <sha>` OK |
| Commits autoritativos modificados | **NO** | Sin checkout destructivo sobre SHAs certificados |
| Tags movidos | **NO** | Sin `git tag -f` |
| `D:\EMPLEADOS_IA_CERT` | **NO tocado** | Operación solo en repo cloud |

### Estado Git al inicio (agente cloud)

```
HEAD detached at 1a85532 (rama hotfix login, posterior a V1 certificado)
Archivos no versionados relevantes:
  INTERCAMBIO/SALIDA/CIERRE_CANDIDATO_FINAL_FASE2.md
  INTERCAMBIO/SALIDA/MATRIZ_ESTADO_REAL_FINAL_FASE2.md
```

### Ramas/tags relacionados

| Referencia | Contiene / apunta |
|---|---|
| `e8cb853` (V1) | Ancestro de `cursor/v1-hotfix-login-acceso-85e4`, `origin/cursor/v1-candidata-final-release-r2` |
| `dc1e6cd` (V2) | `cursor/convergencia-final-fase2-85e4`, tag `fase2-candidato-final-certificado` |
| Hotfix V1 login (fuera de cert V1) | `1a855325d67921b5d53c015605741d94a3eab32b` (5 commits sobre `e8cb853`) |

### Alembic (solo lectura)

| Versión | baseline_head | Archivos migración |
|---|---|---|
| V1 `e8cb853` | `d1e2f3a4b5c6` | 21 |
| V2 `dc1e6cd` | `1341a1b2c3d4e` | 53 |

### Configuración versionada para reconstrucción

Incluida en ambos respaldos: `docker-compose.yml`, `.env.example`, `backend/Dockerfile`, `frontend/Dockerfile`, `backend/alembic/`, scripts de arranque, tests, documentación INTERCAMBIO.

---

## 2. Respaldo V1

| Campo | Valor |
|---|---|
| SHA | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| Artefacto | `INTERCAMBIO/RESPALDOS/EIAAX_PREINTEGRACION/EIAAX_V1_e8cb853_20260831T015348Z.tar.gz` |
| SHA-256 | `d63c50c6941ced5fc239a3dfbb81c701ed00714e9c713e810246149c8a31c7dc` |
| Tamaño | 2 003 082 bytes |
| Método | `git archive` (sin `.git/`, sin secretos) |
| Manifiesto | `MANIFEST_V1_e8cb853.json` |

**Contenido recuperable:** código fuente, migraciones (21), tests (52 archivos), frontend, backend, docs, compose, capabilities.

**Regenerar:**

```bash
./INTERCAMBIO/RESPALDOS/EIAAX_PREINTEGRACION/REGENERAR_RESPALDOS.sh
```

---

## 3. Respaldo V2 / Fase 2

| Campo | Valor |
|---|---|
| SHA | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| Tag | `fase2-candidato-final-certificado` |
| Artefacto | `INTERCAMBIO/RESPALDOS/EIAAX_PREINTEGRACION/EIAAX_V2_dc1e6cd_20260831T015348Z.tar.gz` |
| SHA-256 | `075b68ae0003268baffe0a420a980b5e7de94536e8520c04918fd54a36abcb97` |
| Tamaño | 2 617 180 bytes |
| Correspondencia SHA | **CONFIRMADA** (archive generado desde commit exacto) |
| Manifiesto | `MANIFEST_V2_dc1e6cd.json` |

**Contenido recuperable:** código V2 completo, migraciones (53), tests (99 archivos), módulos Fase 2 (MB-06..MB-12, comercial, SSO, SCIM, etc.).

**Backups anteriores:** no eliminados (este respaldo es adicional).

---

## 4. Respaldo PostgreSQL

| Campo | Valor |
|---|---|
| Estado | **NO EJECUTABLE** en entorno agente cloud |
| Motivo | `pg_dump`, `psql` y Docker no disponibles en VM cloud |
| Acción requerida (pre-integración en entorno CERT) | Ejecutar `pg_dump` lógico de `empleados_ia_cert-postgres-1` **antes** de migrar BD en convergencia |
| Validación | `pg_restore --list` sobre dump (sin restaurar sobre BD productiva) |

**No se improvisó dump ni se expusieron credenciales.**

---

## 5. Rama de convergencia preparada

| Campo | Valor |
|---|---|
| Rama | `cursor/eiaax-convergencia-v1-v2` |
| Base inicial | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` (V2 certificado) |
| Merge masivo | **NO realizado** |
| V1 certificado | **Intacto** en `e8cb853` |
| V2 certificado | **Intacto** en `dc1e6cd` |

Worktree Windows sugerido (ejecución local futura, no realizada aquí):

```powershell
git worktree add D:\EMPLEADOS_IA_EIAAX_CONVERGENCIA cursor/eiaax-convergencia-v1-v2
```

---

## 6. Recomendación pre-integración

| Veredicto | Condición |
|---|---|
| **GO condicionado** | Iniciar integración **solo después** de: (1) respaldo PG en CERT, (2) validar rama convergencia, (3) ejecutar plan por bloques |

**NO-GO** si: se omite respaldo PG, se intenta merge masivo V1→V2, o se aplican 32 migraciones nuevas sin entorno de prueba aislado.

---

## 7. Ubicación de artefactos

```
INTERCAMBIO/RESPALDOS/EIAAX_PREINTEGRACION/
  EIAAX_V1_e8cb853_20260831T015348Z.tar.gz
  EIAAX_V2_dc1e6cd_20260831T015348Z.tar.gz
  MANIFEST_V1_e8cb853.json
  MANIFEST_V2_dc1e6cd.json
  REGENERAR_RESPALDOS.sh

INTERCAMBIO/SALIDA/EIAAX_PREINTEGRACION/
  01_RESPALDO_PREINTEGRACION.md  (este archivo)
  02_DIFERENCIAL_V1_V2.md
  03_RIESGOS_CONVERGENCIA.md
  04_PLAN_INTEGRACION_CONTROLADA.md
```
