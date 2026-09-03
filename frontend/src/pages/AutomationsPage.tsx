import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { AutomationItem } from "../api";
import {
  activateAutomation,
  deleteAutomation,
  disableAutomation,
  duplicateAutomation,
  fetchAutomations,
  pauseAutomation,
  runAutomationNow,
} from "../api";
import { EmptyState } from "../components/AsyncState";

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Borrador",
  ACTIVE: "Activa",
  PAUSED: "Pausada",
  DISABLED: "Desactivada",
  ERROR: "Error",
};

const TRIGGER_LABEL: Record<string, string> = {
  SCHEDULE: "Programado",
  MANUAL: "Manual",
  INTERNAL_EVENT: "Evento interno",
};

export function AutomationsPage() {
  const [items, setItems] = useState<AutomationItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const load = () =>
    fetchAutomations()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"));

  useEffect(() => {
    load();
  }, []);

  const filtered = items.filter((a) => {
    if (statusFilter && a.status !== statusFilter) return false;
    if (filter && !a.name.toLowerCase().includes(filter.toLowerCase())) return false;
    return true;
  });

  async function handleDelete(id: string, name: string) {
    if (!window.confirm(`¿Eliminar automatización "${name}"?`)) return;
    try {
      await deleteAutomation(id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo eliminar");
    }
  }

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
        <input placeholder="Buscar nombre" value={filter} onChange={(e) => setFilter(e.target.value)} title="Buscar" />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} title="Filtrar estado">
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_LABEL).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {filtered.length === 0 && items.length === 0 ? (
        <EmptyState
          title="Sin automatizaciones"
          message="EIAAX puede proponer automatizaciones desde diagnóstico, oportunidades o solución IA. También puede crearlas manualmente cuando corresponda."
          action={<Link to="/automatizaciones/nueva" className="btn primary">Crear automatización</Link>}
        />
      ) : (
      <div className="panel table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Disparador</th>
              <th>Frecuencia</th>
              <th>Última</th>
              <th>Próxima</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr><td colSpan={7} className="muted">Sin automatizaciones.</td></tr>
            )}
            {filtered.map((a) => (
              <tr key={a.id}>
                <td className="cell-truncate" title={a.name}>{a.name}</td>
                <td><span className={`badge status-${a.status}`}>{STATUS_LABEL[a.status] || a.status}</span></td>
                <td>{TRIGGER_LABEL[a.trigger_type] || a.trigger_type}</td>
                <td>{a.schedule_type || "—"}</td>
                <td className="mono">{a.last_run_at?.slice(0, 19) || "—"}</td>
                <td className="mono">{a.next_run_at?.slice(0, 19) || "—"}</td>
                <td className="actions-cell">
                  <button type="button" className="btn-icon" title="Ejecutar ahora" onClick={() => runAutomationNow(a.id).then(load).catch((e) => setError(e.message))}>▶</button>
                  <Link className="btn-icon" to={`/automatizaciones/${a.id}/editar`} title="Editar">✎</Link>
                  <button type="button" className="btn-icon" title="Duplicar" onClick={() => duplicateAutomation(a.id).then(load)}>⧉</button>
                  {a.status !== "ACTIVE" ? (
                    <button type="button" className="btn-icon" title="Activar" onClick={() => activateAutomation(a.id).then(load)}>✓</button>
                  ) : (
                    <button type="button" className="btn-icon" title="Pausar" onClick={() => pauseAutomation(a.id).then(load)}>⏸</button>
                  )}
                  {a.status !== "DISABLED" && (
                    <button type="button" className="btn-icon" title="Desactivar" onClick={() => disableAutomation(a.id).then(load)}>⊘</button>
                  )}
                  <Link to={`/automatizaciones/${a.id}/ejecuciones`} title="Historial">📋</Link>
                  {a.status === "DRAFT" && (
                    <button type="button" className="btn-icon" title="Eliminar" onClick={() => handleDelete(a.id, a.name)}>×</button>
                  )}
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
