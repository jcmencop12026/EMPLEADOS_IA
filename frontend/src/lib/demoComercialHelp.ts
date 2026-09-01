import type { ContextualHelpContent } from "../components/ContextualHelp";

export const HELP_DEMO_COMERCIAL: ContextualHelpContent = {
  title: "Demo comercial",
  summary:
    "Recorrido con datos ficticios para mostrar EIAAX antes de recibir información del prospecto. Todo está etiquetado como DEMO.",
  sections: [
    {
      heading: "Qué verá el prospecto",
      body: "Empresa ficticia, problema, indicadores ANTES/PROYECTADO/REAL, hallazgos, oportunidades, Empleados IA e informes.",
    },
    {
      heading: "Evaluación real",
      body: "Use «Quiero evaluar mi empresa» para iniciar el flujo real de expediente sin duplicar procesos comerciales.",
    },
  ],
};

export const AUDIENCIAS = [
  { id: "GERENCIA", label: "Gerencia" },
  { id: "OPERACION", label: "Operación" },
  { id: "SISTEMAS", label: "Sistemas" },
  { id: "FINANCIERO", label: "Financiero" },
] as const;

export type AudienciaId = (typeof AUDIENCIAS)[number]["id"];
