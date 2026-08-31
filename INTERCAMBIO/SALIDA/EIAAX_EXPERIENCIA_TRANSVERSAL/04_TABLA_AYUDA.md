# 04 — Tabla y ayuda contextual

## Superficies con EiaaxTable

| Pantalla | prefsKey | Características |
|----------|----------|-----------------|
| `EvaluacionesPage` | `evaluaciones_lista_v1` | Sort, búsqueda, columnas, paginación, badges estado |
| `EvaluacionConsolePage` (Impacto) | `eval_impacto_v1` | Indicadores ANTES/PROYECTADO/REAL |

**No migradas** (evolución futura): TrabajoPage, OportunidadesPage, AdminUsersPage — ya tienen patrones propios reutilizables como referencia.

## Superficies con ContextualHelp

| Pantalla | Contenido |
|----------|-----------|
| Lista evaluaciones | `HELP_EVALUACIONES_LISTA` |
| Formulario crear | `HELP_EVALUACION_CREAR` |
| Consola — Resumen | `HELP_CONSOLA_RESUMEN` |
| Consola — Análisis | `HELP_CONSOLA_ANALISIS` |
| Consola — Impacto | `HELP_CONSOLA_IMPACTO` |
| Consola — Vista Entidad | `HELP_CONSOLA_VISTA_ENTIDAD` |

## P2 BP1 cerrados en esta entrega

| Brecha | Acción |
|--------|--------|
| Vista Entidad JSON crudo | `VistaEntidadPreview` legible |
| Códigos técnicos visibles | `evaluacionLabels.ts` en lista y consola |
| CSS faltante (tabs, success, detail-dl) | Añadido en `styles.css` |
| Mensaje oportunidad con UUID | Mensaje genérico en español |
| Trazabilidad UUID truncado | Fechas localizadas + textos español |
