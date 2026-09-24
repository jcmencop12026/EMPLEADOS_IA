import type { ContextualHelpContent } from "../components/ContextualHelp";

export const HELP_MESA_AYUDA: ContextualHelpContent = {
  title: "Mesa de Ayuda",
  summary:
    "Gestione solicitudes, incidentes, consultas y problemas recurrentes con clasificación, prioridad, SLA y trazabilidad.",
  sections: [
    {
      heading: "Flujo del caso",
      body: "Solicitud → clasificación → asignación → diagnóstico → resolución → validación → cierre.",
    },
    {
      heading: "Prioridad",
      body: "La prioridad se sugiere según impacto y urgencia. Evite marcar todo como urgente; ajustes requieren motivo.",
    },
    {
      heading: "Autoservicio",
      body: "Antes de abrir un caso, busque soluciones conocidas o casos similares abiertos.",
    },
  ],
};

export const HELP_CASO_DETALLE: ContextualHelpContent = {
  title: "Detalle del caso",
  summary: "Revise resumen, actividad, diagnóstico, evidencias, SLA y trazabilidad en las pestañas.",
  sections: [
    {
      heading: "Diagnóstico",
      body: "Registre síntoma, hipótesis y causa validada por separado. No presente hipótesis como causa confirmada.",
    },
    {
      heading: "Validación",
      body: "Resuelto no es lo mismo que cerrado: el solicitante puede validar antes del cierre definitivo.",
    },
  ],
};

export const ESTADO_ETIQUETAS: Record<string, string> = {
  NUEVO: "Nuevo",
  CLASIFICADO: "Clasificado",
  ASIGNADO: "Asignado",
  EN_ANALISIS: "En análisis",
  EN_PROCESO: "En progreso",
  PENDIENTE_USUARIO: "Esperando información",
  PENDIENTE_TERCERO: "Esperando tercero",
  RESUELTO: "Resuelto",
  VALIDACION_PENDIENTE: "Validación pendiente",
  CERRADO: "Cerrado",
  CANCELADO: "Cancelado",
};

export const SLA_ETIQUETAS: Record<string, string> = {
  DENTRO: "En tiempo",
  PROXIMO: "Próximo a vencer",
  VENCIDO: "Vencido",
  NO_APLICA: "Sin SLA",
};
