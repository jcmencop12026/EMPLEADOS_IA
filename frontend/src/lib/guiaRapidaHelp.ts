import type { ContextualHelpContent } from "../components/ContextualHelp";

export const HELP_GUIA_RAPIDA: ContextualHelpContent = {
  screen: "Guía rápida — Primer ejercicio EIAAX",
  purpose:
    "Recorrido mínimo para operar EIAAX como un solo producto: desde la necesidad de una empresa hasta la presentación y medición de resultados.",
  needs: "Permisos de evaluación, diagnóstico y operación según su rol.",
  steps: [
    "Crear o seleccionar empresa o prospecto en Empresas y prospectos.",
    "Registrar necesidad y objetivo en la evaluación.",
    "Completar información adaptativa solicitada por EIAAX.",
    "Ejecutar diagnóstico y revisar hallazgos y oportunidades.",
    "Revisar la solución IA proyectada y autorizar empleados o automatizaciones propuestas.",
    "Presentar a la empresa en modo Presentación / Ver como empresa.",
    "Avanzar propuesta y contrato desde la cabina.",
    "Implementar, operar empleados IA y medir resultados.",
    "Generar informe y publicar lo acordado a la Vista Empresa.",
  ],
  expected:
    "Al finalizar, el operador comprende qué ocurre, qué falta, qué propone EIAAX y qué debe hacer a continuación — sin conocer la arquitectura interna.",
};

export const GUIA_PASOS = [
  { n: 1, titulo: "Empresa o prospecto", ruta: "/empresas", detalle: "Seleccione o cree la entidad desde Empresas y prospectos." },
  { n: 2, titulo: "Necesidad y objetivo", ruta: "/evaluaciones", detalle: "Registre el problema y el resultado esperado en la evaluación." },
  { n: 3, titulo: "Información adaptativa", ruta: "/evaluaciones", detalle: "Complete solo lo que EIAAX determine necesario según sector y profundidad." },
  { n: 4, titulo: "Diagnóstico", ruta: "/evaluaciones?tab=diagnostico", detalle: "Ejecute la evaluación desde la cabina — no desde laboratorios demo." },
  { n: 5, titulo: "Oportunidades", ruta: "/oportunidades", detalle: "Revise oportunidades detectadas y priorice atención." },
  { n: 6, titulo: "Solución IA", ruta: "/evaluaciones?tab=solucion", detalle: "EIAAX propone empleados, automatizaciones y arquitectura; usted revisa y autoriza." },
  { n: 7, titulo: "Autorización", ruta: "/aprobaciones", detalle: "Resuelva pendientes de gobierno antes de activar en producción." },
  { n: 8, titulo: "Presentación", ruta: "/empresas", detalle: "Use Presentar o Ver como empresa — sin costos internos ni datos no publicados." },
  { n: 9, titulo: "Propuesta y contrato", ruta: "/evaluaciones?tab=contrato", detalle: "Gestione etapa comercial desde la pestaña Contrato de la cabina." },
  { n: 10, titulo: "Implementación", ruta: "/implementacion", detalle: "Supervise hitos y riesgos de implementación." },
  { n: 11, titulo: "Operación", ruta: "/operaciones", detalle: "Monitoree empleados IA, ejecuciones y consumo." },
  { n: 12, titulo: "Resultados", ruta: "/evaluaciones?tab=resultados", detalle: "Compare antes, proyectado y real en la cabina." },
  { n: 13, titulo: "Informe", ruta: "/evaluaciones?tab=informes", detalle: "Genere o programe informes desde la cabina." },
  { n: 14, titulo: "Vista Empresa", ruta: "/evaluaciones?tab=vista-empresa", detalle: "Publique exactamente lo que verá la entidad." },
  { n: 15, titulo: "Centro de Control", ruta: "/", detalle: "Supervise todo desde la consola maestra con contexto global o por empresa." },
] as const;
