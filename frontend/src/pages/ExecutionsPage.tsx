import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, fetchExecutions, type ExecutionItem } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { APPROVAL_STATUS, EXECUTION_STATUS, label } from "../lib/labels";

export function ExecutionsPage() {
  const [items, setItems] = useState<ExecutionItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchExecutions()
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar ejecuciones."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Cargando ejecuciones…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Ejecuciones</h1>
        <p className="muted">Planes de trabajo y resultados</p>
      </header>
      {items.length === 0 ? (
        <EmptyState
          title="Sin ejecuciones"
          message="Las ejecuciones aparecen cuando EIAAX procesa solicitudes de trabajo, empleados IA o automatizaciones autorizadas."
          action={<Link to="/operaciones/solicitud" className="btn primary">Nueva solicitud</Link>}
        />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Solicitud</th>
                <th>Estado</th>
                <th>Confianza</th>
                <th>Aprobación</th>
                <th>Inicio</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="cell-truncate" title={item.request}>
                    {item.request}
                  </td>
                  <td>
                    <span className={`badge status-${item.status}`} title={item.status}>
                      {label(EXECUTION_STATUS, item.status)}
                    </span>
                  </td>
                  <td>{item.confidence != null ? `${(item.confidence * 100).toFixed(0)}%` : "—"}</td>
                  <td>{label(APPROVAL_STATUS, item.approval_status)}</td>
                  <td className="mono">{item.created_at?.slice(0, 19).replace("T", " ")}</td>
                  <td>
                    <Link to={`/ejecuciones/${item.id}`} title="Ver detalle">Detalle</Link>
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
