# 10 — Runtime y evidencia visual

## Entorno

- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8010` (SQLite dev)
- Frontend: `npm run dev -- --host 127.0.0.1 --port 5180`
- Login: `admin` / `Admin2026*`

**Importante:** Tras integración, reiniciar backend para cargar routers nuevos (`gobierno-operacional`, `partners`, `motor-economico`). Un proceso uvicorn previo sin reinicio devolvía 404.

## Capturas (`/opt/cursor/artifacts/screenshots/`)

| Archivo | Contenido |
|---------|-----------|
| `01_login_appshell.png` | Login + AppShell + Centro de Control |
| `02_evaluaciones.png` | Evaluaciones / ejecuciones |
| `03_expediente_siguiente_accion.png` | Centro operaciones + siguiente acción |
| `04_vista_entidad.png` | Detalle ejecución + trazabilidad |
| `05_partners_mb03.png` | Partners y aliados MB-03 (vacío, listo para alta) |
| `06_centro_confianza.png` | Centro de Confianza + menú |
| `07_theme_dark.png` | Tema oscuro |
| `08_sidebar_collapsed.png` | Sidebar colapsado |

## Recorridos runtime

| # | Recorrido | Estado |
|---|-----------|--------|
| 1 | EIAAX autónomo (org → expediente → evaluación → hallazgo → acción → oportunidad) | OK — sin PIIAX |
| 2 | Capacidad externa — proveedor no disponible, estado controlado | OK (tests + UI operaciones) |
| 3 | Aprobación sensible → gobierno → decisión → auditoría | OK (flujo aprobación visible) |
| 4 | Partner grant → acceso → revocación | OK (tests backend; UI MB-03 operativa) |
| 5 | Economía privada — autorizado sí / no autorizado no / Vista Entidad no expone | OK (tests motor + integración) |

## APIs verificadas en runtime

```bash
GET /api/gobierno-operacional/confianza  → 200 (controles con evidencia)
GET /api/partners                        → 200 (lista vacía)
GET /health/ready                        → 200
```

## Tema y navegación

- Toggle claro/oscuro funcional
- Sidebar expandir/colapsar funcional
- Menú muestra Centro de Confianza y Partners y aliados tras bootstrap permisos
