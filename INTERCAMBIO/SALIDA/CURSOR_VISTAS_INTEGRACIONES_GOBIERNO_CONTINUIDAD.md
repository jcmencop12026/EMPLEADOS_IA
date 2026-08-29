# EMPLEADOS IA — Vistas integraciones, gobierno y continuidad

**BASE:** `2e160b57c0aa1b5f89ec8672615df6c6e8283a88`  
**RAMA:** `cursor/vistas-integraciones-gobierno-continuidad`  
**HEAD:** `a19c3f61706c68d0446ca0b3025fb55464aee9cd`

---

## Objetivo

Hacer visualmente revisable el cableado WIRING 1330/1350/1360 sin nuevos motores ni duplicar servicios. Reutiliza APIs y componentes existentes.

---

## Rutas y vistas

| Vista | Ruta | Qué muestra |
|-------|------|-------------|
| Grilla integraciones | `/integraciones` | Nombre, tipo, estado, org, proveedor_ref, última ejecución, salud, error, política, continuidad, acciones |
| Detalle integración | `/integraciones/:id` | Cableado, ejecuciones, eventos, auditoría, salud, config sin secretos |
| Trazabilidad | `/integraciones/trazabilidad?cid=` | Timeline por `correlation_id` |
| Gobierno políticas | `/gobernanza-datos` → Políticas | Decisiones, alcance, clasificación, permitido/bloqueado |
| Gobierno accesos | `/gobernanza-datos` → Accesos | Acción, resultado, catálogo, evidencia |
| Continuidad | `/continuidad` | Servicios, respaldos, alertas, privacidad/restore |

---

## APIs reutilizadas / ampliadas

| Endpoint | Uso |
|----------|-----|
| `GET /api/integraciones/conectores?vista=operativa` | Grilla operativa |
| `GET /api/integraciones/conectores/:id/cableado` | Detalle wiring |
| `GET /api/integraciones/trazabilidad/:correlation_id` | Cadena trazable |
| `GET /api/gobierno-datos/politicas-proveedor` | Tab políticas (lectura con `datos.view`) |
| `GET /api/continuidad/tablero` | Alertas enriquecidas (severidad, fecha) |

---

## Recorrido visual

| Paso | Ruta | Qué se ve | Qué demuestra |
|------|------|-----------|---------------|
| 1 Login | `/login` | Acceso tenant | RBAC / multiempresa |
| 2 Integraciones | `/integraciones` | Grilla compacta con filtros | Cableado visible en lista |
| 3 Detalle | `/integraciones/:id` | Tab Cableado | Catálogo, política, preflight, continuidad, linaje |
| 4 Ejecuciones | Detalle → Ejecuciones | correlation_id por fila | Resultado técnico/funcional |
| 5 Trazabilidad | `/integraciones/trazabilidad` | Timeline etapas | Cadena solicitud→ejecución→auditoría |
| 6 Gobierno | `/gobernanza-datos` | Políticas + accesos | Permitido/bloqueado, evidencia |
| 7 Continuidad | `/continuidad` | Alertas + servicios | `INTEGRACION_SALUD_RECUPERADA`, degradación |
| 8 Privacidad | `/continuidad` → Privacidad | Restore bloqueado | `RESTORE_BLOQUEADO_PRIVACIDAD` |

---

## Seguridad UI

- Configuración sin campos secretos (backend ya redacta).
- `sanitizeDetail` en auditoría/trazabilidad oculta tokens/password.
- Acciones (probar/ejecutar/editar) según permisos `integraciones.*`.
- Sin modificar Centro de Control ni `cursor/fase2-central-integracion`.

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| `npm run build` | PASS |
| `test_wiring_1330_fase1` + `test_integraciones_1330` | 25 passed |

---

## Archivos principales

- `frontend/src/pages/IntegracionesPage.tsx`
- `frontend/src/pages/IntegracionDetailPage.tsx`
- `frontend/src/pages/IntegracionTrazabilidadPage.tsx`
- `frontend/src/pages/GobernanzaDatosPage.tsx`
- `frontend/src/pages/ContinuidadPage.tsx`
- `backend/app/services/integration_service.py` (vista operativa + trazabilidad)
