import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  crearSolicitudInformacionExterna,
  downloadPresentacionPdf,
  fetchEvaluacion,
  fetchEvaluacionProcessingStatus,
  fetchEvaluacionCambiosInformacion,
  fetchPresentacionReal,
  fetchSiguienteAccion,
  listEntidadesExternas,
  type EvaluacionExpedienteDetail,
  type EvaluacionProcessingStatus,
  type EvaluacionCambioInformacion,
  type PresentacionPayload,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { PresentacionView } from "../components/PresentacionView";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { AUDIENCIAS, HELP_DEMO_COMERCIAL, type AudienciaId } from "../lib/demoComercialHelp";
import { meetingCues } from "../lib/meetingCoach";

export function PresentacionRealPage() {
  const { expedienteId } = useParams<{ expedienteId: string }>();
  const [audiencia, setAudiencia] = useState<AudienciaId>("GERENCIA");
  const [data, setData] = useState<PresentacionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);  const [pdfLoading, setPdfLoading] = useState(false);
  const [coachOpen, setCoachOpen] = useState(true);
  const [clientMode, setClientMode] = useState(false);
  const [expediente, setExpediente] = useState<EvaluacionExpedienteDetail | null>(null);
  const [requestingData, setRequestingData] = useState(false);
  const [requestMessage, setRequestMessage] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<EvaluacionProcessingStatus | null>(null);
  const [cambios, setCambios] = useState<EvaluacionCambioInformacion | null>(null);
  const [nextAction, setNextAction] = useState<Record<string, unknown> | null>(null);

  usePageAssistantContext(
    { expediente_id: expedienteId, audiencia, titulo: data?.titulo },
    Boolean(expedienteId),
  );

  useEffect(() => {
    if (!expedienteId) return;
    let active = true;
    const refresh = async () => {
      const [presentation, expResult, procResult, nextResult] = await Promise.all([
        fetchPresentacionReal(expedienteId, audiencia).catch(() => null),
        fetchEvaluacion(expedienteId).catch(() => null),
        fetchEvaluacionProcessingStatus(expedienteId).catch(() => null),
        fetchEvaluacionCambiosInformacion(expedienteId).catch(() => null),
        fetchSiguienteAccion(expedienteId).catch(() => null),
      ]);
      if (!active) return;
      if (presentation) setData(presentation);
      if (expResult) setExpediente(expResult);
      if (procResult) setProcessingStatus(procResult);
      if (cambiosResult) setCambios(cambiosResult);
      if (nextResult) setNextAction(nextResult);
      setLoading(false);
    };    setLoading(true);
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => { active = false; window.clearInterval(timer); };
  }, [expedienteId, audiencia]);

  const pendientes = useMemo(
    () => expediente?.informacion.filter(
      (i) => i.obligatorio && (i.estado === "PENDIENTE" || i.estado === "INCOMPLETO"),
    ) ?? [],
    [expediente],
  );

  async function solicitarDatosFaltantes() {
    if (!expedienteId || !expediente) return;
    if (!pendientes.length) {
      setRequestMessage("No hay información obligatoria pendiente.");
      return;
    }
    setRequestingData(true);
    setRequestMessage(null);
    try {
      const entidades = await listEntidadesExternas(expedienteId);
      const entidad = entidades[0] as { id?: string } | undefined;
      if (!entidad?.id) {
        throw new Error("Primero habilite el espacio de la empresa/prospecto para solicitar información.");
      }
      for (const item of pendientes.slice(0, 5)) {
        await crearSolicitudInformacionExterna(entidad.id, {
          titulo: item.etiqueta,          descripcion: item.explicacion ?? "Información necesaria para continuar el análisis con mayor confianza.",
          informacion_item_id: item.id,
        });
      }
      setRequestMessage(`Solicitud enviada: ${Math.min(pendientes.length, 5)} dato(s) prioritario(s).`);
    } catch (e) {
      setRequestMessage(e instanceof Error ? e.message : "No se pudo solicitar la información.");
    } finally {
      setRequestingData(false);
    }
  }

  async function onPdf() {
    if (!expedienteId) return;
    setPdfLoading(true);
    try {
      await downloadPresentacionPdf(expedienteId, audiencia, false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el PDF");
    } finally {
      setPdfLoading(false);
    }
  }

  if (!expedienteId) return <p className="error">Expediente no especificado</p>;
  const cues = meetingCues(audiencia, { expediente, presentacion: data });
  const infoPct = expediente?.porcentaje_informacion ?? 0;
  const hallazgos = expediente?.hallazgos.length ?? 0;
  const oportunidades = expediente?.oportunidades_vinculadas.length ?? 0;  const fallbackProcessing = infoPct < 100
    ? { pct: Math.max(5, Math.min(35, Math.round(infoPct * 0.35))), label: "Recibiendo información", eta: "Esperando información suficiente" }
    : hallazgos === 0
      ? { pct: 55, label: "Preparado para procesar", eta: "Sin ejecución activa" }
      : oportunidades === 0
        ? { pct: 78, label: "Hallazgos disponibles", eta: "Pendiente valoración de oportunidades" }
        : { pct: 100, label: "Primera salida disponible", eta: "Resultados listos" };
  const processing = processingStatus?.status === "PROCESSING"
    ? { pct: processingStatus.progress, label: "Procesando evaluación", eta: `Transcurrido ${Math.max(1, Math.round((processingStatus.elapsed_ms ?? 0) / 1000))} s` }
    : processingStatus?.status === "DONE"
      ? { pct: 100, label: "Procesamiento completado", eta: processingStatus.duration_ms != null ? `Duración real ${(processingStatus.duration_ms / 1000).toFixed(1)} s` : "Completado" }
      : processingStatus?.status === "ERROR"
        ? { pct: 100, label: "Procesamiento con error", eta: "Requiere revisión" }
        : fallbackProcessing;
  const suggestedCue = cues[Math.min(cues.length - 1, Math.floor((processing.pct / 101) * cues.length))];

  return (
    <div className={`ops-page presentacion-ejecutiva-page ${clientMode ? "presentacion-cliente-mode" : ""}`}>
      {!clientMode && <p><Link to={`/evaluaciones/${expedienteId}`}>← Volver al expediente</Link></p>}

      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Presentación ejecutiva</h1>
            <p className="muted">{data?.empresa ?? "Organización"} · {data?.expediente_codigo ?? expedienteId}</p>
          </div>          {!clientMode && <ContextualHelp content={HELP_DEMO_COMERCIAL} />}
        </div>
      </header>

      {!clientMode && <div className="presentacion-mode-banner" role="note">
        <strong>Presentar en reunión</strong>
        <span className="muted small">Consola privada para conducir la conversación.</span>
        <Link to={`/evaluaciones/${expedienteId}?tab=vista-empresa`} className="btn small secondary">Ver como empresa</Link>
        <button type="button" className="btn small primary" onClick={() => setClientMode(true)}>Vista para presentar</button>
      </div>}

      {clientMode && <div className="presentacion-client-toolbar">
        <span>Vista limpia para la empresa</span>
        <button type="button" className="btn small secondary" onClick={() => setClientMode(false)}>Volver a mi consola</button>
      </div>}

      <nav className="tab-bar" aria-label="Audiencia">
        {AUDIENCIAS.map((a) => <button key={a.id} type="button" className={audiencia === a.id ? "tab active" : "tab"} onClick={() => setAudiencia(a.id)}>{a.label}</button>)}
      </nav>

      <section className="meeting-public-topics" aria-label="Temas visibles para la empresa">
        <span>CONVERSACIÓN EJECUTIVA</span>
        <div>{cues.map((cue) => <strong key={cue.publicTitle}>{cue.publicTitle}</strong>)}</div>
      </section>

      {!clientMode && <section className="meeting-processing-brief" aria-label="Procesamiento y sugerencia de conversación">
        <div className="meeting-processing-brief__top">
          <div><span>PROCESAMIENTO EIAAX</span><strong>{processing.label}</strong></div>
          <div><b>{processing.pct}%</b><span>{processing.eta}</span></div>
        </div>        <div className="meeting-processing-brief__track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={processing.pct}>
          <i style={{ width: `${processing.pct}%` }} />
        </div>
        {suggestedCue && <div className="meeting-processing-brief__next">
          <span>Mientras procesa, converse sobre</span><strong>{suggestedCue.publicTitle}</strong>
          <small>Su asistente privado tiene abajo la explicación y un ejemplo listo para contar.</small>
          {pendientes.length > 0 && <div className="meeting-data-request">
            <span>Faltan {pendientes.length} dato(s) prioritario(s): {pendientes.slice(0, 3).map((i) => i.etiqueta).join(" · ")}</span>
            <button type="button" className="btn small primary" onClick={solicitarDatosFaltantes} disabled={requestingData}>
              {requestingData ? "Solicitando…" : "Solicitar datos prioritarios"}
            </button>
          </div>}
          {requestMessage && <p className="small meeting-data-request__message">{requestMessage}</p>}
          {nextAction?.principal && <div className="meeting-next-action"><span>Siguiente acción sugerida</span><strong>{String((nextAction.principal as Record<string, unknown>).titulo ?? "Continuar análisis")}</strong><small>{String((nextAction.principal as Record<string, unknown>).descripcion ?? "")}</small></div>}
        </div>}
      </section>}

      {!clientMode && cambios && <section className="meeting-change-brief" aria-label="Cambios y aprendizaje del expediente" data-help="Resumen privado que se actualiza con la información validada. Le indica qué cambió, qué aprendió EIAAX, qué conviene preguntar y qué resultados ya puede presentar.">
        <div className="meeting-change-brief__head"><span>CAMBIOS DESDE LA INFORMACIÓN RECIBIDA</span><strong>{cambios.que_cambio}</strong></div>
        <div className="meeting-change-brief__grid">
          <article><b>Qué aprendimos</b>{cambios.que_aprendimos.length ? cambios.que_aprendimos.slice(0, 3).map((x) => <span key={x.campo}>{x.titulo} · {x.validacion}</span>) : <span>Sin aprendizaje nuevo validado.</span>}</article>
          <article><b>Qué preguntar ahora</b>{cambios.que_preguntar_ahora.length ? cambios.que_preguntar_ahora.map((x) => <span key={x.campo}>{x.titulo}</span>) : <span>No hay preguntas obligatorias pendientes.</span>}</article>
          <article><b>Qué podemos mostrar ya</b>{cambios.que_podemos_mostrar_ya.length ? cambios.que_podemos_mostrar_ya.map((x) => <span key={x}>{x}</span>) : <span>Aún no hay salida suficientemente sustentada.</span>}</article>
          <article className="meeting-change-brief__next"><b>Siguiente acción</b><strong>{cambios.siguiente_accion?.titulo ?? "Continuar evaluación"}</strong><span>{cambios.siguiente_accion?.descripcion}</span></article>
        </div>
      </section>}
      {!clientMode && <section className="meeting-coach" aria-label="Guion privado de reunión">
        <div className="meeting-coach__head">
          <div><span>ASISTENTE DE REUNIÓN · SOLO PARA USTED</span><strong>Qué explicar ahora</strong></div>
          <button type="button" className="btn small secondary" onClick={() => setCoachOpen((v) => !v)}>{coachOpen ? "Ocultar" : "Mostrar"}</button>
        </div>
        {coachOpen && <div className="meeting-coach__grid">
          {cues.map((cue) => <article key={cue.title} className="meeting-coach__cue">
            <span className="meeting-coach__public">EN PANTALLA: {cue.publicTitle}</span>
            <h3>{cue.title}</h3>
            <p>{cue.talk}</p>
            <div className="meeting-coach__example"><strong>Ejemplo para contar:</strong> {cue.example}</div>
          </article>)}
        </div>}
      </section>}

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Cargando presentación…</p>}
      {data && !loading && <PresentacionView
        data={data}
        expedienteId={expedienteId}
        esDemo={false}
        onDownloadPdf={clientMode ? undefined : onPdf}
        pdfLoading={pdfLoading}
        backLink={clientMode ? undefined : { to: `/evaluaciones/${expedienteId}`, label: "← Expediente de evaluación" }}
      />}
    </div>
  );
}
