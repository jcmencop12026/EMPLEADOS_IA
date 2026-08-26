import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchAuditLogs, type AuditLog } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";

export function AuditPage() {
  const [rows, setRows] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchAuditLogs()
      .then(setRows)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar auditoría."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Cargando auditoría…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Auditoría</h1>
        <p className="muted">Registro de acciones del sistema</p>
      </header>
      {rows.length === 0 ? (
        <EmptyState title="Sin registros" message="No hay entradas de auditoría." />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Acción</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{new Date(r.created_at).toLocaleString()}</td>
                  <td>{r.action}</td>
                  <td className="cell-truncate" title={r.detail || ""}>{r.detail ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
