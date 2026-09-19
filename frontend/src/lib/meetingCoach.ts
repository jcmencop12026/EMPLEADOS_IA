import type { EvaluacionExpedienteDetail, PresentacionPayload } from "../api";
import type { AudienciaId } from "./demoComercialHelp";

export type MeetingCue = {
  title: string;
  publicTitle: string;
  talk: string;
  example: string;
  source?: "empresa" | "general";
};

type MeetingContext = {
  expediente?: EvaluacionExpedienteDetail | null;
  presentacion?: PresentacionPayload | null;
};

const COMMON: MeetingCue[] = [
  { title: "Qué es un Empleado IA", publicTitle: "Empleados IA en su operación", talk: "Explique que no reemplazamos necesariamente sus sistemas: EIAAX incorpora capacidad inteligente sobre procesos existentes y PIIAX conecta las fuentes autorizadas.", example: "Un Analista de Cartera IA revisa vencimientos, prioriza riesgo y propone acciones; el responsable humano conserva el control definido.", source: "general" },
  { title: "De recomendación a ejecución", publicTitle: "Del análisis a la acción", talk: "Diferencie tres niveles: solo lectura, acción asistida con aprobación y automatización autorizada. La empresa decide hasta dónde llega cada agente.", example: "Podemos iniciar leyendo información y recomendando; cuando exista confianza, habilitar acciones específicas con trazabilidad.", source: "general" },
  { title: "Cómo demostramos valor", publicTitle: "Resultados que se pueden medir", talk: "Conecte cada iniciativa con línea base, meta conservadora, responsable, condición de éxito y resultado real.", example: "Si proponemos reducir un ciclo de 14 a 10 días, medimos adopción, cumplimiento y tiempo real obtenido.", source: "general" },
];
const BY_AUDIENCE: Record<AudienciaId, MeetingCue[]> = {
  GERENCIA: [{ title: "Qué cambia para la dirección", publicTitle: "Control, productividad y valor", talk: "Centre la conversación en visibilidad, decisiones, capacidad, costos y resultados.", example: "La dirección pasa de recibir un informe tardío a conocer prioridades, desviaciones y oportunidades con seguimiento medible.", source: "general" }],
  SISTEMAS: [{ title: "Cómo nos conectamos", publicTitle: "Integración segura con sus sistemas", talk: "Explique API, base de datos, archivos, correo, webhooks o automatización de interfaz. Empiece por el acceso mínimo necesario y preferiblemente solo lectura.", example: "Si el ERP tiene API usamos API; si no, podemos comenzar con archivos controlados y evolucionar la integración sin reemplazar el ERP.", source: "general" }],
  OPERACION: [{ title: "Cómo cambia el proceso", publicTitle: "Procesos más controlados", talk: "Baje la propuesta a actividad, responsable, momento, SLA, evidencia y supervisión.", example: "Una tarea atrasada genera seguimiento, alerta o escalamiento según la regla acordada y queda trazabilidad del cumplimiento.", source: "general" }],
  FINANCIERO: [{ title: "Cómo cuidamos la promesa económica", publicTitle: "Valor con supuestos verificables", talk: "Separe potencial, meta conservadora y resultado realizado. Muestre costos, condiciones y compromisos que explican el resultado.", example: "Una recuperación proyectada se presenta como potencial condicionado hasta que la operación real demuestre el valor capturado.", source: "general" }],
};

function companyCues(ctx: MeetingContext): MeetingCue[] {
  const exp = ctx.expediente;
  const pres = ctx.presentacion;
  if (!exp) return [];
  const out: MeetingCue[] = [];
  const pendientes = exp.informacion.filter((i) => i.obligatorio && (i.estado === "PENDIENTE" || i.estado === "INCOMPLETO"));
  if (pendientes.length) {
    out.push({ title: "Datos que conviene pedir ahora", publicTitle: "Información para profundizar", talk: `Faltan ${pendientes.length} requisito(s) para elevar la confianza. Priorice: ${pendientes.slice(0, 3).map((i) => i.etiqueta).join("; ")}.`, example: "Explique que pedir información adicional no retrasa el proceso: permite separar hipótesis de conclusiones y mejora la precisión.", source: "empresa" });
  }
  const h = exp.hallazgos.find((x) => x.visible_entidad) ?? exp.hallazgos[0];
  if (h) out.push({ title: "Hallazgo de esta empresa", publicTitle: "Qué estamos encontrando", talk: `${h.titulo}. ${h.impacto_resumen ?? h.descripcion ?? "Revíselo con el equipo para validar alcance e impacto."}`, example: `Preséntelo como ${h.tipo_contenido.toLowerCase()} con confianza ${h.confianza.toLowerCase()}, no como una certeza absoluta si aún falta evidencia.`, source: "empresa" });
  const ind = pres?.graficos?.series?.[0];
  if (ind) out.push({ title: "Indicador para conversar", publicTitle: "Impacto medible", talk: `${ind.nombre}: situación actual ${ind.antes ?? "—"}${ind.unidad ?? ""}, meta conservadora ${ind.proyectado ?? "—"}${ind.unidad ?? ""}${ind.real != null ? `, resultado real ${ind.real}${ind.unidad ?? ""}` : ""}.`, example: "Use este indicador para conectar el diagnóstico con una meta verificable y evitar promesas abstractas.", source: "empresa" });
  return out;
}

export function meetingCues(audiencia: AudienciaId, ctx: MeetingContext = {}): MeetingCue[] {
  return [...companyCues(ctx), ...BY_AUDIENCE[audiencia], ...COMMON];
}
