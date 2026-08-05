# CURSOR_004 — No se puede acceder a 127.0.0.1:5180

## Qué significa el error

| Síntoma | Causa |
|--------|--------|
| `ERR_CONNECTION_REFUSED` en **5180** | No hay servidor Vite (frontend B1 no instalado o `ARRANCAR.bat` no levantó npm). |
| `dir frontend\package.json` → no existe | Tu carpeta sigue en **fase B0** (solo API en 8010). |
| `curl .../health` → `"phase":"B0"` | Mismo caso: falta actualizar código **B1** desde GitHub. |

El backend en **8010** puede estar bien (B0) mientras la web en **5180** no existe hasta tener B1 + Node + `ARRANCAR.bat`.

## Solución (PowerShell en `D:\EMPLEADOS_IA`)

```powershell
cd D:\EMPLEADOS_IA
git fetch origin
git pull origin main
```

Comprueba que exista el frontend:

```powershell
dir .\frontend\package.json
```

Si el archivo existe:

```powershell
.\CREAR_ENTORNO.bat
.\ARRANCAR.bat
```

- API: http://127.0.0.1:8010/health → debe mostrar `"phase":"B1"`.
- Web: http://127.0.0.1:5180 — login **admin** / **Admin2026***.

**Importante:** `ARRANCAR.bat` deja la ventana del frontend abierta; no la cierres. Si solo arrancaste la API, 5180 seguirá rechazando conexión.

## Si `git pull` dice "Already up to date" y sigues en B0

1. `git log -1 --oneline` — debe verse un commit tipo `feat(B1): auth JWT...`.
2. Si no: `git fetch origin` y `git reset --hard origin/main` (solo si no tienes cambios locales que quieras guardar).
3. Alternativa: ejecutar `.\scripts\ACTUALIZAR_B1.ps1`.

## Node.js

`CREAR_ENTORNO.bat` necesita **Node.js LTS** en el PATH. Sin Node, no se crea `frontend\node_modules` y `ARRANCAR.bat` se detiene con aviso.

## Verificación realizada (cloud)

- Push de commits B1 a `origin/main` en este turno.
- Build frontend y health B1 verificados en entorno agente (no PostgreSQL Windows del usuario).
