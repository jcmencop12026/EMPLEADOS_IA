# Aplicar B1 en `D:\EMPLEADOS_IA` (si `git pull` aún muestra fase B0)

El commit **B1** puede no estar en GitHub hasta que lo integres con el **bundle** o hagas `push` desde tu PC.

## Método 1 — Git bundle (recomendado)

1. Descarga del agente Cursor el archivo **`EMPLEADOS_IA_B1.bundle`** (artefactos de la ejecución).
2. Copia el bundle a `D:\EMPLEADOS_IA\EMPLEADOS_IA_B1.bundle`.
3. PowerShell:

```powershell
cd D:\EMPLEADOS_IA
git pull .\EMPLEADOS_IA_B1.bundle main
git push origin main
CREAR_ENTORNO.bat
ARRANCAR.bat
```

4. Comprueba: http://127.0.0.1:8010/health → `"phase": "B1"`.
5. Web: http://127.0.0.1:5180 — `admin` / `Admin2026*`.

## Método 2 — Solo `git pull` (si ya subiste B1 a GitHub)

```powershell
cd D:\EMPLEADOS_IA
git pull origin main
CREAR_ENTORNO.bat
ARRANCAR.bat
```

## Verificación rápida

```powershell
curl http://127.0.0.1:8010/health
```

Debe incluir `"phase":"B1"`.
