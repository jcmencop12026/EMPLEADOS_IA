# B1 — Núcleo mínimo (auth, org, auditoría, UI)

## Verificación realizada

| Prueba | Resultado |
|--------|-----------|
| Backend `/health` phase B1 | CI cloud (uvicorn import) |
| Login JWT + `/api/auth/me` | CI cloud |
| Frontend `npm run build` | CI cloud |
| Windows ARRANCAR.bat | Pendiente usuario |
| Push GitHub desde agente cloud | Bloqueado (403 cursor bot) — usar `RECIBIR_B1_OFFLINE.ps1` o agente local |

## Credenciales bootstrap (solo local)

- Usuario: `admin`
- Contraseña: `Admin2026*`
- Organización: `Empresa demo`

## URLs

- Frontend: http://127.0.0.1:5180
- API: http://127.0.0.1:8010/docs
- BD SQLite: `data/enterprise_ai_os.db`

## Actualizar en PC

```powershell
cd D:\EMPLEADOS_IA
git pull origin main
CREAR_ENTORNO.bat
ARRANCAR.bat
```
