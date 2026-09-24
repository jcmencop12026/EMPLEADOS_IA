import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  downloadPresentacionPdf,
  askDemoReunion,
  createDemoSala, updateDemoSala, inviteDemoSala, fetchDemoSalaPresenter, renewDemoSala, type DemoSala,
  fetchDemoPresentacion,
  type PresentacionPayload,
  ApiError,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { DemoBanner } from "../components/DemoBanner";
import { PresentacionView } from "../components/PresentacionView";
import { DemoExecutiveIntelligence, type DemoMetricSelection } from "../components/DemoExecutiveIntelligence";
import { DemoTraceability } from "../components/DemoTraceability";
import { DemoExecutiveClose } from "../components/DemoExecutiveClose";
import { AUDIENCIAS, HELP_DEMO_COMERCIAL, type AudienciaId } from "../lib/demoComercialHelp";
import { DEMO_MEETING_TOPICS } from "../lib/demoMeetingCatalog";
import { useContextualAssistant } from "../context/ContextualAssistantContext";

export function PresentacionEjecutivaPage() {
  const { expedienteId } = useParams<{ expedienteId: string }>();
  const [searchParams] = useSearchParams();
  const preparar = searchParams.get("preparar") === "1";
  const { setAssistantEnabled } = useContextualAssistant();
  const [tipoReunion, setTipoReunion] = useState("DEMO_INTEGRAL");
  const [temasActivos, setTemasActivos] = useState<string[]>(() => DEMO_MEETING_TOPICS.map((t) => t.label));
  const [temaDetalle, setTemaDetalle] = useState(DEMO_MEETING_TOPICS[0].id);
  const [reunionIniciada, setReunionIniciada] = useState(false);
  const [temaEnVivo, setTemaEnVivo] = useState(DEMO_MEETING_TOPICS[0].id);
  const [temasInteres, setTemasInteres] = useState<string[]>([]);
  const [audiencia, setAudiencia] = useState<AudienciaId>("GERENCIA");
  const [vistaReunion, setVistaReunion] = useState<"TEMA"|"IMPACTO"|"DETALLE"|"CIERRE"|"GERENTE">("TEMA");
  const [data, setData] = useState<PresentacionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [preguntaElia, setPreguntaElia] = useState("");
  const [respuestaElia, setRespuestaElia] = useState<string | null>(null);
  const [eliaLoading, setEliaLoading] = useState(false);
  const [eliaError, setEliaError] = useState<string | null>(null);
  const [sala, setSala] = useState<DemoSala | null>(null);
  const [salaError, setSalaError] = useState<string | null>(null);
  const [metricPrivada, setMetricPrivada] = useState<DemoMetricSelection | null>(null);
  const [inviteEmail, setInviteEmail] = useState(""); const [inviteNombre,setInviteNombre]=useState(""); const [inviteEstado,setInviteEstado]=useState<string|null>(null); const [nivelRevelacion,setNivelRevelacion]=useState<"DEMO"|"PRELIMINAR"|"PROPUESTA">("DEMO"); const [eliaPublicar,setEliaPublicar]=useState(false); const [borradorGerente,setBorradorGerente]=useState<string>("");

  useEffect(() => {
    setAssistantEnabled(!reunionIniciada);
    return () => setAssistantEnabled(true);
  }, [reunionIniciada, setAssistantEnabled]);

  useEffect(() => {
    if (!sala?.codigo) return;
    const id=window.setInterval(()=>fetchDemoSalaPresenter(sala.codigo).then(r=>setSala(prev=>prev?{...prev,...r}:prev)).catch(()=>{}),2000);
    return ()=>window.clearInterval(id);
  }, [sala?.codigo]);

  useEffect(() => {
    if (!expedienteId) return;
    setLoading(true);
    fetchDemoPresentacion(expedienteId, audiencia)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [expedienteId, audiencia]);

  const temaSeleccionado = useMemo(() => DEMO_MEETING_TOPICS.find((t) => t.id === temaEnVivo) ?? DEMO_MEETING_TOPICS[0], [temaEnVivo]);

  const dataEnVivo = useMemo<PresentacionPayload | null>(() => {
    if (!data || !reunionIniciada) return data;
    const tema = temaSeleccionado;
    return {
      ...data,
      etiqueta: `${data.etiqueta} · ${tema.label}`,
      secciones: [
        { titulo: `Lectura ejecutiva · ${tema.label}`, contenido: tema.narrativa },
        { titulo: "Hallazgos demostrativos", contenido: tema.hallazgos },
        { titulo: "Oportunidades priorizadas", contenido: tema.oportunidades },
        { titulo: "Qué necesitaríamos para evaluarlo en su entidad", contenido: tema.minimo },
      ],
      indicadores: tema.series,
      graficos: {
        tipo: "COMPARATIVO_DEMO",
        nota: `DEMO ${tema.label}: escenario ficticio preparado; antes vs. proyectado, no resultado real.`,
        series: tema.series,
      },
    };
  }, [data, reunionIniciada, temaSeleccionado]);

  async function onPdf() {
    if (!expedienteId) return;
    setPdfLoading(true);
    try {
      await downloadPresentacionPdf(expedienteId, audiencia, true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el PDF");
    } finally {
      setPdfLoading(false);
    }
  }

  async function abrirSala() {
    if (!expedienteId) return;
    try { const r=await createDemoSala(expedienteId, temaEnVivo, tipoReunion); setSala(r); setSalaError(null); }
    catch(e){setSalaError(e instanceof Error?e.message:"No se pudo abrir la sala");}
  }
  async function renovarAccesoGerente(){ if(!sala)return; setSalaError(null); try{const r=await renewDemoSala(sala.codigo,4);setSala({...sala,...r});setInviteEstado("Acceso renovado. El enlace anterior quedó invalidado; copie o reenvíe el nuevo.");}catch(e){setSalaError(e instanceof ApiError?e.detail:e instanceof Error?e.message:"No se pudo renovar el acceso");}}
  async function enviarInvitacionSala() {
    if(!sala || !inviteEmail.trim()) return; setInviteEstado("Enviando invitación…");
    try{await inviteDemoSala(sala.codigo,inviteEmail.trim(),inviteNombre.trim()||"Gerencia");setInviteEstado(`Invitación enviada a ${inviteEmail.trim()}`);}
    catch(e){setInviteEstado(e instanceof ApiError ? e.detail : e instanceof Error ? e.message : "No se pudo enviar la invitación");}
  }
  async function mostrarAlGerente(payload: Record<string, unknown>) {
    if (!sala) return;
    try { const r=await updateDemoSala(sala.codigo,{tema:temaEnVivo,visible:{...payload,nivel:nivelRevelacion}}); setSala({...sala,...r}); } catch(e){setSalaError(e instanceof Error?e.message:"No se pudo sincronizar");}
  }

  async function preguntarElia(e: React.FormEvent) {
    e.preventDefault();
    if (!expedienteId || !preguntaElia.trim()) return;
    setEliaLoading(true);
    try { const r = await askDemoReunion(expedienteId, preguntaElia.trim(), temaEnVivo); setRespuestaElia(r.respuesta); setBorradorGerente(r.respuesta); setEliaError(null); setError(null); if(eliaPublicar&&sala){await mostrarAlGerente({titulo:`ELIA · ${temaSeleccionado.label}`,subtitulo:"Análisis solicitado por el presentador",respuesta:r.respuesta});} }
    catch (e) { setRespuestaElia(null); setEliaError(e instanceof ApiError ? e.detail : e instanceof Error ? e.message : "ELIA no pudo responder"); }
    finally { setEliaLoading(false); }
  }

  if (!expedienteId) return <p className="error">Expediente no especificado</p>;

  return (
    <div className={`ops-page presentacion-ejecutiva-page ${reunionIniciada ? "meeting-mode" : ""}`}>
      {!reunionIniciada && <DemoBanner />}
      {!reunionIniciada && <p><Link to="/demo">← Volver a demo comercial</Link></p>}

      {!reunionIniciada && <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Presentación ejecutiva</h1>
            <p className="muted">
              {data?.empresa ?? "Empresa ficticia"} · {data?.expediente_codigo}
            </p>
          </div>
          <ContextualHelp content={HELP_DEMO_COMERCIAL} />
        </div>
      </header>}

      {preparar && !reunionIniciada && (
        <section className="panel compact-panel meeting-prep">
          <div className="section-header"><div><h2>Preparar reunión</h2><p className="muted">EIIAX prepara el escenario, los mínimos requeridos y los paquetes ficticios antes de iniciar.</p></div></div>
          <div className="meeting-prep-grid">
            <label><strong>Propósito</strong><select value={tipoReunion} onChange={(e) => setTipoReunion(e.target.value)}><option value="DEMO_INTEGRAL">Demostración integral</option><option value="DEMO_TEMATICA">Demostración temática</option><option value="RESULTADOS">Evaluación / presentación de resultados</option><option value="PROPUESTA">Propuesta / contratación</option><option value="IMPLEMENTACION">Implementación</option><option value="SEGUIMIENTO">Seguimiento</option></select></label>
            <div className="meeting-topic-picker"><div className="meeting-topic-picker-head"><div><strong>Áreas de exploración ejecutiva</strong><span className="muted small"> · Seleccione qué quiere demostrar.</span></div><div className="meeting-topic-actions"><button type="button" className="btn small" onClick={()=>setTemasActivos(DEMO_MEETING_TOPICS.map(t=>t.label))}>Todos</button><button type="button" className="btn small" onClick={()=>setTemasActivos([])}>Ninguno</button></div></div><div className="meeting-topic-grid">{DEMO_MEETING_TOPICS.map((tema) => {const selected=temasActivos.includes(tema.label); return <button type="button" key={tema.id} className={`meeting-topic-card ${selected ? "selected" : ""} ${temaDetalle === tema.id ? "focused" : ""}`} onClick={()=>setTemaDetalle(tema.id)}><span className="meeting-topic-check" aria-hidden="true" onClick={(e)=>{e.stopPropagation();setTemasActivos(prev=>selected?prev.filter(x=>x!==tema.label):[...prev,tema.label])}}>{selected?"✓":"+"}</span><strong>{tema.label}</strong><small>{tema.demuestra.slice(0,2).join(" · ")}</small></button>})}<div className="meeting-topic-card exploratory"><span className="meeting-topic-check">＋</span><strong>Otros temas</strong><small>EIIAX investiga, cruza procesos y detecta oportunidades adicionales.</small></div></div></div>
          </div>
          {(() => { const tema = DEMO_MEETING_TOPICS.find((t) => t.id === temaDetalle)!; return <div className="meeting-topic-detail"><div><strong>{tema.label}</strong><span className="muted small"> · Paquete demo: {tema.paquete}</span><h3>Mínimos que pediríamos a la entidad</h3><ul>{tema.minimo.map((x) => <li key={x}>{x}</li>)}</ul></div><div><h3>Qué demostramos con el paquete ficticio</h3><ul>{tema.demuestra.map((x) => <li key={x}>{x}</li>)}</ul></div></div>; })()}
          <div className="executive-value-strip"><strong>EIIAX busca impacto, no solo indicadores:</strong><span>↑ mayores ingresos</span><span>↓ pérdidas y glosas</span><span>↓ costos</span><span>↑ productividad</span><span>↔ procesos y cuellos de botella</span><span>⚠ riesgos y controles</span></div>
          <div className="info-box"><strong>{temasActivos.length} paquete(s) preparados.</strong> Son puertas de entrada, no límites: durante la reunión EIIAX puede cruzar áreas, revisar flujos completos e identificar otras oportunidades.</div>
          <button type="button" className="btn primary" disabled={temasActivos.length === 0} onClick={() => { const focused = DEMO_MEETING_TOPICS.find((t) => t.id===temaDetalle && temasActivos.includes(t.label)); const first = focused ?? DEMO_MEETING_TOPICS.find((t) => temasActivos.includes(t.label)); if (first) setTemaEnVivo(first.id); setVistaReunion("TEMA"); setReunionIniciada(true); window.scrollTo({top:0,behavior:"smooth"}); }}>Iniciar reunión</button>
        </section>
      )}

      <div id="presentacion-demo" />
      {reunionIniciada && <nav className="meeting-view-tabs" aria-label="Vista de reunión"><button className={vistaReunion==="TEMA"?"active":""} onClick={()=>setVistaReunion("TEMA")}>Tema activo</button><button className={vistaReunion==="IMPACTO"?"active":""} onClick={()=>setVistaReunion("IMPACTO")}>Impacto y gráficos</button><button className={vistaReunion==="DETALLE"?"active":""} onClick={()=>setVistaReunion("DETALLE")}>Detalle y trazabilidad</button><button className={vistaReunion==="GERENTE"?"active":""} onClick={()=>setVistaReunion("GERENTE")}>👁 Vista del Gerente</button><button className={vistaReunion==="CIERRE"?"active":""} onClick={()=>setVistaReunion("CIERRE")}>Resumen y cierre</button></nav>}
      {reunionIniciada && vistaReunion==="GERENTE" && <section className="panel presenter-guest-monitor"><div className="section-header"><div><span className="semantic-badge hecho">CONTROL DEL PRESENTADOR</span><h2>Lo que está viendo el Gerente</h2><p className="muted">Réplica local de la publicación vigente. Usted decide qué se revela.</p></div></div>{sala?.guest_token?<iframe title="Vista actual del gerente" src={`/sala-demo/${sala.codigo}?token=${encodeURIComponent(sala.guest_token)}`} />:<div className="info-box">Abra una sala para activar la vista controlada.</div>}<div className="presenter-interest-feed"><strong>Señales de interés del Gerente</strong>{sala?.intereses?.length?<ul>{[...sala.intereses].reverse().slice(0,5).map((x,i)=><li key={i}><b>{x.accion.replaceAll("_"," ")}</b> · {x.tema}{x.detalle?` — ${x.detalle}`:""}</li>)}</ul>:<span className="muted"> Aún no ha marcado intereses.</span>}</div></section>}
      {reunionIniciada && (() => {
        const disponibles = DEMO_MEETING_TOPICS.filter((t) => temasActivos.includes(t.label));
        const tema = disponibles.find((t) => t.id === temaEnVivo) ?? disponibles[0];
        if (!tema) return null;
        return (
          <section className={`panel demo-live-panel ${vistaReunion==="TEMA"?"meeting-main-active":"meeting-main-hidden"}`}>
            <div className="section-header"><div><span className="semantic-badge hecho">REUNIÓN EN CURSO</span><h2>{tema.label}</h2><p className="muted">Caso ficticio preparado: {tema.paquete}</p></div><div className="meeting-room-controls">{!sala ? <button type="button" className="btn primary small" onClick={abrirSala}>Abrir sala para gerente</button> : <><span className="semantic-badge hecho">SALA {sala.codigo}</span><button type="button" className="btn small" disabled={!sala.guest_url} onClick={()=>sala.guest_url&&navigator.clipboard.writeText(sala.guest_url)}>Copiar enlace</button><button type="button" className="btn small primary" onClick={renovarAccesoGerente}>↻ Renovar acceso</button></>}</div></div>
            {salaError && <p className="error">{salaError}</p>}
            {sala && !sala.guest_url && <p className="info-box small">Sala creada y protegida. Para usarla desde otro computador falta configurar la URL pública vigente del entorno.</p>}
            {sala && sala.guest_url && <><div className="meeting-guest-access"><strong>Acceso del gerente:</strong><span className="semantic-badge hecho">● REMOTO ACTIVO</span><input type="text" readOnly value={sala.guest_url} aria-label="Enlace del gerente" /><a className="btn small primary" href={sala.guest_url} target="_blank" rel="noreferrer">Abrir pantalla gerente</a></div><div className="meeting-invite-row"><strong>Invitar al gerente:</strong><input type="text" placeholder="Nombre" value={inviteNombre} onChange={e=>setInviteNombre(e.target.value)} /><input type="email" placeholder="correo@empresa.com" value={inviteEmail} onChange={e=>setInviteEmail(e.target.value)} /><button type="button" className="btn small primary" disabled={!inviteEmail.trim()} onClick={enviarInvitacionSala}>Enviar invitación</button>{inviteEstado&&<span className="meeting-invite-status small" role="status">{inviteEstado}</span>}</div></>}
            <div className="demo-live-topicbar">{disponibles.map((t) => <button key={t.id} type="button" className={`live-topic-card ${tema.id === t.id ? "active" : ""}`} onClick={() => { setTemaEnVivo(t.id); setVistaReunion("TEMA"); }}><strong>{t.label}</strong><small>{t.demuestra[0]}</small></button>)}<div className="live-topic-card exploratory"><strong>＋ Otros temas</strong><small>EIIAX puede cruzar procesos y explorar nuevas oportunidades fuera del catálogo.</small></div></div>
            {sala && <div className="meeting-share-actions controlled-publish"><label>Nivel visible <select value={nivelRevelacion} onChange={e=>setNivelRevelacion(e.target.value as any)}><option value="DEMO">Demo · capacidad</option><option value="PRELIMINAR">Preliminar · evidencia resumida</option><option value="PROPUESTA">Propuesta · metodología y alcance</option></select></label><button type="button" className="btn small primary" onClick={()=>mostrarAlGerente({titulo:tema.label,subtitulo:nivelRevelacion==="DEMO"?`Caso ficticio: ${tema.paquete} · Oportunidades priorizadas`:`Evaluación ${nivelRevelacion.toLowerCase()} · información controlada`,contenido:[...tema.hallazgos.slice(0,nivelRevelacion==="DEMO"?3:5),...tema.oportunidades.slice(0,nivelRevelacion==="PROPUESTA"?3:2).map(x=>`Oportunidad: ${x}`)],metodologia:nivelRevelacion==="PROPUESTA"?["Conocer y conectar","Analizar y detectar","Validar y priorizar","Implementar","Medir y mejorar"]:undefined})}>PUBLICAR AL GERENTE</button><span className="muted small">ELIA puede conocer más; el Gerente solo recibe esta capa.</span></div>}
            <div className="demo-live-grid">
              <div><h3>Datos mínimos que necesitaríamos de su entidad</h3><ul>{tema.minimo.map((x) => <li key={x}>{x}</li>)}</ul></div>
              <div><h3>Indicadores ficticios preparados</h3><ul>{tema.indicadores.map((x) => <li key={x}><strong>{x}</strong></li>)}</ul></div>
              <div><h3>Hallazgos y oportunidades de impacto</h3><ul>{tema.hallazgos.map((x) => <li key={x}>{x}</li>)}{tema.oportunidades.map((x) => <li key={`op-${x}`}><strong>Oportunidad:</strong> {x}</li>)}</ul></div>
            </div>
            <div className="demo-interest-row">
              <button type="button" className={`btn small ${temasInteres.includes(tema.id) ? "primary" : "secondary"}`} onClick={() => setTemasInteres((prev) => prev.includes(tema.id) ? prev.filter((x) => x !== tema.id) : [...prev, tema.id])}>
                {temasInteres.includes(tema.id) ? "✓ Interés registrado" : "Registrar interés en este tema"}
              </button>
              <span className="muted small">Se usará para crear el alcance real al cerrar la reunión.</span>
            </div>
            <section className="elia-meeting-copilot">
              <div className="elia-meeting-head"><div><span className="semantic-badge hecho">ELIA · COPILOTO</span><h3>Preguntas en vivo</h3></div><div className="elia-live-controls"><span className="muted small">Contexto activo: {tema.label}</span><label><input type="checkbox" checked={eliaPublicar} onChange={e=>setEliaPublicar(e.target.checked)} disabled={!sala}/> Publicar próxima respuesta al gerente</label></div></div>
              <p className="muted small">Pregunte como lo haría el gerente. ELIA cruza el caso demo y distingue lo simulado de lo que requiere datos reales.</p>
              <form className="elia-question-form" onSubmit={preguntarElia}>
                <input value={preguntaElia} onChange={(e) => setPreguntaElia(e.target.value)} placeholder="Pregunte sobre el demo o solicite un análisis adicional para la reunión…" />
                <button className="btn primary" type="submit" disabled={eliaLoading || !preguntaElia.trim()}>{eliaLoading ? "Analizando…" : "Preguntar a ELIA"}</button>
              </form>
              {eliaError && <div className="error elia-inline-error" role="alert"><strong>ELIA no pudo completar la respuesta:</strong> {eliaError}</div>}
              {respuestaElia && <div className="elia-answer elia-editorial"><strong>ELIA · BORRADOR PRIVADO</strong><p>{respuestaElia}</p><label className="elia-edit-label">Editar antes de publicar<textarea value={borradorGerente} onChange={e=>setBorradorGerente(e.target.value)} rows={3}/></label><div className="elia-share-row"><span className="muted small">Privado hasta que usted decida publicarlo. Revise cifras, fuentes y alcance.</span>{sala && <button type="button" className="btn small primary" disabled={!borradorGerente.trim()} onClick={()=>mostrarAlGerente({titulo:`ELIA · ${tema.label}`,subtitulo:"Hallazgo preparado y autorizado por el presentador",respuesta:borradorGerente,nota:"Contenido presentado durante la reunión; su validación con datos reales depende del alcance acordado."})}>Preparar y publicar</button>}</div></div>}
            </section>
            <p className="meeting-demo-note muted small"><strong>DEMO:</strong> cifras simuladas; no corresponden a una entidad real.</p>
          </section>
        );
      })()}
      {!reunionIniciada && <nav className="tab-bar" aria-label="Audiencia">
        {AUDIENCIAS.map((a) => <button key={a.id} type="button" className={audiencia === a.id ? "tab active" : "tab"} onClick={() => setAudiencia(a.id)}>{a.label}</button>)}
      </nav>}

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Cargando presentación…</p>}

      {data && !loading && (
        <>
          {!reunionIniciada && <PresentacionView data={dataEnVivo ?? data} expedienteId={expedienteId} esDemo onDownloadPdf={onPdf} pdfLoading={pdfLoading} />}
          {reunionIniciada && vistaReunion==="IMPACTO" && <DemoExecutiveIntelligence topic={DEMO_MEETING_TOPICS.find(t=>t.id===temaEnVivo) ?? DEMO_MEETING_TOPICS[0]} onMetricSelect={(m)=>{setMetricPrivada(m);setVistaReunion("DETALLE")}} />}
          {reunionIniciada && vistaReunion==="DETALLE" && <DemoTraceability topic={DEMO_MEETING_TOPICS.find(t=>t.id===temaEnVivo) ?? DEMO_MEETING_TOPICS[0]} metric={metricPrivada?.topicId===temaEnVivo?metricPrivada:null} />}
          {reunionIniciada && vistaReunion==="CIERRE" && (
            <section className="panel meeting-close">
              <h2>Resumen ejecutivo y cierre</h2>
              <DemoExecutiveClose canPublish={!!sala} onPublishCommitments={()=>mostrarAlGerente({titulo:"Compromisos de la IPS / Gerencia",subtitulo:"Condiciones necesarias para materializar y medir los beneficios",compromisos:[{responsable:"IPS / Gerencia",descripcion:"Entregar datos completos por el medio y periodicidad acordados.",evidencia:"Entrega validada",fecha:"Antes de validar línea base",beneficio:"Habilita cálculo y priorización confiables",estado:"PROPUESTO"},{responsable:"IPS / Gerencia",descripcion:"Designar funcionario líder y suplente para ejecución y seguimiento.",evidencia:"Responsables formalmente definidos",fecha:"Antes de iniciar implementación",beneficio:"Evita bloqueos y asegura ejecución",estado:"PROPUESTO"},{responsable:"IPS / Gerencia",descripcion:"Garantizar aplicación de los ajustes de proceso aprobados.",evidencia:"Evidencia de implementación",fecha:"Según plan acordado",beneficio:"Condición para materializar el beneficio",estado:"PROPUESTO"},{responsable:"EIIAX",descripcion:"Validar línea base, supuestos, indicadores y trazabilidad antes de fijar metas.",evidencia:"Línea base y ficha de medición aprobadas",fecha:"Antes de comprometer meta",beneficio:"Evita presentar estimaciones como resultados",estado:"PROPUESTO"},{responsable:"EIIAX + IPS",descripcion:"Medir resultado real contra línea base y documentar desviaciones y dependencias.",evidencia:"Acta o tablero de medición",fecha:"Durante seguimiento",beneficio:"Demuestra beneficio realizado y condiciones cumplidas",estado:"PROPUESTO"}],nota:"Los beneficios mostrados son potenciales y dependen del cumplimiento de estos compromisos y de la validación con datos reales."})} />
              <p className="muted">Registre únicamente los temas que el prospecto quiere evaluar con información real. EIIAX reutilizará esta selección para crear el expediente y generar los requisitos correspondientes.</p>
              <div className="demo-live-topicbar">
                {DEMO_MEETING_TOPICS.filter((t) => temasActivos.includes(t.label)).map((t) => (
                  <button key={t.id} type="button" className={`btn small ${temasInteres.includes(t.id) ? "primary" : "secondary"}`} onClick={() => setTemasInteres((prev) => prev.includes(t.id) ? prev.filter((x) => x !== t.id) : [...prev, t.id])}>{temasInteres.includes(t.id) ? "✓ " : ""}{t.label}</button>
                ))}
              </div>
              {temasInteres.length > 0 ? (
                <Link to={`/evaluaciones?nuevo=1&sector=salud&temas=${encodeURIComponent(temasInteres.join(","))}&area=${encodeURIComponent(DEMO_MEETING_TOPICS.filter((t) => temasInteres.includes(t.id)).map((t) => t.label).join(" + "))}`} className="btn primary">Crear evaluación real con este alcance</Link>
              ) : <span className="muted small">Seleccione al menos un tema de interés para convertir la demostración en evaluación real.</span>}
            </section>
          )}
        </>
      )}
    </div>
  );
}
