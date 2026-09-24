import type { ContextualHelpContent } from "../components/ContextualHelp";

export const HELP_RESULTADOS_HUB: ContextualHelpContent = {
  screen: "Inteligencia de resultados",
  purpose: "Consulta indicadores dinámicos, compara ANTES / PROYECTADO / REAL y accede a informes de impacto.",
  needs: "Permiso resultados.view. Para gestionar indicadores: resultados.manage.",
  steps: [
    "Filtre por expediente o busque por nombre de indicador.",
    "Revise la tabla: PROYECTADO nunca equivale a resultado conseguido.",
    "Genere un informe de impacto desde un expediente vinculado.",
  ],
  expected: "Visión clara del impacto medido y proyectado con trazabilidad.",
};

export const HELP_ANTES_PROYECTADO_REAL: ContextualHelpContent = {
  screen: "ANTES · PROYECTADO · REAL",
  purpose: "Capa semántica unificada de medición de impacto.",
  sections: [
    { title: "ANTES", body: "Línea base o valor inicial registrado con evidencia." },
    { title: "PROYECTADO", body: "Expectativa o inferencia — se muestra diferenciado, no como logro." },
    { title: "REAL", body: "Medición posterior con evidencia registrada. Sin REAL: «sin medición posterior»." },
  ],
};
