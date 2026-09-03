import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

type Hallazgo = {
  id: string;
  titulo: string;
  descripcion: string;
  categoria: string;
  severidad: string;
  confianza: string;
  prioridad?: number;
  impacto_economico?: number;
  causa_probable?: string;
  tipo?: string;
  indicador?: string;
  valor?: string;
  evidencia?: Record<string, unknown>;
  fuentes?: Array<Record<string, string>>;
  fuentes_consultadas?: string[];
  evidencia_documental?: Array<Record<string, unknown>>;
  criterios_confianza?: Record<string, unknown>;
};

type Propuesta = {
  id: string;
  problema: string;
  evidencia: string;
  causa_probable?: string;
  impacto: string;
  accion_propuesta: string;
  responsable_sugerido?: string;
  plazo?: string;
  meta?: string;
  confianza: string;
  prioridad?: number;
  indicador_seguimiento?: string;
};

type Especialista = {
  employee_name: string;
  employee_code?: string;
  specialty?: string;
  domain: string;
  score: number;
  factors?: Record<string, number>;
};

type Diagnostico = {
  id: string;
  ips_name: string;
  estado: string;
  work_plan_id?: string | null;
  resumen_ejecutivo: {
    principales_problemas?: string[];
    impacto_acumulado?: number | string;
    oportunidades_principales?: string[];
    indicadores_criticos?: Record<string, unknown>;
    acciones_prioritarias?: string[];
  };
  calidad_datos: Record<string, {
    nivel_calidad?: string;
    registros?: number;
    campos_faltantes?: string[];
    completitud?: number;
  }>;
  indicadores: Record<string, Record<string, unknown>>;
  trazabilidad: Record<string, unknown>;
  hallazgos: Hallazgo[];
  oportunidades: Propuesta[];
  plan_accion: Array<Array<{ titulo: string; estado: string; responsable?: string; accion?: string; plazo?: string; meta?: string }>>;
  planes_accion?: Array<{ id: string; work_plan_id?: string | null; titulo: string; tareas: Array<{ titulo: string; estado: string }> }>;
  especialistas: {
    dominios?: string[];
    dominio_principal?: string;
    tipo_problema?: string;
    asignaciones?: Especialista[];
    equipo?: Array<Especialista & { rol?: string; razon_rol?: string; razon_seleccion?: string }>;
    lider?: Especialista & { razon_seleccion?: string };
    consolidador?: Especialista;
    validador?: Especialista & { razon_rol?: string };
    disidente?: Especialista & { razon_rol?: string };
    razon_seleccion_global?: string;
  };
  comparacion_historica: { disponible?: boolean; comparaciones?: Record<string, unknown> };
  conocimiento?: {
    utilizado?: boolean;
    mensaje?: string | null;
    fuentes?: Array<{ titulo?: string; document_id?: string }>;
    requiere_validacion?: boolean;
  };
  experiencia: { casos_similares?: Array<{ ips_name: string; similitud: number; evaluacion?: string }> };
  suficiencia_datos?: { clasificacion?: string; puntaje?: number; limitaciones?: string[] };
  hipotesis?: Array<{
    id: string;
    titulo: string;
    estado: string;
    confianza: string;
    dominio: string;
    evidencia_a_favor?: string[];
    evidencia_en_contra?: string[];
    informacion_faltante?: unknown[];
    impacto_potencial?: number | string;
  }>;
  hipotesis_principal?: { id: string; titulo: string; estado: string } | null;
  contrastes?: Array<{ hipotesis_titulo: string; especialista: string; postura: string; argumento: string }>;
  alternativas?: Array<{ alternativa_id: string; descripcion: string; fundamento: string; plazo?: string; confianza?: string }>;
  priorizacion?: { metodologia?: string; ranking?: Array<{ ranking: number; titulo: string; prioridad: number; por_que_primero?: string; tipo?: string }> };
  escenarios?: { escenarios?: Record<string, { nombre: string; valor_recuperable_estimado?: number | string; supuestos?: string[] }> };
  finops?: Array<{ referencia: string; beneficio_esperado?: number; certidumbre?: string; roi?: number; advertencia?: string }>;
  recomendacion_consolidada?: Record<string, unknown>;
};

