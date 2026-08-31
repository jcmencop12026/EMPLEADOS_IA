# 07 — Experiencia transversal

## Integrado selectivamente

| Componente | Origen | Estado |
|------------|--------|--------|
| `brand.ts`, `identityAssets.ts` | Experiencia | Integrado |
| `BrandMark` | Experiencia | AppShell |
| `ThemeProvider`, `useTheme`, `ThemeToggle` | Experiencia | `main.tsx` + AppShell |
| Tokens semánticos / tema claro-oscuro | Experiencia | Funcional |
| `EiaaxTable` | Experiencia | Disponible |
| `ContextualHelp`, `evaluacionHelp.ts` | Experiencia | Disponible |
| `VistaEntidadPreview` | Experiencia + BP2 | Consola evaluación |
| Sidebar persistente | Experiencia | AppShell |
| Labels español | Experiencia + BP2 | Parcial en evaluaciones |
| Centro de Confianza (página) | Gobierno + experiencia | `/centro-confianza` |

## Mecanismos de identidad

- HERO, CORPORATIVO, EX08, MICRO — sin inventar activos oficiales nuevos
- Resolución vía `identityAssets.ts`

## Resolución conflictos BP2

- Consola evaluación BP2 como superficie principal
- Componentes transversales como capa visual/reutilizable
- Una sola experiencia de navegación (menú unificado)

## Pendiente menor (P2)

- Fusión profunda de `EvaluacionConsolePage` estilos/densidad con todos los tokens de experiencia transversal
