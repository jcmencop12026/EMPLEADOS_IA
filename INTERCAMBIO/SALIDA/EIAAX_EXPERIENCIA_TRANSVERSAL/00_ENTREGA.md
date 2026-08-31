# EIAAX — Experiencia Transversal

> **EIAAX — EXPERIENCIA TRANSVERSAL FINALIZADA**  
> **SHA inicial:** `7e9abba11f4c4f216142c6c70d662229ffc585bb` (BP1 certificado)  
> **Rama:** `cursor/eiaax-experiencia-transversal-9a85` (sin merge a rama central)  
> **Agente:** D — Desarrollo  
> **Voz/TTS:** No disponible (no bloqueante)

---

## Resumen ejecutivo

Infraestructura reutilizable de experiencia EIAAX sobre BP1 certificado, **sin rediseño artístico global** ni alteración de lógica de negocio. Preserva sidebar C2, funcionalidad existente y prepara integración posterior por GENERAL.

| Área | Entregable |
|------|------------|
| Identidad central | `lib/brand.ts`, `lib/identityAssets.ts`, `BrandMark` |
| Niveles de marca | HERO, CORPORATIVO, EX 08, MICRO |
| App Shell | Sidebar colapsable + identidad por nivel + topbar EIAAX |
| Claro/oscuro | Tokens semánticos + `ThemeProvider` |
| Tabla reutilizable | `EiaaxTable` |
| Ayuda contextual | `ContextualHelp` |
| BP1 P2 visual | Vista Entidad legible, labels español, CSS faltante |
| Pruebas | `vitest` 8 tests + `npm run build` PASS |

---

## Documentación

| Doc | Contenido |
|-----|-----------|
| [01_COMPONENTES.md](./01_COMPONENTES.md) | API de componentes transversales |
| [02_TOKENS_IDENTIDAD.md](./02_TOKENS_IDENTIDAD.md) | Tokens CSS, niveles de marca, activos |
| [03_NAVEGACION_SHELL.md](./03_NAVEGACION_SHELL.md) | AppShell, sidebar, header, org context |
| [04_TABLA_AYUDA.md](./04_TABLA_AYUDA.md) | EiaaxTable y ContextualHelp |
| [05_PRUEBAS_CAPTURAS.md](./05_PRUEBAS_CAPTURAS.md) | Build, tests, capturas |
| [06_P0_P1_P2.md](./06_P0_P1_P2.md) | Clasificación hallazgos |
| [07_INTEGRACION_GENERAL.md](./07_INTEGRACION_GENERAL.md) | Notas para merge GENERAL / BP2 |

---

## SHA

| Etapa | SHA |
|-------|-----|
| Inicial (BP1) | `7e9abba11f4c4f216142c6c70d662229ffc585bb` |
| Final | `817960a` — `feat(experiencia): sistema transversal EIAAX` |

---

## Veredicto

**Experiencia transversal APTA para integración GENERAL** — infraestructura base lista; migración masiva de tablas y tema global quedan como evolución incremental.
