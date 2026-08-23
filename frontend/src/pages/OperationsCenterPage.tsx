import { useState } from "react";
import { Link } from "react-router-dom";
import type { PlanResult } from "../api";
import { submitWorkRequest } from "../api";

const SAMPLE_RIPS = {
  usuarios: [
    {
      tipoDocumentoIdentificacion: "CC",
      numDocumentoIdentificacion: "1234567890",
      codSexo: "M",
      fechaNacimiento: "1980-01-15",
    },
  ],
  consultas: [
    {
      codConsulta: "890201",
      numDocumentoIdentificacion: "9999999999",
    },
  ],
  procedimientos: [],
  medicamentos: [],
  otrosServicios: [],
};

export function OperationsCenterPage() {
  const [query, setQuery] = useState(
    "Analiza estos documentos/RIPS y dime qué problemas existen.",
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [mode, setMode] = useState<"rips" | "docint">("rips");

  async function runRequest(context?: Record<string, unknown>) {
    setLoading(true);
    setError(null);
    try {
      const res = await submitWorkRequest(query, context ?? { tool: mode, rips: SAMPLE_RIPS });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al ejecutar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Centro de Operaciones</h1>
        <p className="muted">Orquestador E2E · Workspace Salud</p>
      </header>

      <section className="panel ops-main">
        <label className="ops-label" htmlFor="ops-query">
          ¿Qué necesita hacer hoy?
        </label>
        <textarea
          id="ops-query"
          className="ops-input"
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="ops-actions">
          <button type="button" className="btn primary" disabled={loading} onClick={() => runRequest()}>
            {loading ? "Ejecutando…" : "Ejecutar análisis"}
          </button>
          <Link className="btn" to="/empleados/nuevo" title="Crear empleado IA">
            Crear empleado
          </Link>
          <button
            type="button"
            className={`btn ${mode === "rips" ? "active" : ""}`}
            disabled={loading}
            onClick={() => {
              setMode("rips");
              runRequest({ tool: "rips", rips: SAMPLE_RIPS });
            }}
          >
            RIPS
          </button>
          <button
            type="button"
            className={`btn ${mode === "docint" ? "active" : ""}`}
            disabled={loading}
            onClick={() => {
              setMode("docint");
              runRequest({
                tool: "docint",
                documents: [
                  {
                    id: "d1",
                    tipo_documento: "CC",
                    numero_documento: "123",
                    fecha: "2026-01-01",
                    contenido: "Corto",
                  },
                ],
              });
            }}
          >
            DOCINT
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </section>

      {result && (
        <section className="panel result-panel">
          <div className="result-header">
            <h2>Resultado</h2>
            <span className={`badge status-${result.status}`}>{result.status}</span>
          </div>
          <p>{result.summary || result.objective}</p>
          {result.confidence != null && (
            <p className="muted">Confianza: {(result.confidence * 100).toFixed(0)}%</p>
          )}
          {result.approval_status === "PENDING" && (
            <p className="warn">Esperando aprobación humana — ver Ejecuciones o Aprobaciones.</p>
          )}
          {result.result?.findings && result.result.findings.length > 0 && (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Severidad</th>
                  <th>Código</th>
                  <th>Hallazgo</th>
                </tr>
              </thead>
              <tbody>
                {result.result.findings.map((f, i) => (
                  <tr key={i}>
                    <td>{f.severity}</td>
                    <td className="mono">{f.code}</td>
                    <td>{f.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <Link className="btn link" to={`/ejecuciones/${result.plan_id}`}>
            Ver trazabilidad completa
          </Link>
        </section>
      )}
    </div>
  );
}