const SECCIONES = [
  { id: "resumen", label: "Resumen" },
  { id: "calidad", label: "Calidad de datos" },
  { id: "indicadores", label: "Indicadores" },
  { id: "hallazgos", label: "Hallazgos" },
  { id: "hipotesis", label: "Hipótesis" },
  { id: "oportunidades", label: "Oportunidades" },
  { id: "alternativas", label: "Alternativas" },
  { id: "impacto", label: "Impacto/FINOPS" },
  { id: "plan", label: "Plan de acción" },
  { id: "seguimiento", label: "Seguimiento" },
  { id: "especialistas", label: "Especialistas" },
  { id: "trazabilidad", label: "Trazabilidad" },
  { id: "experiencia", label: "Experiencia" },
] as const;

const FUENTE_ES: Record<string, string> = {
  facturacion: "Facturación",
  radicacion: "Radicación",
  glosas: "Glosas",
  cartera: "Cartera",
  pagos: "Pagos",
  contratos: "Contratos",
  conciliacion: "Conciliación",
  respuestas_glosa: "Respuestas glosa",
};

const DOMINIO_ES: Record<string, string> = {
  facturacion: "Facturación",
  radicacion: "Radicación",
  glosas: "Glosas",
  cartera: "Cartera",
  contratos: "Contratos",
  rips: "RIPS",
  estrategico: "Estratégico",
  ideacion: "Ideación",
};

function formatMoney(val: unknown): string {
  if (typeof val === "number") return `$${val.toLocaleString("es-CO")}`;
  if (val === "Información insuficiente") return "Información insuficiente";
  return String(val ?? "—");
}

function formatPct(val: unknown): string {
  if (val === "Información insuficiente") return "Información insuficiente";
  if (typeof val === "number") return `${val}%`;
  return String(val ?? "—");
}

function severidadBadge(s: string) {
  const cls = s === "ALTA" ? "badge-sev-alta" : s === "MEDIA" ? "badge-sev-media" : "badge-sev-baja";
  return <span className={`badge ${cls}`}>{s}</span>;
}

