import type { PresentacionIndicador } from "../api";

type Props = { series: PresentacionIndicador[]; esDemo?: boolean; nota?: string };

function fmt(v: number | null | undefined, unidad?: string | null) {
  if (v == null) return "Pendiente";
  return `${v.toLocaleString("es-CO", { maximumFractionDigits: 1 })}${unidad ? ` ${unidad}` : ""}`;
}
function ratio(v: number | null | undefined, max: number) {
  if (v == null || max <= 0) return 0;
  return Math.max(3, Math.min(100, (Math.abs(v) / max) * 100));
}
function variacion(a: number | null | undefined, b: number | null | undefined) {
  if (a == null || b == null || a === 0) return null;
  return ((b - a) / Math.abs(a)) * 100;
}

export function PresentacionIndicadoresChart({ series, esDemo, nota }: Props) {
  if (!series.length) return <p className="muted">Sin indicadores publicables para graficar.</p>;
  return (
    <section className="panel presentacion-executive-chart" aria-label="Comparación ejecutiva situación actual, meta conservadora y resultado real">
      <div className="presentacion-chart-header">
        <div><span className="presentacion-chart-kicker">IMPACTO MEDIBLE</span><h3>Situación actual → meta conservadora → resultado real</h3></div>
        {esDemo && <span className="badge demo-badge">SIMULACIÓN</span>}
      </div>
      {nota && <p className="muted small">{nota}</p>}
      <div className="presentacion-impact-grid">
        {series.slice(0, 6).map((s) => {
          const values = [s.antes, s.proyectado, s.real].filter((v): v is number => typeof v === "number");
          const max = Math.max(1, ...values.map(Math.abs));
          const delta = variacion(s.antes, s.proyectado);
          return <article key={s.nombre} className="presentacion-impact-card">
            <div className="presentacion-impact-card__head"><strong>{s.nombre}</strong>{delta != null && <span className="presentacion-impact-delta">{delta > 0 ? "+" : ""}{delta.toFixed(1)}%</span>}</div>
            {s.periodo && <span className="muted small">{s.periodo}</span>}
            <div className="presentacion-impact-bars">
              <div className="impact-line"><span>Actual</span><div className="impact-track"><i className="impact-fill impact-fill--actual" style={{width:`${ratio(s.antes,max)}%`}} /></div><b>{fmt(s.antes,s.unidad)}</b></div>
              <div className="impact-line"><span>Meta conservadora</span><div className="impact-track"><i className="impact-fill impact-fill--meta" style={{width:`${ratio(s.proyectado,max)}%`}} /></div><b>{fmt(s.proyectado,s.unidad)}</b></div>
              <div className="impact-line"><span>Real</span><div className="impact-track"><i className="impact-fill impact-fill--real" style={{width:`${ratio(s.real,max)}%`}} /></div><b>{fmt(s.real,s.unidad)}</b></div>
            </div>
          </article>;
        })}
      </div>
      <p className="presentacion-chart-footnote">La meta es una proyección conservadora condicionada a los supuestos y compromisos acordados; el resultado real se incorpora durante la operación.</p>
    </section>
  );
}
