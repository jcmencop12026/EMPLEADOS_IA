# CERTIFICACIÓN D — UX C2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** D  
**SHA:** `b19b04dd438f5b13b422e9a760f54fa074fb52ed`  
**Fecha:** 2026-08-31  
**Modo:** Revisión UX estática + build; sin rediseño; sin Sistema Identidad EIAAX

---

## Veredicto obligatorio

# C2 UX APTO

---

## Resumen

La UX C2 introduce **OrganizationContextBar** visible solo para usuarios con `platform.organization.view`, badge "Viendo: {organización}", y actualización de CC/Mi Trabajo al cambiar contexto. Home C1-R1, NoModulesPage y hotfix login **preservados**. Textos en español. Build frontend PASS.

| P0 UX | P1 UX | P2 UX |
|-------|-------|-------|
| 0 | 0 | 2 |

**Nota evidencia visual:** certificación basada en revisión de código fuente, estilos CSS y build exitoso. Capturas browser runtime no generadas en esta sesión (P2).

---

## Verificación visual/funcional (1–20)

| # | Control UX | Resultado | Evidencia |
|---|------------|-----------|-----------|
| 1 | ContextBar solo cuando corresponde | **PASS** | `if (!canSelectOrganization) return null` — requiere `platform.organization.view` |
| 2 | Selector comprensible | **PASS** | `<select>` con label "Organización:"; opción "(mi organización)" |
| 3 | Org activa identificable | **PASS** | `selectValue`; badge al ver otra org |
| 4 | "Viendo: {organización}" correcto | **PASS** | `effectiveOrganizationName` en badge L47-49 |
| 5 | Cambio org actualiza CC | **PASS** | `CentroControlPage` → `fetchCentroControlResumen(periodo, organizationQueryParam)` |
| 6 | Cambio org actualiza Mi Trabajo | **PASS** | `TrabajoPage` → `organization_id: organizationQueryParam` en params |
| 7 | Badge Mi Trabajo actualiza contexto | **PASS** | `AppShell` `fetchTrabajoResumen(organizationQueryParam)` + listener `ORGANIZATION_CONTEXT_EVENT` |
| 8 | Sin datos residuales tenant anterior | **PASS** | `useEffect` recarga al cambiar `organizationQueryParam` |
| 9 | Sidebar coherente | **PASS** | `MENU` sin cambio semántico; extraído en C1-R1 |
| 10 | Home/fallback C1-R1 | **PASS** | `HomePage`/`resolveHomeRoute` sin diff |
| 11 | Usuario restringido → primera vista | **PASS** | `HomePage` redirect logic intacta |
| 12 | NoModulesPage preservada | **PASS** | Sin diff |
| 13 | Login/hotfix preservado | **PASS** | `LoginPage.tsx` sin diff C1-R1→C2 |
| 14 | MFA/SSO preservados | **PASS** | Sin diff auth frontend |
| 15 | Textos en español | **PASS** | "Organización:", "Viendo:", "Sin módulos habilitados", etc. |
| 16 | Sin botones rotos/desbordados | **PASS** | CSS `.org-context-bar` con flex/gap; build sin errores |
| 17 | Sin rutas muertas nuevas | **PASS** | Sin rutas nuevas en `App.tsx` |
| 18 | Sin loops/403 como home inicial | **PASS** | `HomePage` redirect solo si `home !== "/"` |
| 19 | Sin regresión visual CC material | **PASS** | CC añade banner contexto opcional; estructura secciones intacta |
| 20 | Sin regresión visual Mi Trabajo material | **PASS** | Banner contexto opcional `isViewingOtherOrganization` |

---

## Componentes UX C2 revisados

### OrganizationContextBar

- Render condicional SUPERADMIN/plataforma
- Select con org home + lista ACTIVE
- Badge `Viendo: {nombre}` solo en cross-org

### Estilos (`styles.css`)

```css
.org-context-bar { /* barra contexto */ }
.org-context-badge { /* badge viendo */ }
```

### CentroControlPage / TrabajoPage

- Banner informativo cuando `isViewingOtherOrganization`
- Recarga datos al cambiar `organizationQueryParam`

---

## Evidencia representativa (código)

| Escenario | Archivo | Elemento clave |
|-----------|---------|----------------|
| SUPERADMIN selector | `OrganizationContextBar.tsx` | `<select id="org-context-select">` |
| Badge contexto | `OrganizationContextBar.tsx` | `Viendo: {effectiveOrganizationName}` |
| CC con org | `CentroControlPage.tsx` | `organizationQueryParam` en fetch |
| Mi Trabajo con org | `TrabajoPage.tsx` | `organization_id: organizationQueryParam` |
| Tenant sin selector | `useOrganizationContext.tsx` | `canSelectOrganization: false` → fallback |

---

## Hallazgos P0 / P1 / P2

### P0 / P1

**Ninguno.**

### P2

| ID | Hallazgo |
|----|----------|
| P2-C2-D01 | Capturas visuales browser (SUPERADMIN A/B, tenant, CC, Mi Trabajo) no generadas — certificación por inspección código + build |
| P2-C2-D02 | Warning Vite chunk >500 kB — preexistente |

---

## Build

```bash
cd /tmp/cert-c2-a/frontend && npm ci && npm run build
# ✓ built in 1.39s — 134 modules
```

---

*Certificación D UX — 2026-08-31*
