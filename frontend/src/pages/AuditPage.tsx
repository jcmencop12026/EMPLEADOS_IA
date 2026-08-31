import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchAuditLogs, type AuditLog } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { formatAuditAction } from "../lib/labels";

export function AuditPage() {
  const [rows, setRows] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtroAccion, setFiltroAccion] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const q = filtroAccion ? `?accion=${encodeURIComponent(filtroAccion)}&limit=100` : "?limit=100";
    fetchAuditLogs(q)
      .then(setRows)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar auditoría."))
      .finally(() => setLoading(false));
  }, [filtroAccion]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Cargando auditoría…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Auditoría</h1>
        <p className="muted">Registro de acciones del sistema — consulta en español</p>
      </header>

      <div className="card" style={{ marginBottom: "1rem", padding: "0.75rem 1rem" }}>
        <label>
          Filtrar por acción{" "}
          <input
            type="text"
            value={filtroAccion}
            onChange={(e) => setFiltroAccion(e.target.value)}
            placeholder="ej. gobierno, evaluacion, seguridad"
            style={{ marginLeft: "0.5rem", minWidth: 240 }}
          />
        </label>
        <button type="button" className="btn btn-secondary" style={{ marginLeft: "0.5rem" }} onClick={load}>
          Buscar
        </button>
      </div>

      {rows.length === 0 ? (
        <EmptyState title="Sin registros" message="No hay entradas de auditoría para los filtros aplicados." />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Acción</th>
                <th>Usuario</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{new Date(r.created_at).toLocaleString()}</td>
                  <td>{r.accion_etiqueta || formatAuditAction(r.action)}</td>
                  <td>{r.usuario ?? "—"}</td>
                  <td className="cell-truncate" title={r.detail || ""}>
                    {r.detail ?? "—"}
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
