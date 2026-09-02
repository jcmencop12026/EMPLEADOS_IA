# Causa raíz: por qué 70eb5e1 no resolvió el caso real Windows

**Fecha:** 2026-09-02  
**SHA corregido:** ver commit actual en rama `cursor/convergencia-comercial-v1-85e4`

---

## A. Evidencia del fallo real

Mensaje observado en Windows:

```
ERROR: PYTHON NOT FOUND:
no python.exe candidates detected.
Tried PATH, where.exe, py launcher, registry and standard install paths.
```

Ese texto corresponde al código **anterior a 70eb5e1** (commit `7e6f4e4`).  
Si el usuario ejecutó tras `git pull`, posibles causas de código viejo:

- `arrancar_convergencia_windows.ps1` no completó `git pull` (conflictos/red)
- ejecución directa de `preparar_demo_eiaax.ps1` desde copia cacheada
- worktree sin actualizar al SHA `70eb5e1`

El script actual imprime bloque `PYTHON DISCOVERY` y mensajes distintos.

---

## B. Fallo de diseño en 70eb5e1 (aun con código nuevo)

Incluso con 70eb5e1 desplegado, el diseño tenía **tres defectos**:

### B1. pyvenv.cfg solo añadía rutas si el archivo existía en disco

`Get-EiaaxPythonCandidatesFromPyvenvCfg` llamaba `Get-EiaaxResolvedPythonPath`, que exige `Test-Path` exitoso.

Si `home = C:\Python312` fue movido/eliminado pero el venv INTEGRADO sigue funcionando:

- pyvenv.cfg se leía
- **ningún candidato** se añadía (rutas obsoletas)
- no había sonda del venv funcional

### B2. No se usaba el venv INTEGRADO como sonda

El ejecutable conocido:

`D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo\Scripts\python.exe`

no se ejecutaba para obtener `sys.base_prefix` / `sys._base_executable`.

### B3. Bug de scope en `Build-EiaaxPythonResolutionPlan`

El scriptblock `$addCandidate` usaba `$script:seen` persistente entre invocaciones.  
En la segunda llamada (p. ej. `Resolve-EiaaxPython` tras un `Build` previo en tests), los candidatos quedaban vacíos aunque la sonda sys funcionara.

---

## C. Corrección definitiva (SHA nuevo)

### Autoridad única: `Resolve-EiaaxPython`

| Consumidor | Función |
|------------|---------|
| `preparar_demo_eiaax.ps1` | `Resolve-EiaaxPython` (una sola vez) |
| `Find-EiaaxPython` | alias → `Resolve-EiaaxPython` |
| tests | misma función |

### Cadena de descubrimiento (con diagnóstico visible)

1. `EIAAX_PYTHON`
2. venv convergencia existente
3. **venv INTEGRADO** → `Invoke-EiaaxPythonSysProbe` (`sys.base_prefix`, `sys._base_executable`)
4. pyvenv.cfg (marca rutas obsoletas `[no existe]`)
5. py / where / PATH / registro / estándar
6. fallback: venv INTEGRADO como **creador** `python -m venv` si base ausente pero venv funcional

### Bloque obligatorio en consola

```
PYTHON DISCOVERY
Fuente 1: EIAAX_PYTHON .......... no definido
Fuente 2: venv convergencia ..... no existe
Fuente 3: venv integrado ........ encontrado (...)
sys.base_prefix ............... ...
sys._base_executable .......... ...
pyvenv.cfg .................... leido
pyvenv.cfg home ............... C:\... [no existe]
Validacion python -V .......... PASS
Python base ................... <ruta>
```

---

## D. Comando único (sin cambios)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\EMPLEADOS_IA_CONVERGENCIA\scripts\windows\arrancar_convergencia_windows.ps1
```

Verificar en salida: `Codigo activo SHA: <sha>` debe coincidir con el commit entregado.

---

## E. Criterio WINDOWS REAL OPERATIVO

`EIAAX <sha> — WINDOWS REAL OPERATIVO` solo si PASS:

- bloque PYTHON DISCOVERY con sys.base_prefix o creador venv
- venv `D:\EMPLEADOS_IA_CONVERGENCIA\.venv-eiaax-demo` creado
- `/health` identity + PID/CMD worktree convergencia

Fallo: `EIAAX — WINDOWS NO CERTIFICADO` + `CAUSA: ...`
