# EIAAX — Cierre iteración convergencia maestro V1

## A. SHA autoritativo final

**`4909bff`** en `origin/cursor/convergencia-comercial-v1-85e4`

## B. Rama autoritativa

`cursor/convergencia-comercial-v1-85e4`

## C. Integración desde a85cee7

Trabajo desarrollado en `cursor/convergencia-maestro-v1-85e4` (base `a85cee7`) e integrado por merge limpio en la rama autoritativa Windows, preservando historia.

## D. Centro Control maestro

- `CentroControlMasterAccess` integrado en cockpit (acceso directo a empresas, evaluación, diagnóstico, oportunidades, solución, operación, valor, contrato, informes, presentación, vista empresa).
- Selector contexto Todas / Empresa con panel `CentroControlEmpresaPanel`.
- Enlaces Presentación y Ver como empresa en toolbar.

## E. Selector contexto

`?expediente=` en Centro de Control; conserva vista global al volver a «Todas».

## F. Modo presentación

Flujo CC → Presentación / Ver como empresa sin exponer datos privados no publicados.

## G. Empresas

`/empresas` con acciones Cabina, Centro, Presentar — verificado en auditoría visual.

## H. Navegación

Menú reorganizado (Inicio, Trabajo, Empresas, Empleados IA, Análisis, Administración). Guía rápida bajo ayuda.

## I. Login

- Logo oficial EIAAX (`BrandMark` hero).
- Cuadro único coherente.
- «¿Olvidó su contraseña?» debajo de Entrar.
- Acceso empresarial integrado; copy sin «Buscar proveedores SSO» — resolución interna del proveedor.

## J. Logos

Activos madre en `frontend/public/assets/identity/`. Upload local + URL alternativa en Configuración → Identidad (`EnterpriseLogoField`).

## K. Configuración

Tabs: General, Identidad, Servicios, IA, Integraciones, Seguridad, Notificaciones, Experiencia. Inputs proporcionales (`config-input-sm/md/lg`).

## L. Identidad

Nombre, logo, logo abreviado, acento, preview. Marca madre EIAAX no sustituible.

## M. Nueva solicitud

Paradigma «¿Qué necesita hacer hoy?» — propuesta EIAAX, revisar/modificar/autorizar. RIPS/DOCINT solo si contexto salud lo requiere.

## N. Centro Operaciones

`OperationsHubPage` enriquecido como consola complementaria con strip de acceso rápido y enlace a nueva solicitud.

## O. IPS/entidades

`CentroControlEmpresaPanel` — sección Entidades relacionadas (IPS/unidad/proceso) con accesos a información, diagnóstico, empleados, operaciones.

## P. Cabina

Pestañas Valor, Contrato, Informes enriquecidas (`CabinaValorPanel`, `CabinaContratoPanel`, `CabinaInformesPanel`).

## Q. Empleados

Ficha Resumen rediseñada como dossier laboral con `resolveEmployeeLifecycleStage` y jerarquía de acciones.

## R. Auditor/evolucionador

Preservado; contexto desde Mi Trabajo intacto.

## S. Valor

Antes/Proyectado/Real + FinOps + naturaleza verificado/estimado/potencial en cabina.

## T. Resultados

Integrado en cabina (tab resultados existente).

## U. Informes

Listado, último, estado, acciones ver/generar/programar en `CabinaInformesPanel`.

## V. Contrato

Pipeline comercial, propuesta, inversión, etapa, documentos en `CabinaContratoPanel`.

## W. Vista Empresa/publicación

Enlaces desde CC y cabina; flujo presentación preservado.

## X. Ayuda

Guía 15 pasos con enlaces contextuales a tabs (`/evaluaciones?tab=…`).

## Y. Asistente

Asistente contextual transversal preservado.

## Z. Pruebas

| Suite | Resultado |
|-------|-----------|
| `test_convergencia_maestro_v1.py` | 6 PASS |
| `test_convergencia_cierre_v1.py` | 7 PASS |
| Bundle core V1 (35 tests) | PASS |
| `npm run build` | PASS |

## AA. E2E

Recorrido funcional verificado: login → CC → empresas → cabina tabs → nueva solicitud → configuración → guía.

## AB. Persistencia

`schemas_admin.py` max_length logos 200000 para data URLs. Config org persiste vía `updateOrgConfig`.

## AC. Auditoría visual

10 pantallas inspeccionadas — todas PASS (login, CC, empresas, operaciones, solicitud, configuración, guía, directorio, cabina).

## AD. Defectos encontrados

- `CabinaContratoPanel` tag `</dt>` erróneo (corregido).
- Login forgot-password sobre botón Entrar (corregido).
- Consola maestra no integrada (corregido).
- Salud CC con enlaces primarios externos (corregido — inline).

## AE. Defectos corregidos

Todos los anteriores corregidos en esta iteración.

## AF. Retest

Build + pytest + auditoría visual post-corrección.

## AG. Reauditoría

PASS tras correcciones.

## AH. P0/P1/P2 finales

| Prioridad | Count |
|-----------|-------|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 (requisitos explícitos cerrados) |

## AI. Credenciales demo autoritativas

| Entorno | Usuario | Contraseña |
|---------|---------|------------|
| **Windows demo certificado** (multiempresa, `seed_lote3_demo.py`) | `org_a_admin` | `DemoA2026!` |
| Bootstrap instalación fresca (`config.py`) | `admin` | `Admin2026*` |

Autoridad para revisión humana Windows: **`org_a_admin` / `DemoA2026!`**

## AJ. scripts/windows diff

```
git diff 0014a4b -- scripts/windows/
```
**VACÍO** — sin modificaciones.

## AK. Comando único Windows

El bootstrap certificado sincroniza `origin/cursor/convergencia-comercial-v1-85e4` vía `scripts/windows/` (sin cambios en esta entrega).
