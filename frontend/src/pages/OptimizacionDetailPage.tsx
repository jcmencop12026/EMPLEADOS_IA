import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { OptimizacionRecomendacion } from "../api";
import { aprobarRecomendacionOptimizacion, fetchOptimizacionRecomendacion } from "../api";

export function OptimizacionDetailPage() {
  const { recId } = useParams<{ recId: string }>();
  const [detail, setDetail] = useState<OptimizacionRecomendacion | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!recId) return;
    fetchOptimizacionRecomendacion(recId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, [recId]);

  async function onAprobar() {
    if (!recId) return;
    const justificacion = window.prompt("Justificación de aprobación:");
    if (!justificacion) return;
    try {
      await aprobarRecomendacionOptimizacion(recId, justificacion);
      const updated = await fetchOptimizacionRecomendacion(recId);
      setDetail(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al aprobar");
    }
  }

  if (!detail) {
    return <div className="page"><p className="muted">Cargando…</p></div>;
  }

  const seleccionados = (detail.items ?? []).filter((i) => i.seleccionado);
  const excluidos = (detail.items ?? []).filter((i) => !i.seleccionado);

  return (
    <div className="page">
      <header className="page-header">
        <p className="muted"><Link to="/optimizacion">← Optimización</Link></p>
        <h1>{detail.codigo}</h1>
        <p className="muted">{detail.objetivo} — {detail.estado}</p>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {!detail.factible && (
        <div className="alert alert-error">
          Sin solución factible: {(detail.conflictos as string[])?.join("; ") ?? "Restricciones en conflicto"}
        </div>
      )}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Resumen del portafolio</h2>
        <p>Valor: {detail.valor_esperado_total?.toLocaleString("es-CO")}</p>
        <p>Costo: {detail.costo_esperado_total?.toLocaleString("es-CO")}</p>
        <p>Impacto: {detail.impacto_esperado_total?.toLocaleString("es-CO")}</p>
        <p>ROI: {detail.roi_esperado != null ? detail.roi_esperado.toFixed(2) : "—"}</p>
        {detail.estado === "PROPUESTA" && (
          <button type="button" className="btn btn-primary" onClick={onAprobar}>
            Aprobar recomendación
          </button>
        )}
      </section>

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Selección recomendada (orden)</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Orden</th>
              <th>Oportunidad</th>
              <th>Puntuación</th>
              <th>Factores</th>
            </tr>
          </thead>
          <tbody>
            {seleccionados.map((i) => (
              <tr key={i.opportunity_id}>
                <td>{i.orden}</td>
                <td>
                  <Link to={`/oportunidades/${i.opportunity_id}`}>{i.opportunity_id.slice(0, 8)}…</Link>
                </td>
                <td>{i.puntuacion_total}</td>
                <td>
                  <pre style={{ fontSize: "0.75rem", margin: 0 }}>
                    {JSON.stringify(i.factores?.contribuciones ?? i.factores, null, 0)}
                  </pre>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Excluidas</h2>
        {excluidos.length === 0 ? (
          <p className="muted">Ninguna</p>
        ) : (
          <ul>
            {excluidos.map((i) => (
              <li key={i.opportunity_id}>
                {i.opportunity_id.slice(0, 8)}… — {i.exclusion_razon} (puntuación: {i.puntuacion_total})
              </li>
            ))}
          </ul>
        )}
      </section>

      {detail.explicacion && (
        <section className="card">
          <h2>Explicación</h2>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem" }}>
            {JSON.stringify(detail.explicacion, null, 2)}
          </pre>
        </section>
      )}
    </div>
  );
}
