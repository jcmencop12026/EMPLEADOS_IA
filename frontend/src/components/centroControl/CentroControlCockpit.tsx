import { Link } from "react-router-dom";
import type { CentroControlResumen } from "../../api";
import { ValorComparacionChart } from "../charts/ValorComparacionChart";
import { cicloEtapaIndexFromEstado } from "../../lib/cicloOperativo";
import { CentroControlMasterAccess } from "./CentroControlMasterAccess";
import { AttentionPanel, CycleStepper, KpiStrip } from "../v1";

type Props = {
  data: CentroControlResumen;
  periodo: string;
  expedienteId?: string;
  compact?: boolean;
  isDemoExpediente?: boolean;
  expedienteEstado?: string | null;
};

function fmtNum(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
}

const KPI_PRIORITY = new Set([
  "employees_active",
  "executions_running",
  "approvals_pending",
  "opportunities_open",
  "realized_value",
  "failed_executions",
]);

export function CentroControlCockpit({ data, periodo, expedienteId, compact = false, isDemoExpediente = false, expedienteEstado }: Props) {
  const indicadores = data.resumen_ejecutivo.indicadores;
  const kpis = indicadores.filter((i) => KPI_PRIORITY.has(i.id)).slice(0, 6);
  const fallbackKpis = kpis.length > 0 ? kpis : indicadores.slice(0, 6);
  const etapaActualIdx = expedienteId ? cicloEtapaIndexFromEstado(expedienteEstado) : -1;

  const oportunidades = data.oportunidades;
  const atencionTop = data.atencion_requerida.slice(0, compact ? 3 : 6);

  const valorChartPuntos = [
    { label: "Verificado", valor: typeof data.valor_consolidado?.verificado === "number" ? data.valor_consolidado.verificado : null },
    { label: "Realizado", valor: typeof data.valor_consolidado?.realizado === "number" ? data.valor_consolidado.realizado : null },
    { label: "Potencial", valor: typeof data.valor_consolidado?.potencial === "number" ? data.valor_consolidado.potencial : null, proyectado: true },
  ];

  const kpiItems = fallbackKpis.map((ind) => ({
    id: ind.id,
    label: ind.label,
    value: ind.disponible ? (ind.valor ?? "—") : (ind.estado ?? "Pendiente"),
    tone: ind.id === "failed_executions" && ind.valor ? "attention" as const : ind.id === "realized_value" ? "value" as const : "default" as const,
    href: ind.enlace,
  }));

  return (
    <div className={`cc-cockpit ${compact ? "cc-cockpit--compact" : ""}`}>
      <section className="panel compact-panel v1-cc-command" aria-label="Ciclo operativo">
        <div className="v1-cc-command__head">
          <div>
            <h2 className="section-title">Ciclo operativo EIAAX</h2>
            <p className="muted small">De conocer a mejorar — navegue por etapa con contexto conservado</p>
          </div>
          {expedienteId && (
            <Link to={`/evaluaciones/${expedienteId}`} className="btn small secondary">Abrir cabina</Link>
          )}
        </div>
        <CycleStepper
          currentIndex={etapaActualIdx}
          expedienteId={expedienteId}
          isDemo={isDemoExpediente}
          compact={compact}
        />
      </section>

      <section className="cc-first-viewport panel compact-panel">
        <div className="cc-first-head">
          <div>
            <h2 className="section-title">Resumen de mando</h2>
            <p className="muted small">Periodo: {periodo === "mtd" ? "mes actual" : periodo}</p>
          </div>
          <div className="cc-first-actions">
            <Link to="/trabajo" className="btn small secondary">Mi trabajo</Link>
            <Link to="/operaciones" className="btn small secondary">Operaciones</Link>
          </div>
        </div>

        <KpiStrip items={kpiItems} />

        <div className="cc-first-grid">
          <AttentionPanel
            items={atencionTop.map((item, i) => ({
              id: `${item.tipo}-${i}`,
              title: item.titulo,
              detail: item.tipo,
              href: item.enlace,
              priority: item.prioridad === "alta" ? "alta" : "media",
            }))}
            emptyMessage="Sin asuntos críticos pendientes. El tablero está al día."
          />
          <div className="cc-zone-next v1-executive-card">
            <div className="v1-executive-card__head">
              <h3>Oportunidades y valor</h3>
            </div>
            <div className="v1-executive-card__body">
              <dl className="detail-grid compact">
                <dt>Detectadas</dt>
                <dd>{oportunidades?.resumen?.oportunidades_detectadas ?? "—"}</dd>
                <dt>Aprobables</dt>
                <dd>{oportunidades?.resumen?.pendientes_aprobacion ?? "—"}</dd>
                <dt>Activas</dt>
                <dd>{oportunidades?.resumen?.activas ?? "—"}</dd>
                <dt>Materializadas</dt>
                <dd>{oportunidades?.resumen?.materializadas ?? "—"}</dd>
                <dt>Valor realizado</dt>
                <dd>{fmtNum(data.valor_consolidado?.realizado ?? data.resumen_ejecutivo?.valor?.realizado)}</dd>
                <dt>Valor potencial</dt>
                <dd>{fmtNum(data.valor_consolidado?.potencial)}</dd>
              </dl>
              <p className="cc-inline-links">
                <Link to="/oportunidades">Centro de oportunidades</Link>
                {" · "}
                <Link to="/costos-valor">Valoración</Link>
              </p>
            </div>
          </div>
        </div>
        {compact && valorChartPuntos.some((p) => p.valor != null) && (
          <div className="cc-compact-chart-strip">
            <ValorComparacionChart title="Valor consolidado" puntos={valorChartPuntos} unidad="COP" compact />
          </div>
        )}
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
                <dt>Costo periodo</dt><dd>{data.finops?.dashboard?.total_cost_label ?? "—"}</dd>
                <dt>ROI</dt><dd>{data.finops?.dashboard?.roi_label ?? "—"}</dd>
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