export function DiagnosticoIpsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diag, setDiag] = useState<Diagnostico | null>(null);
  const [seccion, setSeccion] = useState<string>("resumen");
  const [hallazgoSel, setHallazgoSel] = useState<Hallazgo | null>(null);
  const [propSel, setPropSel] = useState<Set<string>>(new Set());
  const [pregunta, setPregunta] = useState("¿Por qué tengo menos caja si facturé más?");
  const [respuesta, setRespuesta] = useState<Record<string, unknown> | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);
  const [planMsg, setPlanMsg] = useState<string | null>(null);
  const [lastWorkPlanId, setLastWorkPlanId] = useState<string | null>(null);
  const [modoDemo, setModoDemo] = useState<"completo" | "parcial" | string | null>(null);
  const [labAbierto, setLabAbierto] = useState(false);

  const ejecutarAnalisisMotor = useCallback(async (caseId: string) => {
    setLoading(true);
    setError(null);
    setRespuesta(null);
    setFeedbackMsg(null);
    setPlanMsg(null);
    setLastWorkPlanId(null);
    setHallazgoSel(null);
    setPropSel(new Set());
    setModoDemo(caseId);
    try {
      const demo = await api<{ request_text: string; datasets: Record<string, unknown[]> }>(`/api/salud/motor/demo/${caseId}`);
      const res = await api<{ id: string }>("/api/salud/analisis", {
        method: "POST",
        body: JSON.stringify({
          ips_name: `IPS Motor ${caseId}`,
          request_text: demo.request_text,
          inline_datasets: demo.datasets,
        }),
      });
      const full = await api<Diagnostico>(`/api/salud/diagnostico/${res.id}`);
      setDiag(full);
      setSeccion("resumen");
      if (full.hallazgos.length > 0) setHallazgoSel(full.hallazgos[0]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al ejecutar análisis motor");
    } finally {
      setLoading(false);
    }
  }, []);

  const ejecutarAnalisis = useCallback(async (parcial: boolean) => {
    setLoading(true);
    setError(null);
    setRespuesta(null);
    setFeedbackMsg(null);
    setPlanMsg(null);
    setLastWorkPlanId(null);
    setHallazgoSel(null);
    setPropSel(new Set());
    setModoDemo(parcial ? "parcial" : "completo");
    try {
      let datasets: Record<string, unknown[]>;
      if (parcial) {
        const demo = await api<Record<string, unknown[]>>("/api/salud/demo/datasets");
        datasets = { facturacion: demo.facturacion ?? [] };
      } else {
        datasets = await api<Record<string, unknown[]>>("/api/salud/demo/datasets");
      }
      const res = await api<{ id: string }>("/api/salud/analisis", {
        method: "POST",
        body: JSON.stringify({
          ips_name: parcial ? "IPS Demo Parcial" : "IPS Demo Salud",
          request_text: "Analiza la situación financiera y operativa de esta IPS.",
          inline_datasets: datasets,
        }),
      });
      const full = await api<Diagnostico>(`/api/salud/diagnostico/${res.id}`);
      setDiag(full);
      setSeccion("resumen");
      if (full.hallazgos.length > 0) setHallazgoSel(full.hallazgos[0]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al ejecutar análisis");
    } finally {
      setLoading(false);
    }
  }, []);

  const indicadoresClave = useMemo(() => {
    if (!diag) return null;
    const ind = diag.indicadores;
    const fact = ind.facturacion ?? {};
    const rad = ind.radicacion ?? {};
    const glo = ind.glosas ?? {};
    const car = ind.cartera ?? {};
    const aging = (car.aging ?? {}) as Record<string, number>;
    return {
      facturado: fact.valor_facturado,
      facturas: fact.cantidad_facturas,
      noRadicadas: rad.facturas_no_radicadas,
      pctRadicado: rad.porcentaje_radicado,
      glosado: glo.valor_glosado,
      pctGlosa: glo.porcentaje_glosa,
      cartera91: aging["91+"],
      saldoTotal: car.saldo_total,
    };
  }, [diag]);

  async function preguntar() {
    if (!diag) return;
    try {
      const res = await api<Record<string, unknown>>(`/api/salud/pregunta/${diag.id}`, {
        method: "POST",
        body: JSON.stringify({ pregunta }),
      });
      setRespuesta(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al responder");
    }
  }

  async function enviarFeedback(hallazgoId: string, tipo: string) {
    if (!diag) return;
    try {
      await api("/api/salud/feedback", {
        method: "POST",
        body: JSON.stringify({ target_type: "hallazgo", target_id: hallazgoId, feedback_type: tipo, comment: "" }),
      });
      setFeedbackMsg(`Retroalimentación registrada: ${tipo.replace(/_/g, " ").toLowerCase()}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al registrar retroalimentación");
    }
  }

  async function crearPlan() {
    if (!diag || propSel.size === 0) return;
    try {
      const res = await api<{ titulo: string; work_plan_id?: string; tareas: unknown[] }>(`/api/salud/analisis/${diag.id}/plan-accion`, {
        method: "POST",
        body: JSON.stringify({ propuesta_ids: Array.from(propSel) }),
      });
      setLastWorkPlanId(res.work_plan_id ?? null);
      setPlanMsg(`Plan creado: ${res.titulo} (${res.tareas.length} tareas)`);
      const full = await api<Diagnostico>(`/api/salud/diagnostico/${diag.id}`);
      setDiag(full);
      setSeccion("plan");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al crear plan");
    }
  }

  async function registrarResultado(propId: string) {
    if (!diag) return;
    const prop = diag.oportunidades.find((p) => p.id === propId);
    if (!prop) return;
    try {
      await api(`/api/salud/propuestas/${propId}/resultado`, {
        method: "POST",
        body: JSON.stringify({ meta: prop.meta, resultado: "8,1 días", outcome: "MEJORO" }),
      });
      setPlanMsg(`Seguimiento registrado para: ${prop.problema}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al registrar seguimiento");
    }
  }

  function toggleProp(id: string) {
    setPropSel((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function renderIndicadores() {
    if (!diag) return null;
    const ind = diag.indicadores;
    const cards = [
      { key: "facturacion", titulo: "Facturación", datos: [
        ["Valor facturado", formatMoney(ind.facturacion?.valor_facturado)],
        ["Cantidad facturas", ind.facturacion?.cantidad_facturas ?? "Información insuficiente"],
        ["Concentración pagador", formatPct(ind.facturacion?.concentracion_principal_pagador_pct)],
      ]},
      { key: "radicacion", titulo: "Radicación", datos: [
        ["Valor radicado", formatMoney(ind.radicacion?.valor_radicado)],
        ["Facturas sin radicar", ind.radicacion?.facturas_no_radicadas ?? "Información insuficiente"],
        ["% radicado", formatPct(ind.radicacion?.porcentaje_radicado)],
        ["Días factura→radicación", ind.radicacion?.tiempo_promedio_factura_radicacion_dias ?? "Información insuficiente"],
      ]},
      { key: "glosas", titulo: "Glosas", datos: [
        ["Valor glosado", formatMoney(ind.glosas?.valor_glosado)],
        ["% glosa", formatPct(ind.glosas?.porcentaje_glosa)],
      ]},
      { key: "cartera", titulo: "Cartera", datos: [
        ["Saldo total", formatMoney(ind.cartera?.saldo_total)],
        ["Cartera 91+ días", formatMoney((ind.cartera?.aging as Record<string, number>)?.["91+"])],
        ["Recaudo", formatMoney(ind.cartera?.recaudo)],
      ]},
    ];

    return (
      <div className="salud-kpi-grid">
        {cards.map((c) => {
          const bloque = ind[c.key] as { disponible?: boolean; mensaje?: string } | undefined;
          const insuf = bloque?.disponible === false;
          return (
            <div key={c.key} className="salud-kpi-card">
              <h3>{c.titulo}</h3>
              {insuf ? (
                <p className="salud-insuficiente">{bloque?.mensaje ?? "Información insuficiente"}</p>
              ) : (
                <dl className="salud-dl">
                  {c.datos.map(([k, v]) => (
                    <div key={k} className="salud-dl-row">
                      <dt>{k}</dt>
                      <dd>{String(v)}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  function renderHallazgoDetalle(h: Hallazgo) {
    const propRel = diag?.oportunidades.find((p) => p.problema === h.titulo);
    return (
      <div className="salud-detalle-panel">
        <h3>Cadena de trazabilidad</h3>
        <ol className="salud-cadena">
          <li><strong>Qué ocurrió:</strong> {h.descripcion}</li>
          <li><strong>Dato/evidencia:</strong> {h.valor ?? h.indicador ?? "—"} {h.evidencia ? `(${JSON.stringify(h.evidencia).slice(0, 120)}…)` : ""}</li>
          <li><strong>Posible causa:</strong> {h.causa_probable ?? "Requiere validación operativa"}</li>
          <li><strong>Impacto:</strong> {formatMoney(h.impacto_economico)}</li>
          <li><strong>Recomendación:</strong> {propRel?.accion_propuesta ?? "Ver oportunidades"}</li>
          <li><strong>Acción propuesta:</strong> {propRel?.accion_propuesta ?? "—"}</li>
        </ol>
        {h.fuentes_consultadas && h.fuentes_consultadas.length > 0 && (
          <p className="muted">Fuentes documentales: {h.fuentes_consultadas.join(" · ")}</p>
        )}
        {h.fuentes && h.fuentes.length > 0 && (
          <p className="muted">Fuentes de datos: {h.fuentes.map((f) => `${f.dataset ?? ""} ${f.calculo ?? f.regla ?? ""}`).join(" · ")}</p>
        )}
        <div className="ops-actions">
          <button type="button" className="btn" title="Marcar hallazgo como correcto" onClick={() => enviarFeedback(h.id, "CORRECTO")}>Correcto</button>
          <button type="button" className="btn" title="Marcar como parcialmente correcto" onClick={() => enviarFeedback(h.id, "PARCIALMENTE_CORRECTO")}>Parcial</button>
          <button type="button" className="btn danger" title="Marcar como incorrecto" onClick={() => enviarFeedback(h.id, "INCORRECTO")}>Incorrecto</button>
        </div>
      </div>
    );
  }

  return (
    <div className="ops-page salud-page">
      <header className="page-header compact">
        <h1>Diagnóstico IPS</h1>
        <p className="muted">
          Motor especializado vertical Salud · En producción, ejecute diagnósticos desde la cabina de evaluación de la empresa.
        </p>
        {diag && (
          <p className="muted">
            Conocimiento documental: {diag.conocimiento?.utilizado ? "utilizado" : (diag.conocimiento?.mensaje ?? "sin documentos autorizados adicionales")}
            {diag.conocimiento?.requiere_validacion ? " · requiere validación humana" : ""}
          </p>
        )}
      </header>

      <section className="panel compact-panel salud-productivo-hint">
        <p className="muted">
          <strong>Flujo productivo:</strong> abra la evaluación de la empresa en{" "}
          <Link to="/empresas">Empresas y prospectos</Link> o{" "}
          <Link to="/evaluaciones">Evaluaciones EIAAX</Link> y use la pestaña Diagnóstico de la cabina.
        </p>
      </section>

      <section className="panel compact-panel salud-lab-panel">
        <button
          type="button"
          className="salud-lab-toggle"
          onClick={() => setLabAbierto((v) => !v)}
          aria-expanded={labAbierto}
        >
          {labAbierto ? "▾" : "▸"} Laboratorio / casos demo (vertical Salud)
        </button>
        {labAbierto && (
          <div className="salud-toolbar ops-main">
            <p className="muted small">
              Casos técnicos y datos sintéticos para validar el motor IPS. No forman parte del recorrido operativo estándar.
            </p>
            <button type="button" className="btn" disabled={loading} onClick={() => ejecutarAnalisis(false)}>
              {loading && modoDemo === "completo" ? "Analizando…" : "Ejecutar diagnóstico (datos demo)"}
            </button>
            <button type="button" className="btn" disabled={loading} onClick={() => ejecutarAnalisis(true)} title="Solo facturación — debe mostrar Información insuficiente en otros dominios">
              {loading && modoDemo === "parcial" ? "Analizando…" : "Demo datos incompletos"}
            </button>
            {["A", "B", "C", "D", "E", "CONSULTOR"].map((c) => (
              <button key={c} type="button" className="btn" disabled={loading} onClick={() => ejecutarAnalisisMotor(c)} title={`Caso adversarial ${c}`}>
                {loading && modoDemo === c ? "…" : `Caso ${c}`}
              </button>
            ))}
          </div>
        )}
        {diag && <span className="badge">{diag.ips_name} · {diag.estado}</span>}
        {error && <p className="error">{error}</p>}
        {feedbackMsg && <p className="salud-ok">{feedbackMsg}</p>}
        {planMsg && <p className="salud-ok">{planMsg}</p>}
      </section>

      {diag && (
        <>
          {indicadoresClave && modoDemo === "completo" && (
            <section className="panel salud-kpi-bar">
              <div className="salud-kpi-mini"><span>Facturado</span><strong>{formatMoney(indicadoresClave.facturado)}</strong><em>{String(indicadoresClave.facturas)} facturas</em></div>
              <div className="salud-kpi-mini"><span>Sin radicar</span><strong>{String(indicadoresClave.noRadicadas ?? "—")}</strong></div>
              <div className="salud-kpi-mini"><span>Glosado</span><strong>{formatMoney(indicadoresClave.glosado)}</strong></div>
              <div className="salud-kpi-mini"><span>Cartera 91+</span><strong>{formatMoney(indicadoresClave.cartera91)}</strong></div>
            </section>
          )}

          <nav className="tab-bar salud-tabs" aria-label="Secciones del diagnóstico">
            {SECCIONES.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`tab-btn ${seccion === s.id ? "active" : ""}`}
                onClick={() => setSeccion(s.id)}
              >
                {s.label}
              </button>
            ))}
          </nav>

          {seccion === "resumen" && (
            <section className="panel" id="seccion-resumen">
              <h2>Resumen ejecutivo</h2>
              {diag.suficiencia_datos?.clasificacion && (
                <p className="muted">Suficiencia de datos: <strong>{diag.suficiencia_datos.clasificacion}</strong></p>
              )}
              {diag.hipotesis_principal && (
                <p className="muted">Hipótesis principal: {diag.hipotesis_principal.titulo} ({diag.hipotesis_principal.estado})</p>
              )}
              {diag.recomendacion_consolidada?.recomendacion && (
                <p><strong>Recomendación:</strong> {String(diag.recomendacion_consolidada.recomendacion)}</p>
              )}
              <div className="salud-resumen-grid">
                <div>
                  <h3>Principales problemas</h3>
                  <ul>{(diag.resumen_ejecutivo.principales_problemas ?? []).map((p) => <li key={p}>{p}</li>)}</ul>
                </div>
                <div>
                  <h3>Impacto acumulado</h3>
                  <p className="salud-impacto">{formatMoney(diag.resumen_ejecutivo.impacto_acumulado)}</p>
                </div>
                <div>
                  <h3>Acciones prioritarias</h3>
                  <ul>{(diag.resumen_ejecutivo.acciones_prioritarias ?? []).map((a) => <li key={a}>{a}</li>)}</ul>
                </div>
              </div>
            </section>
          )}

          {seccion === "calidad" && (
            <section className="panel" id="seccion-calidad">
              <h2>Calidad de datos</h2>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr><th>Fuente</th><th>Registros</th><th>Calidad</th><th>Completitud</th><th>Campos faltantes</th></tr>
                  </thead>
                  <tbody>
                    {Object.entries(diag.calidad_datos).map(([fuente, q]) => (
                      <tr key={fuente}>
                        <td>{FUENTE_ES[fuente] ?? fuente}</td>
                        <td>{q.registros ?? 0}</td>
                        <td>{q.nivel_calidad ?? "—"}</td>
                        <td>{q.completitud != null ? `${(q.completitud * 100).toFixed(0)}%` : "—"}</td>
                        <td className="cell-truncate">{(q.campos_faltantes ?? []).join(", ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {seccion === "indicadores" && (
            <section className="panel" id="seccion-indicadores">
              <h2>Indicadores</h2>
              {renderIndicadores()}
              <h3 className="salud-sub">Trazabilidad de valores</h3>
              <div className="salud-traza-grid">
                {Object.entries(diag.trazabilidad)
                  .filter(([k]) => k !== "conocimiento")
                  .map(([k, v]) => (
                  <div key={k} className="salud-traza-item">
                    <span>{k.replace(/_/g, " ")}</span>
                    <strong>{typeof v === "number" ? formatMoney(v) : String(v)}</strong>
                  </div>
                ))}
              </div>
              {diag.conocimiento?.fuentes && diag.conocimiento.fuentes.length > 0 && (
                <p className="muted">
                  Conocimiento consultado: {diag.conocimiento.fuentes.map((f) => f.titulo).filter(Boolean).join(" · ")}
                </p>
              )}
            </section>
          )}

          {seccion === "hallazgos" && (
            <section className="panel" id="seccion-hallazgos">
              <h2>Hallazgos</h2>
              <div className="salud-split">
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr><th>Título</th><th>Categoría</th><th>Severidad</th><th>Confianza</th><th>Prioridad</th><th>Impacto</th></tr>
                    </thead>
                    <tbody>
                      {diag.hallazgos.map((h) => (
                        <tr key={h.id} className={hallazgoSel?.id === h.id ? "salud-row-active" : ""} onClick={() => setHallazgoSel(h)} style={{ cursor: "pointer" }}>
                          <td className="cell-truncate">{h.titulo}</td>
                          <td>{FUENTE_ES[h.categoria] ?? h.categoria}</td>
                          <td>{severidadBadge(h.severidad)}</td>
                          <td>{h.confianza}</td>
                          <td>{h.prioridad?.toFixed(1) ?? "—"}</td>
                          <td>{formatMoney(h.impacto_economico)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {hallazgoSel && renderHallazgoDetalle(hallazgoSel)}
              </div>
            </section>
          )}

          {seccion === "hipotesis" && (
            <section className="panel" id="seccion-hipotesis">
              <h2>Causas e hipótesis</h2>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr><th>ID</th><th>Hipótesis</th><th>Estado</th><th>Confianza</th><th>Dominio</th><th>Evidencia a favor</th></tr>
                  </thead>
                  <tbody>
                    {(diag.hipotesis ?? []).map((h) => (
                      <tr key={h.id}>
                        <td>{h.id}</td>
                        <td>{h.titulo}</td>
                        <td>{h.estado}</td>
                        <td>{h.confianza}</td>
                        <td>{DOMINIO_ES[h.dominio] ?? h.dominio}</td>
                        <td className="cell-truncate">{(h.evidencia_a_favor ?? []).join("; ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {(diag.contrastes ?? []).length > 0 && (
                <>
                  <h3 className="salud-sub">Contraste entre especialistas</h3>
                  <ul>
                    {diag.contrastes!.map((c, i) => (
                      <li key={i}><strong>{c.especialista}</strong> ({c.postura}): {c.argumento}</li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          )}

          {seccion === "alternativas" && (
            <section className="panel" id="seccion-alternativas">
              <h2>Alternativas evaluadas</h2>
              {(diag.alternativas ?? []).map((a) => (
                <div key={a.alternativa_id} className="salud-prop-card">
                  <strong>{a.descripcion}</strong>
                  <p className="muted">{a.fundamento}</p>
                  <p className="muted">Plazo: {a.plazo} · Confianza: {a.confianza}</p>
                </div>
              ))}
              <h3 className="salud-sub">Priorización</h3>
              <p className="muted">{diag.priorizacion?.metodologia}</p>
              <ol>
                {(diag.priorizacion?.ranking ?? []).slice(0, 8).map((r) => (
                  <li key={`${r.ranking}-${r.titulo}`}>{r.titulo} — prioridad {r.prioridad?.toFixed(1)}. {r.por_que_primero}</li>
                ))}
              </ol>
            </section>
          )}

          {seccion === "impacto" && (
            <section className="panel" id="seccion-impacto">
              <h2>Impacto y FINOPS</h2>
              <div className="salud-kpi-grid">
                {Object.entries(diag.escenarios?.escenarios ?? {}).map(([k, sc]) => (
                  <div key={k} className="salud-kpi-card">
                    <h3>{sc.nombre}</h3>
                    <p>{formatMoney(sc.valor_recuperable_estimado)}</p>
                    <p className="muted">{(sc.supuestos ?? []).join(" ")}</p>
                  </div>
                ))}
              </div>
              <h3 className="salud-sub">Valor por propuesta (estimado)</h3>
              <div className="table-wrap">
                <table className="data-table">
                  <thead><tr><th>Referencia</th><th>Beneficio</th><th>Certidumbre</th><th>Retorno de inversión</th></tr></thead>
                  <tbody>
                    {(diag.finops ?? []).map((f) => (
                      <tr key={f.referencia}>
                        <td className="cell-truncate">{f.referencia}</td>
                        <td>{formatMoney(f.beneficio_esperado)}</td>
                        <td>{f.certidumbre}</td>
                        <td>{f.roi ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {seccion === "trazabilidad" && (
            <section className="panel" id="seccion-trazabilidad">
              <h2>Trazabilidad del motor</h2>
              <ol className="salud-cadena">
                <li><strong>Solicitud:</strong> {String(diag.recomendacion_consolidada?.solicitud ?? "—")}</li>
                <li><strong>Suficiencia:</strong> {diag.suficiencia_datos?.clasificacion ?? "—"}</li>
                <li><strong>Hipótesis principal:</strong> {diag.hipotesis_principal?.titulo ?? "—"}</li>
                <li><strong>Especialistas:</strong> {(diag.especialistas.asignaciones ?? []).length}</li>
                <li><strong>Contrastes:</strong> {(diag.contrastes ?? []).length}</li>
                <li><strong>Alternativas:</strong> {(diag.alternativas ?? []).length}</li>
              </ol>
              <h3 className="salud-sub">Cadena financiera</h3>
              <div className="salud-traza-grid">
                {Object.entries(diag.trazabilidad)
                  .filter(([k]) => !["conocimiento", "motor"].includes(k))
                  .map(([k, v]) => (
                  <div key={k} className="salud-traza-item">
                    <span>{k.replace(/_/g, " ")}</span>
                    <strong>{typeof v === "number" ? formatMoney(v) : String(v)}</strong>
                  </div>
                ))}
              </div>
            </section>
          )}

          {seccion === "oportunidades" && (
            <section className="panel" id="seccion-oportunidades">
              <h2>Oportunidades y propuestas</h2>
              {diag.oportunidades.map((o) => (
                <div key={o.id} className="salud-prop-card">
                  <label className="check-item">
                    <input type="checkbox" checked={propSel.has(o.id)} onChange={() => toggleProp(o.id)} />
                    <strong>{o.problema}</strong>
                  </label>
                  <p>{o.accion_propuesta}</p>
                  <p className="muted">Evidencia: {o.evidencia}</p>
                  <p className="muted">Causa probable: {o.causa_probable}</p>
                  <p className="muted">{o.responsable_sugerido} · Plazo: {o.plazo} · Confianza: {o.confianza} · Prioridad: {o.prioridad?.toFixed(1)}</p>
                  <p className="muted">Meta: {o.meta} · Indicador: {o.indicador_seguimiento}</p>
                </div>
              ))}
              <div className="ops-actions">
                <button type="button" className="btn primary" disabled={propSel.size === 0} onClick={crearPlan}>
                  Crear plan de acción ({propSel.size} seleccionadas)
                </button>
              </div>
            </section>
          )}

          {seccion === "plan" && (
            <section className="panel" id="seccion-plan">
              <h2>Plan de acción</h2>
              {(lastWorkPlanId || diag.work_plan_id) && (
                <div className="ops-actions" style={{ marginBottom: "1rem" }}>
                  <Link className="btn primary" to={`/operaciones/${lastWorkPlanId ?? diag.work_plan_id}`}>
                    Abrir en Operaciones
                  </Link>
                </div>
              )}
              {(diag.planes_accion ?? []).map((plan) => (
                plan.work_plan_id ? (
                  <p key={plan.id} className="muted">
                    {plan.titulo} —{" "}
                    <Link to={`/operaciones/${plan.work_plan_id}`}>Ver en centro de operaciones</Link>
                  </p>
                ) : null
              ))}
              {diag.plan_accion.length === 0 ? (
                <p className="muted">Seleccione oportunidades en la pestaña anterior para generar un plan.</p>
              ) : (
                diag.plan_accion.flat().map((t, i) => (
                  <div key={i} className="salud-tarea-card">
                    <strong>{t.titulo}</strong>
                    <p>{t.accion ?? t.titulo}</p>
                    <p className="muted">Responsable: {t.responsable} · Plazo: {t.plazo} · Estado: {t.estado}</p>
                    <p className="muted">Meta: {t.meta}</p>
                  </div>
                ))
              )}
            </section>
          )}

          {seccion === "seguimiento" && (
            <section className="panel" id="seccion-seguimiento">
              <h2>Seguimiento</h2>
              <h3>Trazabilidad financiera</h3>
              <div className="salud-traza-grid">
                {Object.entries(diag.trazabilidad).map(([k, v]) => (
                  <div key={k} className="salud-traza-item">
                    <span>{k.replace(/_/g, " ")}</span>
                    <strong>{formatMoney(v)}</strong>
                  </div>
                ))}
              </div>
              <h3>Registrar resultado posterior</h3>
              {diag.oportunidades.slice(0, 2).map((o) => (
                <div key={o.id} className="ops-actions">
                  <span className="cell-truncate">{o.problema}</span>
                  <button type="button" className="btn" onClick={() => registrarResultado(o.id)}>Registrar seguimiento</button>
                </div>
              ))}
            </section>
          )}

          {seccion === "especialistas" && (
            <section className="panel" id="seccion-especialistas">
              <h2>Selección de especialistas</h2>
              {diag.especialistas.lider && (
                <div className="salud-sub" style={{ marginBottom: "0.75rem" }}>
                  <strong>Líder:</strong> {diag.especialistas.lider.employee_name}
                  <span className="muted"> — {diag.especialistas.lider.specialty}</span>
                  {diag.especialistas.razon_seleccion_global && (
                    <p className="muted" style={{ margin: "0.25rem 0 0" }}>{diag.especialistas.razon_seleccion_global}</p>
                  )}
                </div>
              )}
              <p><strong>Dominio principal:</strong> {DOMINIO_ES[diag.especialistas.dominio_principal ?? ""] ?? diag.especialistas.dominio_principal ?? "—"}</p>
              <p><strong>Dominios detectados:</strong> {(diag.especialistas.dominios ?? []).map((d) => DOMINIO_ES[d] ?? d).join(", ")}</p>
              {(diag.especialistas.equipo ?? []).length > 0 && (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr><th>Rol</th><th>Especialista</th><th>Dominio</th><th>Puntaje</th><th>Razón</th></tr>
                    </thead>
                    <tbody>
                      {(diag.especialistas.equipo ?? []).map((s) => (
                        <tr key={`${s.rol}-${s.employee_name}`}>
                          <td>{s.rol ?? "—"}</td>
                          <td>{s.employee_name}<br /><span className="muted">{s.specialty}</span></td>
                          <td>{DOMINIO_ES[s.domain] ?? s.domain}</td>
                          <td>{s.score?.toFixed(2) ?? "—"}</td>
                          <td className="muted" style={{ maxWidth: 280 }}>{s.razon_rol ?? s.razon_seleccion ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {!(diag.especialistas.equipo ?? []).length && (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr><th>Especialista</th><th>Dominio</th><th>Puntaje</th></tr>
                    </thead>
                    <tbody>
                      {(diag.especialistas.asignaciones ?? []).map((s) => (
                        <tr key={`${s.employee_name}-${s.domain}`}>
                          <td>{s.employee_name}</td>
                          <td>{DOMINIO_ES[s.domain] ?? s.domain}</td>
                          <td>{s.score.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {diag.especialistas.validador && (
                <p className="muted">Validador: {diag.especialistas.validador.employee_name}</p>
              )}
            </section>
          )}

          {seccion === "experiencia" && (
            <section className="panel" id="seccion-experiencia">
              <h2>Experiencia</h2>
              <p>Casos similares registrados: {(diag.experiencia.casos_similares ?? []).length}</p>
              <ul>
                {(diag.experiencia.casos_similares ?? []).map((c, i) => (
                  <li key={i}>{c.ips_name} — similitud {c.similitud} {c.evaluacion ? `(${c.evaluacion})` : ""}</li>
                ))}
              </ul>
              <h3>Pregunta natural</h3>
              <div className="ops-actions">
                <input className="ops-input" value={pregunta} onChange={(e) => setPregunta(e.target.value)} placeholder="Escriba una pregunta…" />
                <button type="button" className="btn" onClick={preguntar}>Preguntar</button>
              </div>
              {respuesta && (
                <div className="salud-respuesta">
                  <p>{String(respuesta.respuesta)}</p>
                  <p className="muted">Incertidumbre: {String(respuesta.incertidumbre)}</p>
                  {respuesta.accion_sugerida ? <p className="muted">Acción sugerida: {String(respuesta.accion_sugerida)}</p> : null}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
