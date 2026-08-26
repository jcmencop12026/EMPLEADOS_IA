import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { AutomationItem, AutomationRunItem } from "../api";
import { fetchAutomationRuns, fetchAutomations } from "../api";

export function AutomationRunsPage() {
  const { automationId } = useParams();
  const [automation, setAutomation] = useState<AutomationItem | null>(null);
  const [runs, setRuns] = useState<AutomationRunItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!automationId) return;
    Promise.all([fetchAutomations(), fetchAutomationRuns(automationId)])
      .then(([autos, rs]) => {
        setAutomation(autos.find((a) => a.id === automationId) || null);
        setRuns(rs);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, [automationId]);

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Monitor de ejecuciones</h1>
        <p className="muted">{automation?.name || automationId}</p>
      </header>
      <div className="ops-actions">
        <Link className="btn" to="/automatizaciones">
          ← Volver
        </Link>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="panel table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Programada</th>
              <th>Inicio</th>
              <th>Fin</th>
              <th>Estado</th>
              <th>Intento</th>
              <th>WorkPlan</th>
              <th>Costo</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 && (
              <tr>
                <td colSpan={8} className="muted">
                  Sin ejecuciones.
                </td>
              </tr>
            )}
            {runs.map((r) => (
              <tr key={r.id}>
                <td className="mono">{r.scheduled_for?.slice(0, 19)}</td>
                <td className="mono">{r.started_at?.slice(0, 19) || "—"}</td>
                <td className="mono">{r.finished_at?.slice(0, 19) || "—"}</td>
                <td>
                  <span className={`badge status-${r.status}`}>{r.status}</span>
                </td>
                <td>{r.attempt}</td>
                <td>
                  {r.work_plan_id ? (
                    <Link to={`/ejecuciones/${r.work_plan_id}`} title="Ver ejecución">
                      {r.work_plan_id.slice(0, 8)}
                    </Link>
                  ) : (
                    "—"
                  )}
                </td>
                <td>{r.cost_reference ?? "—"}</td>
                <td className="cell-truncate" title={r.error}>
                  {r.error || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
