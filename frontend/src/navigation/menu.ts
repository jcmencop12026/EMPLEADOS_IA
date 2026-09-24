/** Navegacion principal — fuente unica para sidebar y resolucion de home. */
export type NavItem = { to: string; label: string; end?: boolean; help?: string };
export type NavSection = { id: string; label: string; items: NavItem[]; future?: boolean };

/** Uso cotidiano — visible por defecto. */
export const MENU_PRIMARY: NavSection[] = [
  {
    id: "inicio",
    label: "Inicio",
    items: [
      { to: "/", label: "Centro de Control", end: true, help: "Use esta consola para dirigir el ciclo completo de una empresa o prospecto. Seleccione la organización y EIAAX le mostrará qué sabemos, qué falta, qué encontró, cuánto puede valer, qué requiere decisión y cuál es la siguiente acción." },
      { to: "/ayuda/guia", label: "Guía rápida", help: "Consulte el recorrido práctico de EIAAX cuando necesite saber qué hacer a continuación. Le orienta desde seleccionar una empresa hasta solicitar información, analizarla, presentar resultados e iniciar la implementación." },
    ],
  },
  {
    id: "trabajo",
    label: "Trabajo",
    items: [
      { to: "/trabajo", label: "Mi trabajo", help: "Empiece aquí cuando quiera saber qué requiere su atención hoy. EIAAX reúne pendientes y prioridades y le permite continuar cada tarea sin perder la empresa, expediente o decisión relacionada." },
      { to: "/operaciones", label: "Operaciones", help: "Compruebe qué procesos y ejecuciones están activos, cuáles avanzan correctamente y cuáles presentan incidencias. Use esta vista para intervenir antes de que un retraso afecte resultados o compromisos." },
      { to: "/aprobaciones", label: "Aprobaciones", help: "Aquí llegan las acciones que EIAAX no debe ejecutar sin autorización humana. Revise evidencia, riesgo e impacto y luego apruebe, rechace o devuelva la decisión para ajuste." },
    ],
  },
  {
    id: "empresas",
    label: "Empresas",
    items: [
      { to: "/empresas", label: "Empresas y prospectos", help: "Seleccione o registre la organización con la que va a trabajar. Al entrar en una empresa, EIAAX conserva ese contexto mientras solicita información, evalúa, diagnostica, detecta oportunidades, valora e implementa soluciones." },
      { to: "/evaluaciones", label: "Evaluaciones", help: "Abra el expediente de una empresa para revisar qué sabemos, qué falta y qué evidencia respalda cada conclusión. Desde aquí completa o valida información antes de permitir que EIAAX eleve la confianza del diagnóstico." },
      { to: "/oportunidades", label: "Oportunidades", help: "Revise las mejoras que EIAAX detectó y compárelas por impacto, viabilidad y valor. Use esta sección para decidir cuáles estudiar, presentar o convertir en iniciativas concretas." },
    ],
  },
  {
    id: "empleados",
    label: "Empleados IA",
    items: [
      { to: "/directorio", label: "Directorio", help: "Conozca qué empleado IA puede asumir cada función. Revise su misión, responsabilidades, capacidades y estado antes de asignarle trabajo o evaluar su desempeño." },
      { to: "/automatizaciones", label: "Automatizaciones", help: "Controle qué tareas se ejecutan automáticamente, cuándo se disparan y qué resultado producen. Úsela para detectar fallos, evitar ejecuciones innecesarias y comprobar que cada automatización aporta valor." },
    ],
  },
  {
    id: "resultados",
    label: "Resultados",
    items: [
      { to: "/resultados", label: "Valor y resultados", help: "Compruebe si las acciones implementadas están produciendo el beneficio esperado. Compare metas, resultados obtenidos y valor realizado para decidir si mantener, corregir o escalar la intervención." },
      { to: "/costos-valor", label: "Costos y valor", help: "Compare cuánto cuesta ejecutar la solución con el valor que puede generar y el que realmente ha generado. Úsela para vigilar retorno, desviaciones y sostenibilidad económica." },
      { to: "/comunicaciones", label: "Informes", help: "Prepare la información que se comunicará a dirección o al cliente: hallazgos, decisiones, resultados, compromisos y próximos pasos. Verifique siempre qué contenido está autorizado antes de publicarlo externamente." },
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
