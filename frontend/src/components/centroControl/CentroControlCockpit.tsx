import { Link } from "react-router-dom";
import type { CentroControlResumen } from "../../api";
import { ValorComparacionChart } from "../charts/ValorComparacionChart";
import { CICLO_ETAPAS } from "../../lib/cicloOperativo";
import { CentroControlMasterAccess } from "./CentroControlMasterAccess";

type Props = {
  data: CentroControlResumen;
  periodo: string;
  expedienteId?: string;
  /** Vista compacta cuando hay empresa en contexto (evita scroll duplicado). */
  compact?: boolean;
  isDemoExpediente?: boolean;
};

function fmtNum(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
}

function ValorIndicador({ valor, disponible, estado }: { valor: unknown; disponible: boolean; estado?: string | null }) {
  if (!disponible) return <span className="muted cc-kpi-empty">{estado ?? "Pendiente"}</span>;
  if (valor === null || valor === undefined) return <span className="muted cc-kpi-empty">Pendiente</span>;
  return <strong className="cc-kpi-value">{String(valor)}</strong>;
}

const KPI_PRIORITY = new Set([
  "empleados_activos",
  "ejecuciones",
  "aprobaciones_pendientes",
  "atencion",
  "valor_realizado",
  "salud",
]);

export function CentroControlCockpit({ data, periodo, expedienteId, compact = false, isDemoExpediente = false }: Props) {
  const indicadores = data.resumen_ejecutivo.indicadores;
  const kpis = indicadores.filter((i) => KPI_PRIORITY.has(i.id)).slice(0, 6);
  const fallbackKpis = kpis.length > 0 ? kpis : indicadores.slice(0, 6);

  const finops = data.finops;
  const comercial = data.comercial;
  const oportunidades = data.oportunidades;
  const atencionTop = data.atencion_requerida.slice(0, compact ? 3 : 6);

  const valorChartPuntos = [
    { label: "Verificado", valor: typeof data.valor_consolidado?.verificado === "number" ? data.valor_consolidado.verificado : null },
    { label: "Realizado", valor: typeof data.valor_consolidado?.realizado === "number" ? data.valor_consolidado.realizado : null },
    { label: "Potencial", valor: typeof data.valor_consolidado?.potencial === "number" ? data.valor_consolidado.potencial : null, proyectado: true },
  ];

  return (
    <div className={`cc-cockpit ${compact ? "cc-cockpit--compact" : ""}`}>
      <section className="cc-ciclo-strip panel compact-panel" aria-label="Ciclo operativo">
        <span className="muted small cc-ciclo-label">Ciclo</span>
        <div className="cc-ciclo-scroll">
          {CICLO_ETAPAS.map((etapa, idx) => (
            <span key={etapa} className="cc-ciclo-chip" title={`Etapa ${idx + 1}: ${etapa}`}>
              {etapa}
            </span>
          ))}
        </div>
        {expedienteId && (
          <Link to={`/evaluaciones/${expedienteId}`} className="btn small secondary cc-ciclo-action">
            Cabina
          </Link>
        )}
      </section>

      <section className="cc-first-viewport panel compact-panel">
        <div className="cc-first-head">
          <div>
            <h2 className="section-title">Situación operativa</h2>
            <p className="muted small">Periodo: {periodo === "mtd" ? "mes actual" : periodo}</p>
          </div>
          <div className="cc-first-actions">
            <Link to="/trabajo" className="btn small secondary">Mi trabajo</Link>
            <Link to="/operaciones" className="btn small secondary">Operaciones</Link>
          </div>
        </div>
        <div className="cc-kpi-strip">
          {fallbackKpis.map((ind) => (
            <Link key={ind.id} to={ind.enlace} className="cc-kpi-item" title={ind.label}>
              <span className="cc-kpi-label">{ind.label}</span>
              <ValorIndicador valor={ind.valor} disponible={ind.disponible} estado={ind.estado} />
            </Link>
          ))}
        </div>
        <div className="cc-first-grid">
          <div className="cc-zone-attention">
            <h3 className="cc-subtitle">Requiere atención</h3>
            {atencionTop.length === 0 ? (
              <p className="muted small">Sin asuntos críticos pendientes.</p>
            ) : (
              <ul className="cc-list-compact">
                {atencionTop.map((item) => (
                  <li key={`${item.tipo}-${item.prioridad}-${item.titulo}`}>
                    <Link to={item.enlace}>{item.titulo}</Link>
                    <span className="muted small"> · {item.tipo}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="cc-zone-next">
            <h3 className="cc-subtitle">Oportunidades y valor</h3>
            <dl className="detail-grid compact">
              <dt>Detectadas</dt>
              <dd>{oportunidades?.resumen?.oportunidades_detectadas ?? "—"}</dd>
              <dt>Valor realizado</dt>
              <dd>{fmtNum(data.valor_consolidado?.realizado ?? data.resumen_ejecutivo?.valor?.realizado)}</dd>
              <dt>Pend. aprobación</dt>
              <dd>{data.mi_trabajo?.requieren_aprobacion ?? oportunidades?.resumen?.pendientes_aprobacion ?? "—"}</dd>
            </dl>
            <p className="cc-inline-links">
              <Link to="/oportunidades">Oportunidades</Link>
              {" · "}
              <Link to="/costos-valor">Valoración</Link>
              {expedienteId && (
                <>
                  {" · "}
                  <Link to={isDemoExpediente ? `/demo/presentacion/${expedienteId}` : `/presentacion/${expedienteId}`}>Presentar</Link>
                </>
              )}
            </p>
          </div>
        </div>
      </section>

      {!compact && (
        <>
          <div className="cc-cockpit-grid">
            <section className="cc-zone cc-zone-charts panel compact-panel">
              <ValorComparacionChart title="Valor consolidado" puntos={valorChartPuntos} unidad="COP" />
            </section>
            <section className="cc-zone cc-zone-value panel compact-panel">
              <h2 className="section-title">Valor y resultados</h2>
              <dl className="detail-grid compact">
                <dt>Verificado</dt><dd>{fmtNum(data.valor_consolidado?.verificado)}</dd>
                <dt>Costo periodo</dt><dd>{finops?.dashboard?.total_cost_label ?? "—"}</dd>
                <dt>ROI</dt><dd>{finops?.dashboard?.roi_label ?? "—"}</dd>
                {comercial?.margen_promedio_pct != null && (
                  <><dt>Margen</dt><dd>{comercial.margen_promedio_pct}%</dd></>
                )}
              </dl>
            </section>
          </div>

          <details className="cc-master-access-details panel compact-panel">
            <summary className="cc-master-access-summary">Accesos de profundidad (bajo demanda)</summary>
            <CentroControlMasterAccess expedienteId={expedienteId} embedded />
          </details>
        </>
      )}
    </div>
  );
}
