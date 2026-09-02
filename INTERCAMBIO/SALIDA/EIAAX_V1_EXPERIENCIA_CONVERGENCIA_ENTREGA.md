# EIAAX — Candidato V1 experiencia y convergencia

**SHA:** (ver commit final)  
**Rama:** `cursor/experiencia-v1-convergencia-85e4`  
**Base Windows:** `0014a4b` — **PRESERVADA**

## WINDOWS STARTUP BASE 0014a4b PRESERVADA: **SÍ**

```bash
git diff 0014a4b -- scripts/windows/
# (vacío)
```

Suite `ejecutar_tests_desarrollo_windows.ps1`: **PASS exit 0**

---

## A. Capacidades reutilizadas

| Área | Componente existente reutilizado |
|------|----------------------------------|
| Centro de Control | `CentroControlPage` + API `fetchCentroControlResumen` |
| Asistente | `submitWorkRequest` → `/api/assistant/ask` |
| Identidad | `BrandMark`, `resolveIdentityAsset`, `config_json` organización |
| Empleados IA | `DirectoryPage`, `EmployeeDetailPage`, API employees |
| Demo | `DemoBanner`, `DemoComercialPage` |
| Confianza | `fetchCentroConfianza`, gobierno operacional |
| Config admin | `AdminConfigPage`, `fetchOrgConfig` / `updateOrgConfig` |

## B. Capacidades integradas

- Login empresarial con `BrandMark` y copy EIAAX (sin EMPLEADOS IA en pantalla de acceso)
- Cockpit ejecutivo en Centro de Control (`CentroControlCockpit`)
- Asistente contextual persistente (`EiaaxContextualAssistant`) en Centro de Control
- Identidad empresarial en configuración (nombre, logos, color de acento)
- Topbar con empresa + atribución EIAAX
- Estados vacíos accionables en Directorio Empleados IA
- Centro de Confianza compacto con tablas

## C. Capacidades nuevas (mínimas)

- Activos SVG `eiaax-corporativo.svg`, `ex-08.svg`, `eiaax-hero.svg`
- Hook `useEnterpriseIdentity`
- Campos branding en `OrgConfig` (backend `config_json`)

## D. Defectos corregidos

| Defecto | Corrección |
|---------|------------|
| "Inicio de sesión · EMPLEADOS IA" en login | Eliminado; copy EIAAX |
| Sesión vencida en visita inicial | Solo si hubo 401 real (`eaios_session_expired`) |
| Logo roto/ausente | SVG en `/assets/identity/` |
| Centro de Control disperso | Cockpit jerárquico A–F |
| Empleados IA vacío sin guía | Empty state + CTA diagnóstico/demo/crear |
| Centro de Confianza con tarjetas enormes | Layout compacto + tablas |

## E–F. UX transversal

- Una pantalla / dominio visual en Centro de Control y Confianza
- Español completo en textos modificados
- Jerarquía ejecutiva, menos scroll, ancho aprovechado

## G–P. Flujo y módulos (estado)

| Módulo | Estado V1 candidato |
|--------|---------------------|
| Login/identidad | Corregido visualmente |
| Centro de Control operacional | Cockpit integrado |
| Centro estratégico | Existente (`/centro-estrategico`) — sin duplicar |
| Empresa/Vista empresa | Enlaces desde cockpit → `/mi-espacio`, evaluaciones |
| Diagnóstico → Solución IA | CTA desde directorio vacío → `/diagnosticos` |
| Empleados IA | Directorio con empty state; detalle existente |
| Oportunidades/Valor/FinOps | Pestañas CC existentes + cockpit resumen |
| Presentación/Demo | Enlaces publicación en cockpit |
| Informes/gráficos | Componentes existentes en módulos dedicados |

## Q–S. Identidad, ayuda, tablas

- Identidad centralizada en Admin → Configuración
- Asistente contextual (no chat genérico)
- Tablas compactas en cockpit/confianza; migración EiaaxTable global diferida

## T. Pruebas

| Suite | Resultado |
|-------|-----------|
| `npm run build` | PASS |
| `ejecutar_tests_desarrollo_windows.ps1` | PASS exit 0 |
| Backend representativo (RBAC, orchestrator, MVP) | 32 passed |
| `git diff 0014a4b -- scripts/windows/` | Vacío |

## U–V. Auditoría visual / P2 restantes

- Migración masiva de tablas legacy a `EiaaxTable`: P2
- Cabina empresa con pestañas unificadas: parcial (rutas existen dispersas)
- Gráficos adicionales en Centro de Control resumen: P2 (pestañas Valor/IA mantienen gráficos)

## W–X. Preservación arranque

**WINDOWS STARTUP BASE 0014a4b PRESERVADA: SÍ**

## Y. Comando único revisión Windows

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

**Credenciales demo:** las definidas por seed local (admin demo existente en instalación).

**Recorrido recomendado:** Login → Centro de Control (cockpit) → Directorio Empleados IA → Demo → Vista empresa → Centro estratégico → Centro de Confianza → Admin Configuración (identidad).
