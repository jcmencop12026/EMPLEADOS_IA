# EIAAX — CONVERGENCIA MAESTRO V1 (MACROBLOQUE)

## Identificación

| Campo | Valor |
|-------|-------|
| SHA final | `a36dfe9` |
| Rama | `cursor/convergencia-maestro-v1-85e4` |
| Base Windows certificada | `0014a4b01a3ccf3e849a6609c8c784873f20f497` |
| WINDOWS STARTUP BASE 0014a4b PRESERVADA | **SÍ** (`git diff 0014a4b -- scripts/windows/` vacío) |

## Resumen ejecutivo

Iteración de convergencia de producto centrada en **Centro de Control como consola maestra**, **navegación empresarial**, **acceso operativo a empresas**, **UX transversal** (ancho, KPIs compactos, asistente flotante) y **separación de demo IPS del flujo productivo**.

## A. Capacidades reutilizadas

- Centro de Control (`CentroControlPage`, `CentroControlCockpit`, API `/api/centro-control/resumen-ejecutivo`)
- Cabina empresa 10 pestañas (`EvaluacionConsolePage`)
- Evaluaciones / expedientes (`fetchEvaluaciones`, `fetchEvaluacion`)
- Presentación / Vista Empresa (rutas existentes)
- Siguiente acción (`SiguienteAccionPanel`)
- Asistente contextual (`ContextualAssistantProvider`, `EiaaxContextualAssistant`)
- EiaaxTable, publicación, FinOps, operaciones, RBAC multiempresa
- Infraestructura de ayuda (`ContextualHelp`)

## B. Capacidades integradas

- Selector de contexto **Todas / Empresa** en Centro de Control (`?expediente=`)
- Panel empresa en CC (`CentroControlEmpresaPanel`) con enlaces Cabina / Presentación / Ver como empresa
- Página operativa **Empresas y prospectos** (`/empresas`) con acciones Cabina / Centro / Presentar
- Menú reorganizado: Inicio, Trabajo, Empresas, Empleados IA, Análisis, Administración
- Guía rápida V1 (`/ayuda/guia`) — 15 pasos del recorrido EIAAX
- Acciones Cabina/Centro en listado de Evaluaciones
- Estados vacíos explicativos en Ejecuciones, Aprobaciones, Automatizaciones

## C. Capacidades realmente nuevas

- `EmpresasProspectosPage.tsx`
- `CentroControlEmpresaPanel.tsx`
- `GuiaRapidaPage.tsx` + `guiaRapidaHelp.ts`
- Tests `test_convergencia_maestro_v1.py`

## D. Qué NO se reconstruyó

- Bootstrap Windows (`scripts/windows/**`)
- Entidades duplicadas, dossier, empleados, economía, publicación
- Centro de Control backend (sin API paralela)
- Diagnóstico IPS motor (solo UX: demo → laboratorio colapsable)

## E–Z. Áreas por sección

| Sección | Estado | Notas |
|---------|--------|-------|
| H. Centro Control global | Integrado | Tabs resumen/valor/operación/IA/salud preservados |
| I. Centro Control empresa | Integrado | Selector + panel empresa + enlaces presentación |
| J. Modo presentación | Reutilizado | Enlaces desde CC y Empresas |
| K. Cabina empresa | Mejorado | KPI strip compacta; PIIAX como badge |
| L. Navegación | Reorganizada | Capacidades avanzadas bajo Administración |
| M. Login | Refinado | SSO integrado en tarjeta; olvidó contraseña discreto |
| N. Identidad/logos | Sin cambio funcional | Preservado de iteración P1 |
| O. Configuración | Pendiente P2 | No bloqueante para esta iteración |
| P. Operaciones | Estados vacíos mejorados | CC conectado vía menú |
| Q. Diagnóstico IPS | Demo → laboratorio | Flujo productivo apunta a cabina |
| R. Empleados | Labels español madurez | AUTONOMOUS_CONTROLLED → Autónomo controlado |
| S. Auditor | Sin cambio | Capacidad preservada |
| T. Automatizaciones | Estado vacío explicativo | CTA crear |
| U. Valor/FinOps | Reutilizado en CC | Sin formulario nuevo |
| V. Resultados | Reutilizado | Integrado en panel empresa |
| W. Informes | Reutilizado | Menú → comunicaciones |
| X. Contrato | Reutilizado en cabina | Sin duplicar |
| Y. Vista Empresa | Reutilizado | Enlace Ver como empresa |
| Z. Asistente | Mejorado | Flotante compacto, cerrado por defecto |
| AA. Manual/ayuda | Nuevo | Guía rápida 15 pasos |

## Pruebas

| Suite | Resultado |
|-------|-----------|
| `npm run build` | PASS |
| `test_convergencia_maestro_v1.py` | 6 passed |
| `test_v1_cierre_p1.py` | 6 passed |
| Bundle convergencia (47 tests) | PASS |
| Alembic heads | 1 (`1820a1b2c3d4e`) |

## Auditoría visual

- Build y layout CSS verificados estáticamente
- Login API funcional (`admin` / `Admin2026*`)
- Auditoría navegador completa pendiente de revisión humana Windows (entorno cloud con límite de uso subagente visual)

## Defectos / P2 restantes

- Configuración: rediseño con pestañas (P2)
- Ficha empleado: jerarquía acciones laborales (P2)
- Enriquecimiento profundo pestañas Contrato/Valor/Informes en cabina (parcial, reutiliza APIs)
- Auditoría visual 30+ pantallas en Windows real recomendada

## Comando único revisión humana (Windows)

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

Credenciales: `admin` / `Admin2026*`

## Evidencia scripts/windows

```
git diff 0014a4b01a3ccf3e849a6609c8c784873f20f497 -- scripts/windows/
# (vacío)
```
