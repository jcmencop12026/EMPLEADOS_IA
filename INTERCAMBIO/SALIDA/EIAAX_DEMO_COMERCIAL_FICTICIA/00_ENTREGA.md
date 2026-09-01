# EIAAX — Demo comercial ficticia + Presentación ejecutiva (V1)

## Identificación
| Campo | Valor |
|-------|-------|
| Rama | `cursor/demo-comercial-ficticia-9a85` |
| Base | `cursor/eiaax-centro-informacion-comunicaciones-9a85` |
| SHA inicial | `f32c8157d7f5576ba59f5ca895b88fbe7d06f8e9` |
| SHA final | *(ver commit)* |
| PR | *(draft, sin merge)* |

## Qué reutilizó (no duplicado)
- Expediente evaluación (`evaluacion_service`, `/evaluaciones`)
- Vista Entidad (`VistaEntidadPreview`, `get_vista_entidad`)
- Inteligencia Resultados (ANTES/PROY/REAL, `resultados_service`)
- Informe impacto (`InformeImpactoPage`, narrativa determinística)
- Diagnóstico IPS demo (`DiagnosticoIpsPage`, motor CONSULTOR)
- Centro de Control, Comercial/valor, Centro Información (entrega informes)
- `EiaaxTable`, `ContextualHelp`, tokens/tema existentes

## Qué construyó
- `DemoBanner` — etiqueta **DEMO — DATOS SIMULADOS**
- Hub `/demo` — recorrido guiado coherente
- Semilla unificada `POST /api/demo-comercial/semilla` + script `scripts/demo-comercial-ficticia.py`
- Presentación ejecutiva `/demo/presentacion/:expedienteId` — 4 audiencias (API filtrada, sin IP)
- CTA «Quiero evaluar mi empresa» → `/evaluaciones?nuevo=1&area=…` (flujo real)
- Informes periódicos `/demo/informes-periodicos` — plantillas por periodicidad/audiencia
- Tests `tests/test_demo_comercial_ficticia.py` (5 passed)

## Recorrido demo
1. `/demo` → Cargar demo ficticia (admin)
2. Diagnóstico IPS → Evaluación → Resultados → Informe → Presentación → Comercial → Centro Control
3. CTA evaluación real (sin mezclar datos)

## Recorrido presentación
`/demo/presentacion/{expediente_id}` — pestañas Gerencia / Operación / Sistemas / Financiero

## Build y pruebas
- `npm run build` — OK
- `pytest tests/test_demo_comercial_ficticia.py` — 5 passed

## P0 / P1 / P2
- **P0**: Ninguna
- **P1**: Scheduler envío informes periódicos real; PDF export presentación; gráficos dinámicos
- **P2**: Partners; marca visual assets en `public/assets/identity`

## Riesgos integración
- Demo aislada por `correlation_id` DEMO-COMERCIAL-V1 y prefijo `[DEMO]` en entidad
- Presentación rechaza expedientes no demo (403)
- Sin cambios a autoridades RBAC existentes; semilla requiere `evaluacion.manage`
