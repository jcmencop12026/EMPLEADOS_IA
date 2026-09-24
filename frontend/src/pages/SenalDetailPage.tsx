import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchSignalTrace } from "../api";

export function SenalDetailPage() {
  const { signalId } = useParams<{ signalId: string }>();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!signalId) return;
    fetchSignalTrace(signalId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar trazabilidad"));
  }, [signalId]);

  if (error) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
        <Link to="/senales">Volver a señales</Link>
      </div>
    );
  }

  if (!data) {
    return <div className="page muted">Cargando trazabilidad…</div>;
  }

  const signal = data.signal as Record<string, unknown>;
  const fuente = data.fuente as Record<string, unknown> | null;
  const trazabilidad = data.trazabilidad as { trazas?: Array<{ etapa: string; detalle?: unknown; fecha?: string }> };
  const opportunityId = data.opportunity_id as string | null;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Trazabilidad de señal</h1>
          <p className="muted">Cadena señal → análisis → oportunidad</p>
        </div>
        <Link to="/senales">← Volver</Link>
      </header>

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Señal</h2>
        <dl className="detail-grid">
          <dt>Referencia</dt>
          <dd>{String(signal.referencia ?? "—")}</dd>
          <dt>Tipo / dominio</dt>
          <dd>
            {String(signal.tipo)} / {String(signal.dominio)}
          </dd>
          <dt>Modo ingesta</dt>
          <dd>{String(signal.modo_ingesta)}</dd>
          <dt>Estado</dt>
          <dd>{String(signal.estado_procesamiento)}</dd>
          <dt>Evidencia</dt>
          <dd>{String(signal.evidencia_resumen ?? "—")}</dd>
        </dl>
      </section>

      {fuente && (
        <section className="card" style={{ marginBottom: "1rem" }}>
          <h2>Fuente</h2>
          <dl className="detail-grid">
            <dt>Código</dt>
            <dd>{String(fuente.code)}</dd>
            <dt>Nombre</dt>
            <dd>{String(fuente.name)}</dd>
            <dt>Tipo</dt>
            <dd>{String(fuente.tipo_fuente)}</dd>
          </dl>
        </section>
      )}

      {opportunityId && (
        <section className="card" style={{ marginBottom: "1rem" }}>
          <h2>Oportunidad originada</h2>
          <Link to={`/oportunidades/${opportunityId}`}>Ver oportunidad</Link>
        </section>
      )}

      <section className="card">
        <h2>Etapas de trazabilidad</h2>
        {(trazabilidad?.trazas ?? []).length === 0 ? (
          <p className="muted">Sin etapas registradas.</p>
        ) : (
          <ul>
            {(trazabilidad?.trazas ?? []).map((t, i) => (
              <li key={`${t.etapa}-${i}`}>
                <strong>{t.etapa}</strong>
                {t.fecha ? ` — ${new Date(t.fecha).toLocaleString("es-CO")}` : ""}
                {t.detalle ? (
                  <pre style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
                    {JSON.stringify(t.detalle, null, 2)}
                  </pre>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
