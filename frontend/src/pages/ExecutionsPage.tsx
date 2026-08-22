import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { ExecutionItem } from "../api";
import { fetchExecutions } from "../api";

const STATUS_LABEL: Record<string, string> = {
  COMPLETED: "Completado",
  WAITING_APPROVAL: "Esperando aprobación",
  RUNNING: "En ejecución",
  FAILED: "Fallido",
  READY: "Listo",
};

export function ExecutionsPage() {
  const [items, setItems] = useState<ExecutionItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchExecutions()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Ejecuciones</h1>
        <p className="muted">Planes de trabajo y resultados</p>
      </header>
      {error && <p className="error">{error}</p>}
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
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">
                  Sin ejecuciones aún.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id}>
                <td className="cell-truncate" title={item.request}>
                  {item.request}
                </td>
                <td>
                  <span className={`badge status-${item.status}`}>
                    {STATUS_LABEL[item.status] || item.status}
                  </span>
                </td>
                <td>{item.confidence != null ? `${(item.confidence * 100).toFixed(0)}%` : "—"}</td>
                <td>{item.approval_status}</td>
                <td className="mono">{item.created_at?.slice(0, 19)}</td>
                <td>
                  <Link to={`/ejecuciones/${item.id}`}>Detalle</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
