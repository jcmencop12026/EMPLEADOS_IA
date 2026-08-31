import { label, CONFIANZA, ESTADO_EXPEDIENTE, NIVEL_EVALUACION, TIPO_CONTENIDO } from "../../lib/evaluacionLabels";

type Hallazgo = {
  titulo: string;
  descripcion?: string | null;
  tipo_contenido?: string;
  confianza?: string;
  visible_entidad?: boolean;
};

type Props = {
  data: Record<string, unknown>;
};

export function VistaEntidadView({ data }: Props) {
  const hallazgos = (data.hallazgos as Hallazgo[]) ?? [];
  const informacion = (data.informacion as { etiqueta: string; estado: string }[]) ?? [];
  const impacto = data.impacto as Record<string, unknown> | undefined;
  const oportunidades = (data.oportunidades as { titulo: string; codigo: string; estado: string }[]) ?? [];

  return (
    <div className="vista-entidad-view">
      <div className="vista-entidad-banner">
        <span>Vista Entidad</span>
        <p className="muted small">Previsualización de lo que la entidad vería según visibilidad y permisos.</p>
      </div>

      <section className="vista-entidad-section">
        <h3>{String(data.titulo ?? "Evaluación")}</h3>
        <dl className="detail-dl compact">
          <dt>Entidad</dt><dd>{String(data.entidad_nombre ?? "—")}</dd>
          <dt>Estado</dt><dd>{label(ESTADO_EXPEDIENTE, String(data.estado ?? ""))}</dd>
          <dt>Nivel</dt><dd>{label(NIVEL_EVALUACION, String(data.nivel ?? ""))}</dd>
          <dt>Objetivo</dt><dd>{String(data.objetivo ?? "—")}</dd>
          <dt>Confianza</dt><dd>{label(CONFIANZA, String(data.confianza_global ?? ""))}</dd>
        </dl>
      </section>

      {informacion.length > 0 && (
        <section className="vista-entidad-section">
          <h4>Información compartida</h4>
          <ul className="compact-list">
            {informacion.map((i) => (
              <li key={i.etiqueta}>{i.etiqueta}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="vista-entidad-section">
        <h4>Hallazgos visibles ({hallazgos.length})</h4>
        {hallazgos.length === 0 && <p className="muted">Ningún hallazgo marcado como visible para la entidad.</p>}
        {hallazgos.map((h) => (
          <article key={h.titulo} className="hallazgo-card compact">
            <strong>{h.titulo}</strong>
            {h.tipo_contenido && <span className="badge">{label(TIPO_CONTENIDO, h.tipo_contenido)}</span>}
            {h.confianza && <span className="badge confianza">{label(CONFIANZA, h.confianza)}</span>}
            {h.descripcion && <p>{h.descripcion}</p>}
          </article>
        ))}
      </section>

      {impacto && Array.isArray(impacto.indicadores) && (impacto.indicadores as unknown[]).length > 0 && (
        <section className="vista-entidad-section">
          <h4>Indicadores de impacto</h4>
          <table className="data-table compact-table">
            <thead><tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th></tr></thead>
            <tbody>
              {(impacto.indicadores as Record<string, unknown>[]).map((ind) => (
                <tr key={String(ind.nombre)}>
                  <td>{String(ind.nombre)}</td>
                  <td>{String(ind.antes ?? "—")}</td>
                  <td>{ind.proyectado ? <span className="tag-proyectado">{String(ind.proyectado)}</span> : "—"}</td>
                  <td>{String(ind.real ?? "—")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {oportunidades.length > 0 && (
        <section className="vista-entidad-section">
          <h4>Oportunidades visibles</h4>
          <ul className="compact-list">
            {oportunidades.map((o) => (
              <li key={o.codigo}>{o.codigo} — {o.titulo}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
