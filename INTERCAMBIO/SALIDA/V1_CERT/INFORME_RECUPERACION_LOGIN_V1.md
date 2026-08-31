# Informe final - Recuperacion acceso + mejora login V1

**Proyecto:** EMPLEADOS_IA_CERT  
**BASE SHA certificado:** `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` (NO modificado)  
**Rama hotfix:** `cursor/v1-hotfix-login-acceso-85e4`  
**Fecha:** 2026-08-30

---

## 1. Causa del fallo del inspector (y scripts inline)

Los scripts `*-Inline-e8cb853.ps1` embebian Python con **here-strings de PowerShell** y lo ejecutaban via `python -c $py` dentro de `docker exec`.

**Error real reportado:**

```
SyntaxError: invalid character '€' (U+20AC)
print(f'ORG_ESTADO: {o.status if o else â€"?}')
```

**Causa raiz:** el em dash Unicode (`—`, U+2014) en el codigo Python inline se corrompio a mojibake (`â€"?`) al atravesar la cadena PowerShell -> Docker -> Python. PowerShell/Windows-1252 y el quoting de here-strings hacen fragil cualquier bloque Python complejo inline.

**Correccion:** eliminados los scripts inline. Los nuevos scripts copian archivos Python reales al contenedor con `docker cp`, los ejecutan explicitamente y los borran despues. Sin `python -c`. Sin caracteres Unicode en codigo ejecutable.

---

## 2. Revision de los 3 scripts (completa)

| Script | Estado anterior | Correccion |
|---|---|---|
| `Inspect-AdminUser-Inline-e8cb853.ps1` | FALLA (mojibake + python -c) | **ELIMINADO** -> `Inspect-AdminUser.ps1` |
| `Reset-AdminPassword-Inline-e8cb853.ps1` | Riesgo mismo patron | **ELIMINADO** -> `Reset-AdminPassword.ps1` |
| `Test-LoginApi.ps1` | Sin Python inline; revisado | **OK** - prompt SecureString, limpia memoria |

**Scripts nuevos de entrega unica:**

- `_V1CertCommon.ps1` - helpers compartidos (docker cp, red, contenedor)
- `PASO1-Recuperar-Admin.ps1` - inspeccion + reset opcional + login API
- `PASO2-Desplegar-Hotfix-Frontend.ps1` - build y despliegue frontend hotfix

**Entorno objetivo (sin modificar CERT):**

| Recurso | Valor |
|---|---|
| CERT dir | `D:\EMPLEADOS_IA_CERT` |
| Hotfix worktree | `D:\EMPLEADOS_IA_V1_HOTFIX` |
| Backend container | `empleados_ia_cert-backend-1` |
| Postgres container | `empleados_ia_cert-postgres-1` |
| Backend URL | `http://localhost:18010` |
| Frontend URL | `http://localhost:5180/login` |

---

## 3. Entrega: DOS pasos manuales

### PASO 1 - Recuperar / validar admin

```powershell
cd D:\EMPLEADOS_IA_V1_HOTFIX
git checkout cursor/v1-hotfix-login-acceso-85e4
.\INTERCAMBIO\SALIDA\V1_CERT\PASO1-Recuperar-Admin.ps1 -HotfixRoot "D:\EMPLEADOS_IA_V1_HOTFIX"
```

**Que hace automaticamente:**

1. Inspecciona usuario `admin` (sin hash ni secretos)
2. Pregunta si desea reset (S/N)
3. Si S: prompt oculto **dentro del contenedor** via `getpass`
4. Prueba login API + verificacion SUPERADMIN

**Resultado esperado:**

```
INSPECT: PASS
LOGIN: PASS
ROLE: superadmin
SUPERADMIN CHECK: PASS
PASO 1: PASS
```

**Si falla:**

| Sintoma | Accion automatica sugerida |
|---|---|
| Container not running | `docker start empleados_ia_cert-backend-1` |
| USUARIO no existe / INACTIVO | Responder `S` al prompt de reset |
| LOGIN FAIL tras reset | Repetir reset; verificar `http://localhost:18010/health/ready` |
| SUPERADMIN CHECK FAIL | El script de reset eleva `admin` a `superadmin` |

