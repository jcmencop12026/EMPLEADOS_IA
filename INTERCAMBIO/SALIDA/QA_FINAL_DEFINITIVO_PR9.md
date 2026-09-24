# QA final definitivo — PR #9 / CURSOR-840B

Fecha: 2026-08-24  
Proyecto: `D:\EMPLEADOS_IA`  
Alcance: validación exclusiva de semántica estricta de `is_active` y regresiones enumeradas por el pedido.

## Estado final

> **APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN**

La validación no realizó merge ni ninguna otra operación de integración.

## Identidad validada

- Rama: `cursor/admin-users-roles-840`
- HEAD remoto completo: `aa9ba4303edff0a7d21d531dc4d912863c522050`
- Commit correctivo presente: `3f561a4` — `fix(840b): migration strict is_active — no string semantics`
- Checkout de QA: detached y aislado en `D:\codex-qa-final-pr9-aa9ba43`.

## Valores persistidos y resultado runtime

La matriz se ejecutó mediante `UPDATE` SQL directo, sin normalización previa del ORM. La lectura runtime usó la resolución real de permisos.

| Valor escrito directamente | Tipo/valor leído de SQLite | Runtime |
| --- | --- | --- |
| `1` | `integer / 1` | **ACTIVE** |
| `0` | `integer / 0` | **DENY** |
| `2` | `integer / 2` | **DENY** |
| `-1` | `integer / -1` | **DENY** |
| `yes` | `text / 'yes'` | **DENY** |
| `true` | `text / 'true'` | **DENY** |
| `t` | `text / 't'` | **DENY** |
| `TRUE` | `text / 'TRUE'` | **DENY** |
| `on` | `text / 'on'` | **DENY** |
| texto arbitrario | `text / 'arbitrary'` | **DENY** |
| cadena vacía | `text / ''` | **DENY** |
| `NULL` | N/A: `NOT NULL constraint failed: roles.is_active` | N/A |

Resultado: **PASS**. Únicamente el entero persistido `1` fue interpretado como activo.

## Resultado de migración

La migración separa la normalización por dialecto:

- SQLite: `typeof(is_active) = 'integer' AND is_active = 1` conserva `1`; cualquier otro valor queda en `0`.
- PostgreSQL: `is_active IS TRUE` conserva `TRUE`; cualquier otro valor queda en `FALSE`.

Matriz independiente antes/después del upgrade:

| Entrada | Después del upgrade |
| --- | --- |
| entero `1` | entero `1` |
| entero `0` | entero `0` |
| entero `2` | entero `0` |
| entero `-1` | entero `0` |
| `yes` | entero `0` |
| `true` | entero `0` |
| `t` | entero `0` |
| `TRUE` | entero `0` |
| `on` | entero `0` |
| texto arbitrario | entero `0` |
| cadena vacía | entero `0` |

El fixture duplicado con una definición canónica y otra con `is_active='yes'` dejó al superviviente **inactivo**. No hubo escalamiento.

Resultado de migración: **PASS**.

## Regresiones acotadas

Las pruebas focales terminaron `50 passed, 2 warnings in 47.72s`.

- deduplicación determinística: **PASS**;
- intersección de permisos: **PASS**;
- mínimo privilegio, incluida intersección vacía: **PASS**;
- remapeo de `role_permissions`: **PASS**;
- huérfanos posteriores: `0`, **PASS**;
- rol inexistente: **DENY / PASS**;
- rol inactivo: **DENY / PASS**;
- error de base de datos: **DENY / PASS**;
- aislamiento cross-tenant: **PASS**.

## Roundtrip

`upgrade → downgrade → upgrade`: **PASS**.

- índice parcial final presente;
- integridad final correcta;
- relaciones huérfanas: `0`.

La deduplicación aplicada durante el primer upgrade es irreversible en cuanto a reconstruir las filas duplicadas originales; el downgrade elimina el índice, no recrea duplicados. Es la pérdida esperada ya documentada para esta migración.

## PostgreSQL

`POSTGRESQL REAL: NO CERTIFICADO`

Se detectó el servicio local `postgresql-x64-18` en ejecución, pero el entorno no proporcionó cliente ni credenciales de conexión utilizables. No se atribuye PASS a PostgreSQL real.

## Suite, build, audit y Git

| Validación | Resultado exacto |
| --- | --- |
| Pruebas focales | **PASS** — `50 passed, 2 warnings in 47.72s` |
| `pytest` completo | **PASS** — `112 passed, 3 warnings in 173.74s` |
| `npm ci` | **PASS** — 73 paquetes instalados/auditados, 0 vulnerabilidades |
| `npm run build` | **PASS** — Vite 6.4.3, 59 módulos, `275.37 kB` JS (`84.17 kB` gzip), `2.35s` |
| `npm audit` | **PASS** — `found 0 vulnerabilities` |
| `git diff --check` | **PASS** — sin salida en el worktree limpio |
| Estado del worktree | **PASS** — sin cambios versionados ni no versionados |

Observación no bloqueante: al comprobar adicionalmente el rango del commit `3f561a4`, Git señala espacios finales en dos líneas del informe Markdown `INTERCAMBIO/SALIDA/CURSOR_CIERRE_FINAL_840B.md`. No afecta el código, las pruebas ni el `git diff --check` solicitado sobre el checkout limpio.

## Conclusión

Todos los valores corruptos y numéricos no canónicos probados producen DENY en runtime y se normalizan a inactivo durante la migración. La corrupción `yes` en un duplicado no activa al superviviente, y las regresiones acotadas continúan aprobadas.

No se modificó código, no se hizo merge, push, rebase o cherry-pick, y no se tocó PR #6, #7, #8 ni #10. La única escritura de esta validación es este informe.
