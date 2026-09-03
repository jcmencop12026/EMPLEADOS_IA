/** Navegacion principal — fuente unica para sidebar y resolucion de home. */
export type NavItem = { to: string; label: string; end?: boolean };
export type NavSection = { id: string; label: string; items: NavItem[]; future?: boolean };

/** Uso cotidiano — visible por defecto. */
export const MENU_PRIMARY: NavSection[] = [
  {
    id: "inicio",
    label: "Inicio",
    items: [
      { to: "/", label: "Centro de Control", end: true },
      { to: "/ayuda/guia", label: "Guía rápida" },
    ],
  },
  {
    id: "trabajo",
    label: "Trabajo",
    items: [
      { to: "/trabajo", label: "Mi trabajo" },
      { to: "/operaciones", label: "Operaciones" },
      { to: "/aprobaciones", label: "Aprobaciones" },
    ],
  },
  {
    id: "empresas",
    label: "Empresas",
    items: [
      { to: "/empresas", label: "Empresas y prospectos" },
      { to: "/evaluaciones", label: "Evaluaciones" },
      { to: "/oportunidades", label: "Oportunidades" },
    ],
  },
  {
    id: "empleados",
    label: "Empleados IA",
    items: [
      { to: "/directorio", label: "Directorio" },
      { to: "/automatizaciones", label: "Automatizaciones" },
    ],
  },
  {
    id: "resultados",
    label: "Resultados",
    items: [
      { to: "/resultados", label: "Valor y resultados" },
      { to: "/costos-valor", label: "Costos y valor" },
      { to: "/comunicaciones", label: "Informes" },
    ],
  },
];

/** Administración y módulos avanzados — sección colapsable. */
export const MENU_ADVANCED: NavSection[] = [
  {
    id: "analisis",
    label: "Análisis avanzado",
    items: [
      { to: "/lineas-base", label: "Líneas base" },
      { to: "/comercial", label: "Comercial" },
      { to: "/centro-negocios", label: "Centro de Negocios" },
      { to: "/arquitecto-transformacion", label: "Arquitecto transformación" },
      { to: "/centro-confianza", label: "Centro de Confianza" },
      { to: "/diagnosticos", label: "Diagnósticos" },
      { to: "/inteligencia-externa", label: "Inteligencia externa" },
      { to: "/senales", label: "Señales" },
      { to: "/implementacion", label: "Implementación" },
      { to: "/ejecuciones", label: "Ejecuciones" },
      { to: "/operaciones/solicitud", label: "Nueva solicitud" },
      { to: "/conocimiento", label: "Conocimiento" },
      { to: "/tco", label: "TCO" },
      { to: "/partners", label: "Partners" },
      { to: "/continuidad", label: "Continuidad" },
      { to: "/soporte", label: "Mesa de Ayuda" },
      { to: "/integraciones", label: "Integraciones" },
      { to: "/aprendizaje", label: "Aprendizaje" },
      { to: "/optimizacion", label: "Optimización" },
      { to: "/gobernanza-datos", label: "Gobierno de datos" },
      { to: "/comercial/segmentacion", label: "Segmentación" },
      { to: "/salud/diagnostico", label: "Diagnóstico IPS" },
      { to: "/capacidades", label: "Capacidades" },
      { to: "/herramientas", label: "Herramientas" },
      { to: "/empleados/auditoria", label: "Auditoría empleados" },
      { to: "/test-lab", label: "Laboratorio" },
    ],
  },
  {
    id: "admin",
    label: "Administración",
    items: [
      { to: "/administracion/empresas", label: "Empresas plataforma" },
      { to: "/administracion/usuarios", label: "Usuarios" },
      { to: "/administracion/roles", label: "Roles y permisos" },
      { to: "/administracion/organizacion", label: "Organización" },
      { to: "/administracion/configuracion", label: "Configuración" },
      { to: "/administracion/proveedores-ia", label: "Proveedores IA" },
      { to: "/administracion/seguridad", label: "Seguridad" },
      { to: "/administracion/identidad", label: "Identidad empresarial" },
      { to: "/mi-seguridad", label: "Mi seguridad" },
      { to: "/notificaciones", label: "Notificaciones" },
      { to: "/auditoria", label: "Auditoría" },
    ],
  },
];

export const MENU: NavSection[] = [...MENU_PRIMARY, ...MENU_ADVANCED];
