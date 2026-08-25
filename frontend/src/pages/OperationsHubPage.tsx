import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { OperationItem, OperationSummary } from "../api";
import { cancelOperation, fetchOperationsCenter, fetchOperationsSummary } from "../api";

const BUCKETS: Array<{ key: keyof OperationSummary; label: string }> = [
  { key: "running", label: "En ejecución" },
  { key: "pending", label: "Pendientes" },
  { key: "approval", label: "Esperando aprobación" },
  { key: "error", label: "Con error" },
  { key: "overdue", label: "Vencidos" },
];

export function OperationsHubPage() {
  const [rows, setRows] = useState<OperationItem[]>([]);
  const [summary, setSummary] = useState<OperationSummary | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [bucket, setBucket] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (activeBucket = bucket) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (status) params.set("status", status);
      if (activeBucket) params.set("bucket", activeBucket);
      const [items, stats] = await Promise.all([
        fetchOperationsCenter(params.toString()),
        fetchOperationsSummary(),
      ]);
      setRows(items);
      setSummary(stats);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const filtered = useMemo(() => rows, [rows]);

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Operaciones</h1>
        <p className="muted">Supervisión de trabajos, ejecuciones y aprobaciones de la plataforma.</p>
      </header>

      <div className="ops-actions">
        <Link className="btn primary" to="/operaciones/solicitud" title="Nueva solicitud de trabajo">
          + Nueva solicitud
        </Link>
        <input
          placeholder="Buscar trabajo o proceso"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Buscar"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filtrar estado">
          <option value="">Todos los estados</option>
          <option value="CREATED">Pendiente</option>
          <option value="RUNNING">En ejecución</option>
          <option value="WAITING_APPROVAL">Esperando aprobación</option>
          <option value="COMPLETED">Completado</option>
          <option value="FAILED">Fallido</option>
          <option value="CANCELLED">Cancelado</option>
        </select>
        <button type="button" className="btn" title="Aplicar filtros" onClick={() => void load()}>
          Filtrar
        </button>
      </div>

      {summary && (
        <div className="panel ops-indicators">
          {BUCKETS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`indicator ${bucket === item.key ? "active" : ""}`}
              title={`Filtrar: ${item.label}`}
              onClick={() => {
                const next = bucket === item.key ? "" : item.key;
                setBucket(next);
                void load(next);
              }}
            >
              <strong>{summary[item.key]}</strong>
              <span className="muted">{item.label}</span>
            </button>
          ))}
        </div>
      )}

      {loading && <p className="muted">Cargando operaciones…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && filtered.length === 0 && (
        <p className="muted">No hay operaciones para los filtros seleccionados.</p>
      )}

      <div className="panel table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Trabajo</th>
              <th>Proceso</th>
              <th>Responsable</th>
              <th>Empleado IA</th>
              <th>Estado</th>
              <th>Progreso</th>
              <th>Aprobaciones</th>
              <th>Inicio</th>
              <th>Última actividad</th>
              <th>Resultado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id}>
                <td className="cell-truncate" title={row.trabajo}>
                  {row.trabajo}
                </td>
                <td>{row.proceso || "—"}</td>
                <td>{row.responsable || "—"}</td>
                <td>{row.empleado_ia || "—"}</td>
                <td>
                  <span className={`badge status-${row.estado_codigo}`}>{row.estado}</span>
                </td>
                <td>{row.progreso}</td>
                <td>{row.aprobaciones_pendientes}</td>
                <td>{row.inicio ? new Date(row.inicio).toLocaleString() : "—"}</td>
                <td>{row.ultima_actividad ? new Date(row.ultima_actividad).toLocaleString() : "—"}</td>
                <td className="cell-truncate" title={row.resultado || ""}>
                  {row.resultado || "—"}
                </td>
                <td className="notification-actions">
                  <Link to={`/operaciones/${row.id}`} title="Ver detalle">
                    👁
                  </Link>
                  {row.acciones.includes("cancelar") && (
                    <button type="button" title="Cancelar" onClick={() => void cancelOperation(row.id).then(() => load())}>
                      ×
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
