import type { PresentacionCompromiso } from "../api";

type Props = { items: PresentacionCompromiso[] };

export function PresentacionCompromisos({ items }: Props) {
  if (!items.length) return null;
  return (
    <section className="panel presentacion-commitments" aria-label="Compromisos para capturar el valor">
      <div className="presentacion-commitments__head">
        <div><span>DE LA OPORTUNIDAD AL RESULTADO</span><h2>Compromisos para capturar el valor</h2></div>
        <p>El resultado depende de acciones verificables de EIAAX y de la empresa.</p>
      </div>
      <div className="presentacion-commitments__grid">
        {items.map((item) => (
          <article key={`${item.oportunidad}-${item.kpi}`} className="presentacion-commitment-card">
            <div className="presentacion-commitment-card__top">
              <div><span>{item.estado}</span><h3>{item.oportunidad}</h3><small>{item.proceso}</small></div>
              <strong>{item.meta_conservadora}</strong>
            </div>
            <div className="presentacion-commitment-card__split">
              <div><b>EIAAX se compromete</b><p>{item.accion_eiaax}</p></div>
              <div><b>La empresa se compromete</b><p>{item.compromiso_empresa}</p></div>
            </div>
            <dl className="presentacion-commitment-card__facts">
              <div><dt>Responsable</dt><dd>{item.responsable}</dd></div>
              <div><dt>Cuándo</dt><dd>{item.cuando}</dd></div>
              <div><dt>Frecuencia</dt><dd>{item.frecuencia}</dd></div>
              <div><dt>KPI</dt><dd>{item.kpi}</dd></div>
              <div><dt>Línea base</dt><dd>{item.linea_base}</dd></div>
              <div><dt>Meta conservadora</dt><dd>{item.meta_conservadora}</dd></div>
              <div><dt>Adherencia mínima</dt><dd>{item.adherencia_minima}</dd></div>
              <div><dt>Evidencia</dt><dd>{item.evidencia}</dd></div>
            </dl>
            <p className="presentacion-commitment-card__condition"><strong>Condición de resultado:</strong> {item.condicion_resultado}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
