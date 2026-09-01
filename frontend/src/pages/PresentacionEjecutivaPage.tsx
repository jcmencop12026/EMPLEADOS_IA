import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchDemoPresentacion, type DemoPresentacion } from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { DemoBanner } from "../components/DemoBanner";
import { AUDIENCIAS, HELP_DEMO_COMERCIAL, type AudienciaId } from "../lib/demoComercialHelp";

export function PresentacionEjecutivaPage() {
  const { expedienteId } = useParams<{ expedienteId: string }>();
  const [audiencia, setAudiencia] = useState<AudienciaId>("GERENCIA");
  const [data, setData] = useState<DemoPresentacion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!expedienteId) return;
    setLoading(true);
    fetchDemoPresentacion(expedienteId, audiencia)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [expedienteId, audiencia]);

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
          <div className="presentacion-sections">
            {data.secciones.map((sec) => (
              <section key={sec.titulo} className="panel presentacion-section">
                <h2>{sec.titulo}</h2>
                <ul>
                  {(sec.contenido ?? []).map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </section>
            ))}
          </div>

          {data.informe_resumen && (
            <section className="panel muted-box">
              <h3>Informe vinculado</h3>
              <p>{data.informe_resumen.titulo} (v{data.informe_resumen.version})</p>
              <Link to={`/resultados?expediente_id=${expedienteId}`} className="btn">
                Ver resultados e informe
              </Link>
            </section>
          )}

          <p className="muted small presentacion-ip-note">
            Presentación sin prompts, reglas internas, algoritmos ni configuraciones reproducibles.
          </p>
        </>
      )}
    </div>
  );
}
