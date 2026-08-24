import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { AutomationItem } from "../api";
import {
  activateAutomation,
  fetchAutomations,
  pauseAutomation,
  runAutomationNow,
} from "../api";

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Borrador",
  ACTIVE: "Activa",
  PAUSED: "Pausada",
  DISABLED: "Desactivada",
  ERROR: "Error",
};

export function AutomationsPage() {
  const [items, setItems] = useState<AutomationItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  const load = () =>
    fetchAutomations()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));

  useEffect(() => {
    load();
  }, []);

  const filtered = items.filter((a) =>
    !filter || a.name.toLowerCase().includes(filter.toLowerCase()) || a.status === filter,
  );

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Automatizaciones</h1>
        <p className="muted">Programador de trabajos · Orquestador</p>
      </header>
      <div className="ops-actions">
        <Link className="btn primary" to="/automatizaciones/nueva" title="Crear automatización">
          + Crear
        </Link>
        <input
          placeholder="Buscar nombre"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          title="Buscar"
        />
        <select value={filter} onChange={(e) => setFilter(e.target.value)} title="Filtrar estado">
          <option value="">Todos</option>
          <option value="ACTIVE">ACTIVE</option>
          <option value="DRAFT">DRAFT</option>
          <option value="PAUSED">PAUSED</option>
        </select>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="panel table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Trigger</th>
              <th>Frecuencia</th>
              <th>Última</th>
              <th>Próxima</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">
                  Sin automatizaciones.
                </td>
              </tr>
            )}
            {filtered.map((a) => (
              <tr key={a.id}>
                <td className="cell-truncate" title={a.name}>
                  {a.name}
                </td>
                <td>
                  <span className={`badge status-${a.status}`}>{STATUS_LABEL[a.status] || a.status}</span>
                </td>
                <td>{a.trigger_type}</td>
                <td>{a.schedule_type || "—"}</td>
                <td className="mono">{a.last_run_at?.slice(0, 19) || "—"}</td>
                <td className="mono">{a.next_run_at?.slice(0, 19) || "—"}</td>
                <td className="actions-cell">
                  <button type="button" className="btn-icon" title="Ejecutar ahora" onClick={() => runAutomationNow(a.id).then(load)}>
                    ▶
                  </button>
                  {a.status !== "ACTIVE" ? (
                    <button type="button" className="btn-icon" title="Activar" onClick={() => activateAutomation(a.id).then(load)}>
                      ✓
                    </button>
                  ) : (
                    <button type="button" className="btn-icon" title="Pausar" onClick={() => pauseAutomation(a.id).then(load)}>
                      ⏸
                    </button>
                  )}
                  <Link to={`/automatizaciones/${a.id}/ejecuciones`} title="Historial">
                    ⧉
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
