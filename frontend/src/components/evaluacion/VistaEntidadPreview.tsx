import {
  labelConfianza,
  labelEstadoEvaluacion,
  labelNivelEvaluacion,
  labelTipoContenido,
} from "../../lib/evaluacionLabels";

type Hallazgo = {
  titulo?: string;
  descripcion?: string;
  tipo_contenido?: string;
  confianza?: string;
  visible_entidad?: boolean;
};

type InfoItem = {
  etiqueta?: string;
  estado?: string;
};

type ImpactoIndicador = {
  hallazgo?: string;
  antes?: unknown;
  proyectado?: unknown;
  real?: unknown;
  confianza?: unknown;
};

type VistaEntidadData = {
  codigo?: string;
  titulo?: string;
  entidad_nombre?: string;
  estado?: string;
  nivel?: string;
  objetivo?: string;
  area_proceso?: string;
  confianza_global?: string;
  porcentaje_informacion?: number;
  hallazgos?: Hallazgo[];
  informacion?: InfoItem[];
  impacto?: { indicadores?: ImpactoIndicador[]; nota?: string };
  oportunidades?: Array<{ titulo?: string; codigo?: string }>;
};

/** Vista Entidad legible — representa exactamente lo que verá la empresa. */
export function VistaEntidadPreview({ data }: { data: Record<string, unknown> }) {
  const v = data as VistaEntidadData;

  return (
    <div className="vista-entidad-readable">
      <header className="vista-entidad-header">
        <h3>{v.titulo ?? "Expediente"}</h3>
        <p className="muted">
          {v.codigo} · {v.entidad_nombre} · {labelEstadoEvaluacion(String(v.estado ?? ""))} ·{" "}
          {labelNivelEvaluacion(String(v.nivel ?? ""))}
        </p>
      </header>

      <dl className="detail-dl">
        {v.objetivo && (
          <>
            <dt>Objetivo</dt>
            <dd>{v.objetivo}</dd>
          </>
        )}
        {v.area_proceso && (
          <>
            <dt>Área / proceso</dt>
            <dd>{v.area_proceso}</dd>
          </>
        )}
        <dt>Información completada</dt>
        <dd>{v.porcentaje_informacion != null ? `${v.porcentaje_informacion}%` : "—"}</dd>
        <dt>Confianza global</dt>
        <dd>{labelConfianza(v.confianza_global)}</dd>
      </dl>

      <section className="vista-entidad-section">
        <h4>Hallazgos visibles para la entidad</h4>
        {(v.hallazgos ?? []).length === 0 ? (
          <p className="muted">No hay hallazgos publicados para la entidad.</p>
        ) : (
          <ul className="vista-entidad-list">
            {(v.hallazgos ?? []).map((h, i) => (
              <li key={i} className="hallazgo-card compact">
                <strong>{h.titulo}</strong>
                {h.descripcion && <p>{h.descripcion}</p>}
                <div className="hallazgo-meta">
                  <span className="badge">{labelTipoContenido(String(h.tipo_contenido ?? ""))}</span>
                  <span className="badge confianza">{labelConfianza(String(h.confianza ?? ""))}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {(v.informacion ?? []).length > 0 && (
        <section className="vista-entidad-section">
          <h4>Información recibida (resumen)</h4>
          <ul className="vista-entidad-list compact">
            {(v.informacion ?? []).map((item, i) => (
              <li key={i}>
                {item.etiqueta} — <span className="badge estado-recibido">Recibido</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {v.impacto?.indicadores && v.impacto.indicadores.length > 0 && (
        <section className="vista-entidad-section">
          <h4>Impacto (vista entidad)</h4>
          {v.impacto.nota && <p className="muted small">{v.impacto.nota}</p>}
          <div className="table-wrap">
            <table className="data-table compact-table">
              <thead>
                <tr>
                  <th>Indicador</th>
                  <th>Antes</th>
                  <th>Proyectado</th>
                  <th>Real</th>
                </tr>
              </thead>
              <tbody>
                {v.impacto.indicadores.map((ind, i) => (
                  <tr key={i}>
                    <td>{String(ind.hallazgo ?? "—")}</td>
                    <td>{ind.antes != null ? String(ind.antes) : "—"}</td>
                    <td>{ind.proyectado != null ? <span className="tag-proyectado">{String(ind.proyectado)}</span> : "—"}</td>
                    <td>{ind.real != null ? String(ind.real) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {(v.oportunidades ?? []).length > 0 && (
        <section className="vista-entidad-section">
          <h4>Oportunidades compartidas</h4>
          <ul className="vista-entidad-list compact">
            {(v.oportunidades ?? []).map((o, i) => (
              <li key={i}>{o.titulo ?? o.codigo ?? "Oportunidad"}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
