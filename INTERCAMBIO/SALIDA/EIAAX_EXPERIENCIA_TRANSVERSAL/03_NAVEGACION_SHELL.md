# 03 — Navegación y App Shell

## Preservación C2

- `OrganizationContextBar` intacto en topbar
- `OrganizationProvider` sin cambios de lógica
- Menú desde `navigation/menu.ts` + RBAC
- Colapso de secciones: `eaios_menu_sections` (localStorage)
- Colapso sidebar: `eaios_menu_collapsed` (localStorage)

## Cambios de experiencia

| Elemento | Antes | Después |
|----------|-------|---------|
| Marca sidebar expandido | Texto estático | `BrandMark level="corporativo"` |
| Marca sidebar colapsado | Oculta | `BrandMark level="ex08"` |
| Topbar | «EMPLEADOS IA · Plataforma empresarial» | Product line + descriptor EIAAX |
| Tema | Solo media query parcial | Toggle claro/oscuro + tokens |

## Header

Orden en `.topbar-actions`:

1. `ThemeToggle`
2. `OrganizationContextBar`
3. Campana notificaciones

## Responsive

- Título topbar con ellipsis en viewports estrechos
- Consola evaluación: header apilable en `<768px`
