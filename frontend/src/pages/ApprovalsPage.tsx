import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, decideApproval, fetchApprovals, type ApprovalItem } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";

export function ApprovalsPage() {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchApprovals()
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar aprobaciones."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function decide(id: string, decision: "approve" | "reject") {
    setActing(id);
    try {
      await decideApproval(id, decision);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo procesar la decisión.");
    } finally {
      setActing(null);
    }
  }

  if (loading) return <LoadingState message="Cargando aprobaciones…" />;
  if (error && items.length === 0) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Aprobaciones pendientes</h1>
        <p className="muted">Solicitudes que requieren revisión humana</p>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      {items.length === 0 ? (
        <EmptyState title="Sin pendientes" message="No hay aprobaciones esperando decisión." />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Acción</th>
                <th>Empleado</th>
                <th>Motivo</th>
                <th>Fecha</th>
                <th>Plan</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.action}</td>
                  <td>{item.employee_name || "—"}</td>
                  <td className="cell-truncate" title={item.reason}>{item.reason}</td>
                  <td className="mono">{new Date(item.created_at).toLocaleString()}</td>
                  <td>
                    <Link to={`/ejecuciones/${item.work_plan_id}`}>Ver ejecución</Link>
                  </td>
                  <td className="notification-actions">
                    <button type="button" className="btn" disabled={acting === item.id} onClick={() => decide(item.id, "approve")} title="Aprobar">
                      ✓
                    </button>
                    <button type="button" className="btn" disabled={acting === item.id} onClick={() => decide(item.id, "reject")} title="Rechazar">
                      ×
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
