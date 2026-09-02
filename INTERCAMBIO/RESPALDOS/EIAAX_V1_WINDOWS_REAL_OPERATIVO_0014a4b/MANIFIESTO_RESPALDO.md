# MANIFIESTO DE RESPALDO — EIAAX V1 Windows Real Operativo

| Campo | Valor |
|-------|-------|
| **PROYECTO** | EIAAX |
| **TIPO** | BASE WINDOWS REAL OPERATIVA |
| **SHA corto** | `0014a4b` |
| **SHA completo** | `0014a4b01a3ccf3e849a6609c8c784873f20f497` |
| **Tag** | `eiaax-v1-windows-real-operativo-0014a4b` |
| **Tag object (annotated)** | `03216bf69894e18dd4db389c0ee3c824cc656efb` |
| **Rama de origen** | `cursor/convergencia-comercial-v1-85e4` |
| **Alembic head/current** | `1820a1b2c3d4e` |
| **Resultado Windows real** | backend ownership PASS · frontend ownership PASS · Process ownership PASS · Runtime identity PASS · EIAAX accesible |
| **Fecha respaldo (UTC)** | `2026-09-02T03:59:23Z` |
| **Agente** | A (preservación independiente) |

---

## Advertencia de alcance temporal

**ESTA BASE ES ANTERIOR AL MACROBLOQUE FINAL DE EXPERIENCIA V1.**

Preserva el último estado confirmado operativo en Windows real antes de continuar la transformación visual/funcional V1.

---

## Artefacto bundle

| Campo | Valor |
|-------|-------|
| **Archivo** | `eiaax-v1-windows-real-operativo-0014a4b.bundle` |
| **Ubicación remota (agente)** | `INTERCAMBIO/RESPALDOS/EIAAX_V1_WINDOWS_REAL_OPERATIVO_0014a4b/eiaax-v1-windows-real-operativo-0014a4b.bundle` |
| **Ubicación objetivo Windows** | `D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_WINDOWS_REAL_OPERATIVO_0014a4b\eiaax-v1-windows-real-operativo-0014a4b.bundle` |
| **Tamaño** | 7 289 063 bytes (7,0 MiB) |
| **SHA-256** | `70c6b011bbebacc9f6bf97f0323f4fff6fc05f66f62712440b50adaacf8c0a28` |

### Materialización local Windows

El agente remoto **no tiene acceso** a `D:\`. El bundle fue generado y verificado en el repositorio/intercambio del agente.

**Pendiente en Windows:** copiar el bundle y este manifiesto a la ruta `D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_WINDOWS_REAL_OPERATIVO_0014a4b\` y verificar SHA-256 local.

---

## Verificación del bundle

```
$ git bundle verify eiaax-v1-windows-real-operativo-0014a4b.bundle
eiaax-v1-windows-real-operativo-0014a4b.bundle is okay
The bundle contains these 2 refs:
0014a4b01a3ccf3e849a6609c8c784873f20f497 refs/remotes/origin/cursor/convergencia-comercial-v1-85e4
03216bf69894e18dd4db389c0ee3c824cc656efb refs/tags/eiaax-v1-windows-real-operativo-0014a4b
The bundle records a complete history.
```

**Resultado:** `git bundle verify` — **PASS**

---

## Prueba de restauración (temporal, no productiva)

### Método A — clone desde bundle + checkout tag

```bash
git clone eiaax-v1-windows-real-operativo-0014a4b.bundle restored_repo
cd restored_repo
git checkout eiaax-v1-windows-real-operativo-0014a4b
git rev-parse HEAD
# → 0014a4b01a3ccf3e849a6609c8c784873f20f497
```

**Resultado:** PASS

### Método B — fetch rama desde bundle

```bash
mkdir restore && cd restore && git init
git fetch ../eiaax-v1-windows-real-operativo-0014a4b.bundle \
  refs/remotes/origin/cursor/convergencia-comercial-v1-85e4:refs/heads/cursor/convergencia-comercial-v1-85e4
git checkout cursor/convergencia-comercial-v1-85e4
git rev-parse HEAD
# → 0014a4b01a3ccf3e849a6609c8c784873f20f497
```

**Resultado:** PASS

---

## Tag en origin

```
$ git ls-remote --tags origin eiaax-v1-windows-real-operativo-0014a4b
03216bf69894e18dd4db389c0ee3c824cc656efb  refs/tags/eiaax-v1-windows-real-operativo-0014a4b
```

**Confirmación:** tag publicado en `origin` — **PASS**  
**Commit del tag (`^{commit}`):** `0014a4b01a3ccf3e849a6609c8c784873f20f497` — **PASS**

---

## Base de datos demo local Windows

| Campo | Valor |
|-------|-------|
| **Ruta** | `D:\EMPLEADOS_IA_CONVERGENCIA\data\eiaax_integrado_demo.db` |
| **Estado** | **BD DEMO LOCAL WINDOWS: PENDIENTE DE COPIA** |

El agente remoto **no tiene acceso** a la BD en disco Windows. Esto **no invalida** el respaldo del código. No se tocó la BD activa.

**Recomendación Windows:** antes de transformación V1, copiar manualmente la BD demo y registrar SHA-256 en copia local de este manifiesto.

---

## Método de restauración recomendado

### Opción 1 — desde tag en origin (repositorio existente)

```bash
git fetch origin tag eiaax-v1-windows-real-operativo-0014a4b
git checkout eiaax-v1-windows-real-operativo-0014a4b
# o
git checkout 0014a4b01a3ccf3e849a6609c8c784873f20f497
```

### Opción 2 — desde bundle (sin depender de GitHub)

```bash
git clone D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_WINDOWS_REAL_OPERATIVO_0014a4b\eiaax-v1-windows-real-operativo-0014a4b.bundle EIAAX_RESTORE_0014a4b
cd EIAAX_RESTORE_0014a4b
git checkout eiaax-v1-windows-real-operativo-0014a4b
```

### Post-restauración

Ejecutar scripts Windows de arranque y verificación ownership/Alembic/runtime identity según runbook operativo.

---

## Limitaciones

1. Bundle generado en entorno remoto Linux; **copia física a `D:\` pendiente** en máquina Windows.
2. **BD demo no respaldada** por este agente; requiere copia manual en Windows.
3. El bundle contiene historia completa hasta `0014a4b`; no incluye commits posteriores a la transformación V1 (por diseño).
4. Restauración verificada en ubicación temporal; no se modificaron repositorios productivos durante la prueba.

---

## Checklist de recuperabilidad

| Verificación | Estado |
|--------------|--------|
| TAG → `0014a4b` | PASS |
| BUNDLE → `git bundle verify` | PASS |
| RESTAURACIÓN TEMPORAL (tag) | PASS |
| RESTAURACIÓN TEMPORAL (rama) | PASS |
| SHA RESTAURADO → `0014a4b` | PASS |
| SHA-256 registrado | PASS |
| Manifiesto completo | PASS |
| Tag publicado en origin | PASS |

---

**Estado:** `EIAAX — BASE 0014a4b RESPALDADA Y RECUPERABILIDAD VERIFICADA` (código)
