import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { DiagnosticSummary } from "../api";
import { fetchDiagnostics, generateDiagnostic } from "../api";

export function DiagnosticosPage() {
  const [items, setItems] = useState<DiagnosticSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  function load() {
    setLoading(true);
    fetchDiagnostics()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar diagnósticos"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  async function onGenerate() {
    setGenerating(true);
    setError(null);
    try {
      await generateDiagnostic({});
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el diagnóstico");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Diagnósticos transversales</h1>
          <p className="muted">
            Análisis multidominio: señales → indicadores → hallazgos → diagnóstico → oportunidades.
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={onGenerate} disabled={generating}>
          {generating ? "Generando…" : "Generar diagnóstico"}
        </button>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        {loading ? (
          <p className="muted">Cargando…</p>
        ) : items.length === 0 ? (
          <p className="muted">No hay diagnósticos generados. Ingrese señales y pulse «Generar diagnóstico».</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Estado</th>
                <th>Periodo</th>
                <th>Dominios</th>
                <th>Prioridad</th>
                <th>Resumen</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {items.map((d) => (
                <tr key={d.id}>
                  <td>
                    <Link to={`/diagnosticos/${d.id}`}>{d.codigo}</Link>
                  </td>
                  <td>{d.estado}</td>
                  <td>
                    {d.periodo_inicio ? new Date(d.periodo_inicio).toLocaleDateString("es-CO") : "—"}
                    {" — "}
                    {d.periodo_fin ? new Date(d.periodo_fin).toLocaleDateString("es-CO") : "—"}
                  </td>
                  <td>{(d.dominios ?? []).join(", ") || "—"}</td>
                  <td>{d.prioridad_score?.toFixed(2) ?? "—"}</td>
                  <td>{d.resumen ?? "—"}</td>
                  <td>{d.created_at ? new Date(d.created_at).toLocaleString("es-CO") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
