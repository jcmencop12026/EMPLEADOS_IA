import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchSecuritySummary, type SecuritySummary } from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";

export function AdminSecurityPage() {
  const [data, setData] = useState<SecuritySummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    fetchSecuritySummary()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar seguridad"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Cargando panel de seguridad…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Seguridad</h1>
        <p className="muted">Resumen administrativo del tenant</p>
      </header>
      <div className="dashboard-grid">
        <div className="panel dashboard-card"><span className="dashboard-card-value">{data.users_active}</span><span className="dashboard-card-label">Usuarios activos</span></div>
        <div className="panel dashboard-card"><span className="dashboard-card-value">{data.users_inactive}</span><span className="dashboard-card-label">Usuarios inactivos</span></div>
        <div className="panel dashboard-card"><span className="dashboard-card-value">{data.users_blocked}</span><span className="dashboard-card-label">Usuarios bloqueados</span></div>
        <div className="panel dashboard-card"><span className="dashboard-card-value">{data.roles_total}</span><span className="dashboard-card-label">Roles</span></div>
      </div>
      <section className="panel">
        <h2>Eventos administrativos recientes</h2>
        <table className="data-table">
          <thead><tr><th>Fecha</th><th>Acción</th><th>Detalle</th></tr></thead>
          <tbody>
            {data.recent_events.map((ev, i) => (
              <tr key={`${ev.action}-${i}`}>
                <td className="mono">{new Date(ev.created_at).toLocaleString()}</td>
                <td>{ev.action}</td>
                <td className="cell-truncate">{ev.detail || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
