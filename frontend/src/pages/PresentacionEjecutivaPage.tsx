import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  downloadPresentacionPdf,
  fetchDemoPresentacion,
  type PresentacionPayload,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { DemoBanner } from "../components/DemoBanner";
import { PresentacionView } from "../components/PresentacionView";
import { AUDIENCIAS, HELP_DEMO_COMERCIAL, type AudienciaId } from "../lib/demoComercialHelp";

export function PresentacionEjecutivaPage() {
  const { expedienteId } = useParams<{ expedienteId: string }>();
  const [audiencia, setAudiencia] = useState<AudienciaId>("GERENCIA");
  const [data, setData] = useState<PresentacionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    if (!expedienteId) return;
    setLoading(true);
    fetchDemoPresentacion(expedienteId, audiencia)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [expedienteId, audiencia]);

  async function onPdf() {
    if (!expedienteId) return;
    setPdfLoading(true);
    try {
      await downloadPresentacionPdf(expedienteId, audiencia, true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el PDF");
    } finally {
      setPdfLoading(false);
    }
  }

  if (!expedienteId) return <p className="error">Expediente no especificado</p>;

  return (
    <div className="ops-page presentacion-ejecutiva-page">
      <DemoBanner />
      <p><Link to="/demo">← Volver a demo comercial</Link></p>

      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Presentación ejecutiva</h1>
            <p className="muted">
              {data?.empresa ?? "Empresa ficticia"} · {data?.expediente_codigo}
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
        <>
          <PresentacionView
            data={data}
            expedienteId={expedienteId}
            esDemo
            onDownloadPdf={onPdf}
            pdfLoading={pdfLoading}
          />
          <p>
            <Link
              to={`/evaluaciones?nuevo=1&area=${encodeURIComponent("Facturación y glosas")}`}
              className="btn primary"
            >
              Quiero evaluar mi empresa
            </Link>
          </p>
        </>
      )}
    </div>
  );
}
