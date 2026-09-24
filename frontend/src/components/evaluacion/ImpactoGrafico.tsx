type Punto = { serie: string; valor: string; numerico: number | null; es_proyeccion: boolean };

type Props = {
  nombre: string;
  unidad?: string | null;
  grafico?: { puntos: Punto[]; unidad?: string | null } | null;
  antes?: string | null;
  proyectado?: string | null;
  real?: string | null;
};

const SERIE_LABELS: Record<string, string> = {
  antes: "Antes",
  proyectado: "Proyectado",
  real: "Real",
};

export function ImpactoGrafico({ nombre, unidad, grafico, antes, proyectado, real }: Props) {
  const puntos = grafico?.puntos ?? [];
  const maxNum = Math.max(
    ...puntos.map((p) => (p.numerico != null ? Math.abs(p.numerico) : 0)),
    1,
  );

  if (puntos.length < 2) {
    return (
      <tr>
        <td>{nombre}</td>
        <td>{antes ?? "—"}</td>
        <td>{proyectado ? <span className="tag-proyectado">{proyectado}</span> : "—"}</td>
        <td>{real ?? "—"}</td>
        <td className="muted">—</td>
      </tr>
    );
  }

  return (
    <tr>
      <td>{nombre}{unidad ? ` (${unidad})` : ""}</td>
      <td>{antes ?? "—"}</td>
      <td>{proyectado ? <span className="tag-proyectado">{proyectado}</span> : "—"}</td>
      <td>{real ?? "—"}</td>
      <td>
        <div className="impacto-bars" role="img" aria-label={`Gráfico ${nombre}`}>
          {puntos.map((p) => (
            <div key={p.serie} className="impacto-bar-row">
              <span className="impacto-bar-label">{SERIE_LABELS[p.serie] ?? p.serie}</span>
              <div className="impacto-bar-track">
                <div
                  className={`impacto-bar-fill ${p.es_proyeccion ? "proyectado" : ""}`}
                  style={{ width: p.numerico != null ? `${Math.min(100, (Math.abs(p.numerico) / maxNum) * 100)}%` : "8%" }}
                  title={p.valor}
                />
              </div>
              <span className="impacto-bar-value">{p.valor}</span>
            </div>
          ))}
        </div>
      </td>
    </tr>
  );
}
