/** Instructivo operativo V1 — fuente única mantenible (10 partes). */

export type InstructivoParte = {
  id: number;
  titulo: string;
  resumen: string;
  puntos: string[];
};

export const INSTRUCTIVO_PARTES: InstructivoParte[] = [
  {
    id: 1,
    titulo: "Conceptos básicos",
    resumen: "Qué es cada pieza del ciclo EIAAX y cómo se relacionan.",
    puntos: [
      "Centro de Control: consola maestra para ver contexto, atención, valor y siguiente acción.",
      "Empresa/prospecto: entidad con la que trabaja; puede tener evaluación y expediente.",
      "Evaluación/expediente: cabina donde vive el ciclo comercial y operativo de una empresa.",
      "Información adaptativa: solo lo que EIAAX determina necesario según sector y profundidad.",
      "Diagnóstico, hallazgos y oportunidades: salida analítica con evidencia y confianza.",
      "Solución IA: empleados y automatizaciones propuestos — usted autoriza.",
      "Presentación vs Vista Empresa: reunión en vivo vs consulta posterior publicada.",
    ],
  },
  {
    id: 2,
    titulo: "Primer ejercicio — Clínica Demo Horizonte",
    resumen: "Recorrido DEMO con datos simulados claramente identificados.",
    puntos: [
      "Entrar al Centro de Control y seleccionar «Clínica Demo Horizonte» en contexto.",
      "Revisar necesidad: reprocesos en facturación/radicación/auditoría documental.",
      "Sincronizar información requerida y cargar documentos recibidos en Diagnóstico.",
      "Ejecutar evaluación, revisar hallazgos, oportunidades, solución y valor proyectado.",
      "Preparar presentación, ver Vista Empresa y volver al Centro de Control.",
    ],
  },
  {
    id: 3,
    titulo: "Información y documentos",
    resumen: "Dónde cargar archivos que entrega una IPS o empresa.",
    puntos: [
      "Ruta: Empresa → Evaluación → pestaña Diagnóstico → Información adaptativa.",
      "Use «Cargar documento» en cada ítem (PDF, Excel, CSV, contratos, soportes).",
      "Los archivos quedan versionados y vinculados al expediente — no volver a pedirlos.",
      "Conocimiento global (/conocimiento) es corpus IA; no sustituye evidencias del expediente.",
    ],
  },
  {
    id: 4,
    titulo: "Qué ve / qué no ve la empresa",
    resumen: "Separación estricta entre información publicable e interna.",
    puntos: [
      "La empresa ve solo contenido marcado publicable o en Vista Empresa.",
      "No ve: costos internos, márgenes, prompts, otras organizaciones, reglas privadas.",
      "Use «Ver como empresa» antes de publicar para validar exactamente la experiencia.",
    ],
  },
  {
    id: 5,
    titulo: "Presentación comercial",
    resumen: "Presentar en reunión vs publicar para consulta posterior.",
    puntos: [
      "Presentar en reunión: modo Presentación con audiencia seleccionada.",
      "Publicar: desde Vista Empresa / espacio externo tras validar visibilidad.",
      "Revise que hallazgos y oportunidades tengan visibilidad correcta antes de mostrar.",
    ],
  },
  {
    id: 6,
    titulo: "Después de contratar",
    resumen: "Transición de demo a implementación y operación real.",
    puntos: [
      "Contrato e implementación se gestionan desde la cabina (pestaña Contrato).",
      "La Vista Empresa evoluciona: demo → datos reales → operación → resultados.",
      "No prometa tiempo real si la fuente de datos es periódica o manual.",
    ],
  },
  {
    id: 7,
    titulo: "Operación diaria",
    resumen: "Dónde mirar cada mañana.",
    puntos: [
      "Centro de Control: atención requerida, aprobaciones, valor, salud.",
      "Centro de operaciones: trabajos activos, vencimientos, errores.",
      "Mi trabajo: bandeja personal priorizada.",
    ],
  },
  {
    id: 8,
    titulo: "Errores e incidencias",
    resumen: "Qué hacer cuando algo falla.",
    puntos: [
      "Ejecuciones fallidas: revisar detalle y reintentar o escalar a soporte.",
      "Información faltante: registrar en expediente y solicitar complemento.",
      "Mesa de Ayuda: casos formales con trazabilidad.",
    ],
  },
  {
    id: 9,
    titulo: "Glosario (español)",
    resumen: "Términos operativos en lenguaje empresarial.",
    puntos: [
      "Expediente = evaluación EIAAX de una empresa.",
      "Hallazgo = hecho o inferencia detectada con evidencia.",
      "Oportunidad = mejora priorizable con valor potencial.",
      "Empleado IA = agente configurado con autonomía supervisada.",
      "PROYECTADO/SIMULADO = no afirmar ahorro real en demos.",
    ],
  },
  {
    id: 10,
    titulo: "Navegación",
    resumen: "Mapa de pantallas principales.",
    puntos: [
      "Inicio: Centro de Control + esta guía.",
      "Trabajo: operaciones, ejecuciones, aprobaciones.",
      "Empresas: prospectos, evaluaciones, oportunidades.",
      "Análisis avanzado y Administración: módulos de profundidad (menú colapsable).",
    ],
  },
];

export const DEMO_HORIZONTE_NOMBRE = "Clínica Demo Horizonte";
export const DEMO_HORIZONTE_ETIQUETA = "DEMO — DATOS SIMULADOS";
