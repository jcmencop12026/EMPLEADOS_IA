import { Link } from "react-router-dom";
import type { CentroControlResumen } from "../../api";
import { ValorComparacionChart } from "../charts/ValorComparacionChart";
import { CentroControlMasterAccess } from "./CentroControlMasterAccess";

type Props = {
  data: CentroControlResumen;
  periodo: string;
  expedienteId?: string;
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

export function CentroControlCockpit({ data, periodo, expedienteId }: Props) {
  const indicadores = data.resumen_ejecutivo.indicadores;
  const kpis = indicadores.filter((i) => KPI_PRIORITY.has(i.id)).slice(0, 6);
  const fallbackKpis = kpis.length > 0 ? kpis : indicadores.slice(0, 6);

  const empleados = data.empleados_ia?.items?.slice(0, 5) ?? [];
  const finops = data.finops;
  const comercial = data.comercial;
  const oportunidades = data.oportunidades;

  const valorChartPuntos = [
    { label: "Verificado", valor: typeof data.valor_consolidado?.verificado === "number" ? data.valor_consolidado.verificado : null },
    { label: "Realizado", valor: typeof data.valor_consolidado?.realizado === "number" ? data.valor_consolidado.realizado : null },
    { label: "Potencial", valor: typeof data.valor_consolidado?.potencial === "number" ? data.valor_consolidado.potencial : null, proyectado: true },
  ];
  const consumoChartPuntos = [
    { label: "Tokens periodo", valor: typeof finops?.tokens_periodo === "number" ? finops.tokens_periodo : null },
    { label: "Costo", valor: typeof finops?.dashboard?.total_cost === "number" ? finops.dashboard.total_cost : null },
    { label: "Valor generado", valor: typeof finops?.dashboard?.total_value === "number" ? finops.dashboard.total_value : null, proyectado: true },
  ];

  return (
    <div className="cc-cockpit">
      <CentroControlMasterAccess expedienteId={expedienteId} />

      <section className="cc-zone cc-zone-status panel compact-panel">
        <div className="cc-zone-head">
          <h2 className="section-title">Estado general</h2>
          <p className="muted small">Lectura ejecutiva inmediata del periodo seleccionado</p>
        </div>
        <div className="cc-kpi-strip">
          {fallbackKpis.map((ind) => (
            <Link key={ind.id} to={ind.enlace} className="cc-kpi-item" title={ind.label}>
              <span className="cc-kpi-label">{ind.label}</span>
              <ValorIndicador valor={ind.valor} disponible={ind.disponible} estado={ind.estado} />
            </Link>
          ))}
        </div>
      </section>

      <div className="cc-cockpit-grid">
        <section className="cc-zone cc-zone-charts panel compact-panel">
          <ValorComparacionChart title="Valor consolidado" puntos={valorChartPuntos} unidad="COP" />
        </section>
        <section className="cc-zone cc-zone-charts panel compact-panel">
          <ValorComparacionChart title="Consumo y costos IA" puntos={consumoChartPuntos} />
        </section>
      </div>

      <div className="cc-cockpit-grid">
        <section className="cc-zone cc-zone-attention panel compact-panel">
          <h2 className="section-title">Atención requerida</h2>
          {data.atencion_requerida.length === 0 ? (
            <p className="muted">Sin asuntos críticos pendientes en este momento.</p>
          ) : (
            <table className="data-table compact-table cc-table-fill">
              <thead>
                <tr><th>#</th><th>Tipo</th><th>Asunto</th><th></th></tr>
              </thead>
              <tbody>
                {data.atencion_requerida.slice(0, 6).map((item) => (
                  <tr key={`${item.tipo}-${item.prioridad}-${item.titulo}`}>
                    <td>{item.prioridad}</td>
                    <td>{item.tipo}</td>
                    <td>{item.titulo}</td>
                    <td><Link to={item.enlace}>Ver</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="cc-zone cc-zone-operation panel compact-panel">
          <h2 className="section-title">Operación</h2>
          <div className="cc-mini-grid">
            <div>
              <h3 className="cc-subtitle">Empleados IA</h3>
              {empleados.length === 0 ? (
                <p className="muted">Sin empleados activos visibles. <Link to="/directorio">Ir al directorio</Link></p>
              ) : (
                <ul className="cc-list-compact">
                  {empleados.map((e) => (
                    <li key={e.id}><Link to={e.enlace}>{e.nombre}</Link> · {e.estado}</li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h3 className="cc-subtitle">Mi trabajo</h3>
              <dl className="detail-grid compact">
                <dt>Pendientes</dt><dd>{data.mi_trabajo?.pendientes ?? "—"}</dd>
                <dt>Aprobaciones</dt><dd>{data.mi_trabajo?.requieren_aprobacion ?? "—"}</dd>
              </dl>
              <p><Link to="/trabajo">Abrir bandeja</Link> · <Link to="/ejecuciones">Ejecuciones</Link></p>
            </div>
          </div>
        </section>
      </div>

      <div className="cc-cockpit-grid">
        <section className="cc-zone cc-zone-opportunities panel compact-panel">
          <h2 className="section-title">Oportunidades</h2>
          {!oportunidades?.disponible ? (
            <p className="muted">{oportunidades?.estado ?? "Sin información disponible"}</p>
          ) : (
            <dl className="detail-grid compact">
              <dt>Detectadas</dt><dd>{oportunidades.resumen?.oportunidades_detectadas ?? "—"}</dd>
              <dt>En seguimiento</dt><dd>{oportunidades.estados_operativos?.seguimiento ?? "—"}</dd>
              <dt>Materializadas</dt><dd>{oportunidades.resumen?.materializadas ?? "—"}</dd>
              <dt>Pend. aprobación</dt><dd>{oportunidades.resumen?.pendientes_aprobacion ?? "—"}</dd>
            </dl>
          )}
          <p><Link to="/oportunidades">Ver oportunidades</Link></p>
        </section>

        <section className="cc-zone cc-zone-approvals panel compact-panel">
          <h2 className="section-title">Aprobaciones y automatizaciones</h2>
          <dl className="detail-grid compact">
            <dt>Aprobaciones pendientes</dt><dd>{data.mi_trabajo?.requieren_aprobacion ?? "—"}</dd>
            <dt>Tareas pendientes</dt><dd>{data.mi_trabajo?.pendientes ?? "—"}</dd>
          </dl>
          <p>
            <Link to="/aprobaciones">Bandeja de aprobaciones</Link>
            {" · "}
            <Link to="/automatizaciones">Automatizaciones</Link>
            {" · "}
            <Link to="/ejecuciones">Ejecuciones</Link>
          </p>
        </section>
      </div>

      <div className="cc-cockpit-grid">
        <section className="cc-zone cc-zone-value panel compact-panel">
          <h2 className="section-title">Valor y resultados</h2>
          <dl className="detail-grid compact">
            <dt>Valor realizado</dt><dd>{fmtNum(data.valor_consolidado?.realizado ?? data.resumen_ejecutivo?.valor?.realizado)}</dd>
            <dt>Verificado</dt><dd>{fmtNum(data.valor_consolidado?.verificado)}</dd>
            <dt>Costo periodo</dt><dd>{finops?.dashboard?.total_cost_label ?? "—"}</dd>
            <dt>ROI</dt><dd>{finops?.dashboard?.roi_label ?? "—"}</dd>
            {comercial?.margen_promedio_pct != null && (
              <><dt>Margen promedio</dt><dd>{comercial.margen_promedio_pct}%</dd></>
            )}
          </dl>
          <p>
            <Link to="/costos-valor">Valoración</Link>
            {" · "}
            <Link to="/centro-estrategico">Centro estratégico</Link>
          </p>
        </section>

        <section className="cc-zone cc-zone-publish panel compact-panel">
          <h2 className="section-title">Publicación y vista empresa</h2>
          <p className="muted small">
            Lo que analiza EIAAX es privado hasta que usted lo prepara y publica para la empresa.
          </p>
          <div className="cc-publish-actions">
            <Link className="btn secondary" to="/demo">Demo comercial</Link>
            <Link className="btn secondary" to="/mi-espacio">Vista empresa</Link>
            <Link className="btn secondary" to="/evaluaciones">Evaluaciones / Cabina</Link>
            <Link className="btn secondary" to="/demo/presentacion/demo">Presentación ejecutiva</Link>
          </div>
        </section>
      </div>
    </div>
  );
}
