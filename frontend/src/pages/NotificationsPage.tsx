import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchNotifications, NotificationItem, transitionNotification } from "../api";

function sourcePath(item: NotificationItem) {
  if (item.type === "APPROVAL_REQUIRED" && item.source_id && item.metadata?.approval_id) {
    return `/ejecuciones/${item.source_id}?approval=${encodeURIComponent(String(item.metadata.approval_id))}`;
  }
  if (!item.source_id) return null;
  if (item.source_type === "work_plan") return `/ejecuciones/${item.source_id}`;
  if (item.source_type === "employee") return `/empleados/${item.source_id}`;
  return null;
}

export function NotificationsPage() {
  const [rows, setRows] = useState<NotificationItem[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [type, setType] = useState("");
  const [date, setDate] = useState("");
  const [sortAsc, setSortAsc] = useState(false);
  const [error, setError] = useState("");
  const load = () => fetchNotifications().then(setRows).catch((e) => setError(String(e)));
  useEffect(load, []);
  const filtered = useMemo(() => rows.filter((row) =>
    (!search || `${row.title} ${row.message}`.toLowerCase().includes(search.toLowerCase())) &&
    (!status || row.status === status) && (!severity || row.severity === severity) &&
    (!type || row.type === type) && (!date || row.created_at.slice(0, 10) === date)
  ).sort((a, b) => (sortAsc ? 1 : -1) * a.created_at.localeCompare(b.created_at)), [rows, search, status, severity, type, date, sortAsc]);
  const act = async (id: string, action: "read" | "acknowledge" | "dismiss") => {
    await transitionNotification(id, action); await load(); window.dispatchEvent(new Event("notifications-changed"));
  };
  return <div className="ops-page notifications-page">
    <div className="page-header"><h1>Centro de notificaciones</h1><div className="muted">Alertas operativas y solicitudes que requieren atención.</div></div>
    <div className="notification-filters panel">
      <input aria-label="Buscar" placeholder="Buscar" value={search} onChange={(e) => setSearch(e.target.value)} />
      <select aria-label="Estado" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Estado</option>{["NEW","READ","ACKNOWLEDGED","DISMISSED"].map(x=><option key={x}>{x}</option>)}</select>
      <select aria-label="Severidad" value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="">Severidad</option>{["LOW","MEDIUM","HIGH","CRITICAL"].map(x=><option key={x}>{x}</option>)}</select>
      <select aria-label="Tipo" value={type} onChange={(e) => setType(e.target.value)}><option value="">Tipo</option>{[...new Set(rows.map(r=>r.type))].map(x=><option key={x}>{x}</option>)}</select>
      <input aria-label="Fecha" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <button className="btn" title="Ordenar por fecha" onClick={() => setSortAsc(!sortAsc)}>↕ Fecha</button>
    </div>
    {error && <p className="error">{error}</p>}
    <div className="notification-grid-wrap"><table className="grid notification-grid"><thead><tr><th>Fecha</th><th>Severidad</th><th>Tipo</th><th>Título</th><th>Origen</th><th>Estado</th><th>Destinatario</th><th>Acciones</th></tr></thead>
      <tbody>{filtered.map(row => <tr key={row.id} className={row.status === "NEW" ? "notification-new" : ""}>
        <td>{new Date(row.created_at).toLocaleString()}</td><td><span className={`severity severity-${row.severity.toLowerCase()}`}>{row.severity}</span></td><td>{row.type}</td>
        <td title={row.message}><strong>{row.title}</strong><div className="muted notification-message">{row.message}</div></td><td>{row.source_type}</td><td>{row.status}</td><td>{row.recipient_user_id || row.recipient_role || "Todos"}</td>
        <td className="notification-actions">
          <button title="Marcar leído" onClick={() => act(row.id,"read")}>✓</button><button title="Acknowledge" onClick={() => act(row.id,"acknowledge")}>◎</button><button title="Descartar" onClick={() => act(row.id,"dismiss")}>×</button>
          {sourcePath(row) && <Link title="Ir al origen" to={sourcePath(row)!}>↗</Link>}
        </td></tr>)}</tbody></table></div>
  </div>;
}
