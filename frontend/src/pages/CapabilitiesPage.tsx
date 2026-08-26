import { useEffect, useState } from "react";
import type { CatalogItem } from "../api";
import {
  createCapability,
  fetchCapabilitiesCatalog,
  setCapabilityStatus,
  updateCapability,
} from "../api";

export function CapabilitiesPage() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", code: "", category: "", description: "", risk_level: "LOW" });

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchCapabilitiesCatalog(search || undefined));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar las capacidades");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createCapability(form);
      setShowForm(false);
      setForm({ name: "", code: "", category: "", description: "", risk_level: "LOW" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear");
    }
  }

  async function toggleStatus(item: CatalogItem) {
    try {
      await setCapabilityStatus(item.id, item.status !== "ACTIVA");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cambiar estado");
    }
  }

  const filtered = items.filter((i) => !statusFilter || i.status === statusFilter);

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Capacidades</h1>
        <p className="muted">Catálogo de competencias funcionales asignables a Empleados IA</p>
      </header>
      <div className="ops-actions">
        <input placeholder="Buscar…" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} title="Estado">
          <option value="">Todos</option>
          <option value="ACTIVA">Activa</option>
          <option value="INACTIVA">Inactiva</option>
        </select>
        <button type="button" className="btn" onClick={load}>Buscar</button>
        <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>+ Nueva</button>
      </div>
      {showForm && (
        <form className="panel form-grid" onSubmit={handleCreate}>
          <input required placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input placeholder="Código (opcional)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <input placeholder="Categoría" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          <select value={form.risk_level} onChange={(e) => setForm({ ...form, risk_level: e.target.value })}>
            <option value="LOW">Bajo</option>
            <option value="MEDIUM">Medio</option>
            <option value="HIGH">Alto</option>
            <option value="CRITICAL">Crítico</option>
          </select>
          <textarea placeholder="Descripción" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <button type="submit" className="btn primary">Guardar</button>
        </form>
      )}
      {loading && <p className="muted">Cargando…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && filtered.length === 0 && <p className="muted">Sin capacidades registradas.</p>}
      {!loading && filtered.length > 0 && (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr><th>Código</th><th>Nombre</th><th>Categoría</th><th>Riesgo</th><th>Estado</th><th>Acciones</th></tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td className="mono">{item.code}</td>
                  <td>{item.name}</td>
                  <td>{item.category || "—"}</td>
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
