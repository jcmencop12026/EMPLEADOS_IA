import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchEvaluacion, fetchEvaluacionTrazabilidad, syncInformacionExpediente, type EvaluacionExpedienteDetail } from "../../api";
import { EspacioExternoAdminPanel } from "../espacioExterno/EspacioExternoAdminPanel";

type Props = { evaluacionId: string; mode: "documentos" | "requisitos" | "espacio_externo" | "historial" };

export function CentroControlEmpresaExtras({ evaluacionId, mode }: Props) {
  const [exp, setExp] = useState<EvaluacionExpedienteDetail | null>(null);
  const [traza, setTraza] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (mode === "espacio_externo") return;
    const load = async () => {
      try {
        const data = mode === "requisitos" || mode === "documentos"
          ? await syncInformacionExpediente(evaluacionId)
          : await fetchEvaluacion(evaluacionId);
        setExp(data);
      } catch {
        fetchEvaluacion(evaluacionId).then(setExp).catch(() => setExp(null));
      }
    };
    void load();
    if (mode === "historial") fetchEvaluacionTrazabilidad(evaluacionId).then(setTraza).catch(() => setTraza(null));
  }, [evaluacionId, mode]);

  const pendientes = useMemo(() => exp?.informacion.filter((i) => i.obligatorio && (i.estado === "PENDIENTE" || i.estado === "INCOMPLETO")) ?? [], [exp]);
  const conEvidencia = useMemo(() => exp?.informacion.filter((i) => Boolean(i.evidencia_ref)) ?? [], [exp]);

  if (mode === "espacio_externo") return <EspacioExternoAdminPanel expedienteId={evaluacionId} />;

  if (!exp) return <section className="panel compact-panel"><p className="muted">Cargando contexto…</p></section>;

  if (mode === "requisitos") return (
    <section className="panel compact-panel cc-context-extra">
      <div className="cc-context-extra__head"><div><span>REQUISITOS DE INFORMACIÓN</span><h2>{pendientes.length} pendiente(s)</h2></div><Link className="btn small secondary" to={`/evaluaciones/${evaluacionId}`} data-help="Abra la cabina de evaluación para revisar, completar o validar la información de este expediente. Use esta acción cuando necesite trabajar el requisito internamente antes de solicitarlo o confirmarlo con la empresa.">Abrir cabina</Link></div>
      {pendientes.length === 0 ? <p className="success">No hay requisitos obligatorios pendientes.</p> : (
        <div className="cc-context-extra__list">{pendientes.map((i, idx) => <article key={i.id} data-help={`${i.etiqueta}. ${i.explicacion || "Información necesaria para continuar el análisis."}${i.por_que ? ` EIAAX la utilizará para ${i.por_que.toLowerCase()}.` : ""}${i.impacto_precision ? ` Si falta: ${i.impacto_precision}` : " Si falta, la confianza y precisión del diagnóstico permanecen limitadas."}`}><b>{idx + 1}. {i.etiqueta}</b><span>{i.explicacion || "Información requerida para continuar el análisis."}{i.por_que ? ` · Para qué: ${i.por_que}` : ""}</span><em>{i.estado}</em></article>)}</div>
      )}
      <p className="muted small">Desde aquí ve exactamente qué falta. La solicitud formal al cliente se gestiona en “Espacio externo”.</p>
    </section>
  );

  if (mode === "documentos") return (
    <section className="panel compact-panel cc-context-extra">
      <div className="cc-context-extra__head"><div><span>DOCUMENTOS Y EVIDENCIAS</span><h2>{conEvidencia.length} requisito(s) con evidencia</h2></div><Link className="btn small secondary" to={`/evaluaciones/${evaluacionId}`}>Gestionar en cabina</Link></div>
      <div className="cc-context-extra__list">{exp.informacion.map((i) => <article key={i.id}><b>{i.etiqueta}</b><span>{i.evidencia_ref ? "Evidencia asociada" : "Sin evidencia asociada"}</span><em>{i.estado}</em></article>)}</div>
    </section>
  );

  const eventos = (traza?.items as Array<Record<string, unknown>> | undefined) ?? (traza?.eventos as Array<Record<string, unknown>> | undefined) ?? [];
  return (
    <section className="panel compact-panel cc-context-extra">
      <div className="cc-context-extra__head"><div><span>HISTORIAL Y TRAZABILIDAD</span><h2>Actividad del expediente</h2></div><Link className="btn small secondary" to={`/evaluaciones/${evaluacionId}?tab=vista-empresa`}>Vista empresa</Link></div>
      {eventos.length ? <div className="cc-context-extra__list">{eventos.slice(0, 12).map((e, idx) => <article key={String(e.id ?? idx)}><b>{String(e.accion ?? e.tipo ?? e.evento ?? "Evento")}</b><span>{String(e.detalle ?? e.descripcion ?? "Registro de trazabilidad")}</span><em>{String(e.fecha ?? e.created_at ?? "")}</em></article>)}</div> : <p className="muted">La trazabilidad detallada está disponible en la cabina del expediente.</p>}
    </section>
  );
}
