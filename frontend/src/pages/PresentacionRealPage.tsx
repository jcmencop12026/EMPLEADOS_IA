import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  downloadPresentacionPdf,
  fetchPresentacionReal,
  type PresentacionPayload,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { PresentacionView } from "../components/PresentacionView";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { AUDIENCIAS, HELP_DEMO_COMERCIAL, type AudienciaId } from "../lib/demoComercialHelp";

export function PresentacionRealPage() {
  const { expedienteId } = useParams<{ expedienteId: string }>();
  const [audiencia, setAudiencia] = useState<AudienciaId>("GERENCIA");
  const [data, setData] = useState<PresentacionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState(false);

  usePageAssistantContext(
    { expediente_id: expedienteId, audiencia, titulo: data?.titulo },
    Boolean(expedienteId),
  );

  useEffect(() => {
    if (!expedienteId) return;
    setLoading(true);
    fetchPresentacionReal(expedienteId, audiencia)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [expedienteId, audiencia]);

  async function onPdf() {
    if (!expedienteId) return;
    setPdfLoading(true);
    try {
      await downloadPresentacionPdf(expedienteId, audiencia, false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el PDF");
    } finally {
      setPdfLoading(false);
    }
  }

  if (!expedienteId) return <p className="error">Expediente no especificado</p>;

  return (
    <div className="ops-page presentacion-ejecutiva-page">
      <p>
        <Link to={`/evaluaciones/${expedienteId}`}>← Volver al expediente</Link>
      </p>

      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Presentación ejecutiva</h1>
            <p className="muted">
              {data?.empresa ?? "Organización"} · {data?.expediente_codigo ?? expedienteId}
            </p>
          </div>
          <ContextualHelp content={HELP_DEMO_COMERCIAL} />
        </div>
      </header>

      <nav className="tab-bar" aria-label="Audiencia">
        {AUDIENCIAS.map((a) => (
          <button
            key={a.id}
            type="button"
            className={audiencia === a.id ? "tab active" : "tab"}
            onClick={() => setAudiencia(a.id)}
          >
            {a.label}
          </button>
        ))}
      </nav>

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Cargando presentación…</p>}

      {data && !loading && (
        <PresentacionView
          data={data}
          expedienteId={expedienteId}
          esDemo={false}
          onDownloadPdf={onPdf}
          pdfLoading={pdfLoading}
          backLink={{ to: `/evaluaciones/${expedienteId}`, label: "← Expediente de evaluación" }}
        />
      )}
    </div>
  );
}
