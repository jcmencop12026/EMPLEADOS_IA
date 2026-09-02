import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  crearIndicador,
  crearOportunidadDesdeHallazgo,
  evaluarExpediente,
  fetchEvaluacion,
  fetchEvaluacionImpacto,
  fetchEvaluacionTrazabilidad,
  fetchInformesImpacto,
  fetchPiiaxStatus,
  fetchVistaEntidad,
  setHallazgoVisibilidad,
  updateEvaluacionInformacion,
  type EvaluacionExpedienteDetail,
  type EvaluacionHallazgo,
  type EvaluacionInfoItem,
} from "../api";
import { EiaaxContextualAssistant } from "../components/EiaaxContextualAssistant";
import { EiaaxTable } from "../components/EiaaxTable";
import { EspacioExternoAdminPanel } from "../components/espacioExterno/EspacioExternoAdminPanel";
import { AccionesExternasPanel } from "../components/evaluacion/AccionesExternasPanel";
import { EiaaxAskPanel } from "../components/evaluacion/EiaaxAskPanel";
import { EmpresaOperacionPanel } from "../components/evaluacion/EmpresaOperacionPanel";
import { ImpactoGrafico } from "../components/evaluacion/ImpactoGrafico";
import { SiguienteAccionPanel } from "../components/evaluacion/SiguienteAccionPanel";
import { SolucionIaProyectadaPanel } from "../components/evaluacion/SolucionIaProyectadaPanel";
import { VistaEntidadView } from "../components/evaluacion/VistaEntidadView";
import { usePermissions } from "../hooks/usePermissions";
import { CONFIANZA, ESTADO_EXPEDIENTE, label, TIPO_CONTENIDO } from "../lib/evaluacionLabels";

type Tab =
  | "empresa"
  | "diagnostico"
  | "solucion"
  | "operacion"
  | "consumo"
  | "valor"
  | "resultados"
  | "informes"
  | "contrato"
  | "vista-empresa";

const TABS: { id: Tab; label: string }[] = [
  { id: "empresa", label: "Empresa" },
  { id: "diagnostico", label: "Diagnóstico" },
  { id: "solucion", label: "Solución IA" },
  { id: "operacion", label: "Operación" },
  { id: "consumo", label: "Consumo" },
  { id: "valor", label: "Valor" },
  { id: "resultados", label: "Resultados" },
  { id: "informes", label: "Informes" },
  { id: "contrato", label: "Contrato" },
  { id: "vista-empresa", label: "Vista Empresa" },
];

const ESTADO_INFO_LABELS: Record<string, string> = {
  RECIBIDO: "Recibido",
  INCOMPLETO: "Incompleto",
  PENDIENTE: "Pendiente",
  OPCIONAL: "Opcional",
};

