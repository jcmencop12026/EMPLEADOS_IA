import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { OperationItem, OperationSummary } from "../api";
import { cancelOperation, fetchOperationsCenter, fetchOperationsSummary } from "../api";

const BUCKETS: Array<{ key: keyof OperationSummary; label: string }> = [
  { key: "running", label: "En ejecución" },
  { key: "pending", label: "Pendientes" },
  { key: "approval", label: "Requieren aprobación" },
  { key: "due_soon", label: "Próximos a vencer" },
  { key: "overdue", label: "Vencidos" },
  { key: "error", label: "Con error" },
];

export function OperationsHubPage() {
  const [rows, setRows] = useState<OperationItem[]>([]);
  const [summary, setSummary] = useState<OperationSummary | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [prioridad, setPrioridad] = useState("");
  const [vencimientoFiltro, setVencimientoFiltro] = useState("");
  const [orden, setOrden] = useState("");
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
      if (prioridad) params.set("prioridad", prioridad);
      if (vencimientoFiltro) params.set("vencimiento_filtro", vencimientoFiltro);
      if (orden) params.set("orden", orden);
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
        <select value={prioridad} onChange={(e) => setPrioridad(e.target.value)} aria-label="Filtrar prioridad">
          <option value="">Todas las prioridades</option>
          <option value="BAJA">Baja</option>
          <option value="MEDIA">Media</option>
          <option value="ALTA">Alta</option>
          <option value="CRITICA">Crítica</option>
        </select>
        <select
          value={vencimientoFiltro}
          onChange={(e) => setVencimientoFiltro(e.target.value)}
          aria-label="Filtrar vencimiento"
        >
          <option value="">Todo vencimiento</option>
          <option value="sin_vencimiento">Sin vencimiento</option>
          <option value="vencido">Vencido</option>
          <option value="vence_hoy">Vence hoy</option>
          <option value="proximo">Próximo a vencer</option>
        </select>
        <select value={orden} onChange={(e) => setOrden(e.target.value)} aria-label="Ordenar">
          <option value="">Más recientes</option>
          <option value="prioridad">Prioridad</option>
          <option value="vencimiento">Vencimiento</option>
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
              <th>Prioridad</th>
              <th>Estado</th>
              <th>Vencimiento</th>
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
                  <span className={`badge priority-${row.prioridad_codigo}`} title={row.prioridad}>
                    {row.prioridad}
                  </span>
                </td>
                <td>
                  <span className={`badge status-${row.estado_codigo}`}>{row.estado}</span>
                </td>
                <td>
                  <span className={`badge due-${row.vencimiento_codigo}`} title={row.vencimiento_estado}>
                    {row.vencimiento ? new Date(row.vencimiento).toLocaleString() : row.vencimiento_estado}
                  </span>
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
