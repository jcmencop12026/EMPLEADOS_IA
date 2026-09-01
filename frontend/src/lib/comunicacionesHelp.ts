import type { ContextualHelpContent } from "../components/ContextualHelp";

export const HELP_CENTRO_INFORMACION: ContextualHelpContent = {
  screen: "Centro de Información y Comunicaciones",
  purpose: "Gestiona notificaciones operativas, entrega de informes, plantillas y trazabilidad de comunicaciones EIAAX.",
  needs: "Permiso communications.view. Para enviar: communications.send.",
  expected: "Bandeja con estados claros, sin duplicar el motor de notificaciones 820.",
};

export const HELP_ENTREGA_INFORME: ContextualHelpContent = {
  screen: "Entrega de informe",
  purpose: "Comparte un informe de impacto con destinatarios autorizados, fijando la versión entregada.",
  expected: "Informes INTERNO no pueden publicarse como visibles para entidad. REAL y PROYECTADO se distinguen en el contenido.",
};
