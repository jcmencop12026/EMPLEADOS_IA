# 05 — Pruebas y capturas

## Build frontend

```bash
cd frontend && npm run build
```

**Resultado:** PASS (Vite 6, 147 módulos)

## Tests componentes (Vitest)

```bash
cd frontend && npm test
```

| Suite | Tests |
|-------|-------|
| `brand.test.ts` | 2 |
| `identityAssets.test.ts` | 2 |
| `evaluacionLabels.test.ts` | 4 |
| **Total** | **8 PASS** |

## Recorrido navegador (Puppeteer 1280×900)

| Captura | Escenario |
|---------|-----------|
| `exp_sidebar_expanded.png` | Sidebar expandido + identidad corporativa |
| `exp_sidebar_collapsed.png` | Sidebar colapsado + marca EX 08 |
| `exp_theme_dark.png` | Tema oscuro activo |
| `exp_evaluaciones_tabla.png` | EiaaxTable en lista evaluaciones |

Ruta: `/opt/cursor/artifacts/screenshots/`

## Verificaciones manuales

- [x] Sidebar colapsable con persistencia
- [x] Cambio claro/oscuro
- [x] Tabla: búsqueda, orden, columnas, paginación
- [x] Ayuda contextual en evaluaciones
- [x] Vista Entidad sin JSON como UI final
- [x] Textos en español en superficies BP1 tocadas
