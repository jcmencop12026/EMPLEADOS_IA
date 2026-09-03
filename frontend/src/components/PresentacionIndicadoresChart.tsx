import type { PresentacionIndicador } from "../api";

type Props = {
  series: PresentacionIndicador[];
  esDemo?: boolean;
  nota?: string;
};

function maxVal(series: PresentacionIndicador[]): number {
  let m = 1;
  for (const s of series) {
    for (const v of [s.antes, s.proyectado, s.real]) {
      if (typeof v === "number" && v > m) m = v;
    }
  }
  return m;
}

function barHeight(value: number | null | undefined, max: number): string {
  if (value == null || max <= 0) return "0%";
  return `${Math.max(4, Math.round((value / max) * 100))}%`;
}

export function PresentacionIndicadoresChart({ series, esDemo, nota }: Props) {
  if (!series.length) {
    return <p className="muted">Sin indicadores publicables para graficar.</p>;
  }

  const max = maxVal(series);

  return (
    <section className="panel presentacion-chart-panel" aria-label="Gráficos ANTES PROYECTADO REAL">
      <div className="presentacion-chart-header">
        <h3>Indicadores — comparación</h3>
        {esDemo && <span className="badge demo-badge">SIMULADO</span>}
      </div>
      {nota && <p className="muted small">{nota}</p>}

      <div className="presentacion-charts">
        {series.map((s) => (
          <div key={s.nombre} className="presentacion-chart-row" title={s.nombre}>
            <div className="presentacion-chart-label" title={s.nombre}>
              {s.nombre}
              {s.periodo ? <span className="muted small"> · {s.periodo}</span> : null}
            </div>
            <div className="presentacion-chart-bars" role="img" aria-label={`${s.nombre}: antes, proyectado y real`}>
              <div className="chart-bar-group">
                <div
                  className="chart-bar chart-bar-antes"
                  style={{ height: barHeight(s.antes, max) }}
                  title={`ANTES: ${s.antes ?? "—"} ${s.unidad ?? ""}`}
                />
                <span className="chart-bar-tag">ANTES</span>
              </div>
              <div className="chart-bar-group">
                <div
                  className="chart-bar chart-bar-proy"
                  style={{ height: barHeight(s.proyectado, max) }}
                  title={`PROYECTADO: ${s.proyectado ?? "—"} ${s.unidad ?? ""} (no es realizado)`}
                />
                <span className="chart-bar-tag tag-proyectado">PROY.</span>
              </div>
              <div className="chart-bar-group">
                <div
                  className="chart-bar chart-bar-real"
                  style={{ height: barHeight(s.real, max) }}
                  title={`REAL: ${s.real ?? "pendiente"} ${s.unidad ?? ""}`}
                />
                <span className="chart-bar-tag">REAL</span>
              </div>
            </div>
            <div className="presentacion-chart-values muted small">
              {s.antes ?? "—"} / {s.proyectado ?? "—"} / {s.real ?? "—"} {s.unidad}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
