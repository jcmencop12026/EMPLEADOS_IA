import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  crearOportunidadDesdeHallazgo,
  evaluarExpediente,
  fetchEvaluacion,
  fetchEvaluacionImpacto,
  fetchEvaluacionTrazabilidad,
  fetchVistaEntidad,
  generarPropuestaDesdeDossier,
  setHallazgoVisibilidad,
  syncFlujoInformacion,
  updateEvaluacionInformacion,
  type EvaluacionExpedienteDetail,
  type EvaluacionHallazgo,
  type EvaluacionInfoItem,
} from "../api";
import { EiaaxAskPanel } from "../components/evaluacion/EiaaxAskPanel";
import { usePermissions } from "../hooks/usePermissions";

type Tab = "resumen" | "informacion" | "analisis" | "impacto" | "oportunidades" | "vista-entidad" | "trazabilidad";

const TABS: { id: Tab; label: string }[] = [
  { id: "resumen", label: "Resumen" },
  { id: "informacion", label: "Información" },
  { id: "analisis", label: "Análisis EIAAX" },
  { id: "impacto", label: "Impacto e Indicadores" },
  { id: "oportunidades", label: "Oportunidades" },
  { id: "vista-entidad", label: "Vista Entidad" },
  { id: "trazabilidad", label: "Trazabilidad" },
];

const ESTADO_INFO_LABELS: Record<string, string> = {
  RECIBIDO: "Recibido",
  INCOMPLETO: "Incompleto",
  PENDIENTE: "Pendiente",
  OPCIONAL: "Opcional",
};

