import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { ExternalSignalItem, ExternalSourceItem } from "../api";
import { fetchExternalSignals, fetchExternalSources } from "../api";

const CLASS_LABELS: Record<string, string> = {
  OPORTUNIDAD: "Oportunidad",
  RIESGO: "Riesgo",
  CAMBIO: "Cambio",
  TENDENCIA: "Tendencia",
  EVENTO: "Evento",
  "INFORMACIÓN": "Información",
};

const FRESHNESS_LABELS: Record<string, string> = {
  ACTUAL: "Actual",
  RECIENTE: "Reciente",
  DESACTUALIZADA: "Desactualizada",
  "SIN FECHA VERIFICABLE": "Sin fecha",
};

export function InteligenciaExternaPage() {
  const [sources, setSources] = useState<ExternalSourceItem[]>([]);
  const [signals, setSignals] = useState<ExternalSignalItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filtroClasificacion, setFiltroClasificacion] = useState("");

  useEffect(() => {
    Promise.all([
      fetchExternalSources(),
      fetchExternalSignals(filtroClasificacion ? { classification: filtroClasificacion } : undefined),
    ])
      .then(([src, sig]) => {
        setSources(src);
        setSignals(sig.items ?? []);
        setMessage(sig.message ?? null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"));
  }, [filtroClasificacion]);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Inteligencia externa</h1>
        <p className="muted">
          Fuentes, señales y hallazgos del entorno externo — mercado, competencia, regulación y demanda.
        </p>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Fuentes externas</h2>
        {sources.length === 0 ? (
          <p className="muted">Sin información externa disponible — registre fuentes para comenzar.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Tipo</th>
                <th>Canal</th>
                <th>Confiabilidad</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>{s.source_type}</td>
                  <td>{s.ingestion_channel}</td>
                  <td>{(s.confiabilidad * 100).toFixed(0)}%</td>
                  <td>{s.is_active ? "Activa" : "Inactiva"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <div className="toolbar" style={{ marginBottom: "1rem" }}>
          <h2>Señales externas</h2>
          <label>
            Clasificación{" "}
            <select value={filtroClasificacion} onChange={(e) => setFiltroClasificacion(e.target.value)}>
              <option value="">Todas</option>
              <option value="OPORTUNIDAD">Oportunidad</option>
              <option value="RIESGO">Riesgo</option>
              <option value="TENDENCIA">Tendencia</option>
              <option value="INFORMACIÓN">Información</option>
            </select>
          </label>
        </div>
        {signals.length === 0 ? (
          <p className="muted">{message ?? "Sin señales externas registradas."}</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Fuente</th>
                <th>Clasificación</th>
                <th>Relevancia</th>
                <th>Frescura</th>
                <th>Hecho observado</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((row) => (
                <tr key={row.signal.id}>
                  <td>{row.signal.signal_at ? new Date(row.signal.signal_at).toLocaleDateString("es-CO") : "—"}</td>
                  <td>{row.source?.name ?? row.signal.origen}</td>
                  <td>{CLASS_LABELS[row.external.classification] ?? row.external.classification}</td>
                  <td>{row.external.relevance}</td>
                  <td>{FRESHNESS_LABELS[row.external.freshness_status] ?? row.external.freshness_status}</td>
                  <td>
                    <Link to={`/inteligencia-externa/senales/${row.signal.id}`}>
                      {(row.external.hecho_observado ?? row.signal.evidencia_resumen ?? "Ver detalle").slice(0, 60)}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
