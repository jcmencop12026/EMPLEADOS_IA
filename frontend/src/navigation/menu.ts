/** Navegacion principal — fuente unica para sidebar y resolucion de home. */
export type NavItem = { to: string; label: string; end?: boolean };
export type NavSection = { id: string; label: string; items: NavItem[]; future?: boolean };

export const MENU: NavSection[] = [
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
      { to: "/operaciones", label: "Centro de operaciones" },
      { to: "/operaciones/solicitud", label: "Nueva solicitud" },
      { to: "/ejecuciones", label: "Ejecuciones" },
      { to: "/aprobaciones", label: "Aprobaciones" },
      { to: "/automatizaciones", label: "Automatizaciones" },
    ],
  },
  {
    id: "empresas",
    label: "Empresas",
    items: [
      { to: "/empresas", label: "Empresas y prospectos" },
      { to: "/oportunidades", label: "Oportunidades" },
      { to: "/evaluaciones", label: "Evaluaciones EIAAX" },
    ],
  },
  {
    id: "empleados",
    label: "Empleados IA",
    items: [
      { to: "/directorio", label: "Directorio" },
      { to: "/empleados/auditoria", label: "Auditoría / Evolución" },
      { to: "/capacidades", label: "Capacidades" },
      { to: "/herramientas", label: "Herramientas" },
      { to: "/conocimiento", label: "Conocimiento" },
      { to: "/test-lab", label: "Laboratorio de pruebas" },
    ],
  },
  {
    id: "analisis",
    label: "Análisis y resultados",
    items: [
      { to: "/resultados", label: "Valor y resultados" },
      { to: "/costos-valor", label: "Costos y valor" },
      { to: "/comunicaciones", label: "Informes y comunicaciones" },
      { to: "/centro-confianza", label: "Centro de Confianza" },
    ],
  },
  {
    id: "admin",
    label: "Administración",
    items: [
      { to: "/lineas-base", label: "Líneas base e impacto" },
      { to: "/comercial", label: "Comercial y valor" },
      { to: "/centro-negocios", label: "Centro de Negocios" },
      { to: "/arquitecto-transformacion", label: "Arquitecto de Transformación" },
      { to: "/tco", label: "TCO y aliados" },
      { to: "/implementacion", label: "Implementación" },
      { to: "/comercial/segmentacion", label: "Segmentación y planes" },
      { to: "/partners", label: "Partners y aliados" },
      { to: "/senales", label: "Señales y fuentes" },
      { to: "/diagnosticos", label: "Diagnósticos" },
      { to: "/inteligencia-externa", label: "Inteligencia externa" },
      { to: "/continuidad", label: "Continuidad" },
      { to: "/soporte", label: "Mesa de Ayuda" },
      { to: "/integraciones", label: "Integraciones" },
      { to: "/aprendizaje", label: "Aprendizaje" },
      { to: "/optimizacion", label: "Optimización" },
      { to: "/gobernanza-datos", label: "Gobierno de datos" },
      { to: "/mi-seguridad", label: "Mi seguridad" },
      { to: "/notificaciones", label: "Notificaciones" },
      { to: "/auditoria", label: "Auditoría" },
      { to: "/salud/diagnostico", label: "Diagnóstico IPS (vertical)" },
      { to: "/administracion/empresas", label: "Empresas plataforma" },
      { to: "/administracion/usuarios", label: "Usuarios" },
      { to: "/administracion/roles", label: "Roles y permisos" },
      { to: "/administracion/organizacion", label: "Organización" },
      { to: "/administracion/configuracion", label: "Configuración" },
      { to: "/administracion/proveedores-ia", label: "Proveedores IA" },
      { to: "/administracion/seguridad", label: "Seguridad" },
      { to: "/administracion/identidad", label: "Identidad empresarial" },
    ],
  },
];