### PASO 2 - Desplegar frontend hotfix

```powershell
cd D:\EMPLEADOS_IA_V1_HOTFIX
.\INTERCAMBIO\SALIDA\V1_CERT\PASO2-Desplegar-Hotfix-Frontend.ps1 -HotfixRoot "D:\EMPLEADOS_IA_V1_HOTFIX" -CertDir "D:\EMPLEADOS_IA_CERT"
```

**Que hace automaticamente:**

1. `docker build` imagen `empleados_ia_cert-frontend-hotfix` desde hotfix
2. Detecta red Docker del backend
3. Recrea solo `empleados_ia_cert-frontend-1` (NO toca postgres ni backend data)

**Resultado esperado:**

```
PASO 2: PASS (frontend container started)
Open: http://localhost:5180/login
```

UI: ojo mostrar/ocultar contrasena, enlace "Olvido su contrasena?", mensaje correcto en 401.

**Si falla:**

| Sintoma | Accion |
|---|---|
| docker build failed | Verificar Docker Desktop y espacio en disco |
| network error | Verificar `empleados_ia_cert-backend-1` en ejecucion |
| Login UI sigue mal | Hard refresh (Ctrl+F5); confirmar contenedor frontend nuevo |

---

## 4. Seguridad de contrasena

| Requisito | Cumplimiento |
|---|---|
| No en pantalla | `getpass` en contenedor + `Read-Host -AsSecureString` en Test-LoginApi |
| No en args de proceso visibles | Script Python copiado; sin password en linea de comandos |
| No en Git | Scripts solo referencian rutas; sin secretos |
| No en logs | No se imprime hash ni contrasena |
| No en archivos permanentes | Script temporal en `/tmp/` se elimina tras ejecucion |
| No en chat | Usuario introduce localmente |

---

## 5. Validaciones ejecutadas (agente cloud - NO Windows real)

**Declaracion explicita:** este agente **NO dispone de Windows PowerShell ni del Docker CERT del usuario**. No se afirma "probado en Windows".

| Validacion | Resultado |
|---|---|
| A. Sintaxis PowerShell | SKIP (pwsh no disponible en cloud); revision manual estatica |
| B. Sintaxis Python | PASS (`py_compile`) |
| C. Encoding scripts .ps1 | PASS (ASCII-only) |
| D. Sin mojibake (â€, etc.) | PASS |
| E. Sin python -c inline | PASS |
| F. Seguridad contrasena | PASS (revision estatica) |
| G. `test_v1_hotfix_login.py` (4) | PASS |
| H. `npm run build` frontend | PASS (commit anterior) |

Ejecutar localmente en Windows:

```powershell
# Opcional: validacion adicional tras git pull
Get-ChildItem D:\EMPLEADOS_IA_V1_HOTFIX\INTERCAMBIO\SALIDA\V1_CERT\*.ps1 | ForEach-Object {
  $e = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$null, [ref]$e)
  if ($e) { throw $e } else { Write-Host "OK $($_.Name)" }
}
```

---

## 6. Hotfix frontend (verificado en codigo)

| Archivo | Cambio |
|---|---|
| `frontend/src/api.ts` | Lee `text` antes de `!res.ok` |
| `frontend/src/pages/LoginPage.tsx` | Toggle contrasena; panel olvido |
| `frontend/src/styles.css` | Estilos login |

---

## 7. Restricciones respetadas

- SHA `e8cb853` no reescrito
- Fase 2 no tocada
- PostgreSQL no destruido/recreado
- `D:\EMPLEADOS_IA_CERT` no modificado por estos scripts (solo lectura compose + frontend container)
- Sin merge

---

## VEREDICTO

| Campo | Valor |
|---|---|
| **SCRIPTS WINDOWS** | **APTO** (diseno robusto docker cp; pendiente ejecucion local final) |
| **RECUPERACION ADMIN** | **LISTA** |
| **HOTFIX LOGIN** | **APTO** |
