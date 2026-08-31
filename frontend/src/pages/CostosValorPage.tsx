import { useEffect, useState } from "react";
import type { FinOpsDashboard, FinOpsConsumption } from "../api";
import { fetchFinOpsConsumptions, fetchFinOpsDashboard } from "../api";

export function CostosValorPage() {
  const [summary, setSummary] = useState<FinOpsDashboard | null>(null);
  const [consumptions, setConsumptions] = useState<FinOpsConsumption[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchFinOpsDashboard(), fetchFinOpsConsumptions()])
      .then(([dash, rows]) => {
        setSummary(dash);
        setConsumptions(rows);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Costos y valor</h1>
        <p className="muted">Consumo, valor generado, retorno de inversión y presupuestos por empresa</p>
      </header>
      {error && <p className="error">{error}</p>}
      {summary && (
        <div className="panel metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Costo del período</span>
            <strong>{summary.total_cost_label}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Valor generado</span>
            <strong>{summary.total_value_label}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Ahorro estimado</span>
            <strong>{summary.estimated_savings ?? "—"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Beneficio neto</span>
            <strong>{summary.net_benefit ?? "—"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Retorno de inversión</span>
            <strong>{summary.roi_label}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Ejecuciones</span>
            <strong>{summary.execution_count}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Costo promedio por trabajo</span>
            <strong>{summary.avg_cost_per_work ?? "Costo no disponible"}</strong>
          </div>
        </div>
      )}
      <div className="panel table-wrap">
        <h2>Consumos recientes</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Categoría</th>
              <th>Proveedor</th>
              <th>Modelo</th>
              <th>Costo</th>
              <th>Moneda</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {consumptions.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">
                  Sin consumos registrados.
                </td>
              </tr>
            )}
            {consumptions.map((row) => (
              <tr key={row.id}>
                <td>{row.category || "—"}</td>
                <td>{row.provider || "—"}</td>
                <td>{row.model_name || "—"}</td>
                <td>{row.cost_label}</td>
                <td>{row.currency || "—"}</td>
                <td className="mono">{row.created_at?.slice(0, 19)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
