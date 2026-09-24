import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, fetchDashboardSummary, type DashboardSummary } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { EVENT_TYPE, formatAuditAction, label } from "../lib/labels";

export function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchDashboardSummary()
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar el panel."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Cargando panel…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <EmptyState title="Panel vacío" message="No hay datos disponibles para mostrar." />;

  const cards = [
    { label: "Empleados IA", value: data.employees_total, to: "/directorio" },
    { label: "Empleados activos", value: data.employees_active, to: "/directorio" },
    { label: "Ejecuciones", value: data.executions_total, to: "/ejecuciones" },
    { label: "En curso", value: data.executions_running, to: "/ejecuciones" },
    { label: "Fallidas", value: data.executions_failed, to: "/ejecuciones" },
    { label: "Aprobaciones pendientes", value: data.approvals_pending, to: "/aprobaciones" },
  ];

  return (
    <div className="ops-page dashboard-page">
      <header className="page-header">
        <h1>Panel de control</h1>
        <p className="muted">Resumen operativo · datos en tiempo real</p>
      </header>

      <div className="dashboard-grid">
        {cards.map((card) => (
          <Link key={card.label} to={card.to} className="dashboard-card panel" title={card.label}>
            <span className="dashboard-card-value">{card.value}</span>
            <span className="dashboard-card-label">{card.label}</span>
          </Link>
        ))}
      </div>

      <div className="dashboard-panels">
        <section className="panel">
          <h2>Actividad reciente</h2>
          {data.recent_events.length === 0 ? (
            <EmptyState title="Sin eventos" message="Aún no hay actividad registrada." />
          ) : (
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Evento</th>
                  <th>Plan</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_events.map((ev) => (
                  <tr key={ev.id}>
                    <td className="mono">{new Date(ev.created_at).toLocaleString()}</td>
                    <td>{label(EVENT_TYPE, ev.event_type)}</td>
                    <td>
                      {ev.work_plan_id ? (
                        <Link to={`/ejecuciones/${ev.work_plan_id}`}>{ev.work_plan_id.slice(0, 8)}…</Link>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="panel">
          <h2>Auditoría reciente</h2>
          {data.recent_audit.length === 0 ? (
            <EmptyState title="Sin registros" message="No hay entradas de auditoría recientes." />
          ) : (
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Acción</th>
                  <th>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_audit.map((row) => (
                  <tr key={row.id}>
                    <td className="mono">{new Date(row.created_at).toLocaleString()}</td>
                    <td>{formatAuditAction(row.action)}</td>
                    <td className="cell-truncate" title={row.detail || ""}>{row.detail || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <Link className="btn link" to="/auditoria">Ver auditoría completa</Link>
        </section>
      </div>
    </div>
  );
}
