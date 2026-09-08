import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  crearOportunidadDesdeHallazgo,
  evaluarExpediente,
  fetchEvaluacion,
  fetchEvaluacionImpacto,
  fetchEvaluacionTrazabilidad,
  fetchPiiaxStatus,
  fetchVistaEntidad,
  setHallazgoVisibilidad,
  syncInformacionExpediente,
  updateEvaluacionInformacion,
  type EvaluacionExpedienteDetail,
  type EvaluacionHallazgo,
  type EvaluacionInfoItem,
} from "../api";
import { InformacionAdjuntosPanel } from "../components/evaluacion/InformacionAdjuntosPanel";
import { CadenaAnaliticaPanel } from "../components/evaluacion/CadenaAnaliticaPanel";
import { EspacioExternoAdminPanel } from "../components/espacioExterno/EspacioExternoAdminPanel";
import { AccionesExternasPanel } from "../components/evaluacion/AccionesExternasPanel";
import { CabinaConsumoPanel } from "../components/evaluacion/CabinaConsumoPanel";
import { CabinaContratoPanel } from "../components/evaluacion/CabinaContratoPanel";
import { CabinaInformesPanel } from "../components/evaluacion/CabinaInformesPanel";
import { CabinaResultadosPanel } from "../components/evaluacion/CabinaResultadosPanel";
import { CabinaValorPanel } from "../components/evaluacion/CabinaValorPanel";
import { EiaaxAskPanel } from "../components/evaluacion/EiaaxAskPanel";
import { EmpresaOperacionPanel } from "../components/evaluacion/EmpresaOperacionPanel";
import { SiguienteAccionPanel } from "../components/evaluacion/SiguienteAccionPanel";
import { SolucionIaProyectadaPanel } from "../components/evaluacion/SolucionIaProyectadaPanel";
import { VistaEntidadView } from "../components/evaluacion/VistaEntidadView";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { usePermissions } from "../hooks/usePermissions";
import { CONFIANZA, ESTADO_EXPEDIENTE, label, labelNivelEvaluacion, TIPO_CONTENIDO } from "../lib/evaluacionLabels";
import { mapSiguienteAccionToCabinaTab } from "../lib/siguienteAccionTabMap";
import { formatValorPotencialKpi } from "../lib/formatKpiValue";
import { EmptyState, ExecutiveCard, KpiStrip, PageHeader, TechnicalDetails } from "../components/v1";

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
  const [searchParams, setSearchParams] = useSearchParams();
  const { has } = usePermissions();
  const tabParam = searchParams.get("tab");
  const initialTab = (TABS.some((t) => t.id === tabParam) ? tabParam : "empresa") as Tab;
  const [tab, setTab] = useState<Tab>(initialTab);
  const [exp, setExp] = useState<EvaluacionExpedienteDetail | null>(null);
  const [impacto, setImpacto] = useState<Record<string, unknown> | null>(null);
  const [trazabilidad, setTrazabilidad] = useState<Record<string, unknown> | null>(null);
  const [vistaEntidad, setVistaEntidad] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [askOpen, setAskOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [piiax, setPiiax] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (tabParam && TABS.some((t) => t.id === tabParam)) setTab(tabParam as Tab);
  }, [tabParam]);

  const selectTab = useCallback(
    (next: Tab) => {
      setTab(next);
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev);
          params.set("tab", next);
          return params;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  usePageAssistantContext(
    {
      tab,
      expediente_id: evaluacionId,
      empresa: exp?.entidad_nombre,
      estado: exp?.estado,
      confianza: exp?.confianza_global,
    },
    Boolean(evaluacionId),
  );

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
    fetchEvaluacionImpacto(evaluacionId).then(setImpacto).catch(() => undefined);
  }, [evaluacionId]);

  useEffect(() => {
    if (!evaluacionId) return;
    if (tab === "valor" || tab === "resultados") {
      fetchEvaluacionImpacto(evaluacionId).then(setImpacto).catch(() => undefined);
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
      selectTab("diagnostico");
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
    setMsg("Oportunidad creada correctamente");
    load();
  }

  if (!evaluacionId) return <p className="error">Expediente no especificado</p>;
  if (loading && !exp) return <p className="muted">Cargando expediente…</p>;
  if (!exp) return <p className="error">{error ?? "Expediente no encontrado"}</p>;

  const oportunidadesCount = exp.hallazgos.filter((h) => h.opportunity_id).length;
  const valorKpi = formatValorPotencialKpi(exp.valor_potencial);
  const valorDemoHint = String(exp.valor_potencial ?? "").includes("DEMO") ? "DEMO — DATOS SIMULADOS" : undefined;

  return (
    <div className={`eval-console cabina-empresa-v1 ${askOpen ? "with-ask-panel" : ""}`}>
      <div className="eval-console-main">
        <PageHeader
          eyebrow="Cabina empresa"
          title={exp.titulo}
          subtitle={`${exp.codigo} · ${exp.entidad_nombre}`}
          actions={
            <>
              <Link to="/evaluaciones" className="btn secondary small">← Evaluaciones</Link>
              <Link to="/centro-control" className="btn secondary small">Centro de Control</Link>
              <Link to={`/presentacion/${evaluacionId}`} className="btn secondary small">Presentación</Link>
              <button type="button" className="btn primary" onClick={() => setAskOpen(true)}>
                Preguntar a EIAAX
              </button>
            </>
          }
        />

        <div className="piiax-status-bar compact inline-badge">
          <span className={`piiax-dot ${piiax?.disponible ? "on" : "off"}`} title={piiax?.disponible ? "PIIAX disponible" : "Integración PIIAX no conectada"} />
          <span className="small">{piiax?.disponible ? "PIIAX conectado" : "PIIAX no conectado"}</span>
        </div>

        <KpiStrip
          items={[
            { id: "entidad", label: "Empresa", value: exp.entidad_nombre, wide: true },
            { id: "estado", label: "Estado", value: label(ESTADO_EXPEDIENTE, exp.estado) },
            { id: "info", label: "Información completada", value: `${exp.porcentaje_informacion}%` },
            { id: "conf", label: "Confianza", value: label(CONFIANZA, exp.confianza_global) },
            { id: "opp", label: "Oportunidades", value: oportunidadesCount, tone: oportunidadesCount > 0 ? "success" : "default" },
            {
              id: "valor",
              label: "Valor potencial",
              value: valorKpi.main,
              unit: valorKpi.unit,
              hint: valorDemoHint,
              tone: "value",
              wide: true,
            },
          ]}
        />

        {error && <p className="error">{error}</p>}
        {msg && <p className="success">{msg}</p>}

        <nav className="tab-nav compact-tabs">
          {TABS.map((t) => (
            <button key={t.id} type="button" className={tab === t.id ? "active" : ""} onClick={() => selectTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        {tab === "empresa" && (
          <section className="panel compact-panel">
            <SiguienteAccionPanel
              expedienteId={evaluacionId}
              onNavigateTab={(p) => {
                const mapped = mapSiguienteAccionToCabinaTab(p);
                if (mapped && TABS.some((t) => t.id === mapped)) selectTab(mapped as Tab);
              }}
              onRefresh={load}
            />
            <ExecutiveCard title="Resumen ejecutivo">
            <dl className="detail-dl">
              <dt>Problema</dt><dd>{exp.necesidad ?? "—"}</dd>
              <dt>Objetivo</dt><dd>{exp.objetivo ?? "—"}</dd>
              <dt>Área / proceso</dt><dd>{exp.area_proceso ?? "—"}</dd>
              <dt>Nivel</dt><dd>{labelNivelEvaluacion(exp.nivel)}</dd>
            </dl>
            {exp.oportunidades_vinculadas.length > 0 && (
              <>
                <h3>Oportunidades vinculadas</h3>
                <ul>
                  {exp.oportunidades_vinculadas.map((oid) => (
                    <li key={oid}><Link to={`/oportunidades/${oid}`}>Ver oportunidad vinculada</Link></li>
                  ))}
                </ul>
              </>
            )}
            {has("evaluacion.evaluate") && (
              <button type="button" className="btn primary" onClick={onEvaluar}>
                Ejecutar evaluación preliminar
              </button>
            )}
            </ExecutiveCard>
          </section>
        )}

        {tab === "diagnostico" && (
          <>
            <section className="panel compact-panel">
              <div className="section-head-row">
                <h2>Información adaptativa</h2>
                {has("evaluacion.manage") && evaluacionId && (
                  <button
                    type="button"
                    className="btn small secondary"
                    onClick={() => void syncInformacionExpediente(evaluacionId).then(() => load())}
                  >
                    Sincronizar requisitos
                  </button>
                )}
              </div>
              {exp.informacion.length === 0 && (
                <EmptyState
                  title="Sin requisitos de información"
                  description="Sincronice requisitos según sector y profundidad del expediente para que EIAAX sepa qué información falta."
                  action={
                    has("evaluacion.manage") && evaluacionId ? (
                      <button
                        type="button"
                        className="btn primary small"
                        onClick={() => void syncInformacionExpediente(evaluacionId).then(() => load())}
                      >
                        Sincronizar requisitos
                      </button>
                    ) : undefined
                  }
                />
              )}
              {exp.informacion.map((item) => (
                <InformacionRow
                  key={item.id}
                  expedienteId={evaluacionId!}
                  item={item}
                  editable={has("evaluacion.manage")}
                  onSave={onSaveInfo}
                />
              ))}
            </section>
            <section className="panel compact-panel">
              <CadenaAnaliticaPanel
                expedienteId={evaluacionId!}
                onSyncRequisitos={has("evaluacion.manage") ? () => void syncInformacionExpediente(evaluacionId!).then(() => load()) : undefined}
                onEvaluar={has("evaluacion.evaluate") ? onEvaluar : undefined}
              />
            </section>
            <section className="panel compact-panel">
              <h2>Hallazgos y análisis</h2>
              {exp.hallazgos.length === 0 && (
                <EmptyState
                  title="Sin hallazgos todavía"
                  description="Ejecute la evaluación preliminar para que EIAAX analice el expediente y genere hallazgos accionables."
                  action={
                    has("evaluacion.evaluate") ? (
                      <button type="button" className="btn primary" onClick={onEvaluar}>
                        Ejecutar evaluación preliminar
                      </button>
                    ) : undefined
                  }
                />
              )}
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

        {tab === "operacion" && <EmpresaOperacionPanel expedienteId={evaluacionId} />}

        {tab === "consumo" && (
          <section className="panel compact-panel">
            <CabinaConsumoPanel
              expedienteId={evaluacionId}
              valorPotencial={exp.valor_potencial}
              porcentajeInformacion={exp.porcentaje_informacion}
              confianzaGlobal={exp.confianza_global}
            />
          </section>
        )}

        {tab === "valor" && evaluacionId && (
          <CabinaValorPanel
            expedienteId={evaluacionId}
            impacto={impacto}
            canManageIndicadores={has("evaluacion.indicadores.manage")}
            onImpactoRefresh={() => fetchEvaluacionImpacto(evaluacionId).then(setImpacto)}
          />
        )}

        {tab === "resultados" && (
          <section className="panel compact-panel">
            <CabinaResultadosPanel expedienteId={evaluacionId} impacto={impacto} />
          </section>
        )}

        {tab === "informes" && evaluacionId && (
          <CabinaInformesPanel
            expedienteId={evaluacionId}
            entidadNombre={exp.entidad_nombre}
            areaProceso={exp.area_proceso}
            isDemo={exp.entidad_nombre?.startsWith("[DEMO]")}
          />
        )}

        {tab === "contrato" && evaluacionId && (
          <CabinaContratoPanel expedienteId={evaluacionId} entidadNombre={exp.entidad_nombre} />
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
                  <EmptyState
                    title="Previsualización no disponible"
                    description="Cargando la vista que vería la empresa según permisos y visibilidad configurados."
                  />
                )}
                <p style={{ marginTop: "1rem" }}>
                  <Link className="btn primary" to="/mi-espacio">Abrir portal externo (mi espacio)</Link>
                </p>
              </section>
            )}
            {trazabilidad && (
              <section className="panel compact-panel">
                <h2>Trazabilidad de publicación</h2>
                <h3>Cambios de visibilidad</h3>
                {((trazabilidad.visibilidad as Record<string, unknown>[]) ?? []).length === 0 ? (
                  <EmptyState
                    title="Sin cambios de visibilidad"
                    description="Cuando publique o oculte contenido para la empresa, el historial aparecerá aquí."
                  />
                ) : (
                  <ul>
                    {((trazabilidad.visibilidad as Record<string, unknown>[]) ?? []).map((v) => (
                      <li key={String(v.id)}>
                        {String(v.fecha)} — {v.visible_entidad ? "Visible para empresa" : "Oculto para empresa"}
                      </li>
                    ))}
                  </ul>
                )}
                <TechnicalDetails title="Ver detalle técnico">
                  <p className="mono small">Correlation: {String(trazabilidad.correlation_id ?? "—")}</p>
                  <ul className="mono small">
                    {((trazabilidad.visibilidad as Record<string, unknown>[]) ?? []).map((v) => (
                      <li key={String(v.id)}>
                        {String(v.fecha)} — objeto {String(v.objeto_id)}
                      </li>
                    ))}
                  </ul>
                </TechnicalDetails>
              </section>
            )}
          </>
        )}
      </div>

      <EiaaxAskPanel expedienteId={evaluacionId} open={askOpen} onClose={() => setAskOpen(false)} />
    </div>
  );
}

function InformacionRow({
  expedienteId,
  item,
  editable,
  onSave,
}: {
  expedienteId: string;
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
      <InformacionAdjuntosPanel expedienteId={expedienteId} itemId={item.id} editable={editable} />
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
