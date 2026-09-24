/** Iconos de navegación — recursos Unicode existentes, sin dependencias nuevas. */
const NAV_ICONS: Record<string, string> = {
  "/": "⌂",
  "/ayuda/guia": "?",
  "/trabajo": "☰",
  "/operaciones": "⚙",
  "/aprobaciones": "✓",
  "/empresas": "🏢",
  "/evaluaciones": "📋",
  "/oportunidades": "◎",
  "/directorio": "👤",
  "/automatizaciones": "⟳",
  "/resultados": "📈",
  "/costos-valor": "₿",
  "/comunicaciones": "✉",
  "/notificaciones": "🔔",
  "/admin/usuarios": "⚙",
  "/admin/organizacion": "🏛",
  "/admin/roles": "🔐",
  "/admin/config": "⚙",
  "/admin/seguridad": "🛡",
};

export function navIconFor(to: string): string {
  return NAV_ICONS[to] ?? "•";
}
