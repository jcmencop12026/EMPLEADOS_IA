import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchExternalSignalDetail } from "../api";

export function InteligenciaExternaDetailPage() {
  const { signalId } = useParams<{ signalId: string }>();
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!signalId) return;
    fetchExternalSignalDetail(signalId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, [signalId]);

  if (error) return <div className="page"><p className="error">{error}</p></div>;
  if (!detail) return <div className="page"><p className="muted">Cargando…</p></div>;

  const ext = detail.external as Record<string, unknown>;
  const source = detail.source as Record<string, unknown> | null;
  const oppId = detail.opportunity_id as string | null;

  return (
    <div className="page">
      <header className="page-header">
        <p><Link to="/inteligencia-externa">← Inteligencia externa</Link></p>
        <h1>Detalle de señal externa</h1>
      </header>

      <div className="panel">
        <dl className="detail-grid">
          <dt>Fuente</dt><dd>{(source?.name as string) ?? "—"} ({(source?.source_type as string) ?? ""})</dd>
          <dt>Clasificación</dt><dd>{ext.classification as string}</dd>
          <dt>Relevancia</dt><dd>{ext.relevance as string}</dd>
          <dt>Frescura</dt><dd>{ext.freshness_status as string}</dd>
          <dt>Confianza</dt><dd>{Number(ext.confidence_level).toFixed(2)}</dd>
          <dt className="highlight-verificado">Hecho observado</dt>
          <dd>{ext.hecho_observado as string ?? "—"}</dd>
          <dt>Interpretación</dt><dd>{(ext.interpretacion as string) ?? "—"}</dd>
          <dt>Hipótesis</dt><dd>{(ext.hipotesis as string) ?? "—"}</dd>
          <dt>Es riesgo</dt><dd>{ext.is_risk ? "Sí" : "No"}</dd>
          <dt>Validada</dt><dd>{ext.validated_at ? new Date(ext.validated_at as string).toLocaleString("es-CO") : "Pendiente"}</dd>
          <dt>Oportunidad</dt>
          <dd>
            {oppId ? <Link to={`/oportunidades/${oppId}`}>{oppId.slice(0, 8)}…</Link> : "Sin oportunidad vinculada"}
          </dd>
        </dl>

        {Array.isArray(ext.evidence) && ext.evidence.length > 0 && (
          <section style={{ marginTop: "1rem" }}>
            <h3>Evidencia</h3>
            <ul>
              {(ext.evidence as Array<Record<string, unknown>>).map((ev) => (
                <li key={ev.id as string}>
                  {ev.summary as string ?? "—"}
                  {ev.reference_url ? ` — ${ev.reference_url as string}` : ""}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}
