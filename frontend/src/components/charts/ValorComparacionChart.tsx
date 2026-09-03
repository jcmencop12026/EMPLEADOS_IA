type Punto = {
  label: string;
  valor: number | null;
  proyectado?: boolean;
};

type Props = {
  title: string;
  puntos: Punto[];
  unidad?: string;
};

export function ValorComparacionChart({ title, puntos, unidad }: Props) {
  const numeric = puntos.filter((p) => p.valor != null).map((p) => Math.abs(p.valor as number));
  const max = Math.max(...numeric, 1);

  if (puntos.length === 0) {
    return (
      <div className="valor-chart valor-chart--empty">
        <h3 className="cc-subtitle">{title}</h3>
        <p className="muted">Sin datos para visualizar.</p>
      </div>
    );
  }

  return (
    <div className="valor-chart" role="img" aria-label={title}>
      <h3 className="cc-subtitle">{title}{unidad ? ` (${unidad})` : ""}</h3>
      <div className="impacto-bars">
        {puntos.map((p) => (
          <div key={p.label} className="impacto-bar-row">
            <span className="impacto-bar-label">{p.label}</span>
            <div className="impacto-bar-track">
              <div
                className={`impacto-bar-fill ${p.proyectado ? "proyectado" : ""}`}
                style={{
                  width: p.valor != null ? `${Math.min(100, (Math.abs(p.valor) / max) * 100)}%` : "6%",
                }}
              />
            </div>
            <span className="impacto-bar-value">
              {p.valor != null ? p.valor.toLocaleString("es-CO") : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