export function EvaluacionConsolePage() {
  const { evaluacionId } = useParams<{ evaluacionId: string }>();
  const { has } = usePermissions();
  const [tab, setTab] = useState<Tab>("empresa");
  const [informes, setInformes] = useState<Array<Record<string, unknown>>>([]);
  const [exp, setExp] = useState<EvaluacionExpedienteDetail | null>(null);
  const [impacto, setImpacto] = useState<Record<string, unknown> | null>(null);
  const [trazabilidad, setTrazabilidad] = useState<Record<string, unknown> | null>(null);
  const [vistaEntidad, setVistaEntidad] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [askOpen, setAskOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [piiax, setPiiax] = useState<Record<string, unknown> | null>(null);

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
    fetchPiiaxStatus().then(setPiiax).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!evaluacionId) return;
    if (tab === "valor" || tab === "resultados") {
      fetchEvaluacionImpacto(evaluacionId).then(setImpacto).catch(() => undefined);
    }
    if (tab === "informes") {
      fetchInformesImpacto(evaluacionId)
        .then((r) => setInformes(r.items as unknown as Array<Record<string, unknown>>))
        .catch(() => undefined);
    }
    if (tab === "vista-empresa" && has("evaluacion.vista_entidad")) {
      fetchVistaEntidad(evaluacionId).then(setVistaEntidad).catch(() => undefined);
      fetchEvaluacionTrazabilidad(evaluacionId).then(setTrazabilidad).catch(() => undefined);
    }
  }, [tab, evaluacionId, has]);

  async function onEvaluar() {
    if (!evaluacionId) return;
    try {
      const r = await evaluarExpediente(evaluacionId);
      setExp(r.expediente);
      setMsg(`Evaluación ejecutada — ${r.hallazgos_creados} hallazgo(s) generado(s)`);
      setTab("diagnostico");
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
    <div className={`eval-console cabina-empresa-v1 ${askOpen ? "with-ask-panel" : ""}`}>
      <div className="eval-console-main">
        <header className="eval-console-header cabina-empresa-header">
          <div>
            <Link to="/evaluaciones" className="muted">← Evaluaciones</Link>
            <p className="eyebrow">Cabina empresa V1</p>
            <h1>{exp.titulo}</h1>
            <p className="muted">{exp.codigo} · {exp.entidad_nombre}</p>
          </div>
          <div className="cabina-empresa-header__actions">
            <Link to="/centro-control" className="btn secondary small">Centro de Control</Link>
            <Link to={`/presentacion/${evaluacionId}`} className="btn secondary small">Presentación</Link>
            <button type="button" className="btn primary" onClick={() => setAskOpen(true)}>
              Preguntar a EIAAX
            </button>
          </div>
        </header>

        <div className="piiax-status-bar compact">
          <span className={`piiax-dot ${piiax?.disponible ? "on" : "off"}`} />
          <span>{piiax?.disponible ? "PIIAX disponible" : "PIIAX no conectado"}</span>
        </div>

        <div className="eval-metrics metrics-grid">
          <div className="metric-card"><span className="metric-label">Entidad</span><strong>{exp.entidad_nombre}</strong></div>
          <div className="metric-card"><span className="metric-label">Estado</span><strong>{label(ESTADO_EXPEDIENTE, exp.estado)}</strong></div>
          <div className="metric-card"><span className="metric-label">Información</span><strong>{exp.porcentaje_informacion}%</strong></div>
          <div className="metric-card"><span className="metric-label">Confianza</span><strong>{label(CONFIANZA, exp.confianza_global)}</strong></div>
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

        {tab === "empresa" && (
          <section className="panel compact-panel">
            <SiguienteAccionPanel
              expedienteId={evaluacionId}
              onNavigateTab={(p) => {
                const map: Record<string, Tab> = {
                  resumen: "empresa",
                  empresa: "empresa",
                  informacion: "diagnostico",
                  diagnostico: "diagnostico",
                  analisis: "diagnostico",
                  impacto: "valor",
                  valor: "valor",
                  oportunidades: "resultados",
                  solucion: "solucion",
                };
                if (map[p]) setTab(map[p]);
              }}
              onRefresh={load}
            />
            <h2>Resumen ejecutivo</h2>
            <dl className="detail-dl">
              <dt>Problema</dt><dd>{exp.necesidad ?? "—"}</dd>
              <dt>Objetivo</dt><dd>{exp.objetivo ?? "—"}</dd>
              <dt>Área / proceso</dt><dd>{exp.area_proceso ?? "—"}</dd>
              <dt>Nivel</dt><dd>{exp.nivel}</dd>
            </dl>
            {exp.oportunidades_vinculadas.length > 0 && (
              <>
                <h3>Oportunidades vinculadas</h3>
                <ul>
                  {exp.oportunidades_vinculadas.map((oid) => (
                    <li key={oid}><Link to={`/oportunidades/${oid}`}>Ver oportunidad {oid.slice(0, 8)}…</Link></li>
                  ))}
                </ul>
              </>
            )}
            {has("evaluacion.evaluate") && (
              <button type="button" className="btn primary" onClick={onEvaluar}>
                Ejecutar evaluación preliminar
              </button>
            )}
          </section>
        )}

        {tab === "diagnostico" && (
          <>
            <section className="panel compact-panel">
              <h2>Información adaptativa</h2>
              {exp.informacion.map((item) => (
                <InformacionRow key={item.id} item={item} editable={has("evaluacion.manage")} onSave={onSaveInfo} />
              ))}
            </section>
            <section className="panel compact-panel">
              <h2>Hallazgos y análisis</h2>
              {exp.hallazgos.length === 0 && <p className="muted">Sin hallazgos. Ejecute la evaluación preliminar.</p>}
              {exp.hallazgos.map((h) => (
                <div key={h.id}>
                  <HallazgoCard
                    hallazgo={h}
                    canVisibility={has("evaluacion.visibility")}
                    canOpp={has("evaluacion.manage")}
                    onToggleVisibilidad={() => onToggleVisibilidad(h)}
                    onCrearOportunidad={() => onCrearOportunidad(h)}
                  />
                  {evaluacionId && has("evaluacion.accion.request") && (
                    <AccionesExternasPanel
                      expedienteId={evaluacionId}
                      hallazgoId={h.id}
                      hallazgoTitulo={h.titulo}
                    />
                  )}
                </div>
              ))}
            </section>
          </>
        )}

        {tab === "solucion" && evaluacionId && (
          <SolucionIaProyectadaPanel expedienteId={evaluacionId} canGenerate={has("evaluacion.evaluate")} />
        )}

        {tab === "operacion" && <EmpresaOperacionPanel />}

        {tab === "consumo" && (
          <section className="panel compact-panel">
            <h2>Consumo</h2>
            <p className="muted small">
              Consumo de capacidad IA asociado a empleados y ejecuciones de esta evaluación.
            </p>
            <dl className="detail-grid">
              <dt>Valor potencial</dt><dd>{exp.valor_potencial ?? "—"}</dd>
              <dt>Información completada</dt><dd>{exp.porcentaje_informacion}%</dd>
              <dt>Confianza global</dt><dd>{label(CONFIANZA, exp.confianza_global)}</dd>
            </dl>
            <p>
              <Link to="/costos-valor">Ver costos y valor</Link>
              {" · "}
              <Link to="/ejecuciones">Ejecuciones</Link>
            </p>
          </section>
        )}

        {tab === "valor" && (
          <section className="panel compact-panel">
            <h2>Valor e impacto</h2>
            {!impacto ? (
              <p className="muted">Cargando indicadores de valor…</p>
            ) : (
              <>
                <p className="muted small">{String(impacto.nota)}</p>
                {has("evaluacion.indicadores.manage") && evaluacionId && (
                  <ImpactoIndicadorForm expedienteId={evaluacionId} onCreated={() => fetchEvaluacionImpacto(evaluacionId).then(setImpacto)} />
                )}
                <table className="data-table compact-table">
                  <thead>
                    <tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th><th>Visualización</th></tr>
                  </thead>
                  <tbody>
                    {((impacto.indicadores as Record<string, unknown>[]) ?? []).map((ind) => (
                      <ImpactoGrafico
                        key={String(ind.id ?? ind.nombre)}
                        nombre={String(ind.nombre ?? ind.hallazgo ?? "—")}
                        unidad={ind.unidad as string | null}
                        grafico={ind.grafico as { puntos: { serie: string; valor: string; numerico: number | null; es_proyeccion: boolean }[] } | null}
                        antes={ind.antes as string | null}
                        proyectado={ind.proyectado as string | null}
                        real={ind.real as string | null}
                      />
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </section>
        )}

        {tab === "resultados" && (
          <section className="panel compact-panel">
            <h2>Resultados</h2>
            <p><Link to={`/resultados-inteligencia?expediente=${evaluacionId}`}>Abrir inteligencia de resultados</Link></p>
            {impacto && ((impacto.indicadores as Record<string, unknown>[]) ?? []).length > 0 ? (
              <EiaaxTable
                columns={[
                  { key: "nombre", label: "Indicador", getValue: (r) => String(r.nombre ?? ""), render: (r) => String(r.nombre ?? "—") },
                  { key: "antes", label: "Antes", getValue: (r) => String(r.antes ?? ""), render: (r) => String(r.antes ?? "—") },
                  { key: "proyectado", label: "Proyectado", getValue: (r) => String(r.proyectado ?? ""), render: (r) => String(r.proyectado ?? "—") },
                  { key: "real", label: "Real", getValue: (r) => String(r.real ?? ""), render: (r) => String(r.real ?? "—") },
                ]}
                data={(impacto.indicadores as Record<string, unknown>[]) ?? []}
                rowKey={(r) => String(r.id ?? r.nombre)}
                prefsKey="cabina-resultados"
                searchPlaceholder="Buscar indicador…"
                emptyMessage="Sin resultados registrados"
              />
            ) : (
              <p className="muted">Sin resultados medidos. Defina indicadores en la pestaña Valor.</p>
            )}
          </section>
        )}

        {tab === "informes" && (
          <section className="panel compact-panel">
            <h2>Informes</h2>
            <div className="ops-actions">
              <Link className="btn secondary" to={`/presentacion/${evaluacionId}`}>Presentación ejecutiva</Link>
              <Link className="btn secondary" to="/demo/informes-periodicos">Informes periódicos</Link>
            </div>
            {informes.length > 0 ? (
              <EiaaxTable
                columns={[
                  { key: "titulo", label: "Título", getValue: (r) => String(r.titulo ?? ""), render: (r) => String(r.titulo ?? "—") },
                  { key: "tipo", label: "Tipo", getValue: (r) => String(r.tipo ?? ""), render: (r) => String(r.tipo ?? "—") },
                  { key: "version", label: "Versión", getValue: (r) => String(r.version ?? ""), render: (r) => String(r.version ?? "—") },
                ]}
                data={informes}
                rowKey={(r) => String(r.id)}
                prefsKey="cabina-informes"
                searchPlaceholder="Buscar informe…"
                emptyMessage="Sin informes generados"
              />
            ) : (
              <p className="muted">Genere informes desde Presentación o el módulo de resultados.</p>
            )}
          </section>
        )}

        {tab === "contrato" && (
          <section className="panel compact-panel">
            <h2>Contrato</h2>
            <p className="muted small">
              Gestión contractual y promoción de prospecto a cliente contratado.
            </p>
            <EspacioExternoAdminPanel expedienteId={evaluacionId} />
          </section>
        )}

        {tab === "vista-empresa" && (
          <>
            <EspacioExternoAdminPanel expedienteId={evaluacionId} />
            {has("evaluacion.vista_entidad") && (
              <section className="panel compact-panel vista-entidad-preview">
                <h2>Vista Empresa (previsualización)</h2>
                <p className="muted small">Lo que la empresa vería según permisos y banderas de visibilidad reales.</p>
                {vistaEntidad ? (
                  <VistaEntidadView data={vistaEntidad} />
                ) : (
                  <p className="muted">Cargando vista empresa…</p>
                )}
                <p style={{ marginTop: "1rem" }}>
                  <Link className="btn primary" to="/mi-espacio">Abrir portal externo (mi espacio)</Link>
                </p>
              </section>
            )}
            {trazabilidad && (
              <section className="panel compact-panel">
                <h2>Trazabilidad de publicación</h2>
                <p className="muted">Correlation: {String(trazabilidad.correlation_id ?? "—")}</p>
                <h3>Cambios de visibilidad</h3>
                <ul>
                  {((trazabilidad.visibilidad as Record<string, unknown>[]) ?? []).map((v) => (
                    <li key={String(v.id)}>
                      {String(v.fecha)} — {v.visible_entidad ? "Visible" : "Oculto"} ({String(v.objeto_id).slice(0, 8)})
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>

      <EiaaxAskPanel expedienteId={evaluacionId} open={askOpen} onClose={() => setAskOpen(false)} />

      <EiaaxContextualAssistant
        compact
        title="Asistente contextual"
        context={{
          module: "evaluacion_cabina",
          expediente_id: evaluacionId,
          tab,
          entidad: exp.entidad_nombre,
          estado: exp.estado,
        }}
      />
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
        <span className="badge">{label(TIPO_CONTENIDO, h.tipo_contenido)}</span>
        <span className="badge confianza">{label(CONFIANZA, h.confianza)}</span>
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

function ImpactoIndicadorForm({ expedienteId, onCreated }: { expedienteId: string; onCreated: () => void }) {
  const [nombre, setNombre] = useState("");
  const [antes, setAntes] = useState("");
  const [proyectado, setProyectado] = useState("");
  const [real, setReal] = useState("");

  async function onAdd() {
    if (!nombre.trim()) return;
    await crearIndicador(expedienteId, {
      nombre,
      valor_antes: antes || undefined,
      valor_proyectado: proyectado || undefined,
      valor_real: real || undefined,
    });
    setNombre("");
    setAntes("");
    setProyectado("");
    setReal("");
    onCreated();
  }

  return (
    <div className="impacto-form panel compact-panel">
      <h3>Agregar indicador</h3>
      <div className="form-grid">
        <label>Nombre<input value={nombre} onChange={(e) => setNombre(e.target.value)} /></label>
        <label>Antes<input value={antes} onChange={(e) => setAntes(e.target.value)} /></label>
        <label>Proyectado<input value={proyectado} onChange={(e) => setProyectado(e.target.value)} /></label>
        <label>Real<input value={real} onChange={(e) => setReal(e.target.value)} /></label>
      </div>
      <button type="button" className="btn small primary" onClick={onAdd}>Guardar indicador</button>
    </div>
  );
}
