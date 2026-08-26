import { useEffect, useState } from "react";
import type { CatalogItem } from "../api";
import {
  createTool,
  fetchCapabilitiesCatalog,
  fetchToolsCatalog,
  setToolStatus,
} from "../api";

export function ToolsPage() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [caps, setCaps] = useState<CatalogItem[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", code: "", capability_id: "", tool_type: "PYTHON", risk_level: "LOW", requires_approval: false,
  });

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [tools, capabilities] = await Promise.all([
        fetchToolsCatalog(search || undefined),
        fetchCapabilitiesCatalog(),
      ]);
      setItems(tools);
      setCaps(capabilities.filter((c) => c.status === "ACTIVA"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar las herramientas");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createTool(form);
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear");
    }
  }

  async function toggleStatus(item: CatalogItem) {
    try {
      await setToolStatus(item.id, item.status !== "ACTIVA");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cambiar estado");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Herramientas</h1>
        <p className="muted">Capacidades ejecutables que un Empleado IA puede invocar</p>
      </header>
      <div className="ops-actions">
        <input placeholder="Buscar…" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
        <button type="button" className="btn" onClick={load}>Buscar</button>
        <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>+ Nueva</button>
      </div>
      {showForm && (
        <form className="panel form-grid" onSubmit={handleCreate}>
          <input required placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input placeholder="Código (opcional)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <select required value={form.capability_id} onChange={(e) => setForm({ ...form, capability_id: e.target.value })}>
            <option value="">Capacidad…</option>
            {caps.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select value={form.tool_type} onChange={(e) => setForm({ ...form, tool_type: e.target.value })}>
            <option value="PYTHON">Procesamiento interno</option>
            <option value="RULE">Regla</option>
            <option value="TOOL">Herramienta</option>
            <option value="SQL">Consulta datos</option>
          </select>
          <select value={form.risk_level} onChange={(e) => setForm({ ...form, risk_level: e.target.value })}>
            <option value="LOW">Bajo</option>
            <option value="MEDIUM">Medio</option>
            <option value="HIGH">Alto</option>
            <option value="CRITICAL">Crítico</option>
          </select>
          <label><input type="checkbox" checked={form.requires_approval} onChange={(e) => setForm({ ...form, requires_approval: e.target.checked })} /> Requiere aprobación</label>
          <button type="submit" className="btn primary">Guardar</button>
        </form>
      )}
      {loading && <p className="muted">Cargando…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && items.length === 0 && <p className="muted">Sin herramientas registradas.</p>}
      {!loading && items.length > 0 && (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr><th>Código</th><th>Nombre</th><th>Tipo</th><th>Riesgo</th><th>Estado</th><th>Acciones</th></tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="mono">{item.code}</td>
                  <td>{item.name}</td>
                  <td>{item.tool_type || "—"}</td>
                  <td>{item.risk_level}</td>
                  <td><span className="badge">{item.status}</span></td>
                  <td>
                    <button type="button" className="btn-link" onClick={() => toggleStatus(item)}>
                      {item.status === "ACTIVA" ? "Desactivar" : "Activar"}
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
