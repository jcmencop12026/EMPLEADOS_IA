import type { ContextualHelpContent } from "../ContextualHelp";

export const HELP_EVALUACIONES_LISTA: ContextualHelpContent = {
  screen: "Lista de evaluaciones EIAAX",
  purpose:
    "Gestiona expedientes de evaluación empresarial: entidad, información recopilada, análisis e impacto.",
  needs: "Permiso evaluacion.view. Para crear expedientes necesita evaluacion.manage.",
  steps: [
    "Use la búsqueda para filtrar por código, título o entidad.",
    "Filtre por estado si necesita ver solo borradores, en curso o cerrados.",
    "Pulse «Nueva evaluación» para abrir el formulario de creación.",
    "Haga clic en un código para abrir la consola del expediente.",
  ],
  example: "Busque «IPS-2026» para localizar evaluaciones de una entidad de salud.",
  expected: "Verá la lista actualizada con estados y niveles en español, sin códigos técnicos crudos.",
};

export const HELP_EVALUACION_CREAR: ContextualHelpContent = {
  screen: "Nueva evaluación",
  purpose: "Registra un expediente con el problema, objetivo y nivel de profundidad deseado.",
  needs: "Título, entidad y nivel mínimo. Problema y objetivo mejoran la precisión del análisis.",
  steps: [
    "Indique título descriptivo y nombre de la entidad evaluada.",
    "Seleccione nivel Preliminar para un primer diagnóstico rápido.",
    "Describa el problema y el objetivo de negocio.",
    "Pulse «Crear expediente» para ir a la consola.",
  ],
  expected: "Se crea el expediente en estado Borrador y abre la consola de trabajo.",
};

export const HELP_CONSOLA_RESUMEN: ContextualHelpContent = {
  screen: "Consola — Resumen",
  purpose: "Vista ejecutiva del expediente antes de profundizar en información y análisis.",
  steps: [
    "Revise problema, objetivo y área en el resumen.",
    "Complete información en la pestaña Información si el porcentaje es bajo.",
    "Ejecute la evaluación preliminar cuando tenga contexto mínimo.",
  ],
  expected: "Tras evaluar, se generan hallazgos en la pestaña Análisis EIAAX.",
};

export const HELP_CONSOLA_VISTA_ENTIDAD: ContextualHelpContent = {
  screen: "Vista Entidad",
  purpose: "Previsualiza exactamente lo que vería el cliente: solo hallazgos marcados visibles.",
  needs: "Permiso evaluacion.vista_entidad. Hallazgos deben tener «Visible para entidad» activado.",
  steps: [
    "En Análisis, marque visibles solo hallazgos validados.",
    "Abra esta pestaña antes de compartir resultados.",
    "Verifique impacto y oportunidades compartidas.",
  ],
  expected: "Presentación legible en español, sin datos internos ni JSON técnico.",
};

export const HELP_CONSOLA_IMPACTO: ContextualHelpContent = {
  screen: "Impacto e indicadores",
  purpose: "Compara valores ANTES, PROYECTADO (inferido) y REAL cuando existan mediciones.",
  sections: [
    {
      title: "Proyectado",
      body: "Valores inferidos por EIAAX — se muestran en cursiva/naranja. No sustituyen mediciones reales.",
    },
  ],
  expected: "Tabla clara por hallazgo con confianza asociada.",
};

export const HELP_CONSOLA_ANALISIS: ContextualHelpContent = {
  screen: "Análisis EIAAX",
  purpose: "Hallazgos generados con tipo de contenido, confianza y acciones de visibilidad u oportunidad.",
  steps: [
    "Distinga el hallazgo «Problema original» de oportunidades adicionales.",
    "Marque «Visible para entidad» solo tras validación.",
    "Cree oportunidad desde un hallazgo si procede comercialmente.",
  ],
};