export function EvaluacionConsolePage() {
  const { evaluacionId } = useParams<{ evaluacionId: string }>();
  const navigate = useNavigate();
  const { has } = usePermissions();
  const [tab, setTab] = useState<Tab>("resumen");
  const [exp, setExp] = useState<EvaluacionExpedienteDetail | null>(null);
  const [impacto, setImpacto] = useState<Record<string, unknown> | null>(null);
  const [trazabilidad, setTrazabilidad] = useState<Record<string, unknown> | null>(null);
  const [vistaEntidad, setVistaEntidad] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [askOpen, setAskOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    if (!evaluacionId) return;
    setLoading(true);
    fetchEvaluacion(evaluacionId)
      .then((data) => { setExp(data); setError(null); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [evaluacionId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!evaluacionId) return;
    if (tab === "impacto") {
      fetchEvaluacionImpacto(evaluacionId).then(setImpacto).catch(() => undefined);
    }
    if (tab === "trazabilidad") {
      fetchEvaluacionTrazabilidad(evaluacionId).then(setTrazabilidad).catch(() => undefined);
    }
    if (tab === "vista-entidad" && has("evaluacion.vista_entidad")) {
      fetchVistaEntidad(evaluacionId).then(setVistaEntidad).catch(() => undefined);
    }
  }, [tab, evaluacionId, has]);

  async function onEvaluar() {
    if (!evaluacionId) return;
    try {
      const r = await evaluarExpediente(evaluacionId);
      setExp(r.expediente);
      setMsg(`Evaluación ejecutada — ${r.hallazgos_creados} hallazgo(s) generado(s)`);
      setTab("analisis");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al evaluar");
    }
  }

  async function onSaveInfo(item: EvaluacionInfoItem, respuesta: string) {
    if (!evaluacionId) return;
    const updated = await updateEvaluacionInformacion(evaluacionId, item.id, { respuesta });
    setExp(updated);
  }

  async function onToggleVisibilidad(h: EvaluacionHallazgo) {
    if (!evaluacionId || !has("evaluacion.visibility")) return;
    await setHallazgoVisibilidad(evaluacionId, h.id, !h.visible_entidad);
    load();
  }

  async function onCrearOportunidad(h: EvaluacionHallazgo) {
    if (!evaluacionId) return;
    const r = await crearOportunidadDesdeHallazgo(evaluacionId, h.id);
    setMsg(`Oportunidad creada: ${String(r.opportunity_id ?? "—")}`);
    load();
  }

  if (!evaluacionId) return <p className="error">Expediente no especificado</p>;
  if (loading && !exp) return <p className="muted">Cargando expediente…</p>;
  if (!exp) return <p className="error">{error ?? "Expediente no encontrado"}</p>;

  const oportunidadesCount = exp.hallazgos.filter((h) => h.opportunity_id).length;

  return (
    <div className={`eval-console ${askOpen ? "with-ask-panel" : ""}`}>
      <div className="eval-console-main">
        <header className="eval-console-header">
          <div>
            <Link to="/evaluaciones" className="muted">← Evaluaciones</Link>
            <h1>{exp.titulo}</h1>
            <p className="muted">{exp.codigo}</p>
          </div>
          <div className="ops-actions">
            {has("evaluacion.manage") && (
              <button type="button" className="btn" onClick={async () => {
                if (!evaluacionId) return;
                await syncFlujoInformacion(evaluacionId);
                load();
                setMsg("Catálogo contextual sincronizado");
              }}>Sincronizar info contextual</button>
            )}
            {has("negocio.manage") && (
              <button type="button" className="btn primary" onClick={async () => {
                if (!evaluacionId) return;
                try {
                  const r = await generarPropuestaDesdeDossier(evaluacionId, {});
                  setMsg("Propuesta generada desde dossier");
                  if (r.proposal_id) navigate(`/centro-negocios/propuestas/${r.proposal_id}`);
                } catch (e) {
                  setError(e instanceof Error ? e.message : "No se pudo generar propuesta");
                }
              }}>Generar propuesta →</button>
            )}
            <button type="button" className="btn" onClick={() => setAskOpen(true)}>
              Preguntar a EIAAX
            </button>
          </div>
        </header>

        <div className="eval-metrics metrics-grid">
          <div className="metric-card"><span className="metric-label">Entidad</span><strong>{exp.entidad_nombre}</strong></div>
          <div className="metric-card"><span className="metric-label">Estado</span><strong>{exp.estado}</strong></div>
          <div className="metric-card"><span className="metric-label">Información</span><strong>{exp.porcentaje_informacion}%</strong></div>
          <div className="metric-card"><span className="metric-label">Confianza</span><strong>{exp.confianza_global}</strong></div>
          <div className="metric-card"><span className="metric-label">Oportunidades</span><strong>{oportunidadesCount}</strong></div>
          <div className="metric-card"><span className="metric-label">Valor potencial</span><strong>{exp.valor_potencial ?? "—"}</strong></div>
        </div>

        {error && <p className="error">{error}</p>}
        {msg && <p className="success">{msg}</p>}

        <nav className="tab-nav compact-tabs">
          {TABS.map((t) => (
            <button key={t.id} type="button" className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        {tab === "resumen" && (
          <section className="panel compact-panel">
            <h2>Resumen ejecutivo</h2>
            <dl className="detail-dl">
              <dt>Problema</dt><dd>{exp.necesidad ?? "—"}</dd>
              <dt>Objetivo</dt><dd>{exp.objetivo ?? "—"}</dd>
              <dt>Área / proceso</dt><dd>{exp.area_proceso ?? "—"}</dd>
              <dt>Nivel</dt><dd>{exp.nivel}</dd>
            </dl>
            {has("evaluacion.evaluate") && (
              <button type="button" className="btn primary" onClick={onEvaluar}>
                Ejecutar evaluación preliminar
              </button>
            )}
          </section>
        )}

        {tab === "informacion" && (
          <section className="panel compact-panel">
            <h2>Información adaptativa</h2>
            {exp.informacion.map((item) => (
              <InformacionRow key={item.id} item={item} editable={has("evaluacion.manage")} onSave={onSaveInfo} />
            ))}
          </section>
        )}

        {tab === "analisis" && (
          <section className="panel compact-panel">
            <h2>Hallazgos y análisis</h2>
            {exp.hallazgos.length === 0 && <p className="muted">Sin hallazgos. Ejecute la evaluación preliminar.</p>}
            {exp.hallazgos.map((h) => (
              <HallazgoCard
                key={h.id}
                hallazgo={h}
                canVisibility={has("evaluacion.visibility")}
                canOpp={has("evaluacion.manage")}
                onToggleVisibilidad={() => onToggleVisibilidad(h)}
                onCrearOportunidad={() => onCrearOportunidad(h)}
              />
            ))}
          </section>
        )}

        {tab === "impacto" && impacto && (
          <section className="panel compact-panel">
            <h2>Impacto e indicadores</h2>
            <p className="muted small">{String(impacto.nota)}</p>
            <table className="data-table compact-table">
              <thead>
                <tr><th>Hallazgo</th><th>Antes</th><th>Proyectado</th><th>Real</th><th>Confianza</th></tr>
              </thead>
              <tbody>
                {((impacto.indicadores as Record<string, unknown>[]) ?? []).map((ind, i) => (
                  <tr key={i}>
                    <td>{String(ind.hallazgo)}</td>
                    <td>{ind.antes != null ? String(ind.antes) : "—"}</td>
                    <td>{ind.proyectado != null ? <span className="tag-proyectado">{String(ind.proyectado)}</span> : "—"}</td>
                    <td>{ind.real != null ? String(ind.real) : "—"}</td>
                    <td>{String(ind.confianza ?? "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {tab === "oportunidades" && (
          <section className="panel compact-panel">
            <h2>Oportunidades vinculadas</h2>
            {exp.oportunidades_vinculadas.length === 0 && (
              <p className="muted">Cree o vincule oportunidades desde un hallazgo en la pestaña Análisis.</p>
            )}
            <ul>
              {exp.oportunidades_vinculadas.map((oid) => (
                <li key={oid}><Link to={`/oportunidades/${oid}`}>Ver oportunidad {oid.slice(0, 8)}…</Link></li>
              ))}
            </ul>
            <Link to="/oportunidades" className="btn">Centro de oportunidades →</Link>
          </section>
        )}

        {tab === "vista-entidad" && has("evaluacion.vista_entidad") && (
          <section className="panel compact-panel vista-entidad-preview">
            <h2>Vista Entidad (previsualización)</h2>
            <p className="muted small">Lo que la entidad vería según permisos y banderas de visibilidad reales.</p>
            {vistaEntidad ? (
              <pre className="code-block">{JSON.stringify(vistaEntidad, null, 2)}</pre>
            ) : (
              <p className="muted">Cargando vista entidad…</p>
            )}
          </section>
        )}

        {tab === "trazabilidad" && trazabilidad && (
          <section className="panel compact-panel">
            <h2>Trazabilidad</h2>
            <p className="muted">Correlation: {String(trazabilidad.correlation_id ?? "—")}</p>
            <h3>Cambios de visibilidad</h3>
            <ul>
              {((trazabilidad.visibilidad as Record<string, unknown>[]) ?? []).map((v) => (
                <li key={String(v.id)}>
                  {String(v.fecha)} — {v.visible_entidad ? "Visible" : "Oculto"} ({String(v.objeto_id).slice(0, 8)})
                </li>
              ))}
            </ul>
            <h3>Hallazgos</h3>
            <ul>
              {((trazabilidad.hallazgos as Record<string, unknown>[]) ?? []).map((h) => (
                <li key={String(h.id)}>{String(h.titulo)} — {String(h.confianza)} — {String(h.origen)}</li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <EiaaxAskPanel expedienteId={evaluacionId} open={askOpen} onClose={() => setAskOpen(false)} />
    </div>
  );
}

function InformacionRow({
  item,
  editable,
  onSave,
}: {
  item: EvaluacionInfoItem;
  editable: boolean;
  onSave: (item: EvaluacionInfoItem, respuesta: string) => Promise<void>;
}) {
  const [respuesta, setRespuesta] = useState(item.respuesta ?? "");
  const [saving, setSaving] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(item, respuesta);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={`info-item estado-${item.estado.toLowerCase()}`}>
      <div className="info-item-header">
        <strong>{item.etiqueta}</strong>
        <span className={`badge estado-${item.estado.toLowerCase()}`}>{ESTADO_INFO_LABELS[item.estado] ?? item.estado}</span>
        {!item.obligatorio && <span className="badge">Opcional</span>}
      </div>
      <p className="muted small">{item.explicacion}</p>
      <p className="muted small"><em>Por qué:</em> {item.por_que}</p>
      {item.estado !== "RECIBIDO" && item.impacto_precision && (
        <p className="warning-text small">{item.impacto_precision}</p>
      )}
      {editable && (
        <form onSubmit={onSubmit}>
          <textarea rows={2} value={respuesta} onChange={(e) => setRespuesta(e.target.value)} placeholder="Respuesta o evidencia…" />
          <button type="submit" className="btn small" disabled={saving}>{saving ? "Guardando…" : "Guardar"}</button>
        </form>
      )}
      {!editable && item.respuesta && <p>{item.respuesta}</p>}
    </div>
  );
}

function HallazgoCard({
  hallazgo: h,
  canVisibility,
  canOpp,
  onToggleVisibilidad,
  onCrearOportunidad,
}: {
  hallazgo: EvaluacionHallazgo;
  canVisibility: boolean;
  canOpp: boolean;
  onToggleVisibilidad: () => void;
  onCrearOportunidad: () => void;
}) {
  return (
    <article className="hallazgo-card">
      <header>
        <strong>{h.titulo}</strong>
        <span className="badge">{h.tipo_contenido}</span>
        <span className="badge confianza">{h.confianza}</span>
        {h.es_problema_original && <span className="badge">Problema original</span>}
      </header>
      {h.descripcion && <p>{h.descripcion}</p>}
      {h.explicacion_confianza && <p className="muted small">Confianza: {h.explicacion_confianza}</p>}
      {h.evidencia && <p className="muted small">Evidencia: {h.evidencia}</p>}
      <div className="hallazgo-actions">
        {canVisibility && (
          <label className="visibility-toggle">
            <input type="checkbox" checked={h.visible_entidad} onChange={onToggleVisibilidad} />
            Visible para entidad
          </label>
        )}
        {canOpp && !h.opportunity_id && (
          <button type="button" className="btn small" onClick={onCrearOportunidad}>Crear oportunidad</button>
        )}
        {h.opportunity_id && (
          <Link to={`/oportunidades/${h.opportunity_id}`} className="btn small">Ver oportunidad</Link>
        )}
      </div>
    </article>
  );
}
