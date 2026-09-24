import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { DiagnosticDetail } from "../api";
import { fetchDiagnostic, fetchDiagnosticTrace } from "../api";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";

export function DiagnosticoDetailPage() {
  const { diagnosticId } = useParams<{ diagnosticId: string }>();
  const [detail, setDetail] = useState<DiagnosticDetail | null>(null);
  const [trace, setTrace] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  usePageAssistantContext(
    { diagnostico_id: diagnosticId, codigo: detail?.codigo, resumen: detail?.resumen },
    Boolean(diagnosticId),
  );

  useEffect(() => {
    if (!diagnosticId) return;
    Promise.all([fetchDiagnostic(diagnosticId), fetchDiagnosticTrace(diagnosticId)])
      .then(([d, t]) => {
        setDetail(d);
        setTrace(t);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar diagnóstico"));
  }, [diagnosticId]);

  if (error) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
        <Link to="/diagnosticos">Volver</Link>
      </div>
    );
  }

  if (!detail) {
    return <div className="page muted">Cargando diagnóstico…</div>;
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>{detail.codigo}</h1>
          <p className="muted">{detail.resumen}</p>
        </div>
        <Link to="/diagnosticos">← Volver</Link>
      </header>

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Explicación</h2>
        <dl className="detail-grid">
          <dt>¿Qué está pasando?</dt>
          <dd>{detail.explicacion?.que_esta_pasando ?? "—"}</dd>
          <dt>¿Dónde?</dt>
          <dd>{detail.explicacion?.donde ?? "—"}</dd>
          <dt>¿Desde cuándo?</dt>
          <dd>{detail.explicacion?.desde_cuando ?? "—"}</dd>
          <dt>¿Qué debería hacerse?</dt>
          <dd>{detail.explicacion?.que_deberia_hacerse ?? "—"}</dd>
        </dl>
        {detail.explicacion?.nota_evidencia && (
          <p className="muted" style={{ marginTop: "0.75rem" }}>{detail.explicacion.nota_evidencia}</p>
        )}
      </section>

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Hallazgos ({detail.hallazgos?.length ?? 0})</h2>
        {(detail.hallazgos ?? []).length === 0 ? (
          <p className="muted">Sin hallazgos.</p>
        ) : (
          <ul>
            {(detail.hallazgos ?? []).map((h) => (
              <li key={h.id} style={{ marginBottom: "0.75rem" }}>
                <strong>[{h.tipo_contenido}] {h.codigo}</strong> — {h.que_ocurre}
                <br />
                <span className="muted">
                  Dominio: {h.dominio} · Severidad: {h.severidad} · Confianza: {(h.confianza * 100).toFixed(0)}%
                </span>
                {(h.signal_ids ?? []).map((sid) => (
                  <span key={sid}>
                    {" "}
                    · <Link to={`/senales/${sid}`}>Señal</Link>
                  </span>
                ))}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Causas probables</h2>
        {(detail.causas ?? []).length === 0 ? (
          <p className="muted">Sin causas inferidas.</p>
        ) : (
          <ul>
            {(detail.causas ?? []).map((c) => (
              <li key={c.id}>
                <strong>[{c.tipo}]</strong> {c.descripcion}
                {c.justificacion && <p className="muted">{c.justificacion}</p>}
              </li>
            ))}
          </ul>
        )}
      </section>

      {detail.correlaciones && detail.correlaciones.length > 0 && (
        <section className="card" style={{ marginBottom: "1rem" }}>
          <h2>Correlaciones</h2>
          <ul>
            {detail.correlaciones.map((c) => (
              <li key={c.id}>
                <strong>{c.titulo}</strong>
                <p className="muted">{c.nota_causalidad}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Ítems priorizados</h2>
        {(detail.items_estructurados ?? []).map((item, i) => (
          <div key={i} style={{ borderTop: i ? "1px solid var(--border)" : undefined, paddingTop: "0.75rem", marginTop: "0.75rem" }}>
            <p>
              <strong>Prioridad {item.prioridad?.toFixed(2)}</strong> — {item.hallazgo?.que_ocurre}
            </p>
            {item.accion_recomendada?.accion && <p>Acción: {item.accion_recomendada.accion}</p>}
            {item.opportunity_id && (
              <Link to={`/oportunidades/${item.opportunity_id}`}>Ver oportunidad vinculada</Link>
            )}
          </div>
        ))}
      </section>

      {trace && (
        <section className="card">
          <h2>Trazabilidad</h2>
          <p className="muted">{String(trace.cadena ?? "")}</p>
        </section>
      )}
    </div>
  );
}
